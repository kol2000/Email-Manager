from core.i18n import tx
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QFrame, QDialog, QLineEdit, QMenu, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QColor
from ui.theme import LIGHT_DIALOG_STYLE, LIGHT_INPUT_STYLE, LIGHT_BTN_CANCEL_STYLE, LIGHT_BTN_OK_STYLE, LIGHT_MENU_STYLE, DARK_DIALOG_STYLE, DARK_INPUT_STYLE, DARK_BTN_CANCEL_STYLE, DARK_BTN_OK_STYLE, DARK_MENU_STYLE

class BaseGroupDialog(QDialog):

    def __init__(self, db, title, label_text, parent=None, initial_value='', is_dark=False):
        super().__init__(parent)
        self.db = db
        self.is_dark = is_dark
        self.setWindowTitle(title)
        self.setFixedSize(380, 220)
        self._apply_theme()
        self._init_ui(label_text, initial_value)

    def _apply_theme(self):
        if self.is_dark:
            self.setStyleSheet(DARK_DIALOG_STYLE)
            self.input_style = DARK_INPUT_STYLE
            self.btn_cancel_style = DARK_BTN_CANCEL_STYLE
            self.btn_ok_style = DARK_BTN_OK_STYLE
            self.label_color = '#c9d1d9'
            self.error_color = '#f85149'
        else:
            self.setStyleSheet(LIGHT_DIALOG_STYLE)
            self.input_style = LIGHT_INPUT_STYLE
            self.btn_cancel_style = LIGHT_BTN_CANCEL_STYLE
            self.btn_ok_style = LIGHT_BTN_OK_STYLE
            self.label_color = '#1A1A1A'
            self.error_color = '#D13438'

    def _init_ui(self, label_text, initial_value):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(12)
        label = QLabel(label_text)
        label.setStyleSheet(f'color: {self.label_color}; font-size: 13px;')
        layout.addWidget(label)
        layout.addSpacing(4)
        self.input = QLineEdit()
        self.input.setFixedHeight(38)
        self.input.setStyleSheet(self.input_style)
        self.input.returnPressed.connect(self.try_accept)
        if initial_value:
            self.input.setText(initial_value)
            self.input.selectAll()
        layout.addWidget(self.input)
        self.error_label = QLabel('')
        self.error_label.setFixedHeight(20)
        self.error_label.setStyleSheet(f'color: {self.error_color}; font-size: 12px;')
        layout.addWidget(self.error_label)
        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton(tx('Cancel'))
        btn_cancel.setFixedSize(80, 36)
        btn_cancel.setStyleSheet(self.btn_cancel_style)
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton(tx('OK'))
        btn_ok.setFixedSize(80, 36)
        btn_ok.setStyleSheet(self.btn_ok_style)
        btn_ok.clicked.connect(self.try_accept)
        btn_row.addWidget(btn_cancel)
        btn_row.addSpacing(12)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def try_accept(self):
        raise NotImplementedError

    def get_name(self):
        return self.input.text().strip()

class AddGroupDialog(BaseGroupDialog):

    def __init__(self, db, parent=None, is_dark=False):
        super().__init__(db, tx('New group'), tx('Enter group name:'), parent, is_dark=is_dark)

    def try_accept(self):
        name = self.input.text().strip()
        if not name:
            self.error_label.setText(tx('Group name cannot be empty'))
            return
        existing = [g[1] for g in self.db.get_all_groups()]
        if name in existing:
            self.error_label.setText(tx('Group already exists. Choose another name.'))
            return
        self.accept()

class RenameGroupDialog(BaseGroupDialog):

    def __init__(self, db, old_name, parent=None, is_dark=False):
        self.old_name = old_name
        super().__init__(db, tx('Rename group'), tx('Enter the new group name:'), parent, old_name, is_dark=is_dark)

    def try_accept(self):
        name = self.input.text().strip()
        if not name:
            self.error_label.setText(tx('Group name cannot be empty'))
            return
        if name != self.old_name:
            existing = [g[1] for g in self.db.get_all_groups()]
            if name in existing:
                self.error_label.setText(tx('Group already exists. Choose another name.'))
                return
        self.accept()

