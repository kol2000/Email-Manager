from core.i18n import tx
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QTextBrowser, QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QWidget, QFrame, QScrollArea, QCheckBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from core.email_client import EmailClient
import os

def create_email_client(account, db_manager=None):
    return EmailClient(account[1], account[2], account[6], account[7], client_id=account[10] if len(account) > 10 else None, refresh_token=account[11] if len(account) > 11 else None, account_id=account[0], db_manager=db_manager)
DIALOG_STYLE = "\n    QDialog {\n        background-color: #FFFFFF;\n        font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;\n    }\n    QLabel { color: #1A1A1A; font-size: 13px; }\n    QLineEdit, QTextEdit {\n        padding: 10px 12px;\n        border: 1px solid #E0E0E0;\n        border-radius: 4px;\n        background: #FAFAFA;\n        font-size: 13px;\n    }\n    QLineEdit:focus, QTextEdit:focus {\n        border: 2px solid #0078D4;\n        background: #FFFFFF;\n    }\n    QComboBox {\n        padding: 10px 12px;\n        border: 1px solid #E0E0E0;\n        border-radius: 4px;\n        background: #FAFAFA;\n        font-size: 13px;\n        color: #1A1A1A;\n    }\n    QComboBox:hover { border-color: #B0B0B0; }\n    QComboBox::drop-down { border: none; width: 30px; }\n    QComboBox::down-arrow {\n        image: none;\n        border-left: 5px solid transparent;\n        border-right: 5px solid transparent;\n        border-top: 6px solid #666;\n    }\n    QComboBox QAbstractItemView {\n        background: #FFFFFF;\n        border: 1px solid #E0E0E0;\n        selection-background-color: #E5F1FB;\n        selection-color: #0078D4;\n        outline: none;\n    }\n    QComboBox QAbstractItemView::item {\n        padding: 8px 12px;\n        min-height: 32px;\n        color: #1A1A1A;\n    }\n    QComboBox QAbstractItemView::item:hover { background: #F5F5F5; }\n"
BTN_PRIMARY = '\n    QPushButton {\n        background-color: #0078D4; color: white; border: none;\n        padding: 10px 24px; border-radius: 4px; font-size: 14px; font-weight: 500;\n    }\n    QPushButton:hover { background-color: #1084D9; }\n    QPushButton:pressed { background-color: #006CBE; }\n'
BTN_DEFAULT = '\n    QPushButton {\n        background-color: #FFFFFF; color: #1A1A1A; border: 1px solid #D0D0D0;\n        padding: 10px 24px; border-radius: 4px; font-size: 14px;\n    }\n    QPushButton:hover { background-color: #F5F5F5; }\n'
MENU_STYLE_LIGHT = '\n    QMenu {\n        background: #FFFFFF;\n        border: none;\n        border-radius: 12px;\n        padding: 8px 4px;\n    }\n    QMenu::item {\n        padding: 10px 40px 10px 16px;\n        color: #333333;\n        border-radius: 6px;\n        margin: 2px 6px;\n        font-size: 13px;\n    }\n    QMenu::item:selected {\n        background: #F0F0F0;\n        color: #333333;\n    }\n    QMenu::separator {\n        height: 1px;\n        background: #EEEEEE;\n        margin: 6px 16px;\n    }\n'
MENU_STYLE_DARK = '\n    QMenu {\n        background: #21262d;\n        border: none;\n        border-radius: 12px;\n        padding: 8px 4px;\n    }\n    QMenu::item {\n        padding: 10px 40px 10px 16px;\n        color: #c9d1d9;\n        border-radius: 6px;\n        margin: 2px 6px;\n        font-size: 13px;\n    }\n    QMenu::item:selected {\n        background: #30363d;\n        color: #FFFFFF;\n    }\n    QMenu::separator {\n        height: 1px;\n        background: #30363d;\n        margin: 6px 16px;\n    }\n'
MENU_STYLE = MENU_STYLE_LIGHT

class FluentMessageBox(QDialog):
    TYPES = {'success': {'icon': '✓', 'color': '#10B981'}, 'warning': {'icon': '!', 'color': '#F59E0B'}, 'error': {'icon': '✕', 'color': '#EF4444'}, 'info': {'icon': 'i', 'color': '#3B82F6'}, 'question': {'icon': '?', 'color': '#8B5CF6'}}

    def __init__(self, msg_type, title, message, parent=None, show_cancel=False):
        super().__init__(parent)
        self.msg_type = msg_type
        self.show_cancel = show_cancel
        self.result_value = False
        self.setWindowTitle(title)
        self.setFixedSize(300, 180 if not show_cancel else 190)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.init_ui(title, message)

    def init_ui(self, title, message):
        config = self.TYPES.get(self.msg_type, self.TYPES['info'])
        container = QFrame(self)
        container.setGeometry(0, 0, 300, self.height())
        container.setObjectName('container')
        container.setStyleSheet('\n            #container {\n                background: white;\n                border-radius: 12px;\n            }\n        ')
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        container.setGraphicsEffect(shadow)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        icon_label = QLabel(config['icon'])
        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"\n            background: {config['color']};\n            color: white;\n            font-size: 24px;\n            font-weight: bold;\n            border-radius: 25px;\n        ")
        icon_row = QHBoxLayout()
        icon_row.addStretch()
        icon_row.addWidget(icon_label)
        icon_row.addStretch()
        layout.addLayout(icon_row)
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet('font-size: 15px; font-weight: 600; color: #1F2937; background: transparent; border: none;')
        layout.addWidget(title_label)
        msg_label = QLabel(message)
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet('font-size: 13px; color: #6B7280; background: transparent; border: none;')
        layout.addWidget(msg_label)
        layout.addStretch()
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        if self.show_cancel:
            btn_cancel = QPushButton(tx('Cancel'))
            btn_cancel.setFixedSize(80, 32)
            btn_cancel.setCursor(Qt.PointingHandCursor)
            btn_cancel.setStyleSheet('\n                QPushButton {\n                    background: #F3F4F6;\n                    color: #4B5563;\n                    border: none;\n                    border-radius: 6px;\n                    font-size: 13px;\n                }\n                QPushButton:hover { background: #E5E7EB; }\n            ')
            btn_cancel.clicked.connect(self.reject)
            btn_layout.addWidget(btn_cancel)
        btn_ok = QPushButton(tx('OK'))
        btn_ok.setFixedSize(80 if self.show_cancel else 260, 32)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(f"\n            QPushButton {{\n                background: {config['color']};\n                color: white;\n                border: none;\n                border-radius: 6px;\n                font-size: 13px;\n                font-weight: 500;\n            }}\n            QPushButton:hover {{ opacity: 0.9; }}\n        ")
        btn_ok.clicked.connect(self.on_accept)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def on_accept(self):
        self.result_value = True
        self.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if hasattr(self, '_drag_pos'):
            self.move(event.globalPos() - self._drag_pos)

    @staticmethod
    def success(parent, title, message):
        dialog = FluentMessageBox('success', title, message, parent)
        dialog.exec_()

    @staticmethod
    def warning(parent, title, message):
        dialog = FluentMessageBox('warning', title, message, parent)
        dialog.exec_()

    @staticmethod
    def error(parent, title, message):
        dialog = FluentMessageBox('error', title, message, parent)
        dialog.exec_()

    @staticmethod
    def info(parent, title, message):
        dialog = FluentMessageBox('info', title, message, parent)
        dialog.exec_()

    @staticmethod
    def question(parent, title, message):
        dialog = FluentMessageBox('question', title, message, parent, show_cancel=True)
        dialog.exec_()
        return dialog.result_value
SuccessDialog = lambda title, message, parent=None: FluentMessageBox('success', title, message, parent)

