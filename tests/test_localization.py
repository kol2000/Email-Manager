import os, sys, pathlib, tempfile, unittest, sqlite3, re, string
from unittest.mock import patch, Mock
from contextlib import closing
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'app'))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt5.QtWidgets import QApplication, QLabel, QAbstractButton, QLineEdit, QComboBox
from PyQt5.QtCore import QThread
from core.i18n import TRANSLATIONS, set_language, get_language, tx, tr
from core.catalog import RUSSIAN
from database.db_manager import DatabaseManager
from core.email_client import EmailClient
from ui.main_window import MainWindow
from ui.dialogs import ImportDialog, AccountDetailDialog, ComposeEmailDialog, EmailViewDialog, BatchSendDialog, ManualOAuth2Dialog
APP = QApplication.instance() or QApplication([])

class LocalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = str(pathlib.Path(self.temp.name) / 'emails.db')
        os.environ['EMAIL_MANAGER_DATA_FILE'] = self.db_path
        self.db = DatabaseManager()
        self.db.add_account('demo@example.com','test-password',client_id='test-client',refresh_token='test-refresh')
    def tearDown(self):
        for window in APP.topLevelWidgets(): window.close()
        APP.processEvents()
        self.temp.cleanup()
    def test_catalog_coverage_and_placeholders(self):
        self.assertEqual(set(TRANSLATIONS), {'en','ru'})
        self.assertEqual(set(TRANSLATIONS['en']),set(TRANSLATIONS['ru']))
        parser=string.Formatter()
        pairs=list(RUSSIAN.items())+[(v,TRANSLATIONS['ru'][k]) for k,v in TRANSLATIONS['en'].items()]
        for en,ru in pairs:
            self.assertFalse(re.search('[\u4e00-\u9fff]',en+ru))
            fields=lambda text: sorted(str(name) for _,name,_,_ in parser.parse(text) if name is not None)
            self.assertEqual(fields(en),fields(ru),en)
    def test_legacy_migration_preserves_accounts(self):
        with closing(self.db.get_connection()) as c:
            c.execute("UPDATE accounts SET group_name=?, status=?, account_type=?", ('\u9ed8\u8ba4\u5206\u7ec4','\u6b63\u5e38','\u666e\u901a'))
            c.execute('INSERT INTO groups(name) VALUES (?)',('\u9ed8\u8ba4\u5206\u7ec4',))
            c.execute("UPDATE settings SET value='zh' WHERE key='language'")
            c.commit()
        migrated=DatabaseManager(self.db_path)
        account=migrated.get_all_accounts()[0]
        self.assertEqual(account[1:6],('demo@example.com','test-password','Default','Normal','Standard'))
        self.assertEqual(account[10:12],('test-client','test-refresh'))
        self.assertEqual(migrated.get_setting('language'),'ru')
        DatabaseManager(self.db_path)
        self.assertEqual(len(migrated.get_all_accounts()),1)
    def test_import_and_refresh_are_language_independent(self):
        for language in ('ru','en'):
            set_language(language)
            parsed=ImportDialog.parse_accounts(None,'demo@outlook.com----pw----client----refresh')
            self.assertEqual(parsed[0]['refresh_token'],'refresh')
            account=self.db.get_all_accounts()[0]
            client=EmailClient('demo@outlook.com','pw',client_id='client',refresh_token='refresh',account_id=account[0],db_manager=self.db)
            response=Mock(status_code=200)
            response.json.return_value={'access_token':'access','refresh_token':'rotated','scope':'Mail.Read'}
            with patch('core.email_client.requests.post',return_value=response) as post:
                self.assertEqual(client.get_oauth2_access_token()[0],'access')
                self.assertEqual(post.call_args.kwargs['data']['refresh_token'],'refresh')
            self.assertEqual(self.db.get_all_accounts()[0][11],'rotated')
    def test_windows_and_language_switch(self):
        with patch.object(QThread,'start'):
            main=MainWindow();main.show();APP.processEvents()
            for language in ('ru','en','ru'):
                set_language(language);main.refresh_language();APP.processEvents();APP.processEvents()
                self.assertEqual(main.windowTitle(),tr('app_title'))
                main.open_settings();APP.processEvents()
                self.assertEqual({main.settings_lang_combo.itemData(i) for i in range(main.settings_lang_combo.count())},{'ru','en'})
                main.open_stats_dialog();APP.processEvents()
                main.open_oauth2_dialog();APP.processEvents()
                account=self.db.get_all_accounts()[0]
                dialogs=[ImportDialog(self.db),AccountDetailDialog(account),ComposeEmailDialog(account),EmailViewDialog(account,self.db),BatchSendDialog([account]),ManualOAuth2Dialog(self.db)]
                for dialog in dialogs:
                    dialog.show();APP.processEvents()
                    texts=[dialog.windowTitle()]
                    for widget in dialog.findChildren((QLabel,QAbstractButton,QLineEdit)):
                        texts.append(widget.text())
                    for combo in dialog.findChildren(QComboBox):
                        texts.extend(combo.itemText(i) for i in range(combo.count()))
                    self.assertFalse(any(re.search('[\u4e00-\u9fff]',text) for text in texts), texts)
                    dialog.close()
                inbox=EmailViewDialog(account,self.db)
                self.assertEqual(inbox.folder_combo.itemText(0),tx('Inbox'))
                inbox.close()
            main.close()

if __name__=='__main__': unittest.main()