class Sidebar(QWidget):
    group_selected = pyqtSignal(str)
    theme_changed = pyqtSignal(str)
    language_changed = pyqtSignal()
    settings_clicked = pyqtSignal()
    dashboard_clicked = pyqtSignal()
    oauth_clicked = pyqtSignal()

    def __init__(self, db, is_dark=False):
        super().__init__()
        self.db = db
        self.is_dark = is_dark
        self.init_ui()
        self.load_groups()

    def init_ui(self):
        self.setFixedWidth(280)
        self._apply_base_style()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.logo_widget = QWidget()
        self.logo_widget.setFixedHeight(72)
        self.logo_widget.setStyleSheet('background: transparent; border: none;')
        logo_layout = QHBoxLayout(self.logo_widget)
        logo_layout.setContentsMargins(24, 0, 24, 0)
        logo_icon = QLabel('📧')
        logo_icon.setStyleSheet('font-size: 28px; border: none; background: transparent;')
        self.logo_text = QLabel(tx('Email Manager'))
        self._apply_logo_style()
        logo_layout.addWidget(logo_icon)
        logo_layout.addSpacing(12)
        logo_layout.addWidget(self.logo_text)
        logo_layout.addStretch()
        layout.addWidget(self.logo_widget)
        self.line = QFrame()
        self.line.setFixedHeight(1)
        self._apply_line_style()
        layout.addWidget(self.line)
        layout.addSpacing(12)
        self.btn_all = QPushButton(tx('  📋  All accounts'))
        self.btn_all.setCheckable(True)
        self.btn_all.setChecked(True)
        self._apply_nav_style()
        self.btn_all.clicked.connect(lambda : self.on_nav_click('All'))
        layout.addWidget(self.btn_all)
        self.group_header = QWidget()
        self.group_header.setStyleSheet('background: transparent;')
        gh_layout = QHBoxLayout(self.group_header)
        gh_layout.setContentsMargins(20, 20, 20, 10)
        self.group_title = QLabel(tx('Group'))
        self._apply_group_title_style()
        gh_layout.addWidget(self.group_title)
        gh_layout.addStretch()
        self.btn_add = QPushButton('+')
        self.btn_add.setFixedSize(26, 26)
        self._apply_add_btn_style()
        self.btn_add.clicked.connect(self.add_group)
        gh_layout.addWidget(self.btn_add)
        layout.addWidget(self.group_header)
        self.group_list = QListWidget()
        self.group_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.group_list.customContextMenuRequested.connect(self.show_group_menu)
        self._apply_list_style()
        self.group_list.itemClicked.connect(self.on_group_click)
        layout.addWidget(self.group_list)
        layout.addStretch()
        self.btn_oauth = QPushButton(tx('  🗝  Authorization'))
        self.btn_oauth.setCheckable(True)
        self._apply_oauth_btn_style()
        self.btn_oauth.clicked.connect(self.on_oauth_click)
        layout.addWidget(self.btn_oauth)
        self.btn_dashboard = QPushButton(tx('  📈  Dashboard'))
        self.btn_dashboard.setCheckable(True)
        self._apply_dashboard_btn_style()
        self.btn_dashboard.clicked.connect(self.on_dashboard_click)
        layout.addWidget(self.btn_dashboard)
        self.btn_settings = QPushButton(tx('  ⚙  Settings'))
        self.btn_settings.setCheckable(True)
        self._apply_settings_btn_style()
        self.btn_settings.clicked.connect(self.on_settings_click)
        layout.addWidget(self.btn_settings)
        self.bottom_bar = QWidget()
        self.bottom_bar.setStyleSheet('background: transparent;')
        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.setContentsMargins(16, 12, 16, 16)
        bottom_layout.setSpacing(8)
        self.theme_btn = QPushButton()
        self.theme_btn.setFixedSize(44, 44)
        self._update_theme_btn_icon()
        self._apply_icon_btn_style(self.theme_btn)
        self.theme_btn.clicked.connect(self.show_theme_menu)
        self.theme_btn.setToolTip(tx('Switch theme'))
        bottom_layout.addWidget(self.theme_btn)
        self.lang_btn = QPushButton()
        self.lang_btn.setFixedSize(80, 44)
        self._update_lang_btn_text()
        self._apply_lang_btn_style()
        self.lang_btn.clicked.connect(self.show_lang_menu)
        self.lang_btn.setToolTip(tx('Switch language'))
        bottom_layout.addWidget(self.lang_btn)
        bottom_layout.addStretch()
        layout.addWidget(self.bottom_bar)

    def _apply_base_style(self):
        if self.is_dark:
            self.setStyleSheet('\n                QWidget {\n                    background: #161b22;\n                    border-right: 1px solid #30363d;\n                }\n            ')
        else:
            self.setStyleSheet('\n                QWidget {\n                    background: #F9FAFB;\n                    border-right: 1px solid #E5E7EB;\n                }\n            ')

    def _apply_logo_style(self):
        if self.is_dark:
            self.logo_text.setStyleSheet("\n                font-size: 20px; \n                font-weight: 600; \n                color: #c9d1d9;\n                font-family: 'Segoe UI', 'Microsoft YaHei UI';\n                background: transparent;\n            ")
        else:
            self.logo_text.setStyleSheet("\n                font-size: 20px; \n                font-weight: 600; \n                color: #111827;\n                font-family: 'Segoe UI', 'Microsoft YaHei UI';\n                background: transparent;\n            ")

    def _apply_line_style(self):
        if self.is_dark:
            self.line.setStyleSheet('background-color: #30363d;')
        else:
            self.line.setStyleSheet('background-color: #E5E7EB;')

    def _apply_nav_style(self):
        if self.is_dark:
            self.btn_all.setStyleSheet('\n                QPushButton {\n                    text-align: left;\n                    padding-left: 12px;\n                    border: none;\n                    background: transparent;\n                    color: #c9d1d9;\n                    font-size: 14px;\n                    font-weight: 500;\n                    height: 40px;\n                    margin: 4px 12px;\n                    border-radius: 6px;\n                }\n                QPushButton:hover {\n                    background: #21262d;\n                    color: #FFFFFF;\n                }\n                QPushButton:checked {\n                    background: #1f6feb33;\n                    color: #58a6ff;\n                }\n            ')
        else:
            self.btn_all.setStyleSheet('\n                QPushButton {\n                    text-align: left;\n                    padding-left: 12px;\n                    border: none;\n                    background: transparent;\n                    color: #374151;\n                    font-size: 14px;\n                    font-weight: 500;\n                    height: 40px;\n                    margin: 4px 12px;\n                    border-radius: 6px;\n                }\n                QPushButton:hover {\n                    background: #F3F4F6;\n                    color: #111827;\n                }\n                QPushButton:checked {\n                    background: #EFF6FF;\n                    color: #2563EB;\n                    font-weight: 600;\n                }\n            ')

    def _apply_group_title_style(self):
        if self.is_dark:
            self.group_title.setStyleSheet('\n                background: transparent;\n                color: #8b949e;\n                font-size: 11px;\n                font-weight: 600;\n                text-transform: uppercase;\n                letter-spacing: 2px;\n            ')
        else:
            self.group_title.setStyleSheet('\n                background: transparent;\n                color: #6B7280;\n                font-size: 11px;\n                font-weight: 600;\n                text-transform: uppercase;\n                letter-spacing: 2px;\n            ')

    def _apply_add_btn_style(self):
        if self.is_dark:
            self.btn_add.setStyleSheet('\n                QPushButton {\n                    color: #8b949e;\n                    background: transparent;\n                    border: 1px solid #30363d;\n                    border-radius: 4px;\n                    padding-bottom: 2px;\n                }\n                QPushButton:hover {\n                    color: #58a6ff;\n                    border-color: #58a6ff;\n                    background: #1f6feb11;\n                }\n            ')
        else:
            self.btn_add.setStyleSheet('\n                QPushButton {\n                    color: #6B7280;\n                    background: transparent;\n                    border: 1px solid #E5E7EB;\n                    border-radius: 4px;\n                    padding-bottom: 2px;\n                }\n                QPushButton:hover {\n                    color: #2563EB;\n                    border-color: #2563EB;\n                    background: #EFF6FF;\n                }\n            ')

    def _apply_common_btn_style(self, btn):
        if self.is_dark:
            btn.setStyleSheet('\n                QPushButton {\n                    text-align: left;\n                    padding-left: 12px;\n                    border: none;\n                    background: transparent;\n                    color: #c9d1d9;\n                    font-size: 14px;\n                    font-weight: normal;\n                    height: 40px;\n                    margin: 2px 12px;\n                    border-radius: 6px;\n                }\n                QPushButton:hover {\n                    background: #21262d;\n                    color: #FFFFFF;\n                }\n                QPushButton:checked {\n                    background: #1f6feb33;\n                    color: #58a6ff;\n                }\n            ')
        else:
            btn.setStyleSheet('\n                QPushButton {\n                    text-align: left;\n                    padding-left: 12px;\n                    border: none;\n                    background: transparent;\n                    color: #374151;\n                    font-size: 14px;\n                    font-weight: normal;\n                    height: 40px;\n                    margin: 2px 12px;\n                    border-radius: 6px;\n                }\n                QPushButton:hover {\n                    background: #F3F4F6;\n                    color: #111827;\n                }\n                QPushButton:checked {\n                    background: #EFF6FF;\n                    color: #2563EB;\n                    font-weight: 600;\n                }\n            ')

    def _apply_oauth_btn_style(self):
        self._apply_common_btn_style(self.btn_oauth)

    def _apply_dashboard_btn_style(self):
        self._apply_common_btn_style(self.btn_dashboard)

    def _apply_settings_btn_style(self):
        self._apply_common_btn_style(self.btn_settings)

    def _apply_list_style(self):
        if self.is_dark:
            self.group_list.setStyleSheet('\n                QListWidget {\n                    background: transparent;\n                    border: none;\n                    outline: none;\n                    padding: 4px 12px;\n                }\n                QListWidget::item {\n                    height: 36px;\n                    border-radius: 6px;\n                    padding-left: 12px;\n                    margin-bottom: 2px;\n                    color: #8b949e;\n                }\n                QListWidget::item:hover {\n                    background: #21262d;\n                    color: #c9d1d9;\n                }\n                QListWidget::item:selected {\n                    background: #1f6feb33;\n                    color: #58a6ff;\n                }\n            ')
        else:
            self.group_list.setStyleSheet('\n                QListWidget {\n                    background: transparent;\n                    border: none;\n                    outline: none;\n                    padding: 4px 12px;\n                }\n                QListWidget::item {\n                    height: 36px;\n                    border-radius: 6px;\n                    padding-left: 12px;\n                    margin-bottom: 2px;\n                    color: #4B5563;\n                }\n                QListWidget::item:hover {\n                    background: #F3F4F6;\n                    color: #111827;\n                }\n                QListWidget::item:selected {\n                    background: #EFF6FF;\n                    color: #2563EB;\n                    font-weight: 600;\n                }\n            ')

    def _apply_icon_btn_style(self, btn):
        if self.is_dark:
            btn.setStyleSheet('\n                QPushButton {\n                    background: rgba(255,255,255,0.08);\n                    border: 1px solid rgba(255,255,255,0.1);\n                    border-radius: 16px;\n                    font-size: 18px;\n                }\n                QPushButton:hover {\n                    background: rgba(255,255,255,0.12);\n                    border-color: rgba(88,166,255,0.5);\n                }\n            ')
        else:
            btn.setStyleSheet('\n                QPushButton {\n                    background: rgba(255,255,255,0.5);\n                    border: 1px solid rgba(0,120,212,0.2);\n                    border-radius: 16px;\n                    font-size: 18px;\n                }\n                QPushButton:hover {\n                    background: rgba(255,255,255,0.8);\n                    border-color: rgba(0,120,212,0.5);\n                }\n            ')

    def _apply_lang_btn_style(self):
        if self.is_dark:
            self.lang_btn.setStyleSheet('\n                QPushButton {\n                    background: rgba(255,255,255,0.08);\n                    border: 1px solid rgba(255,255,255,0.1);\n                    border-radius: 16px;\n                    font-size: 13px;\n                    color: #8b949e;\n                }\n                QPushButton:hover {\n                    background: rgba(255,255,255,0.12);\n                    border-color: rgba(88,166,255,0.5);\n                    color: #c9d1d9;\n                }\n            ')
        else:
            self.lang_btn.setStyleSheet('\n                QPushButton {\n                    background: rgba(255,255,255,0.5);\n                    border: 1px solid rgba(0,120,212,0.2);\n                    border-radius: 16px;\n                    font-size: 13px;\n                    color: #1A5A8A;\n                }\n                QPushButton:hover {\n                    background: rgba(255,255,255,0.8);\n                    border-color: rgba(0,120,212,0.5);\n                    color: #004080;\n                }\n            ')

    def _update_theme_btn_icon(self):
        if self.is_dark:
            self.theme_btn.setText('🌙')
        else:
            self.theme_btn.setText('☀️')

    def _update_lang_btn_text(self):
        from core.i18n import get_language
        lang = get_language()
        if lang == 'ru':
            self.lang_btn.setText(tx('RU'))
        else:
            self.lang_btn.setText(tx('EN'))

    def show_theme_menu(self):
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        menu.setStyleSheet(DARK_MENU_STYLE if self.is_dark else LIGHT_MENU_STYLE)
        shadow = QGraphicsDropShadowEffect(menu)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50 if self.is_dark else 30))
        shadow.setOffset(0, 4)
        menu.setGraphicsEffect(shadow)
        action_light = menu.addAction(tx('☀️  Light'))
        action_dark = menu.addAction(tx('🌙  Dark'))
        if self.is_dark:
            action_dark.setEnabled(False)
        else:
            action_light.setEnabled(False)
        action = menu.exec_(QCursor.pos())
        if action == action_light:
            self.theme_changed.emit('light')
        elif action == action_dark:
            self.theme_changed.emit('dark')

    def show_lang_menu(self):
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        menu.setStyleSheet(DARK_MENU_STYLE if self.is_dark else LIGHT_MENU_STYLE)
        shadow = QGraphicsDropShadowEffect(menu)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50 if self.is_dark else 30))
        shadow.setOffset(0, 4)
        menu.setGraphicsEffect(shadow)
        from core.i18n import get_language, set_language
        current_lang = get_language()
        action_ru = menu.addAction(tx('Русский'))
        action_en = menu.addAction('English')
        if current_lang == 'ru':
            action_ru.setEnabled(False)
        else:
            action_en.setEnabled(False)
        action = menu.exec_(QCursor.pos())
        if action == action_ru:
            set_language('ru')
            self._update_lang_btn_text()
            self.lang_changed_signal()
        elif action == action_en:
            set_language('en')
            self._update_lang_btn_text()
            self.lang_changed_signal()

    def lang_changed_signal(self):
        self.language_changed.emit()

    def refresh_language(self):
        from core.i18n import tr
        self.logo_text.setText(tr('app_name'))
        self.btn_all.setText('  📋  ' + tr('all_emails'))
        self.group_title.setText(tr('groups'))
        self.btn_oauth.setText('  🗝  ' + tr('manual_oauth'))
        self.btn_dashboard.setText('  📈  ' + tr('dashboard'))
        self.btn_settings.setText('  ⚙  ' + tr('settings'))
        self._update_lang_btn_text()
        self.theme_btn.setToolTip(tr('switch_theme'))
        self.lang_btn.setToolTip(tr('switch_language'))

    def apply_theme(self, is_dark):
        self.is_dark = is_dark
        self._apply_base_style()
        self._apply_logo_style()
        self._apply_line_style()
        self._apply_nav_style()
        self._apply_group_title_style()
        self._apply_add_btn_style()
        self._apply_oauth_btn_style()
        self._apply_dashboard_btn_style()
        self._apply_settings_btn_style()
        self._apply_list_style()
        self._apply_icon_btn_style(self.theme_btn)
        self._apply_lang_btn_style()
        self._update_theme_btn_icon()

    def load_groups(self):
        self.group_list.clear()
        groups = self.db.get_all_groups()
        for group in groups:
            item = QListWidgetItem('  📁  ' + (tx(group[1]) if group[1] == 'Default' else group[1]))
            item.setData(Qt.UserRole, group[1])
            self.group_list.addItem(item)

    def on_nav_click(self, name):
        self.btn_all.setChecked(name == 'All')
        self.btn_settings.setChecked(False)
        self.btn_dashboard.setChecked(False)
        self.btn_oauth.setChecked(False)
        self.group_list.clearSelection()
        self.group_selected.emit('All')

    def on_group_click(self, item):
        self.btn_all.setChecked(False)
        self.btn_settings.setChecked(False)
        self.btn_dashboard.setChecked(False)
        self.btn_oauth.setChecked(False)
        group_name = item.data(Qt.UserRole)
        self.group_selected.emit(group_name)

    def on_settings_click(self):
        self.btn_all.setChecked(False)
        self.group_list.clearSelection()
        self.btn_dashboard.setChecked(False)
        self.btn_oauth.setChecked(False)
        self.btn_settings.setChecked(True)
        self.settings_clicked.emit()

    def on_dashboard_click(self):
        self.btn_all.setChecked(False)
        self.group_list.clearSelection()
        self.btn_settings.setChecked(False)
        self.btn_oauth.setChecked(False)
        self.btn_dashboard.setChecked(True)
        self.dashboard_clicked.emit()

    def on_oauth_click(self):
        self.btn_all.setChecked(False)
        self.group_list.clearSelection()
        self.btn_settings.setChecked(False)
        self.btn_dashboard.setChecked(False)
        self.btn_oauth.setChecked(True)
        self.oauth_clicked.emit()

    def add_group(self):
        dialog = AddGroupDialog(self.db, self, is_dark=self.is_dark)
        if dialog.exec_():
            name = dialog.get_name()
            if name:
                self.db.add_group(name)
                self.load_groups()

    def show_group_menu(self, pos):
        item = self.group_list.itemAt(pos)
        if not item:
            return
        group_name = item.data(Qt.UserRole)
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        menu.setStyleSheet(DARK_MENU_STYLE if self.is_dark else LIGHT_MENU_STYLE)
        shadow = QGraphicsDropShadowEffect(menu)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50 if self.is_dark else 30))
        shadow.setOffset(0, 4)
        menu.setGraphicsEffect(shadow)
        action_rename = menu.addAction(tx('✏️  Rename'))
        action_delete = menu.addAction(tx('🗑️  Delete'))
        if group_name == 'Default':
            action_delete.setEnabled(False)
        action = menu.exec_(self.group_list.mapToGlobal(pos))
        if action == action_rename:
            self.rename_group(group_name)
        elif action == action_delete:
            self.delete_group(group_name)

    def rename_group(self, old_name):
        dialog = RenameGroupDialog(self.db, old_name, self, is_dark=self.is_dark)
        if dialog.exec_():
            new_name = dialog.get_name()
            if new_name and new_name != old_name:
                self.db.rename_group(old_name, new_name)
                self.load_groups()
                self.group_selected.emit('All')

    def delete_group(self, group_name):
        reply = QMessageBox.question(self, tx('Confirm deletion'), tx('Delete group "{0}"?\nIts accounts will be moved to the default group.', group_name), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_group(group_name)
            self.load_groups()
            self.group_selected.emit('All')
