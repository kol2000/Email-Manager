from core.i18n import tx
import imaplib
import smtplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ssl
import requests
import os
import base64
from datetime import datetime

class EmailClient:
    SMTP_SERVERS = {'outlook.com': ('smtp-mail.outlook.com', 587), 'hotmail.com': ('smtp-mail.outlook.com', 587), 'live.com': ('smtp-mail.outlook.com', 587), 'gmail.com': ('smtp.gmail.com', 587), 'qq.com': ('smtp.qq.com', 465), '163.com': ('smtp.163.com', 465), '126.com': ('smtp.126.com', 465)}

    def __init__(self, email_addr, password, imap_server=None, imap_port=993, client_id=None, refresh_token=None, account_id=None, db_manager=None):
        self.email_addr = email_addr
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.client_id = client_id
        self.refresh_token = refresh_token
        self.access_token = None
        self.connection = None
        self.account_id = account_id
        self.db_manager = db_manager
        if not self.imap_server:
            self.imap_server = self.detect_server(email_addr)

    def detect_server(self, email_addr):
        domain = email_addr.split('@')[-1].lower()
        servers = {'outlook.com': 'outlook.office365.com', 'hotmail.com': 'outlook.office365.com', 'live.com': 'outlook.office365.com', 'gmail.com': 'imap.gmail.com', 'qq.com': 'imap.qq.com', '163.com': 'imap.163.com'}
        return servers.get(domain, f'imap.{domain}')

    def is_outlook(self):
        domain = self.email_addr.split('@')[-1].lower()
        return domain in ['outlook.com', 'hotmail.com', 'live.com', 'msn.com']

    def use_graph_api(self):
        return self.is_outlook() and self.client_id and self.refresh_token

    def get_api_type(self):
        if not self.access_token:
            self.get_oauth2_access_token()
        return getattr(self, '_api_type', 'graph')

    def get_oauth2_access_token(self):
        if not self.client_id or not self.refresh_token:
            return (None, tx('Missing client_id or refresh_token'))
        token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        data = {'client_id': self.client_id, 'refresh_token': self.refresh_token, 'grant_type': 'refresh_token'}
        try:
            response = requests.post(token_url, data=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access_token')
                scope = result.get('scope', '')
                new_refresh_token = result.get('refresh_token')
                if new_refresh_token and new_refresh_token != self.refresh_token:
                    self.refresh_token = new_refresh_token
                    if self.db_manager and self.account_id:
                        try:
                            self.db_manager.update_account_oauth(self.account_id, self.client_id, new_refresh_token)
                        except Exception as e:
                            print(tx('Failed to save new refresh_token: {0}', e))
                if 'outlook.office.com' in scope:
                    self._api_type = 'outlook'
                else:
                    self._api_type = 'graph'
                return (self.access_token, tx('Retrieved successfully'))
            else:
                error_data = response.json()
                error = error_data.get('error_description', response.text)
                return (None, tx('OAuth2 error: {0}', error))
        except Exception as e:
            return (None, tx('Network error: {0}', str(e)))

    def check_status(self):
        if self.use_graph_api():
            (token, msg) = self.get_oauth2_access_token()
            if token:
                headers = {'Authorization': f'Bearer {token}'}
                try:
                    if self._api_type == 'outlook':
                        url = 'https://outlook.office.com/api/v2.0/me/mailfolders/inbox/messages?$top=1'
                    else:
                        url = 'https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$top=1'
                    resp = requests.get(url, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        return ('Normal', tx('Token is valid'))
                    else:
                        return ('Error', tx('API error: {0}', resp.status_code))
                except Exception as e:
                    return ('Error', tx('Network error: {0}', e))
            else:
                return ('Error', msg)
        else:
            (success, msg) = self.connect_imap()
            if success:
                self.disconnect()
                return ('Normal', msg)
            return ('Error', msg)

    def connect_imap(self):
        try:
            context = ssl.create_default_context()
            self.connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, ssl_context=context)
            self.connection.login(self.email_addr, self.password)
            return (True, tx('Connected'))
        except Exception as e:
            return (False, tx('Connection failed: {0}', str(e)))

    def disconnect(self):
        if self.connection:
            try:
                self.connection.logout()
            except:
                pass
            self.connection = None
    FOLDER_MAP = {'graph': {'inbox': 'inbox', 'junk': 'junkemail', 'sent': 'sentitems', 'drafts': 'drafts', 'deleted': 'deleteditems'}, 'outlook': {'inbox': 'inbox', 'junk': 'junkemail', 'sent': 'sentitems', 'drafts': 'drafts', 'deleted': 'deleteditems'}, 'imap': {'inbox': 'INBOX', 'junk': 'Junk', 'sent': 'Sent', 'drafts': 'Drafts', 'deleted': 'Deleted'}, 'imap_gmail': {'inbox': 'INBOX', 'junk': '[Gmail]/Spam', 'sent': '[Gmail]/Sent Mail', 'drafts': '[Gmail]/Drafts', 'deleted': '[Gmail]/Trash'}, 'imap_qq': {'inbox': 'INBOX', 'junk': 'Junk', 'sent': 'Sent Messages', 'drafts': 'Drafts', 'deleted': 'Deleted Messages'}, 'imap_163': {'inbox': 'INBOX', 'junk': '\u5783\u573e\u90ae\u4ef6', 'sent': '\u5df2\u53d1\u9001', 'drafts': '\u8349\u7a3f\u7bb1', 'deleted': '\u5df2\u5220\u9664'}}

    def get_folder_name(self, folder_key):
        if self.use_graph_api():
            api_type = self.get_api_type()
            return self.FOLDER_MAP.get(api_type, self.FOLDER_MAP['graph']).get(folder_key, folder_key)
        else:
            domain = self.email_addr.split('@')[-1].lower()
            if 'gmail' in domain:
                mapping = self.FOLDER_MAP['imap_gmail']
            elif 'qq.com' in domain:
                mapping = self.FOLDER_MAP['imap_qq']
            elif '163.com' in domain or '126.com' in domain:
                mapping = self.FOLDER_MAP['imap_163']
            else:
                mapping = self.FOLDER_MAP['imap']
            return mapping.get(folder_key, folder_key)

    def fetch_emails(self, folder='inbox', limit=50):
        if self.use_graph_api():
            return self.fetch_emails_graph(folder, limit)
        else:
            actual_folder = self.get_folder_name(folder)
            return self.fetch_emails_imap(actual_folder, limit)

    def fetch_emails_graph(self, folder='inbox', limit=50):
        (token, msg) = self.get_oauth2_access_token()
        if not token:
            return ([], msg)
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        folder_name = self.get_folder_name(folder)
        if self._api_type == 'outlook':
            url = f'https://outlook.office.com/api/v2.0/me/mailfolders/{folder_name}/messages'
            params = {'$top': limit, '$orderby': 'ReceivedDateTime desc', '$select': 'Id,Subject,From,ReceivedDateTime,BodyPreview,Body,IsRead,HasAttachments'}
        else:
            url = f'https://graph.microsoft.com/v1.0/me/mailFolders/{folder_name}/messages'
            params = {'$top': limit, '$orderby': 'receivedDateTime desc', '$select': 'id,subject,from,receivedDateTime,bodyPreview,body,isRead,hasAttachments'}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                emails = []
                for msg in data.get('value', []):
                    if self._api_type == 'outlook':
                        from_info = msg.get('From', {}).get('EmailAddress', {})
                        sender = from_info.get('Name', '') or from_info.get('Address', '')
                        date_str = msg.get('ReceivedDateTime', '')
                        subject = msg.get('Subject', tx('(No subject)'))
                        body = msg.get('Body', {}).get('Content', '') or msg.get('BodyPreview', '')
                        uid = msg.get('Id', '')
                    else:
                        from_info = msg.get('from', {}).get('emailAddress', {})
                        sender = from_info.get('name', '') or from_info.get('address', '')
                        date_str = msg.get('receivedDateTime', '')
                        subject = msg.get('subject', tx('(No subject)'))
                        body = msg.get('body', {}).get('content', '') or msg.get('bodyPreview', '')
                        uid = msg.get('id', '')
                    try:
                        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        date = None
                    emails.append({'uid': uid, 'subject': subject, 'sender': sender, 'sender_email': from_info.get('address', '') if self._api_type != 'outlook' else from_info.get('Address', ''), 'date': date, 'body': body, 'is_read': msg.get('isRead', True) if self._api_type != 'outlook' else msg.get('IsRead', True), 'has_attachments': msg.get('hasAttachments', False) if self._api_type != 'outlook' else msg.get('HasAttachments', False)})
                return (emails, tx('Retrieved successfully'))
            else:
                return ([], tx('API error: {0} - {1}', response.status_code, response.text[:200]))
        except Exception as e:
            return ([], tx('Network error: {0}', str(e)))

    def fetch_emails_imap(self, folder='INBOX', limit=50):
        (success, msg) = self.connect_imap()
        if not success:
            return ([], msg)
        try:
            (select_status, select_data) = self.connection.select(folder)
            if select_status != 'OK':
                return ([], tx('Cannot open folder {0}: {1}', folder, select_data))
            (status, messages) = self.connection.search(None, 'ALL')
            if status != 'OK':
                return ([], tx('Failed to retrieve messages'))
            email_ids = messages[0].split()
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            email_ids.reverse()
            emails = []
            for eid in email_ids:
                (status, msg_data) = self.connection.fetch(eid, '(RFC822 FLAGS)')
                if status == 'OK':
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    flags = msg_data[0][0].decode() if isinstance(msg_data[0][0], bytes) else str(msg_data[0][0])
                    is_read = '\\Seen' in flags
                    subject = self.decode_str(email_message.get('Subject', ''))
                    sender = self.decode_str(email_message.get('From', ''))
                    date_str = email_message.get('Date', '')
                    try:
                        date = parsedate_to_datetime(date_str)
                    except:
                        date = None
                    body = self.get_email_body(email_message)
                    emails.append({'uid': eid.decode() if isinstance(eid, bytes) else str(eid), 'subject': subject, 'sender': sender, 'sender_email': self.extract_email_address(sender), 'date': date, 'body': body, 'is_read': is_read, 'has_attachments': self.has_attachments(email_message)})
            return (emails, tx('Retrieved successfully'))
        except Exception as e:
            return ([], tx('Failed to retrieve messages: {0}', str(e)))

    def decode_str(self, s):
        if not s:
            return ''
        decoded_parts = decode_header(s)
        result = []
        for (part, charset) in decoded_parts:
            if isinstance(part, bytes):
                try:
                    result.append(part.decode(charset or 'utf-8', errors='ignore'))
                except:
                    result.append(part.decode('utf-8', errors='ignore'))
            else:
                result.append(part)
        return ''.join(result)

    def get_email_body(self, msg):
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        break
                    except:
                        pass
        else:
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, errors='ignore')
            except:
                pass
        return body[:5000]

    def extract_email_address(self, sender_str):
        import re
        match = re.search('<([^>]+)>', sender_str)
        if match:
            return match.group(1)
        if '@' in sender_str:
            return sender_str.strip()
        return ''

    def has_attachments(self, msg):
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = part.get('Content-Disposition', '')
                if 'attachment' in content_disposition:
                    return True
        return False

    def mark_as_read(self, email_id, folder='inbox', is_read=True):
        if self.use_graph_api():
            return self.mark_as_read_graph(email_id, is_read)
        else:
            actual_folder = self.get_folder_name(folder)
            return self.mark_as_read_imap(email_id, actual_folder, is_read)

    def mark_as_read_graph(self, email_id, is_read=True):
        (token, msg) = self.get_oauth2_access_token()
        if not token:
            return (False, msg)
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        if self._api_type == 'outlook':
            url = f'https://outlook.office.com/api/v2.0/me/messages/{email_id}'
            data = {'IsRead': is_read}
        else:
            url = f'https://graph.microsoft.com/v1.0/me/messages/{email_id}'
            data = {'isRead': is_read}
        try:
            response = requests.patch(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                return (True, tx('Marked successfully'))
            else:
                return (False, tx('Marking failed: {0}', response.status_code))
        except Exception as e:
            return (False, tx('Network error: {0}', str(e)))

    def mark_as_read_imap(self, email_id, folder='INBOX', is_read=True):
        (success, msg) = self.connect_imap()
        if not success:
            return (False, msg)
        try:
            self.connection.select(folder)
            flag_action = '+FLAGS' if is_read else '-FLAGS'
            eid = email_id.encode() if isinstance(email_id, str) else email_id
            self.connection.store(eid, flag_action, '\\Seen')
            return (True, tx('Marked successfully'))
        except Exception as e:
            return (False, tx('Marking failed: {0}', str(e)))
        finally:
            self.disconnect()

    def mark_emails_batch(self, email_ids, folder='inbox', is_read=True, progress_callback=None):
        if self.use_graph_api():
            return self.mark_emails_batch_graph(email_ids, is_read, progress_callback)
        else:
            actual_folder = self.get_folder_name(folder)
            return self.mark_emails_batch_imap(email_ids, actual_folder, is_read, progress_callback)

    def mark_emails_batch_graph(self, email_ids, is_read=True, progress_callback=None):
        (token, msg) = self.get_oauth2_access_token()
        if not token:
            return (0, len(email_ids))
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        if self._api_type == 'outlook':
            base_url = 'https://outlook.office.com/api/v2.0/me/messages'
            data = {'IsRead': is_read}
        else:
            base_url = 'https://graph.microsoft.com/v1.0/me/messages'
            data = {'isRead': is_read}
        success_count = 0
        fail_count = 0
        total = len(email_ids)
        for (i, email_id) in enumerate(email_ids):
            try:
                url = f'{base_url}/{email_id}'
                response = requests.patch(url, headers=headers, json=data, timeout=30)
                if response.status_code == 200:
                    success_count += 1
                else:
                    fail_count += 1
            except:
                fail_count += 1
            if progress_callback:
                progress_callback(i + 1, total)
        return (success_count, fail_count)

    def mark_emails_batch_imap(self, email_ids, folder='INBOX', is_read=True, progress_callback=None):
        (success, msg) = self.connect_imap()
        if not success:
            return (0, len(email_ids))
        success_count = 0
        fail_count = 0
        total = len(email_ids)
        flag_action = '+FLAGS' if is_read else '-FLAGS'
        try:
            self.connection.select(folder)
            for (i, email_id) in enumerate(email_ids):
                try:
                    eid = email_id.encode() if isinstance(email_id, str) else email_id
                    self.connection.store(eid, flag_action, '\\Seen')
                    success_count += 1
                except:
                    fail_count += 1
                if progress_callback:
                    progress_callback(i + 1, total)
        except Exception as e:
            return (0, total)
        finally:
            self.disconnect()
        return (success_count, fail_count)

    def get_attachments(self, email_id, folder='inbox'):
        if self.use_graph_api():
            return self.get_attachments_graph(email_id)
        else:
            actual_folder = self.get_folder_name(folder)
            return self.get_attachments_imap(email_id, actual_folder)

    def get_attachments_graph(self, email_id):
        (token, msg) = self.get_oauth2_access_token()
        if not token:
            return ([], msg)
        headers = {'Authorization': f'Bearer {token}'}
        if self._api_type == 'outlook':
            url = f'https://outlook.office.com/api/v2.0/me/messages/{email_id}/attachments'
        else:
            url = f'https://graph.microsoft.com/v1.0/me/messages/{email_id}/attachments'
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                attachments = []
                for att in data.get('value', []):
                    if self._api_type == 'outlook':
                        attachments.append({'id': att.get('Id', ''), 'name': att.get('Name', ''), 'size': att.get('Size', 0), 'content_type': att.get('ContentType', ''), 'content_bytes': att.get('ContentBytes', '')})
                    else:
                        attachments.append({'id': att.get('id', ''), 'name': att.get('name', ''), 'size': att.get('size', 0), 'content_type': att.get('contentType', ''), 'content_bytes': att.get('contentBytes', '')})
                return (attachments, tx('Retrieved successfully'))
            else:
                return ([], tx('Failed to retrieve attachments: {0}', response.status_code))
        except Exception as e:
            return ([], tx('Network error: {0}', str(e)))

    def get_attachments_imap(self, email_id, folder='INBOX'):
        (success, msg) = self.connect_imap()
        if not success:
            return ([], msg)
        try:
            self.connection.select(folder)
            eid = email_id.encode() if isinstance(email_id, str) else email_id
            (status, msg_data) = self.connection.fetch(eid, '(RFC822)')
            if status != 'OK':
                return ([], tx('Failed to retrieve messages'))
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            attachments = []
            for part in email_message.walk():
                content_disposition = part.get('Content-Disposition', '')
                if 'attachment' in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self.decode_str(filename)
                        content = part.get_payload(decode=True)
                        attachments.append({'id': filename, 'name': filename, 'size': len(content) if content else 0, 'content_type': part.get_content_type(), 'content_bytes': base64.b64encode(content).decode() if content else ''})
            return (attachments, tx('Retrieved successfully'))
        except Exception as e:
            return ([], tx('Failed to retrieve attachments: {0}', str(e)))
        finally:
            self.disconnect()

    def download_attachment(self, attachment):
        content_bytes = attachment.get('content_bytes', '')
        if content_bytes:
            return base64.b64decode(content_bytes)
        return None

    def send_email_with_attachments(self, to_addr, subject, body, attachments=None, cc_addr=None):
        if self.use_graph_api():
            return self.send_email_graph_with_attachments(to_addr, subject, body, attachments, cc_addr)
        else:
            return self.send_email_smtp_with_attachments(to_addr, subject, body, attachments, cc_addr)

    def send_email_graph_with_attachments(self, to_addr, subject, body, attachments=None, cc_addr=None):
        (token, msg) = self.get_oauth2_access_token()
        if not token:
            return (False, msg)
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        to_recipients = [{'emailAddress': {'address': addr.strip()}} for addr in to_addr.split(',') if addr.strip()]
        cc_recipients = []
        if cc_addr:
            cc_recipients = [{'emailAddress': {'address': addr.strip()}} for addr in cc_addr.split(',') if addr.strip()]
        attachment_data = []
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        content = base64.b64encode(f.read()).decode()
                    attachment_data.append({'@odata.type': '#microsoft.graph.fileAttachment', 'name': os.path.basename(file_path), 'contentBytes': content})
        if self._api_type == 'outlook':
            url = 'https://outlook.office.com/api/v2.0/me/sendmail'
            email_data = {'Message': {'Subject': subject, 'Body': {'ContentType': 'Text', 'Content': body}, 'ToRecipients': [{'EmailAddress': {'Address': addr.strip()}} for addr in to_addr.split(',') if addr.strip()], 'Attachments': [{'@odata.type': '#Microsoft.OutlookServices.FileAttachment', 'Name': att['name'], 'ContentBytes': att['contentBytes']} for att in attachment_data]}}
            if cc_addr:
                email_data['Message']['CcRecipients'] = [{'EmailAddress': {'Address': addr.strip()}} for addr in cc_addr.split(',') if addr.strip()]
        else:
            url = 'https://graph.microsoft.com/v1.0/me/sendMail'
            email_data = {'message': {'subject': subject, 'body': {'contentType': 'Text', 'content': body}, 'toRecipients': to_recipients, 'attachments': attachment_data}}
            if cc_recipients:
                email_data['message']['ccRecipients'] = cc_recipients
        try:
            response = requests.post(url, headers=headers, json=email_data, timeout=60)
            if response.status_code in [200, 202]:
                return (True, tx('Sent successfully'))
            else:
                return (False, tx('Sending failed: {0} - {1}', response.status_code, response.text[:200]))
        except Exception as e:
            return (False, tx('Network error: {0}', str(e)))

    def send_email_smtp_with_attachments(self, to_addr, subject, body, attachments=None, cc_addr=None):
        (smtp_server, smtp_port) = self.get_smtp_server()
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_addr
            msg['To'] = to_addr
            msg['Subject'] = subject
            if cc_addr:
                msg['Cc'] = cc_addr
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
                        msg.attach(part)
            all_recipients = [addr.strip() for addr in to_addr.split(',') if addr.strip()]
            if cc_addr:
                all_recipients.extend([addr.strip() for addr in cc_addr.split(',') if addr.strip()])
            if smtp_port == 465:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
            server.login(self.email_addr, self.password)
            server.sendmail(self.email_addr, all_recipients, msg.as_string())
            server.quit()
            return (True, tx('Sent successfully'))
        except Exception as e:
            return (False, tx('Sending failed: {0}', str(e)))

    def get_smtp_server(self):
        domain = self.email_addr.split('@')[-1].lower()
        return self.SMTP_SERVERS.get(domain, (f'smtp.{domain}', 587))

    def send_email(self, to_addr, subject, body, cc_addr=None):
        if self.use_graph_api():
            return self.send_email_graph(to_addr, subject, body, cc_addr)
        else:
            return self.send_email_smtp(to_addr, subject, body, cc_addr)

    def send_email_graph(self, to_addr, subject, body, cc_addr=None):
        (token, msg) = self.get_oauth2_access_token()
        if not token:
            return (False, msg)
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        to_recipients = [{'emailAddress': {'address': addr.strip()}} for addr in to_addr.split(',') if addr.strip()]
        cc_recipients = []
        if cc_addr:
            cc_recipients = [{'emailAddress': {'address': addr.strip()}} for addr in cc_addr.split(',') if addr.strip()]
        if self._api_type == 'outlook':
            url = 'https://outlook.office.com/api/v2.0/me/sendmail'
            email_data = {'Message': {'Subject': subject, 'Body': {'ContentType': 'Text', 'Content': body}, 'ToRecipients': [{'EmailAddress': {'Address': addr.strip()}} for addr in to_addr.split(',') if addr.strip()]}}
            if cc_addr:
                email_data['Message']['CcRecipients'] = [{'EmailAddress': {'Address': addr.strip()}} for addr in cc_addr.split(',') if addr.strip()]
        else:
            url = 'https://graph.microsoft.com/v1.0/me/sendMail'
            email_data = {'message': {'subject': subject, 'body': {'contentType': 'Text', 'content': body}, 'toRecipients': to_recipients}}
            if cc_recipients:
                email_data['message']['ccRecipients'] = cc_recipients
        try:
            response = requests.post(url, headers=headers, json=email_data, timeout=30)
            if response.status_code in [200, 202]:
                return (True, tx('Sent successfully'))
            else:
                return (False, tx('Sending failed: {0} - {1}', response.status_code, response.text[:200]))
        except Exception as e:
            return (False, tx('Network error: {0}', str(e)))

    def send_email_smtp(self, to_addr, subject, body, cc_addr=None):
        (smtp_server, smtp_port) = self.get_smtp_server()
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_addr
            msg['To'] = to_addr
            msg['Subject'] = subject
            if cc_addr:
                msg['Cc'] = cc_addr
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            all_recipients = [addr.strip() for addr in to_addr.split(',') if addr.strip()]
            if cc_addr:
                all_recipients.extend([addr.strip() for addr in cc_addr.split(',') if addr.strip()])
            if smtp_port == 465:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
            server.login(self.email_addr, self.password)
            server.sendmail(self.email_addr, all_recipients, msg.as_string())
            server.quit()
            return (True, tx('Sent successfully'))
        except smtplib.SMTPAuthenticationError as e:
            return (False, tx('Authentication failed: {0}', str(e)))
        except smtplib.SMTPException as e:
            return (False, tx('SMTP error: {0}', str(e)))
        except Exception as e:
            return (False, tx('Sending failed: {0}', str(e)))

    def delete_email(self, email_id, folder='inbox'):
        if self.use_graph_api():
            return self.delete_email_graph(email_id)
        else:
            actual_folder = self.get_folder_name(folder)
            return self.delete_email_imap(email_id, actual_folder)

    def delete_email_graph(self, email_id):
        (token, msg) = self.get_oauth2_access_token()
        if not token:
            return (False, msg)
        headers = {'Authorization': f'Bearer {token}'}
        if self._api_type == 'outlook':
            url = f'https://outlook.office.com/api/v2.0/me/messages/{email_id}'
        else:
            url = f'https://graph.microsoft.com/v1.0/me/messages/{email_id}'
        try:
            response = requests.delete(url, headers=headers, timeout=30)
            if response.status_code in [200, 204]:
                return (True, tx('Deleted successfully'))
            else:
                return (False, tx('Deletion failed: {0}', response.status_code))
        except Exception as e:
            return (False, tx('Network error: {0}', str(e)))

    def delete_email_imap(self, email_id, folder='INBOX'):
        (success, msg) = self.connect_imap()
        if not success:
            return (False, msg)
        try:
            self.connection.select(folder)
            self.connection.store(email_id.encode() if isinstance(email_id, str) else email_id, '+FLAGS', '\\Deleted')
            self.connection.expunge()
            return (True, tx('Deleted successfully'))
        except Exception as e:
            return (False, tx('Deletion failed: {0}', str(e)))
        finally:
            self.disconnect()

    def delete_emails_batch(self, email_ids, folder='inbox', progress_callback=None):
        if self.use_graph_api():
            return self.delete_emails_batch_graph(email_ids, progress_callback)
        else:
            actual_folder = self.get_folder_name(folder)
            return self.delete_emails_batch_imap(email_ids, actual_folder, progress_callback)

    def delete_emails_batch_graph(self, email_ids, progress_callback=None):
        (token, msg) = self.get_oauth2_access_token()
        if not token:
            return (0, len(email_ids))
        headers = {'Authorization': f'Bearer {token}'}
        if self._api_type == 'outlook':
            base_url = 'https://outlook.office.com/api/v2.0/me/messages'
        else:
            base_url = 'https://graph.microsoft.com/v1.0/me/messages'
        success_count = 0
        fail_count = 0
        total = len(email_ids)
        for (i, email_id) in enumerate(email_ids):
            try:
                url = f'{base_url}/{email_id}'
                response = requests.delete(url, headers=headers, timeout=30)
                if response.status_code in [200, 204]:
                    success_count += 1
                else:
                    fail_count += 1
            except:
                fail_count += 1
            if progress_callback:
                progress_callback(i + 1, total)
        return (success_count, fail_count)

    def check_aws_verification_emails(self, limit=50):
        aws_keywords = ['aws', 'amazon']
        try:
            (emails, msg) = self.fetch_emails(folder='inbox', limit=limit)
            if not emails:
                return (False, 0)
            aws_count = 0
            for email_data in emails:
                subject = email_data.get('subject', '').lower()
                if any((kw in subject for kw in aws_keywords)):
                    aws_count += 1
            return (aws_count > 0, aws_count)
        except Exception as e:
            return (False, 0)

    def delete_emails_batch_imap(self, email_ids, folder='INBOX', progress_callback=None):
        (success, msg) = self.connect_imap()
        if not success:
            return (0, len(email_ids))
        success_count = 0
        fail_count = 0
        total = len(email_ids)
        try:
            self.connection.select(folder)
            for (i, email_id) in enumerate(email_ids):
                try:
                    eid = email_id.encode() if isinstance(email_id, str) else email_id
                    self.connection.store(eid, '+FLAGS', '\\Deleted')
                    success_count += 1
                except:
                    fail_count += 1
                if progress_callback:
                    progress_callback(i + 1, total)
            self.connection.expunge()
        except Exception as e:
            return (0, total)
        finally:
            self.disconnect()
        return (success_count, fail_count)