class AccountDetailDialog(QDialog):

    def __init__(self, account, theme_manager=None, parent=None):
        super().__init__(parent)
        self.account = account
        self.theme_manager = theme_manager
        self.is_dark = theme_manager.is_dark() if theme_manager else False
        self.setWindowTitle(tx('Account details'))
        self.setMinimumSize(500, 480)
        self.resize(520, 520)
        self._apply_style()
        self.init_ui()

    def _apply_style(self):
        if self.is_dark:
            self.setStyleSheet("\n                QDialog {\n                    background: #161b22;\n                    font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;\n                }\n            ")
        else:
            self.setStyleSheet(DIALOG_STYLE)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        email_icon = QLabel('📧')
        email_icon.setStyleSheet('font-size: 28px;')
        header_layout.addWidget(email_icon)
        email_info = QVBoxLayout()
        email_info.setSpacing(4)
        email_label = QLabel(self.account[1])
        email_color = '#c9d1d9' if self.is_dark else '#1A1A1A'
        email_label.setStyleSheet(f'font-size: 18px; font-weight: 600; color: {email_color};')
        email_info.addWidget(email_label)
        type_status = QLabel(f'{tx(self.account[5])} · {tx(self.account[4])}')
        type_color = '#8b949e' if self.is_dark else '#666666'
        type_status.setStyleSheet(f'font-size: 13px; color: {type_color};')
        email_info.addWidget(type_status)
        header_layout.addLayout(email_info)
        header_layout.addStretch()
        layout.addWidget(header)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line_color = '#30363d' if self.is_dark else '#E0E0E0'
        line.setStyleSheet(f'background-color: {line_color};')
        line.setFixedHeight(1)
        layout.addWidget(line)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        if self.is_dark:
            scroll.setStyleSheet('QScrollArea { background: transparent; }')
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        self._add_section(content_layout, tx('🔐 Basic information'), [(tx('Email address'), self.account[1]), (tx('Password'), self.account[2]), (tx('Group'), tx(self.account[3]) if self.account[3] == 'Default' else self.account[3]), (tx('Status'), tx(self.account[4])), (tx('Type'), tx(self.account[5]))])
        imap_server = self.account[6] if len(self.account) > 6 and self.account[6] else '-'
        imap_port = str(self.account[7]) if len(self.account) > 7 and self.account[7] else '-'
        smtp_server = self.account[8] if len(self.account) > 8 and self.account[8] else '-'
        smtp_port = str(self.account[9]) if len(self.account) > 9 and self.account[9] else '-'
        self._add_section(content_layout, tx('🌐 Server settings'), [(tx('IMAP server'), imap_server), (tx('IMAP port'), imap_port), (tx('SMTP server'), smtp_server), (tx('SMTP port'), smtp_port)])
        client_id = self.account[10] if len(self.account) > 10 and self.account[10] else '-'
        refresh_token = self.account[11] if len(self.account) > 11 and self.account[11] else '-'
        if client_id != '-' or refresh_token != '-':
            self._add_section(content_layout, tx('🔑 OAuth2 credentials'), [('Client ID', client_id), ('Refresh Token', refresh_token if len(refresh_token) <= 50 else refresh_token[:50] + '...')], copyable=True)
        created_at = str(self.account[12]) if len(self.account) > 12 and self.account[12] else '-'
        last_check = str(self.account[13]) if len(self.account) > 13 and self.account[13] else '-'
        has_aws = tx('Yes') if len(self.account) > 14 and self.account[14] else tx('No')
        remark = self.account[15] if len(self.account) > 15 and self.account[15] else '-'
        self._add_section(content_layout, tx('📋 Other information'), [(tx('Created'), created_at), (tx('Last checked'), last_check), (tx('AWS verification code'), has_aws), (tx('Notes'), remark)])
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_copy = QPushButton(tx('Copy all information'))
        if self.is_dark:
            btn_copy.setStyleSheet('\n                QPushButton {\n                    background: #21262d; color: #c9d1d9; border: 1px solid #30363d;\n                    padding: 10px 20px; border-radius: 6px; font-size: 13px;\n                }\n                QPushButton:hover { background: #30363d; }\n            ')
        else:
            btn_copy.setStyleSheet(BTN_DEFAULT)
        btn_copy.clicked.connect(self.copy_all_info)
        btn_layout.addWidget(btn_copy)
        btn_close = QPushButton(tx('Close'))
        if self.is_dark:
            btn_close.setStyleSheet('\n                QPushButton {\n                    background: #238636; color: white; border: none;\n                    padding: 10px 24px; border-radius: 6px; font-size: 13px; font-weight: 500;\n                }\n                QPushButton:hover { background: #2ea043; }\n            ')
        else:
            btn_close.setStyleSheet(BTN_PRIMARY)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _add_section(self, parent_layout, title, items, copyable=False):
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(12)
        title_label = QLabel(title)
        title_color = '#c9d1d9' if self.is_dark else '#1A1A1A'
        title_label.setStyleSheet(f'font-size: 15px; font-weight: 600; color: {title_color}; border: none; background: transparent;')
        section_layout.addWidget(title_label)
        card = QFrame()
        if self.is_dark:
            card.setStyleSheet('\n                QFrame {\n                    background: #0d1117;\n                    border: 1px solid #30363d;\n                    border-radius: 8px;\n                }\n                QFrame QLabel {\n                    border: none;\n                    background: transparent;\n                }\n            ')
        else:
            card.setStyleSheet('\n                QFrame {\n                    background: #FAFAFA;\n                    border: 1px solid #E0E0E0;\n                    border-radius: 8px;\n                }\n                QFrame QLabel {\n                    border: none;\n                    background: transparent;\n                }\n            ')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(10)
        for (label, value) in items:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl_color = '#8b949e' if self.is_dark else '#666666'
            lbl.setStyleSheet(f'color: {lbl_color}; font-size: 13px; min-width: 90px; border: none; background: transparent;')
            row.addWidget(lbl)
            val = QLabel(str(value) if value else '-')
            val_color = '#c9d1d9' if self.is_dark else '#1A1A1A'
            val.setStyleSheet(f'color: {val_color}; font-size: 13px; border: none; background: transparent;')
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            row.addWidget(val, 1)
            if copyable and value and (value != '-'):
                btn_copy = QPushButton(tx('Copy'))
                btn_copy.setFixedSize(50, 26)
                if self.is_dark:
                    btn_copy.setStyleSheet('\n                        QPushButton {\n                            background: #21262d; color: #58a6ff; border: 1px solid #30363d;\n                            border-radius: 4px; font-size: 11px;\n                        }\n                        QPushButton:hover { background: #30363d; }\n                    ')
                else:
                    btn_copy.setStyleSheet('\n                        QPushButton {\n                            background: #FFFFFF; color: #0078D4; border: 1px solid #D0D0D0;\n                            border-radius: 4px; font-size: 11px;\n                        }\n                        QPushButton:hover { background: #E5F1FB; }\n                    ')
                full_value = self.account[10] if label == 'Client ID' else self.account[11] if label == 'Refresh Token' else value
                btn_copy.clicked.connect(lambda checked, v=full_value: self._copy_to_clipboard(v))
                row.addWidget(btn_copy)
            card_layout.addLayout(row)
        section_layout.addWidget(card)
        parent_layout.addWidget(section)

    def _copy_to_clipboard(self, text):
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(str(text))
        QMessageBox.information(self, tx('Notice'), tx('Copied to clipboard'))

    def copy_all_info(self):
        info_lines = [tx('Email address: {0}', self.account[1]), tx('Password: {0}', self.account[2]), tx('Group: {0}', self.account[3]), tx('Status: {0}', self.account[4]), tx('Type: {0}', self.account[5])]
        if len(self.account) > 6 and self.account[6]:
            info_lines.append(tx('IMAP server: {0}', self.account[6]))
        if len(self.account) > 7 and self.account[7]:
            info_lines.append(tx('IMAP port: {0}', self.account[7]))
        if len(self.account) > 10 and self.account[10]:
            info_lines.append(f'Client ID: {self.account[10]}')
        if len(self.account) > 11 and self.account[11]:
            info_lines.append(f'Refresh Token: {self.account[11]}')
        if len(self.account) > 15 and self.account[15]:
            info_lines.append(tx('Notes: {0}', self.account[15]))
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(info_lines))
        QMessageBox.information(self, tx('Notice'), tx('All information copied to clipboard'))

