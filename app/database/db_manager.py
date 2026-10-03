from core.i18n import tx
import sqlite3
import os
import sys
from datetime import datetime

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class DatabaseManager:

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.environ.get('EMAIL_MANAGER_DATA_FILE')
        if db_path is None:
            base_dir = get_app_dir()
            db_path = os.path.join(base_dir, 'data', 'emails.db')
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("\n            CREATE TABLE IF NOT EXISTS accounts (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                email TEXT UNIQUE NOT NULL,\n                password TEXT NOT NULL,\n                group_name TEXT DEFAULT 'Default',\n                status TEXT DEFAULT 'Unchecked',\n                account_type TEXT DEFAULT 'Standard',\n                imap_server TEXT,\n                imap_port INTEGER DEFAULT 993,\n                smtp_server TEXT,\n                smtp_port INTEGER DEFAULT 465,\n                client_id TEXT,\n                refresh_token TEXT,\n                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                last_check TIMESTAMP\n            )\n        ")
        cursor.execute('PRAGMA table_info(accounts)')
        columns = [col[1] for col in cursor.fetchall()]
        if 'client_id' not in columns:
            cursor.execute('ALTER TABLE accounts ADD COLUMN client_id TEXT')
        if 'refresh_token' not in columns:
            cursor.execute('ALTER TABLE accounts ADD COLUMN refresh_token TEXT')
        if 'has_aws_code' not in columns:
            cursor.execute('ALTER TABLE accounts ADD COLUMN has_aws_code INTEGER DEFAULT 0')
        if 'remark' not in columns:
            cursor.execute('ALTER TABLE accounts ADD COLUMN remark TEXT')
        cursor.execute('\n            CREATE TABLE IF NOT EXISTS settings (\n                key TEXT PRIMARY KEY,\n                value TEXT\n            )\n        ')
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('font_size', '13')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('language', 'ru')")
        cursor.execute('\n            CREATE TABLE IF NOT EXISTS groups (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                name TEXT UNIQUE NOT NULL,\n                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n            )\n        ')
        cursor.execute("\n            CREATE TABLE IF NOT EXISTS emails (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                account_id INTEGER,\n                uid TEXT,\n                sender TEXT,\n                subject TEXT,\n                date TIMESTAMP,\n                body TEXT,\n                is_read INTEGER DEFAULT 0,\n                folder TEXT DEFAULT 'INBOX',\n                FOREIGN KEY (account_id) REFERENCES accounts(id)\n            )\n        ")
        self._migrate_localization(cursor)
        cursor.execute("INSERT OR IGNORE INTO groups (name) VALUES ('Default')")
        conn.commit()
        conn.close()

    def _migrate_localization(self, cursor):
        """Normalize only built-in legacy values, never credentials or mail content."""
        legacy = {
            '\u6b63\u5e38': 'Normal', '\u5f02\u5e38': 'Error',
            '\u672a\u68c0\u6d4b': 'Unchecked', '\u5c01\u7981': 'Blocked',
            '\u5931\u8d25': 'Failed', '\u9a8c\u8bc1\u4e2d': 'Verifying',
            '\u9a8c\u8bc1': 'Verification',
        }
        for old, new in legacy.items():
            cursor.execute('UPDATE accounts SET status = ? WHERE status = ?', (new, old))
        cursor.execute('UPDATE accounts SET account_type = ? WHERE account_type = ?',
                       ('Standard', '\u666e\u901a'))
        old_group = '\u9ed8\u8ba4\u5206\u7ec4'
        cursor.execute('UPDATE accounts SET group_name = ? WHERE group_name = ?', ('Default', old_group))
        if cursor.execute("SELECT 1 FROM groups WHERE name = 'Default'").fetchone():
            cursor.execute('DELETE FROM groups WHERE name = ?', (old_group,))
        else:
            cursor.execute('UPDATE groups SET name = ? WHERE name = ?', ('Default', old_group))
        cursor.execute("UPDATE settings SET value = 'ru' WHERE key = 'language' AND value NOT IN ('ru', 'en')")

    def add_account(self, email, password, group='Default', imap_server=None, imap_port=993, client_id=None, refresh_token=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if not imap_server:
                (imap_server, smtp_server) = self.detect_server(email)
            else:
                smtp_server = imap_server.replace('imap', 'smtp')
            account_type = 'OAuth2' if client_id and refresh_token else 'Standard'
            cursor.execute('\n                INSERT INTO accounts (email, password, group_name, imap_server, imap_port, \n                                      smtp_server, client_id, refresh_token, account_type)\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ', (email, password, group, imap_server, imap_port, smtp_server, client_id, refresh_token, account_type))
            cursor.execute("UPDATE accounts SET status = 'Unchecked' WHERE id = ?", (cursor.lastrowid,))
            conn.commit()
            return (True, tx('Added successfully'))
        except sqlite3.IntegrityError:
            return (False, tx('Email already exists'))
        finally:
            conn.close()

    def detect_server(self, email):
        domain = email.split('@')[-1].lower()
        servers = {'outlook.com': ('imap-mail.outlook.com', 'smtp-mail.outlook.com'), 'hotmail.com': ('imap-mail.outlook.com', 'smtp-mail.outlook.com'), 'gmail.com': ('imap.gmail.com', 'smtp.gmail.com'), 'qq.com': ('imap.qq.com', 'smtp.qq.com'), '163.com': ('imap.163.com', 'smtp.163.com'), '126.com': ('imap.126.com', 'smtp.126.com'), 'sina.com': ('imap.sina.com', 'smtp.sina.com'), 'yahoo.com': ('imap.mail.yahoo.com', 'smtp.mail.yahoo.com')}
        return servers.get(domain, (f'imap.{domain}', f'smtp.{domain}'))

    def get_all_accounts(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts ORDER BY id DESC')
        accounts = cursor.fetchall()
        conn.close()
        return accounts

    def get_accounts_by_group(self, group_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE group_name = ?', (group_name,))
        accounts = cursor.fetchall()
        conn.close()
        return accounts

    def get_account_by_email(self, email):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE email = ?', (email,))
        account = cursor.fetchone()
        conn.close()
        return account

    def update_account_oauth(self, account_id, client_id, refresh_token):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("\n            UPDATE accounts \n            SET client_id = ?, refresh_token = ?, account_type = 'OAuth2'\n            WHERE id = ?\n        ", (client_id, refresh_token, account_id))
        conn.commit()
        conn.close()

    def update_account_status(self, account_id, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('\n            UPDATE accounts SET status = ?, last_check = ? WHERE id = ?\n        ', (status, datetime.now(), account_id))
        conn.commit()
        conn.close()

    def delete_account(self, account_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
        cursor.execute('DELETE FROM emails WHERE account_id = ?', (account_id,))
        conn.commit()
        conn.close()

    def update_account_group(self, account_id, group_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE accounts SET group_name = ? WHERE id = ?', (group_name, account_id))
        conn.commit()
        conn.close()

    def get_all_groups(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM groups')
        groups = cursor.fetchall()
        conn.close()
        return groups

    def add_group(self, name):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO groups (name) VALUES (?)', (name,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def delete_group(self, name):
        if name == 'Default':
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE accounts SET group_name = ? WHERE group_name = ?', ('Default', name))
        cursor.execute('DELETE FROM groups WHERE name = ?', (name,))
        conn.commit()
        conn.close()
        return True

    def rename_group(self, old_name, new_name):
        if old_name == 'Default':
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE groups SET name = ? WHERE name = ?', (new_name, old_name))
            cursor.execute('UPDATE accounts SET group_name = ? WHERE group_name = ?', (new_name, old_name))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_account_count(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM accounts')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def update_aws_code_status(self, account_id, has_code):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE accounts SET has_aws_code = ? WHERE id = ?', (1 if has_code else 0, account_id))
        conn.commit()
        conn.close()

    def update_account_remark(self, account_id, remark):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE accounts SET remark = ? WHERE id = ?', (remark, account_id))
        conn.commit()
        conn.close()

    def get_setting(self, key, default=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

    def set_setting(self, key, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()

    def get_all_accounts_sorted(self, sort_by='id', sort_order='DESC'):
        conn = self.get_connection()
        cursor = conn.cursor()
        valid_columns = ['id', 'email', 'group_name', 'status', 'account_type', 'has_aws_code']
        if sort_by not in valid_columns:
            sort_by = 'id'
        order = 'DESC' if sort_order.upper() == 'DESC' else 'ASC'
        cursor.execute(f'SELECT * FROM accounts ORDER BY {sort_by} {order}')
        accounts = cursor.fetchall()
        conn.close()
        return accounts

    def get_accounts_by_group_sorted(self, group_name, sort_by='id', sort_order='DESC'):
        conn = self.get_connection()
        cursor = conn.cursor()
        valid_columns = ['id', 'email', 'group_name', 'status', 'account_type', 'has_aws_code']
        if sort_by not in valid_columns:
            sort_by = 'id'
        order = 'DESC' if sort_order.upper() == 'DESC' else 'ASC'
        cursor.execute(f'SELECT * FROM accounts WHERE group_name = ? ORDER BY {sort_by} {order}', (group_name,))
        accounts = cursor.fetchall()
        conn.close()
        return accounts