class ImportDialog(QDialog):

    def __init__(self, db, parent=None, default_group=None):
        super().__init__(parent)
        self.db = db
        self.default_group = default_group
        self.setWindowTitle(tx('Import accounts'))
        self.setMinimumSize(720, 540)
        self.resize(760, 560)
        self.setStyleSheet(DIALOG_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        title = QLabel(tx('Import email accounts'))
        title.setStyleSheet('font-size: 20px; font-weight: 600; color: #1A1A1A;')
        layout.addWidget(title)
        info = QLabel(tx('One account per line: email----password----client_id----refresh_token. For password-only accounts: email----password.'))
        info.setStyleSheet('color: #616161; font-size: 13px;')
        info.setWordWrap(True)
        layout.addWidget(info)
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText('example@outlook.com----password----client_id----refresh_token')
        self.text_edit.setMinimumHeight(180)
        layout.addWidget(self.text_edit)
        group_row = QHBoxLayout()
        group_row.addWidget(QLabel(tx('Import into group:')))
        self.group_combo = QComboBox()
        self.group_combo.setMinimumWidth(160)
        current_index = 0
        for (i, group) in enumerate(self.db.get_all_groups()):
            self.group_combo.addItem(tx(group[1]) if group[1] == 'Default' else group[1], group[1])
            if self.default_group and group[1] == self.default_group:
                current_index = i
        self.group_combo.setCurrentIndex(current_index)
        group_row.addWidget(self.group_combo)
        group_row.addStretch()
        btn_file = QPushButton(tx('From file'))
        btn_file.setStyleSheet(BTN_DEFAULT)
        btn_file.clicked.connect(self.import_from_file)
        group_row.addWidget(btn_file)
        btn_clipboard = QPushButton(tx('From clipboard'))
        btn_clipboard.setStyleSheet(BTN_DEFAULT)
        btn_clipboard.clicked.connect(self.import_from_clipboard)
        group_row.addWidget(btn_clipboard)
        layout.addLayout(group_row)
        option_row = QHBoxLayout()
        self.skip_duplicate_cb = QCheckBox(tx('Skip existing email addresses'))
        self.skip_duplicate_cb.setChecked(True)
        self.skip_duplicate_cb.setStyleSheet('color: #616161; font-size: 12px;')
        option_row.addWidget(self.skip_duplicate_cb)
        option_row.addStretch()
        layout.addLayout(option_row)
        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton(tx('Cancel'))
        btn_cancel.setStyleSheet(BTN_DEFAULT)
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton(tx('Import'))
        btn_ok.setStyleSheet(BTN_PRIMARY)
        btn_ok.clicked.connect(self.do_import)
        btn_row.addWidget(btn_cancel)
        btn_row.addSpacing(12)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def import_from_file(self):
        (path, _) = QFileDialog.getOpenFileName(self, tx('Select file'), '', tx('Text files (*.txt);;All files (*.*)'))
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.text_edit.setText(f.read())
            except Exception as e:
                QMessageBox.warning(self, tx('Error'), tx('Read failed: {0}', e))

    def import_from_clipboard(self):
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text and text.strip():
            self.text_edit.setText(text)
        else:
            QMessageBox.warning(self, tx('Notice'), tx('Clipboard is empty or contains no text'))

    def do_import(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, tx('Error'), tx('Enter account information'))
            return
        group = self.group_combo.currentData()
        skip_duplicate = self.skip_duplicate_cb.isChecked()
        (success, fail, skipped) = (0, 0, 0)
        existing_emails = set()
        if skip_duplicate:
            for acc in self.db.get_all_accounts():
                existing_emails.add(acc[1].lower())
        for account_data in self.parse_accounts(text):
            email = account_data.get('email')
            pwd = account_data.get('password')
            client_id = account_data.get('client_id')
            refresh_token = account_data.get('refresh_token')
            if email and pwd and ('@' in email):
                if skip_duplicate and email.lower() in existing_emails:
                    skipped += 1
                    continue
                (ok, _) = self.db.add_account(email, pwd, group, client_id=client_id, refresh_token=refresh_token)
                if ok:
                    success += 1
                    existing_emails.add(email.lower())
                else:
                    fail += 1
            else:
                fail += 1
        result_msg = tx('Successful: {0} | Failed: {1} account(s)', success, fail)
        if skipped > 0:
            result_msg += tx(' | Skipped: {0} account(s)', skipped)
        dialog = SuccessDialog(tx('Import complete'), result_msg, self)
        dialog.exec_()
        if success > 0:
            self.accept()

    def parse_accounts(self, text):
        accounts = []
        text = text.replace('\r\n', '\n').replace('\r', '\n').strip()
        if '$$' in text:
            parts = text.split('$$')
        elif '\n' in text:
            parts = text.split('\n')
        else:
            import re
            parts = re.split('\\$(?=[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,})', text)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            while part.endswith('$'):
                part = part[:-1]
            account_data = {}
            if '----' in part:
                p = part.split('----')
                if len(p) >= 2:
                    account_data['email'] = p[0].strip()
                    account_data['password'] = p[1].strip()
                    if len(p) >= 3 and p[2].strip():
                        account_data['client_id'] = p[2].strip()
                    if len(p) >= 4 and p[3].strip():
                        account_data['refresh_token'] = p[3].strip()
            if account_data and account_data.get('email') and ('@' in account_data.get('email', '')):
                accounts.append(account_data)
        return accounts

class FetchEmailThread(QThread):
    finished = pyqtSignal(list, str)

    def __init__(self, account, folder='inbox', db_manager=None):
        super().__init__()
        self.account = account
        self.folder = folder
        self.db_manager = db_manager

    def run(self):
        client = create_email_client(self.account, self.db_manager)
        (emails, msg) = client.fetch_emails(folder=self.folder, limit=50)
        client.disconnect()
        self.finished.emit(emails, msg)

class EmailViewDialog(QDialog):
    FOLDER_NAMES = {'inbox': 'Inbox', 'junk': 'Junk', 'sent': 'Sent', 'drafts': 'Drafts', 'deleted': 'Deleted'}

    def __init__(self, account, db, parent=None):
        super().__init__(parent)
        self.account = account
        self.db = db
        self.current_folder = 'inbox'
        self.all_emails = []
        self.setWindowTitle(tx('Messages — {0}', account[1]))
        self.setMinimumSize(1000, 650)
        self.setStyleSheet("QDialog { background-color: #F3F3F3; font-family: 'Segoe UI', 'Microsoft YaHei UI'; }")
        self.init_ui()
        self.fetch_emails()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        left_panel = QFrame()
        left_panel.setFixedWidth(390)
        left_panel.setStyleSheet('background: #FFFFFF; border-right: 1px solid #E5E5E5;')
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet('background: #FAFAFA; border-bottom: 1px solid #E5E5E5;')
        toolbar_layout = QVBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(8)
        row1 = QHBoxLayout()
        self.folder_combo = QComboBox()
        self.folder_combo.setStyleSheet('\n            QComboBox {\n                padding: 8px 10px;\n                border: 1px solid #E0E0E0;\n                border-radius: 4px;\n                background: #FAFAFA;\n                font-size: 12px;\n                color: #1A1A1A;\n            }\n            QComboBox:hover { border-color: #B0B0B0; }\n            QComboBox::drop-down { border: none; width: 20px; }\n            QComboBox::down-arrow { image: none; border-left: 4px solid transparent;\n                border-right: 4px solid transparent; border-top: 5px solid #666; }\n            QComboBox QAbstractItemView {\n                background: #FFFFFF;\n                border: 1px solid #E0E0E0;\n                selection-background-color: #E5F1FB;\n                selection-color: #1A1A1A;\n                color: #1A1A1A;\n                outline: none;\n            }\n            QComboBox QAbstractItemView::item {\n                padding: 6px 10px;\n                min-height: 24px;\n                color: #1A1A1A;\n            }\n        ')
        for (key, name) in self.FOLDER_NAMES.items():
            name = tx(name)
            self.folder_combo.addItem(name, key)
        self.folder_combo.currentIndexChanged.connect(self.on_folder_changed)
        row1.addWidget(self.folder_combo)
        self.refresh_btn = QPushButton(tx('Refresh'))
        self.refresh_btn.setStyleSheet('\n            QPushButton {\n                border: 1px solid #E0E0E0;\n                border-radius: 4px;\n                background: #FFFFFF;\n                font-size: 12px;\n                padding: 6px 12px;\n                color: #1A1A1A;\n            }\n            QPushButton:hover { background: #F5F5F5; border-color: #0078D4; }\n        ')
        self.refresh_btn.clicked.connect(self.fetch_emails)
        row1.addWidget(self.refresh_btn)
        row1.addStretch()
        toolbar_layout.addLayout(row1)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tx('Search messages...'))
        self.search_input.setStyleSheet('\n            QLineEdit {\n                padding: 8px 12px;\n                border: 1px solid #E0E0E0;\n                border-radius: 4px;\n                background: #FFFFFF;\n                font-size: 12px;\n            }\n            QLineEdit:focus { border: 2px solid #0078D4; }\n        ')
        self.search_input.textChanged.connect(self.filter_emails)
        toolbar_layout.addWidget(self.search_input)
        from PyQt5.QtWidgets import QGridLayout
        row3 = QGridLayout()
        row3.setSpacing(6)
        toolbar_btn_style = '\n            QPushButton {\n                background-color: #FFFFFF;\n                color: #1A1A1A;\n                border: 1px solid #D0D0D0;\n                padding: 6px 12px;\n                border-radius: 4px;\n                font-size: 11px;\n            }\n            QPushButton:hover { background-color: #F5F5F5; border-color: #0078D4; }\n            QPushButton:disabled { background-color: #F5F5F5; color: #999999; }\n        '
        self.compose_btn = QPushButton(tx('Compose'))
        self.compose_btn.setStyleSheet(toolbar_btn_style)
        self.compose_btn.clicked.connect(self.open_compose_dialog)
        row3.addWidget(self.compose_btn, 0, 0)
        self.reply_btn = QPushButton(tx('Reply'))
        self.reply_btn.setStyleSheet(toolbar_btn_style)
        self.reply_btn.clicked.connect(self.reply_email)
        self.reply_btn.setEnabled(False)
        row3.addWidget(self.reply_btn, 0, 1)
        self.forward_btn = QPushButton(tx('Forward'))
        self.forward_btn.setStyleSheet(toolbar_btn_style)
        self.forward_btn.clicked.connect(self.forward_email)
        self.forward_btn.setEnabled(False)
        row3.addWidget(self.forward_btn, 0, 2)
        self.mark_btn = QPushButton(tx('Mark'))
        self.mark_btn.setStyleSheet(toolbar_btn_style)
        self.mark_btn.clicked.connect(self.toggle_read_status)
        self.mark_btn.setEnabled(False)
        row3.addWidget(self.mark_btn, 1, 0)
        self.delete_btn = QPushButton(tx('Delete'))
        self.delete_btn.setStyleSheet(toolbar_btn_style)
        self.delete_btn.clicked.connect(self.delete_selected_email)
        self.delete_btn.setEnabled(False)
        row3.addWidget(self.delete_btn, 1, 1)
        row3.setColumnStretch(2, 1)
        toolbar_layout.addLayout(row3)
        left_layout.addWidget(toolbar_widget)
        self.loading_label = QLabel(tx('Loading...'))
        self.loading_label.setStyleSheet('padding: 20px; color: #666; font-size: 13px;')
        self.loading_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.loading_label)
        self.email_list = QListWidget()
        self.email_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.email_list.setStyleSheet("\n            QListWidget { \n                background: #FFFFFF; \n                border: none; \n                outline: none;\n                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;\n            }\n            QListWidget::item { \n                padding: 14px 16px; \n                border-bottom: 1px solid #F0F0F0;\n                margin: 0px 8px;\n                color: #1A1A1A;\n            }\n            QListWidget::item:hover { \n                background: #F5F5F5;\n            }\n            QListWidget::item:selected { \n                background: #FFFFFF;\n                color: #1A1A1A;\n                border-left: 3px solid #0078D4;\n            }\n            /* Scrollbar */\n            QScrollBar:vertical {\n                background: #F5F5F5;\n                width: 8px;\n                margin: 0px;\n            }\n            QScrollBar::handle:vertical {\n                background: #C0C0C0;\n                min-height: 30px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background: #A0A0A0;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                height: 0px;\n            }\n            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {\n                background: none;\n            }\n        ")
        self.email_list.itemClicked.connect(self.show_email_content)
        self.email_list.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.email_list)
        layout.addWidget(left_panel)
        right_panel = QWidget()
        right_panel.setStyleSheet('background: #F5F5F5;')
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(24, 24, 24, 24)
        right_layout.setSpacing(12)
        self.subject_label = QLabel(tx('Select a message to view'))
        self.subject_label.setStyleSheet('font-size: 18px; font-weight: 600; color: #1A1A1A; background: transparent;')
        self.subject_label.setWordWrap(True)
        self.info_label = QLabel('')
        self.info_label.setStyleSheet('color: #616161; font-size: 12px; background: transparent;')
        self.attachment_widget = QWidget()
        self.attachment_widget.setStyleSheet('background: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 4px;')
        self.attachment_widget.hide()
        attachment_layout = QHBoxLayout(self.attachment_widget)
        attachment_layout.setContentsMargins(12, 8, 12, 8)
        self.attachment_label = QLabel(tx('Attachments:'))
        self.attachment_label.setStyleSheet('color: #666; font-size: 12px;')
        attachment_layout.addWidget(self.attachment_label)
        self.attachment_list = QHBoxLayout()
        attachment_layout.addLayout(self.attachment_list)
        attachment_layout.addStretch()
        self.content_text = QTextBrowser()
        self.content_text.setReadOnly(True)
        self.content_text.setOpenExternalLinks(True)
        self.content_text.setStyleSheet("\n            QTextBrowser { \n                border: 1px solid #E0E0E0; \n                padding: 16px; \n                background: #FFFFFF; \n                font-size: 14px;\n                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;\n                color: #1A1A1A;\n            }\n            QTextBrowser a {\n                color: #0078D4;\n                text-decoration: underline;\n            }\n            QScrollBar:vertical {\n                background: #F5F5F5;\n                width: 8px;\n            }\n            QScrollBar::handle:vertical {\n                background: #C0C0C0;\n                min-height: 30px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background: #A0A0A0;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                height: 0px;\n            }\n            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {\n                background: none;\n            }\n        ")
        right_layout.addWidget(self.subject_label)
        right_layout.addWidget(self.info_label)
        right_layout.addWidget(self.attachment_widget)
        right_layout.addWidget(self.content_text, 1)
        layout.addWidget(right_panel, 1)

    def on_folder_changed(self, index):
        self.current_folder = self.folder_combo.currentData()
        self.search_input.clear()
        self.fetch_emails()

    def fetch_emails(self):
        self.email_list.clear()
        self.all_emails = []
        self.loading_label.show()
        self.loading_label.setText(tx('Loading...'))
        self.subject_label.setText(tx('Select a message to view'))
        self.info_label.setText('')
        self.content_text.setText('')
        self.attachment_widget.hide()
        self.reset_buttons()
        self.fetch_thread = FetchEmailThread(self.account, self.current_folder, self.db)
        self.fetch_thread.finished.connect(self.on_emails_fetched)
        self.fetch_thread.start()

    def reset_buttons(self):
        self.delete_btn.setEnabled(False)
        self.delete_btn.setText(tx('Delete'))
        self.reply_btn.setEnabled(False)
        self.forward_btn.setEnabled(False)
        self.mark_btn.setEnabled(False)

    def on_selection_changed(self):
        selected_items = self.email_list.selectedItems()
        count = len(selected_items)
        if count == 0:
            self.reset_buttons()
        elif count == 1:
            self.delete_btn.setEnabled(True)
            self.delete_btn.setText(tx('Delete'))
            self.reply_btn.setEnabled(True)
            self.forward_btn.setEnabled(True)
            self.mark_btn.setEnabled(True)
        else:
            self.delete_btn.setEnabled(True)
            self.delete_btn.setText(tx('Delete ({0})', count))
            self.reply_btn.setEnabled(False)
            self.forward_btn.setEnabled(False)
            self.mark_btn.setEnabled(True)
            self.mark_btn.setText(tx('Mark ({0})', count))

    def on_emails_fetched(self, emails, msg):
        self.loading_label.hide()
        self.all_emails = emails
        if not emails:
            folder_name = tx(self.FOLDER_NAMES.get(self.current_folder, self.current_folder))
            self.subject_label.setText(tx('{0}: no messages\n{1}', folder_name, msg))
            return
        self.display_emails(emails)
        if self.current_folder == 'inbox':
            self.check_aws_emails(emails)

    def check_aws_emails(self, emails):
        aws_keywords = ['aws', 'amazon']
        aws_count = 0
        for email_data in emails:
            subject = email_data.get('subject', '').lower()
            if any((kw in subject for kw in aws_keywords)):
                aws_count += 1
        has_aws = aws_count > 0
        self.db.update_aws_code_status(self.account[0], has_aws)

    def display_emails(self, emails):
        self.email_list.clear()
        for email_data in emails:
            item = QListWidgetItem()
            sender = email_data.get('sender', '')[:30]
            subject = email_data.get('subject', tx('(No subject)'))[:40]
            date = email_data.get('date')
            date_str = date.strftime('%m/%d %H:%M') if date else ''
            is_read = email_data.get('is_read', True)
            has_attachments = email_data.get('has_attachments', False)
            att_mark = '📎 ' if has_attachments else ''
            if not is_read:
                item.setText(f'● {att_mark}{sender}\n{subject}\n{date_str}')
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            else:
                item.setText(f'{att_mark}{sender}\n{subject}\n{date_str}')
            item.setData(Qt.UserRole, email_data)
            self.email_list.addItem(item)

    def filter_emails(self, text):
        if not text:
            self.display_emails(self.all_emails)
            return
        text = text.lower()
        filtered = []
        for email_data in self.all_emails:
            sender = email_data.get('sender', '').lower()
            sender_email = email_data.get('sender_email', '').lower()
            subject = email_data.get('subject', '').lower()
            if text in sender or text in sender_email or text in subject:
                filtered.append(email_data)
        self.display_emails(filtered)

    def show_email_content(self, item):
        data = item.data(Qt.UserRole)
        self.current_email = data
        self.current_item = item
        self.delete_btn.setEnabled(True)
        self.reply_btn.setEnabled(True)
        self.forward_btn.setEnabled(True)
        self.mark_btn.setEnabled(True)
        is_read = data.get('is_read', True)
        if not is_read:
            self.mark_btn.setText(tx('Mark as unread'))
            sender = data.get('sender', '')[:30]
            subject = data.get('subject', tx('(No subject)'))[:40]
            date = data.get('date')
            date_str = date.strftime('%m/%d %H:%M') if date else ''
            has_attachments = data.get('has_attachments', False)
            att_mark = '📎 ' if has_attachments else ''
            item.setText(f'{att_mark}{sender}\n{subject}\n{date_str}')
            font = item.font()
            font.setBold(False)
            item.setFont(font)
            data['is_read'] = True
            self.current_email['is_read'] = True
            for email_data in self.all_emails:
                if email_data.get('uid') == data.get('uid'):
                    email_data['is_read'] = True
                    break
            self.auto_mark_as_read(data.get('uid'))
        else:
            self.mark_btn.setText(tx('Mark as unread'))
        self.subject_label.setText(data.get('subject', tx('(No subject)')))
        date = data.get('date')
        date_str = date.strftime('%Y-%m-%d %H:%M') if date else ''
        self.info_label.setText(tx('From: {0}\nDate: {1}', data.get('sender', ''), date_str))
        body = data.get('body', '')
        if '<html' in body.lower() or '<a ' in body.lower() or '<div' in body.lower():
            self.content_text.setHtml(body)
        else:
            self.content_text.setPlainText(body)
        has_attachments = data.get('has_attachments', False)
        if has_attachments:
            self.load_attachments(data.get('uid'))
        else:
            self.attachment_widget.hide()

    def load_attachments(self, email_id):
        self.attachment_thread = GetAttachmentsThread(self.account, email_id, self.current_folder)
        self.attachment_thread.finished.connect(self.on_attachments_loaded)
        self.attachment_thread.start()

    def auto_mark_as_read(self, email_id):
        self.auto_mark_thread = MarkReadThread(self.account, email_id, self.current_folder, True)
        self.auto_mark_thread.start()

    def on_attachments_loaded(self, attachments, msg):
        while self.attachment_list.count():
            item = self.attachment_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.current_attachments = attachments
        if attachments:
            self.attachment_widget.show()
            for att in attachments:
                btn = QPushButton(f"📄 {att['name']} ({self.format_size(att['size'])})")
                btn.setStyleSheet('\n                    QPushButton {\n                        background: #FFFFFF;\n                        border: 1px solid #E0E0E0;\n                        border-radius: 4px;\n                        padding: 4px 8px;\n                        font-size: 11px;\n                        color: #0078D4;\n                    }\n                    QPushButton:hover { background: #E5F1FB; border-color: #0078D4; }\n                ')
                btn.setProperty('attachment', att)
                btn.setToolTip(tx('Click to download this attachment'))
                btn.clicked.connect(self.download_attachment)
                self.attachment_list.addWidget(btn)
            if len(attachments) > 1:
                btn_all = QPushButton(tx('⬇ Download all ({0})', len(attachments)))
                btn_all.setStyleSheet('\n                    QPushButton {\n                        background: #0078D4;\n                        border: none;\n                        border-radius: 4px;\n                        padding: 4px 12px;\n                        font-size: 11px;\n                        color: white;\n                    }\n                    QPushButton:hover { background: #1084D9; }\n                ')
                btn_all.setToolTip(tx('Download all attachments to a selected folder'))
                btn_all.clicked.connect(self.download_all_attachments)
                self.attachment_list.addWidget(btn_all)
        else:
            self.attachment_widget.hide()

    def download_all_attachments(self):
        if not hasattr(self, 'current_attachments') or not self.current_attachments:
            return
        folder = QFileDialog.getExistingDirectory(self, tx('Select destination folder'))
        if not folder:
            return
        success_count = 0
        fail_count = 0
        for att in self.current_attachments:
            try:
                content = create_email_client(self.account).download_attachment(att)
                if content:
                    file_path = os.path.join(folder, att['name'])
                    (base, ext) = os.path.splitext(file_path)
                    counter = 1
                    while os.path.exists(file_path):
                        file_path = f'{base}_{counter}{ext}'
                        counter += 1
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    success_count += 1
                else:
                    fail_count += 1
            except Exception:
                fail_count += 1
        if fail_count == 0:
            QMessageBox.information(self, tx('Success'), tx('Downloaded {0} attachments to:\n{1}', success_count, folder))
        else:
            QMessageBox.warning(self, tx('Partially completed'), tx('Successful: {0}\nFailed: {1} account(s)', success_count, fail_count))

    def format_size(self, size):
        if size < 1024:
            return f'{size} B'
        elif size < 1024 * 1024:
            return f'{size / 1024:.1f} KB'
        else:
            return f'{size / (1024 * 1024):.1f} MB'

    def download_attachment(self):
        btn = self.sender()
        att = btn.property('attachment')
        if not att:
            return
        (path, _) = QFileDialog.getSaveFileName(self, tx('Save attachment'), att['name'])
        if path:
            try:
                content = create_email_client(self.account).download_attachment(att)
                if content:
                    with open(path, 'wb') as f:
                        f.write(content)
                    QMessageBox.information(self, tx('Success'), tx('Attachment saved to:\n{0}', path))
                else:
                    QMessageBox.warning(self, tx('Error'), tx('Failed to download attachment'))
            except Exception as e:
                QMessageBox.warning(self, tx('Error'), tx('Save failed: {0}', e))

    def toggle_read_status(self):
        selected_items = self.email_list.selectedItems()
        count = len(selected_items)
        if count == 0:
            return
        elif count == 1:
            if not hasattr(self, 'current_email') or not self.current_email:
                return
            email_id = self.current_email.get('uid')
            is_read = self.current_email.get('is_read', True)
            new_status = not is_read
            self.mark_btn.setEnabled(False)
            self.mark_btn.setText(tx('Processing...'))
            self.mark_thread = MarkReadThread(self.account, email_id, self.current_folder, new_status)
            self.mark_thread.finished.connect(self.on_mark_finished)
            self.mark_thread.start()
        else:
            from PyQt5.QtWidgets import QMenu
            from PyQt5.QtWidgets import QGraphicsDropShadowEffect
            from PyQt5.QtGui import QColor
            menu = QMenu(self)
            menu.setStyleSheet(MENU_STYLE_LIGHT)
            shadow = QGraphicsDropShadowEffect(menu)
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(0, 0, 0, 30))
            shadow.setOffset(0, 4)
            menu.setGraphicsEffect(shadow)
            action_read = menu.addAction(tx('Mark all as read ({0})', count))
            action_unread = menu.addAction(tx('Mark all as unread ({0})', count))
            action = menu.exec_(self.mark_btn.mapToGlobal(self.mark_btn.rect().bottomLeft()))
            if action == action_read:
                self.batch_mark_emails(selected_items, True)
            elif action == action_unread:
                self.batch_mark_emails(selected_items, False)

    def batch_mark_emails(self, selected_items, is_read):
        email_ids = []
        for item in selected_items:
            data = item.data(Qt.UserRole)
            if data and data.get('uid'):
                email_ids.append(data.get('uid'))
        if not email_ids:
            return
        self.mark_btn.setEnabled(False)
        self.mark_btn.setText(tx('Marking (0/{0})...', len(email_ids)))
        self.batch_mark_thread = BatchMarkReadThread(self.account, email_ids, self.current_folder, is_read)
        self.batch_mark_thread.progress.connect(self.on_batch_mark_progress)
        self.batch_mark_thread.finished.connect(lambda s, f, t: self.on_batch_mark_finished(s, f, t, is_read))
        self.batch_mark_thread.start()

    def on_batch_mark_progress(self, current, total):
        self.mark_btn.setText(tx('Marking ({0}/{1})...', current, total))

    def on_batch_mark_finished(self, success_count, fail_count, total, is_read):
        self.mark_btn.setText(tx('Mark'))
        self.mark_btn.setEnabled(True)
        status_text = tx('read') if is_read else tx('unread')
        if fail_count == 0:
            QMessageBox.information(self, tx('Success'), tx('Marked {0} messages as {1}', success_count, status_text))
        else:
            QMessageBox.warning(self, tx('Partially completed'), tx('Marking complete\nSuccessful: {0}\nFailed: {1} messages', success_count, fail_count))
        self.fetch_emails()

    def on_mark_finished(self, success, msg):
        if success:
            self.current_email['is_read'] = not self.current_email.get('is_read', True)
            is_read = self.current_email['is_read']
            self.mark_btn.setText(tx('Mark as unread') if is_read else tx('Mark as read'))
            self.fetch_emails()
        else:
            QMessageBox.warning(self, tx('Error'), msg)
        self.mark_btn.setEnabled(True)

    def reply_email(self):
        if not hasattr(self, 'current_email') or not self.current_email:
            return
        sender_email = self.current_email.get('sender_email', '')
        if not sender_email:
            sender = self.current_email.get('sender', '')
            import re
            match = re.search('<([^>]+)>', sender)
            if match:
                sender_email = match.group(1)
            elif '@' in sender:
                sender_email = sender.strip()
        subject = self.current_email.get('subject', '')
        original_body = self.current_email.get('body', '')
        date = self.current_email.get('date')
        date_str = date.strftime('%Y-%m-%d %H:%M') if date else ''
        reply_body = tx('\n\n\n-------- Original message --------\nFrom: {0}\nDate: {1}\n\n{2}', self.current_email.get('sender', ''), date_str, original_body)
        dialog = ComposeEmailDialog(self.account, self, reply_to=sender_email, reply_subject=subject, reply_body=reply_body)
        dialog.exec_()

    def forward_email(self):
        if not hasattr(self, 'current_email') or not self.current_email:
            return
        subject = self.current_email.get('subject', '')
        if not subject.startswith('Fwd:') and (not subject.startswith(tx('Fwd:'))):
            subject = f'Fwd: {subject}'
        original_body = self.current_email.get('body', '')
        date = self.current_email.get('date')
        date_str = date.strftime('%Y-%m-%d %H:%M') if date else ''
        forward_body = tx('\n\n\n-------- Forwarded message --------\nFrom: {0}\nDate: {1}\nSubject: {2}\n\n{3}', self.current_email.get('sender', ''), date_str, self.current_email.get('subject', ''), original_body)
        dialog = ComposeEmailDialog(self.account, self, reply_subject=subject, reply_body=forward_body, is_forward=True)
        dialog.exec_()

    def delete_selected_email(self):
        selected_items = self.email_list.selectedItems()
        if not selected_items:
            return
        count = len(selected_items)
        if count == 1:
            if not hasattr(self, 'current_email') or not self.current_email:
                return
            reply = QMessageBox.question(self, tx('Confirm deletion'), tx('Delete this message?'), QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
            email_id = self.current_email.get('uid')
            if not email_id:
                QMessageBox.warning(self, tx('Error'), tx('Could not determine the message ID'))
                return
            self.delete_btn.setEnabled(False)
            self.delete_btn.setText(tx('Deleting...'))
            self.delete_thread = DeleteEmailThread(self.account, email_id, self.current_folder)
            self.delete_thread.finished.connect(self.on_delete_finished)
            self.delete_thread.start()
        else:
            reply = QMessageBox.question(self, tx('Confirm deleting messages'), tx('Delete the selected {0} messages?', count), QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
            email_ids = []
            for item in selected_items:
                data = item.data(Qt.UserRole)
                if data and data.get('uid'):
                    email_ids.append(data.get('uid'))
            if not email_ids:
                QMessageBox.warning(self, tx('Error'), tx('Could not determine the message ID'))
                return
            self.delete_btn.setEnabled(False)
            self.delete_btn.setText(tx('Deleting (0/{0})...', len(email_ids)))
            self.batch_delete_thread = BatchDeleteEmailThread(self.account, email_ids, self.current_folder)
            self.batch_delete_thread.progress.connect(self.on_batch_delete_progress)
            self.batch_delete_thread.finished.connect(self.on_batch_delete_finished)
            self.batch_delete_thread.start()

    def on_batch_delete_progress(self, current, total):
        self.delete_btn.setText(tx('Deleting ({0}/{1})...', current, total))

    def on_batch_delete_finished(self, success_count, fail_count, total):
        self.delete_btn.setText(tx('Delete'))
        if fail_count == 0:
            QMessageBox.information(self, tx('Success'), tx('Deleted {0} messages', success_count))
        else:
            QMessageBox.warning(self, tx('Partially completed'), tx('Deletion complete\nSuccessful: {0}\nFailed: {1} messages', success_count, fail_count))
        self.current_email = None
        self.fetch_emails()

    def on_delete_finished(self, success, msg):
        self.delete_btn.setText(tx('Delete'))
        if success:
            QMessageBox.information(self, tx('Success'), tx('Message deleted'))
            self.current_email = None
            self.fetch_emails()
        else:
            self.delete_btn.setEnabled(True)
            QMessageBox.warning(self, tx('Deletion failed'), msg)

    def open_compose_dialog(self):
        dialog = ComposeEmailDialog(self.account, self)
        dialog.exec_()

class DeleteEmailThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, account, email_id, folder):
        super().__init__()
        self.account = account
        self.email_id = email_id
        self.folder = folder

    def run(self):
        client = create_email_client(self.account)
        (success, msg) = client.delete_email(self.email_id, self.folder)
        self.finished.emit(success, msg)

class BatchDeleteEmailThread(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(int, int, int)

    def __init__(self, account, email_ids, folder):
        super().__init__()
        self.account = account
        self.email_ids = email_ids
        self.folder = folder

    def run(self):
        client = create_email_client(self.account)
        total = len(self.email_ids)

        def progress_callback(current, total):
            self.progress.emit(current, total)
        (success_count, fail_count) = client.delete_emails_batch(self.email_ids, self.folder, progress_callback)
        self.finished.emit(success_count, fail_count, total)

class BatchMarkReadThread(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(int, int, int)

    def __init__(self, account, email_ids, folder, is_read):
        super().__init__()
        self.account = account
        self.email_ids = email_ids
        self.folder = folder
        self.is_read = is_read

    def run(self):
        client = create_email_client(self.account)
        total = len(self.email_ids)

        def progress_callback(current, total):
            self.progress.emit(current, total)
        (success_count, fail_count) = client.mark_emails_batch(self.email_ids, self.folder, self.is_read, progress_callback)
        self.finished.emit(success_count, fail_count, total)

class MarkReadThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, account, email_id, folder, is_read):
        super().__init__()
        self.account = account
        self.email_id = email_id
        self.folder = folder
        self.is_read = is_read

    def run(self):
        client = create_email_client(self.account)
        (success, msg) = client.mark_as_read(self.email_id, self.folder, self.is_read)
        self.finished.emit(success, msg)

class GetAttachmentsThread(QThread):
    finished = pyqtSignal(list, str)

    def __init__(self, account, email_id, folder):
        super().__init__()
        self.account = account
        self.email_id = email_id
        self.folder = folder

    def run(self):
        client = create_email_client(self.account)
        (attachments, msg) = client.get_attachments(self.email_id, self.folder)
        self.finished.emit(attachments, msg)

class SendEmailThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, account, to_addr, subject, body, cc_addr=None, attachments=None):
        super().__init__()
        self.account = account
        self.to_addr = to_addr
        self.subject = subject
        self.body = body
        self.cc_addr = cc_addr
        self.attachments = attachments

    def run(self):
        client = create_email_client(self.account)
        if self.attachments:
            (success, msg) = client.send_email_with_attachments(self.to_addr, self.subject, self.body, self.attachments, self.cc_addr)
        else:
            (success, msg) = client.send_email(self.to_addr, self.subject, self.body, self.cc_addr)
        self.finished.emit(success, msg)

class ComposeEmailDialog(QDialog):

    def __init__(self, account, parent=None, reply_to=None, reply_subject=None, reply_body=None, is_forward=False):
        super().__init__(parent)
        self.account = account
        self.reply_to = reply_to
        self.reply_subject = reply_subject
        self.reply_body = reply_body or ''
        self.is_forward = is_forward
        self.attachments = []
        self.setWindowTitle(tx('Compose — {0}', account[1]))
        self.setMinimumSize(650, 550)
        self.setStyleSheet(DIALOG_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        title_text = tx('Forward message') if self.is_forward else tx('Reply to message') if self.reply_to else tx('Compose')
        title = QLabel(title_text)
        title.setStyleSheet('font-size: 18px; font-weight: 600; color: #1A1A1A;')
        layout.addWidget(title)
        from_row = QHBoxLayout()
        from_label = QLabel(tx('From:'))
        from_label.setFixedWidth(60)
        self.from_input = QLineEdit(self.account[1])
        self.from_input.setReadOnly(True)
        self.from_input.setStyleSheet('background: #F0F0F0; color: #666;')
        from_row.addWidget(from_label)
        from_row.addWidget(self.from_input)
        layout.addLayout(from_row)
        to_row = QHBoxLayout()
        to_label = QLabel(tx('To:'))
        to_label.setFixedWidth(60)
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText(tx('Separate recipients with commas'))
        if self.reply_to:
            self.to_input.setText(self.reply_to)
        to_row.addWidget(to_label)
        to_row.addWidget(self.to_input)
        layout.addLayout(to_row)
        cc_row = QHBoxLayout()
        cc_label = QLabel(tx('Cc:'))
        cc_label.setFixedWidth(60)
        self.cc_input = QLineEdit()
        self.cc_input.setPlaceholderText(tx('Optional; separate addresses with commas'))
        cc_row.addWidget(cc_label)
        cc_row.addWidget(self.cc_input)
        layout.addLayout(cc_row)
        subject_row = QHBoxLayout()
        subject_label = QLabel(tx('Subject:'))
        subject_label.setFixedWidth(60)
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText(tx('Message subject'))
        if self.reply_subject:
            if self.is_forward:
                self.subject_input.setText(self.reply_subject)
            else:
                prefix = 'Re: ' if not self.reply_subject.startswith('Re:') else ''
                self.subject_input.setText(f'{prefix}{self.reply_subject}')
        subject_row.addWidget(subject_label)
        subject_row.addWidget(self.subject_input)
        layout.addLayout(subject_row)
        att_row = QHBoxLayout()
        att_label = QLabel(tx('Attachments:'))
        att_label.setFixedWidth(60)
        att_row.addWidget(att_label)
        self.att_list_widget = QWidget()
        self.att_list_layout = QHBoxLayout(self.att_list_widget)
        self.att_list_layout.setContentsMargins(0, 0, 0, 0)
        self.att_list_layout.setSpacing(4)
        att_row.addWidget(self.att_list_widget, 1)
        btn_add_att = QPushButton(tx('Add attachment'))
        btn_add_att.setStyleSheet('\n            QPushButton {\n                background: #FFFFFF;\n                border: 1px solid #0078D4;\n                color: #0078D4;\n                padding: 6px 12px;\n                border-radius: 4px;\n                font-size: 12px;\n            }\n            QPushButton:hover { background: #E5F1FB; }\n        ')
        btn_add_att.clicked.connect(self.add_attachment)
        att_row.addWidget(btn_add_att)
        layout.addLayout(att_row)
        body_label = QLabel(tx('Message:'))
        layout.addWidget(body_label)
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText(tx('Enter your message here...'))
        self.body_input.setMinimumHeight(180)
        if self.reply_body:
            self.body_input.setText(self.reply_body)
            cursor = self.body_input.textCursor()
            cursor.setPosition(0)
            self.body_input.setTextCursor(cursor)
        layout.addWidget(self.body_input)
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color: #666; font-size: 12px;')
        layout.addWidget(self.status_label)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton(tx('Cancel'))
        btn_cancel.setStyleSheet(BTN_DEFAULT)
        btn_cancel.clicked.connect(self.reject)
        self.btn_send = QPushButton(tx('Send'))
        self.btn_send.setStyleSheet(BTN_PRIMARY)
        self.btn_send.clicked.connect(self.send_email)
        btn_row.addWidget(btn_cancel)
        btn_row.addSpacing(12)
        btn_row.addWidget(self.btn_send)
        layout.addLayout(btn_row)

    def add_attachment(self):
        (paths, _) = QFileDialog.getOpenFileNames(self, tx('Select attachments'), '', tx('All files (*.*)'))
        for path in paths:
            if path and path not in self.attachments:
                self.attachments.append(path)
                self.update_attachment_display()

    def update_attachment_display(self):
        while self.att_list_layout.count():
            item = self.att_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for path in self.attachments:
            filename = os.path.basename(path)
            btn = QPushButton(f"📎 {filename[:20]}{('...' if len(filename) > 20 else '')} ✕")
            btn.setStyleSheet('\n                QPushButton {\n                    background: #F5F5F5;\n                    border: 1px solid #E0E0E0;\n                    border-radius: 4px;\n                    padding: 4px 8px;\n                    font-size: 11px;\n                    color: #666;\n                }\n                QPushButton:hover { background: #FFE0E0; border-color: #D13438; color: #D13438; }\n            ')
            btn.setProperty('path', path)
            btn.clicked.connect(self.remove_attachment)
            self.att_list_layout.addWidget(btn)

    def remove_attachment(self):
        btn = self.sender()
        path = btn.property('path')
        if path in self.attachments:
            self.attachments.remove(path)
            self.update_attachment_display()

    def send_email(self):
        to_addr = self.to_input.text().strip()
        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText()
        cc_addr = self.cc_input.text().strip() or None
        if not to_addr:
            QMessageBox.warning(self, tx('Error'), tx('Enter a recipient address'))
            return
        if not subject:
            QMessageBox.warning(self, tx('Error'), tx('Enter a message subject'))
            return
        self.btn_send.setEnabled(False)
        self.btn_send.setText(tx('Sending...'))
        self.status_label.setText(tx('Sending message...'))
        self.send_thread = SendEmailThread(self.account, to_addr, subject, body, cc_addr, self.attachments if self.attachments else None)
        self.send_thread.finished.connect(self.on_send_finished)
        self.send_thread.start()

    def on_send_finished(self, success, msg):
        self.btn_send.setEnabled(True)
        self.btn_send.setText(tx('Send'))
        if success:
            self.status_label.setText('')
            QMessageBox.information(self, tx('Success'), tx('Message sent successfully!'))
            self.accept()
        else:
            self.status_label.setText(tx('Sending failed: {0}', msg))
            QMessageBox.warning(self, tx('Sending failed'), msg)

class BatchSendThread(QThread):
    progress = pyqtSignal(int, str, bool, str)
    finished = pyqtSignal(int, int)

    def __init__(self, accounts, to_addr, subject, body):
        super().__init__()
        self.accounts = accounts
        self.to_addr = to_addr
        self.subject = subject
        self.body = body

    def run(self):
        success_count = 0
        fail_count = 0
        for (i, acc) in enumerate(self.accounts):
            client = create_email_client(acc)
            (success, msg) = client.send_email(self.to_addr, self.subject, self.body)
            if success:
                success_count += 1
            else:
                fail_count += 1
            self.progress.emit(i, acc[1], success, msg)
        self.finished.emit(success_count, fail_count)

class BatchSendDialog(QDialog):

    def __init__(self, accounts, parent=None):
        super().__init__(parent)
        self.accounts = accounts
        self.setWindowTitle(tx('Send messages — {0} accounts', len(accounts)))
        self.setMinimumSize(650, 550)
        self.setStyleSheet(DIALOG_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        title = QLabel(tx('Send messages ({0} sender accounts)', len(self.accounts)))
        title.setStyleSheet('font-size: 20px; font-weight: 600; color: #1A1A1A;')
        layout.addWidget(title)
        accounts_label = QLabel(tx('Sender accounts: {0}{1}', ', '.join([acc[1] for acc in self.accounts[:3]]), '...' if len(self.accounts) > 3 else ''))
        accounts_label.setStyleSheet('color: #666; font-size: 12px;')
        accounts_label.setWordWrap(True)
        layout.addWidget(accounts_label)
        to_row = QHBoxLayout()
        to_label = QLabel(tx('To:'))
        to_label.setFixedWidth(60)
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText(tx('All accounts will send to these recipients; separate addresses with commas'))
        to_row.addWidget(to_label)
        to_row.addWidget(self.to_input)
        layout.addLayout(to_row)
        subject_row = QHBoxLayout()
        subject_label = QLabel(tx('Subject:'))
        subject_label.setFixedWidth(60)
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText(tx('Message subject'))
        subject_row.addWidget(subject_label)
        subject_row.addWidget(self.subject_input)
        layout.addLayout(subject_row)
        body_label = QLabel(tx('Message:'))
        layout.addWidget(body_label)
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText(tx('Enter your message here...'))
        self.body_input.setMinimumHeight(150)
        layout.addWidget(self.body_input)
        progress_label = QLabel(tx('Sending progress:'))
        layout.addWidget(progress_label)
        self.progress_list = QListWidget()
        self.progress_list.setMaximumHeight(120)
        self.progress_list.setStyleSheet('\n            QListWidget { \n                background: #FAFAFA; \n                border: 1px solid #E0E0E0; \n                border-radius: 4px;\n                font-size: 12px;\n            }\n            QListWidget::item { padding: 4px 8px; }\n        ')
        layout.addWidget(self.progress_list)
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color: #666; font-size: 13px;')
        layout.addWidget(self.status_label)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton(tx('Cancel'))
        btn_cancel.setStyleSheet(BTN_DEFAULT)
        btn_cancel.clicked.connect(self.reject)
        self.btn_send = QPushButton(tx('Send ({0} messages)', len(self.accounts)))
        self.btn_send.setStyleSheet(BTN_PRIMARY)
        self.btn_send.clicked.connect(self.start_send)
        btn_row.addWidget(btn_cancel)
        btn_row.addSpacing(12)
        btn_row.addWidget(self.btn_send)
        layout.addLayout(btn_row)

    def start_send(self):
        to_addr = self.to_input.text().strip()
        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText()
        if not to_addr:
            QMessageBox.warning(self, tx('Error'), tx('Enter a recipient address'))
            return
        if not subject:
            QMessageBox.warning(self, tx('Error'), tx('Enter a message subject'))
            return
        reply = QMessageBox.question(self, tx('Confirm sending'), tx('Send messages using {0} accounts?', len(self.accounts)), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.btn_send.setEnabled(False)
        self.btn_send.setText(tx('Sending...'))
        self.progress_list.clear()
        self.status_label.setText(tx('Sending...'))
        self.send_thread = BatchSendThread(self.accounts, to_addr, subject, body)
        self.send_thread.progress.connect(self.on_progress)
        self.send_thread.finished.connect(self.on_finished)
        self.send_thread.start()

    def on_progress(self, index, email, success, msg):
        status = tx('✓ Success') if success else tx('✗ Failed: {0}', msg[:30])
        item = QListWidgetItem(f'{index + 1}. {email} - {status}')
        if success:
            item.setForeground(Qt.darkGreen)
        else:
            item.setForeground(Qt.red)
        self.progress_list.addItem(item)
        self.progress_list.scrollToBottom()
        self.status_label.setText(tx('Sending... ({0}/{1})', index + 1, len(self.accounts)))

    def on_finished(self, success_count, fail_count):
        self.btn_send.setEnabled(True)
        self.btn_send.setText(tx('Send ({0} messages)', len(self.accounts)))
        self.status_label.setText(tx('Complete. Sent: {0}; failed: {1} messages', success_count, fail_count))
        QMessageBox.information(self, tx('Sending complete'), tx('Sending complete!\nSuccessful: {0}\nFailed: {1} messages', success_count, fail_count))

class ManualOAuth2Dialog(QDialog):
    import_completed = pyqtSignal(int, int)

    def __init__(self, db, parent=None, default_group=None):
        super().__init__(parent)
        self.db = db
        self.default_group = default_group
        self.setWindowTitle(tx('Manual OAuth2 authorization'))
        self.setMinimumSize(500, 400)
        self.resize(500, 450)
        self.setStyleSheet(DIALOG_STYLE)
        self.success_count = 0
        self.is_processing = False
        self.manual_thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        title = QLabel(tx('🔐 Manual OAuth2 authorization'))
        title.setStyleSheet('font-size: 18px; font-weight: 600; color: #1A1A1A;')
        layout.addWidget(title)
        desc = QLabel(tx('Click "Start authorization" to open the Microsoft sign-in page.\nSign in to your Outlook account; the app will then obtain the authorization details.'))
        desc.setStyleSheet('color: #666; font-size: 12px; line-height: 1.5;')
        desc.setWordWrap(True)
        layout.addWidget(desc)
        group_row = QHBoxLayout()
        group_row.addWidget(QLabel(tx('Import into group:')))
        self.group_combo = QComboBox()
        self.group_combo.setMinimumWidth(160)
        current_index = 0
        for (i, group) in enumerate(self.db.get_all_groups()):
            self.group_combo.addItem(tx(group[1]) if group[1] == 'Default' else group[1], group[1])
            if self.default_group and group[1] == self.default_group:
                current_index = i
        self.group_combo.setCurrentIndex(current_index)
        group_row.addWidget(self.group_combo)
        group_row.addStretch()
        layout.addLayout(group_row)
        tip_label = QLabel(tx('💡 Wait for the automatic redirect after sign-in. Do not close the browser manually.'))
        tip_label.setStyleSheet('color: #E67E22; font-size: 11px; padding: 8px 0;')
        layout.addWidget(tip_label)
        self.progress_label = QLabel(tx('Ready'))
        self.progress_label.setStyleSheet('color: #0078D4; font-size: 13px; font-weight: 500;')
        layout.addWidget(self.progress_label)
        self.current_account_label = QLabel('')
        self.current_account_label.setStyleSheet('color: #666; font-size: 12px;')
        layout.addWidget(self.current_account_label)
        result_label = QLabel(tx('Authorization result:'))
        result_label.setStyleSheet('font-size: 13px; font-weight: 500; color: #1A1A1A;')
        layout.addWidget(result_label)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("\n            QTextEdit {\n                border: 1px solid #E0E0E0;\n                border-radius: 4px;\n                background: #FAFAFA;\n                font-size: 12px;\n                font-family: 'Consolas', 'Microsoft YaHei UI', monospace;\n            }\n        ")
        self.result_text.setMinimumHeight(100)
        layout.addWidget(self.result_text, 1)
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton(tx('Start authorization'))
        self.btn_start.setStyleSheet(BTN_PRIMARY)
        self.btn_start.clicked.connect(self.start_manual_auth)
        self.btn_stop = QPushButton(tx('Stop'))
        self.btn_stop.setStyleSheet(BTN_DEFAULT)
        self.btn_stop.clicked.connect(self.stop_auth)
        self.btn_stop.setEnabled(False)
        btn_close = QPushButton(tx('Close'))
        btn_close.setStyleSheet(BTN_DEFAULT)
        btn_close.clicked.connect(self.close_dialog)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def start_manual_auth(self):
        if self.is_processing:
            QMessageBox.warning(self, tx('Notice'), tx('An operation is in progress. Please wait.'))
            return
        self.is_processing = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_label.setText(tx('Opening browser...'))
        self.current_account_label.setText(tx('Sign in to your Outlook account in the browser'))
        group = self.group_combo.currentData()
        self.manual_thread = ManualOAuth2Thread(self.db, group)
        self.manual_thread.progress.connect(self.on_progress)
        self.manual_thread.finished_signal.connect(self.on_finished)
        self.manual_thread.start()

    def stop_auth(self):
        if self.manual_thread:
            self.manual_thread.stop()
        self.is_processing = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_label.setText(tx('Stopped'))

    def on_progress(self, message):
        self.progress_label.setText(message)

    def on_finished(self, email, client_id, refresh_token, error):
        self.is_processing = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        if error:
            self.progress_label.setText(tx('Authorization failed'))
            self.result_text.append(tx('❌ Failed: {0}', error))
        else:
            self.progress_label.setText(tx('Authorization successful!'))
            self.current_account_label.setText(tx('Added: {0}', email))
            self.result_text.append(tx('✅ {0} — authorized and saved', email))
            self.success_count += 1
            self.import_completed.emit(1, 0)

    def close_dialog(self):
        if self.is_processing:
            reply = QMessageBox.question(self, tx('Confirm'), tx('An operation is in progress. Stop and close?'), QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
            self.stop_auth()
        self.accept()

    def closeEvent(self, event):
        if self.is_processing:
            self.stop_auth()
        event.accept()

class ManualOAuth2Thread(QThread):
    progress = pyqtSignal(str)
    finished_signal = pyqtSignal(str, str, str, str)

    def __init__(self, db, group):
        super().__init__()
        self.db = db
        self.group = group
        self.stop_flag = False
        self.selenium_oauth = None

    def run(self):
        try:
            from core.oauth2_helper import SeleniumOAuth2
            self.selenium_oauth = SeleniumOAuth2()
            self.progress.emit(tx('Initializing browser...'))
            (success, error) = self.selenium_oauth.init_driver()
            if not success:
                self.finished_signal.emit('', '', '', tx('Browser initialization failed: {0}', error))
                return
            self.progress.emit(tx('Browser opened. Sign in to an Outlook account...'))
            (client_id, refresh_token, error) = self.selenium_oauth.authorize_semi_auto(email='', progress_callback=lambda msg: self.progress.emit(msg), timeout=300)
            if error:
                self.finished_signal.emit('', '', '', error)
                return
            self.progress.emit(tx('Retrieving account information...'))
            email = self.get_user_email(client_id, refresh_token)
            if not email:
                self.finished_signal.emit('', '', '', tx('Could not retrieve the email address'))
                return
            self.progress.emit(tx('Saving account: {0}', email))
            existing = self.db.get_account_by_email(email)
            if existing:
                self.db.update_account_oauth(existing[0], client_id, refresh_token)
            else:
                self.db.add_account(email, '', self.group, client_id=client_id, refresh_token=refresh_token)
            self.finished_signal.emit(email, client_id, refresh_token, '')
        except Exception as e:
            self.finished_signal.emit('', '', '', tx('Authorization error: {0}', str(e)))
        finally:
            if self.selenium_oauth:
                self.selenium_oauth.close_driver()

    def get_user_email(self, client_id, refresh_token):
        import requests
        token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        data = {'client_id': client_id, 'refresh_token': refresh_token, 'grant_type': 'refresh_token', 'scope': 'offline_access https://outlook.office.com/IMAP.AccessAsUser.All https://outlook.office.com/SMTP.Send'}
        try:
            response = requests.post(token_url, data=data, timeout=30)
            if response.status_code != 200:
                return None
            access_token = response.json().get('access_token')
            if not access_token:
                return None
            headers = {'Authorization': f'Bearer {access_token}'}
            try:
                resp = requests.get('https://outlook.office.com/api/v2.0/me', headers=headers, timeout=10)
                if resp.status_code == 200:
                    return resp.json().get('EmailAddress', '')
            except:
                pass
            try:
                resp = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get('mail') or data.get('userPrincipalName', '')
            except:
                pass
            return None
        except:
            return None

    def stop(self):
        self.stop_flag = True
        if self.selenium_oauth:
            self.selenium_oauth.close_driver()

class PieChartWidget(QWidget):

    def __init__(self, data, colors, parent=None):
        super().__init__(parent)
        self.data = data
        self.colors = colors
        self.setMinimumSize(150, 150)

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QBrush, QPen
        from PyQt5.QtCore import QRectF
        import math
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        size = min(self.width(), self.height()) - 20
        x = (self.width() - size) / 2
        y = (self.height() - size) / 2
        rect = QRectF(x, y, size, size)
        if not self.data:
            painter.setBrush(QBrush(QColor('#E0E0E0')))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect)
            return
        total = sum(self.data.values())
        if total == 0:
            return
        start_angle = 90 * 16
        for (i, (name, value)) in enumerate(self.data.items()):
            span_angle = int(value / total * 360 * 16)
            color = QColor(self.colors[i % len(self.colors)])
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor('#FFFFFF'), 2))
            painter.drawPie(rect, start_angle, -span_angle)
            start_angle -= span_angle
        painter.end()
