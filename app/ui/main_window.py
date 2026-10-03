from core.i18n import tx
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit, QComboBox, QMessageBox, QHeaderView, QFrame, QFileDialog, QCheckBox, QTextEdit, QGraphicsDropShadowEffect, QAbstractItemView, QMenu, QShortcut
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QDragEnterEvent, QDropEvent, QPainter, QPen, QBrush, QKeySequence
from database.db_manager import DatabaseManager
from ui.dialogs import ImportDialog, EmailViewDialog, BatchSendDialog, create_email_client, MENU_STYLE_LIGHT, MENU_STYLE_DARK, ManualOAuth2Dialog, AccountDetailDialog, FluentMessageBox
from ui.sidebar import Sidebar
from ui.theme import ThemeManager, LIGHT_THEME, DARK_THEME
from ui.system_tray import SystemTrayManager
from core.i18n import tr, set_language, get_language

class StatusCheckThread(QThread):
    status_updated = pyqtSignal(int, str)
    aws_updated = pyqtSignal(int, bool)
    progress_updated = pyqtSignal(int, int)
    finished_all = pyqtSignal()

    def __init__(self, accounts, db):
        super().__init__()
        self.accounts = accounts
        self.db = db
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def run(self):
        total = len(self.accounts)
        for (i, account) in enumerate(self.accounts):
            if self._stop_flag:
                break
            self.progress_updated.emit(i + 1, total)
            client = create_email_client(account, self.db)
            (status, _) = client.check_status()
            self.db.update_account_status(account[0], status)
            self.status_updated.emit(account[0], status)
            if status == 'Normal' and (not self._stop_flag):
                try:
                    (has_aws, _) = client.check_aws_verification_emails(limit=30)
                    self.db.update_aws_code_status(account[0], has_aws)
                    self.aws_updated.emit(account[0], has_aws)
                except:
                    pass
        self.finished_all.emit()

class FluentCheckBox(QCheckBox):

    def __init__(self, parent=None, is_dark=False):
        super().__init__(parent)
        self.is_dark = is_dark
        self.setFixedSize(24, 24)

    def set_dark_mode(self, is_dark):
        self.is_dark = is_dark
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRect(4, 4, 16, 16)
        if self.is_dark:
            bg_color = '#0d1117'
            border_color = '#484f58'
            check_color = '#3fb950'
            focus_color = '#58a6ff'
        else:
            bg_color = '#FFFFFF'
            border_color = '#9CA3AF'
            check_color = '#2563EB'
            focus_color = '#2563EB'
        if self.hasFocus():
            border_color = focus_color
            painter.setPen(QPen(QColor(border_color), 1.5))
        else:
            painter.setPen(QPen(QColor(border_color), 1.5))
        painter.setBrush(QBrush(QColor(bg_color)))
        painter.drawRoundedRect(rect, 3, 3)
        if self.isChecked():
            painter.setBrush(QBrush(QColor(check_color)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 3, 3)
            painter.setPen(QPen(Qt.white, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(7, 12, 10, 15)
            painter.drawLine(10, 15, 17, 8)
        painter.end()

class FluentButton(QPushButton):

    def __init__(self, text, btn_type='default', parent=None, is_dark=False):
        super().__init__(text, parent)
        self.btn_type = btn_type
        self.is_dark = is_dark
        self.setup_style()

    def setup_style(self):
        theme_data = DARK_THEME if self.is_dark else LIGHT_THEME
        key_map = {'primary': 'button_primary', 'success': 'button_success', 'warning': 'button_warning', 'danger': 'button_danger', 'subtle': 'button_subtle', 'default': 'button_default'}
        theme_key = key_map.get(self.btn_type, 'button_default')
        style = theme_data.get(theme_key, theme_data['button_default'])
        self.setStyleSheet(style)

    def set_dark_mode(self, is_dark):
        self.is_dark = is_dark
        self.setup_style()

class FluentCard(QFrame):

    def __init__(self, parent=None, is_dark=False):
        super().__init__(parent)
        self.is_dark = is_dark
        self._apply_style()
        self._apply_shadow()

    def _apply_style(self):
        if self.is_dark:
            self.setStyleSheet('\n                QFrame {\n                    background-color: #161b22;\n                    border: none;\n                    border-radius: 12px;\n                }\n            ')
        else:
            self.setStyleSheet('\n                QFrame {\n                    background-color: #FFFFFF;\n                    border: none;\n                    border-radius: 12px;\n                }\n            ')

    def _apply_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        if self.is_dark:
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(0, 0, 0, 60))
            shadow.setOffset(0, 4)
        else:
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(0, 0, 0, 30))
            shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def set_dark_mode(self, is_dark):
        self.is_dark = is_dark
        self._apply_style()
        self._apply_shadow()

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.current_group = 'All'
        self.sort_by = 'id'
        self.sort_order = 'DESC'
        self.theme_manager = ThemeManager(self.db, self)
        self.theme_manager.load_theme()
        self.load_settings()
        self._display_language = get_language()
        self.init_ui()
        self.setup_shortcuts()
        self.load_accounts()
        self.tray_manager = SystemTrayManager(self)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.txt'):
                    event.acceptProposedAction()
                    self.show_drag_overlay(True)
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.show_drag_overlay(False)

    def dropEvent(self, event: QDropEvent):
        self.show_drag_overlay(False)
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.txt'):
                self.import_from_dropped_file(file_path)
                break
        event.acceptProposedAction()

    def show_drag_overlay(self, show):
        if not hasattr(self, 'drag_overlay'):
            self.drag_overlay = QLabel(self)
            self.drag_overlay.setAlignment(Qt.AlignCenter)
        is_dark = self.theme_manager.is_dark()
        if is_dark:
            self.drag_overlay.setStyleSheet('\n                QLabel {\n                    background-color: rgba(35, 134, 54, 0.9);\n                    color: white;\n                    font-size: 24px;\n                    font-weight: 600;\n                    border: 3px dashed white;\n                    border-radius: 16px;\n                }\n            ')
        else:
            self.drag_overlay.setStyleSheet('\n                QLabel {\n                    background-color: rgba(0, 120, 212, 0.9);\n                    color: white;\n                    font-size: 24px;\n                    font-weight: 600;\n                    border: 3px dashed white;\n                    border-radius: 16px;\n                }\n            ')
        self.drag_overlay.setText(tx('📥 Drop to import accounts'))
        if show:
            self.drag_overlay.setGeometry(50, 50, self.width() - 100, self.height() - 100)
            self.drag_overlay.raise_()
            self.drag_overlay.show()
        else:
            self.drag_overlay.hide()

    def import_from_dropped_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if not content.strip():
                QMessageBox.warning(self, tr('warning'), tx('The file is empty'))
                return
            dialog = ImportDialog(self.db, self, default_group=None if self.current_group == 'All' else self.current_group)
            dialog.text_edit.setText(content)
            if dialog.exec_():
                self.load_accounts()
                self.load_group_filter()
                self.sidebar.load_groups()
        except Exception as e:
            QMessageBox.warning(self, tr('warning'), tx('Failed to read file: {0}', e))

    def load_settings(self):
        lang = self.db.get_setting('language', 'ru')
        set_language(lang)
        self.font_size = int(self.db.get_setting('font_size', '13'))

    def init_ui(self):
        self.setWindowTitle(tr('app_title'))
        self.setMinimumSize(1200, 700)
        self.resize(1600, 850)
        self._apply_global_style()
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.sidebar = Sidebar(self.db, is_dark=self.theme_manager.is_dark())
        self.sidebar.group_selected.connect(self.on_group_selected)
        self.sidebar.theme_changed.connect(self.set_theme)
        self.sidebar.language_changed.connect(self.refresh_language)
        self.sidebar.settings_clicked.connect(self.open_settings)
        self.sidebar.dashboard_clicked.connect(self.open_stats_dialog)
        self.sidebar.oauth_clicked.connect(self.open_oauth2_dialog)
        main_layout.addWidget(self.sidebar)
        self.content = QWidget()
        self._apply_content_style()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(28, 28, 28, 28)
        content_layout.setSpacing(20)
        self.create_header(content_layout)
        self.create_toolbar(content_layout)
        self.create_table(content_layout)
        main_layout.addWidget(self.content, 1)
        self.load_group_filter()

    def _apply_global_style(self):
        is_dark = self.theme_manager.is_dark()
        if is_dark:
            self.setStyleSheet(f"\n                QMainWindow {{ \n                    background: #0d1117;\n                }}\n                QWidget {{ \n                    font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif; \n                    font-size: {self.font_size}px; \n                }}\n                QCheckBox {{\n                    spacing: 8px;\n                }}\n                QCheckBox::indicator {{\n                    width: 16px;\n                    height: 16px;\n                    border: 2px solid #30363d;\n                    border-radius: 3px;\n                    background: #0d1117;\n                }}\n                QCheckBox::indicator:hover {{\n                    border-color: #58a6ff;\n                }}\n                QCheckBox::indicator:checked {{\n                    background: #238636;\n                    border-color: #238636;\n                }}\n                QToolTip {{\n                    background-color: #21262d;\n                    color: #e6edf3;\n                    border: none;\n                    padding: 8px 14px;\n                    border-radius: 8px;\n                    font-size: 12px;\n                }}\n                QScrollBar:vertical {{\n                    background: #0d1117;\n                    width: 10px;\n                    margin: 0px;\n                }}\n                QScrollBar::handle:vertical {{\n                    background: #30363d;\n                    min-height: 30px;\n                    border-radius: 5px;\n                }}\n                QScrollBar::handle:vertical:hover {{\n                    background: #484f58;\n                }}\n                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{\n                    height: 0px;\n                }}\n                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{\n                    background: none;\n                }}\n            ")
        else:
            self.setStyleSheet(f"\n                QMainWindow {{ \n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, \n                        stop:0 #F8F9FA, stop:1 #E9ECEF);\n                }}\n                QWidget {{ \n                    font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif; \n                    font-size: {self.font_size}px; \n                }}\n                QCheckBox {{\n                    spacing: 8px;\n                }}\n                QCheckBox::indicator {{\n                    width: 16px;\n                    height: 16px;\n                    border: 2px solid #C0C0C0;\n                    border-radius: 3px;\n                    background: #FFFFFF;\n                }}\n                QCheckBox::indicator:hover {{\n                    border-color: #0078D4;\n                }}\n                QCheckBox::indicator:checked {{\n                    background: #0078D4;\n                    border-color: #0078D4;\n                }}\n                QToolTip {{\n                    background-color: #FFFFFF;\n                    color: #333333;\n                    border: none;\n                    padding: 8px 14px;\n                    border-radius: 8px;\n                    font-size: 12px;\n                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);\n                }}\n                QScrollBar:vertical {{\n                    background: transparent;\n                    width: 10px;\n                    margin: 0px;\n                }}\n                QScrollBar::handle:vertical {{\n                    background: #C0C0C0;\n                    min-height: 30px;\n                    border-radius: 5px;\n                }}\n                QScrollBar::handle:vertical:hover {{\n                    background: #A0A0A0;\n                }}\n                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{\n                    height: 0px;\n                }}\n                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{\n                    background: none;\n                }}\n            ")

    def _apply_content_style(self):
        if self.theme_manager.is_dark():
            self.content.setStyleSheet('\n                background: #0d1117;\n                border-top-left-radius: 16px;\n            ')
        else:
            self.content.setStyleSheet('\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, \n                    stop:0 #FFFFFF, stop:1 #FAFBFC);\n                border-top-left-radius: 16px;\n            ')

    def create_header(self, layout):
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet('background: transparent;')
        h_layout = QHBoxLayout(self.header_widget)
        h_layout.setContentsMargins(0, 0, 0, 0)
        title_area = QVBoxLayout()
        self.title_label = QLabel(tr('email_management'))
        self.title_label.setStyleSheet(f"font-size: 28px; font-weight: 600; color: {self.theme_manager.get_color('text')};")
        self.subtitle_label = QLabel(tr('manage_all_accounts'))
        self.subtitle_label.setStyleSheet(f"font-size: 14px; color: {self.theme_manager.get_color('text_secondary')}; margin-top: 4px;")
        title_area.addWidget(self.title_label)
        title_area.addWidget(self.subtitle_label)
        h_layout.addLayout(title_area)
        h_layout.addStretch()
        is_dark = self.theme_manager.is_dark()
        self.header_buttons = QWidget()
        self.header_buttons.setStyleSheet('background: transparent;')
        buttons_layout = QHBoxLayout(self.header_buttons)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        self.stats_card = FluentCard(is_dark=is_dark)
        self.stats_card.setFixedSize(160, 60)
        stats_layout = QVBoxLayout(self.stats_card)
        stats_layout.setContentsMargins(12, 8, 12, 8)
        stats_layout.setSpacing(2)
        self.stats_count = QLabel('0')
        self.stats_count.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {self.theme_manager.get_color('accent')};")
        self.stats_text = QLabel(tr('current_group'))
        self.stats_text.setStyleSheet(f"font-size: 11px; color: {self.theme_manager.get_color('text_secondary')};")
        stats_layout.addWidget(self.stats_count)
        stats_layout.addWidget(self.stats_text)
        buttons_layout.addWidget(self.stats_card)
        h_layout.addWidget(self.header_buttons)
        layout.addWidget(self.header_widget)

    def create_toolbar(self, layout):
        is_dark = self.theme_manager.is_dark()
        self.toolbar = FluentCard(is_dark=is_dark)
        toolbar_layout = QVBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        toolbar_layout.setSpacing(10)
        t_layout = QHBoxLayout()
        toolbar_layout.addLayout(t_layout)
        t_layout.setSpacing(12)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('🔍 ' + tr('search_email'))
        self.search_input.setFixedWidth(280)
        self.search_input.setStyleSheet(self.theme_manager.get_theme()['input'])
        self.search_input.textChanged.connect(self.filter_accounts)
        t_layout.addWidget(self.search_input)
        self.group_filter = QComboBox()
        self.group_filter.setFixedWidth(140)
        self.group_filter.setStyleSheet(self.theme_manager.get_theme()['combo'])
        self.group_filter.currentTextChanged.connect(self.on_group_filter_changed)
        t_layout.addWidget(self.group_filter)
        self.btn_sort = FluentButton(tr('sort_by'), 'default', is_dark=is_dark)
        self.btn_sort.clicked.connect(self.show_sort_menu)
        t_layout.addWidget(self.btn_sort)
        t_layout.addStretch()
        t_layout = QHBoxLayout()
        t_layout.setSpacing(12)
        toolbar_layout.addLayout(t_layout)
        self.btn_import = FluentButton(tr('import_email'), 'default', is_dark=is_dark)
        self.btn_import.clicked.connect(self.import_accounts)
        self.btn_export = FluentButton(tr('export_backup'), 'default', is_dark=is_dark)
        self.btn_export.clicked.connect(self.export_accounts)
        self.btn_move = FluentButton(tr('move_group'), 'default', is_dark=is_dark)
        self.btn_move.clicked.connect(self.batch_move_group)
        self.btn_send = FluentButton(tr('batch_send'), 'default', is_dark=is_dark)
        self.btn_send.clicked.connect(self.batch_send_email)
        self.btn_check = FluentButton(tr('batch_check'), 'default', is_dark=is_dark)
        self.btn_check.clicked.connect(self.batch_check_status)
        self.btn_delete = FluentButton(tr('batch_delete'), 'default', is_dark=is_dark)
        self.btn_delete.clicked.connect(self.batch_delete)
        t_layout.addWidget(self.btn_import)
        t_layout.addWidget(self.btn_export)
        t_layout.addWidget(self.btn_move)
        t_layout.addWidget(self.btn_send)
        t_layout.addWidget(self.btn_check)
        t_layout.addWidget(self.btn_delete)
        t_layout.addStretch()
        layout.addWidget(self.toolbar)

    def create_table(self, layout):
        is_dark = self.theme_manager.is_dark()
        self.table_card = FluentCard(is_dark=is_dark)
        table_layout = QVBoxLayout(self.table_card)
        table_layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([tr('col_checkbox'), tr('col_index'), tr('col_email'), tr('col_password'), tr('col_group'), tr('col_status'), tr('col_type'), tr('col_aws'), tr('col_operation')])
        self.table.setStyleSheet(self.theme_manager.get_theme()['table'])
        for i in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(i)
            if item:
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(False)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setSectionResizeMode(5, QHeaderView.Interactive)
        header.setSectionResizeMode(6, QHeaderView.Interactive)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        header.setSectionResizeMode(8, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 44)
        self.table.setColumnWidth(1, 50)
        self.table.setColumnWidth(7, 60)
        table_layout.addWidget(self.table)
        self.table_bottom = QWidget()
        self._apply_table_bottom_style()
        bottom_layout = QHBoxLayout(self.table_bottom)
        bottom_layout.setContentsMargins(20, 14, 20, 14)
        self.drag_hint = QLabel(tx('💡 Drag a TXT file into this window to import accounts'))
        self._apply_drag_hint_style()
        bottom_layout.addWidget(self.drag_hint)
        bottom_layout.addStretch()
        self.page_info = QLabel(tr('total_records', 0))
        self._apply_page_info_style()
        bottom_layout.addWidget(self.page_info)
        table_layout.addWidget(self.table_bottom)
        layout.addWidget(self.table_card, 1)

    def _apply_table_bottom_style(self):
        if self.theme_manager.is_dark():
            self.table_bottom.setStyleSheet('\n                background: #161b22;\n                border-top: 1px solid #30363d;\n                border-bottom-left-radius: 12px;\n                border-bottom-right-radius: 12px;\n            ')
        else:
            self.table_bottom.setStyleSheet('\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #FAFBFC, stop:1 #F3F4F6);\n                border-top: 1px solid #E5E7EB;\n                border-bottom-left-radius: 12px;\n                border-bottom-right-radius: 12px;\n            ')

    def _apply_drag_hint_style(self):
        if self.theme_manager.is_dark():
            self.drag_hint.setStyleSheet('color: #6e7681; font-size: 12px;')
        else:
            self.drag_hint.setStyleSheet('color: #9CA3AF; font-size: 12px;')

    def _apply_page_info_style(self):
        if self.theme_manager.is_dark():
            self.page_info.setStyleSheet('color: #8b949e; font-size: 13px; font-weight: 500;')
        else:
            self.page_info.setStyleSheet('color: #6B7280; font-size: 13px; font-weight: 500;')

    def load_group_filter(self):
        self.group_filter.blockSignals(True)
        current_group = self.current_group
        self.group_filter.clear()
        self.group_filter.addItem(tr('all_groups'), 'All')
        for group in self.db.get_all_groups():
            self.group_filter.addItem(tx(group[1]) if group[1] == 'Default' else group[1], group[1])
        if current_group != 'All':
            index = self.group_filter.findData(current_group)
            if index >= 0:
                self.group_filter.setCurrentIndex(index)
        self.group_filter.blockSignals(False)

    def load_accounts(self):
        if self.current_group == 'All':
            accounts = self.db.get_all_accounts_sorted(self.sort_by, self.sort_order)
        else:
            accounts = self.db.get_accounts_by_group_sorted(self.current_group, self.sort_by, self.sort_order)
        self.table.setRowCount(len(accounts))
        is_dark = self.theme_manager.is_dark()
        text_color = self.theme_manager.get_color('text')
        text_secondary = self.theme_manager.get_color('text_secondary')
        text_muted = self.theme_manager.get_color('text_muted')
        accent_color = self.theme_manager.get_color('accent')
        success_color = self.theme_manager.get_color('success')
        danger_color = self.theme_manager.get_color('danger')
        font_bold = self.font()
        font_bold.setBold(True)
        for (row, acc) in enumerate(accounts):
            self.table.setRowHeight(row, 44)
            cb = FluentCheckBox(is_dark=is_dark)
            cb.setProperty('account_id', acc[0])
            cb_widget = QWidget()
            cb_widget.setStyleSheet('background: transparent; border: none;')
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, cb_widget)
            num_item = QTableWidgetItem(str(row + 1))
            num_item.setForeground(QColor(text_muted))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, num_item)
            email_widget = QWidget()
            email_widget.setStyleSheet('QWidget { background: transparent; border: none; }')
            email_layout = QHBoxLayout(email_widget)
            email_layout.setContentsMargins(4, 0, 4, 0)
            email_layout.setSpacing(4)
            email_label = QLabel(acc[1])
            email_label.setStyleSheet(f'QLabel {{ color: {text_color}; font-size: 13px; background: transparent; }}')
            email_layout.addWidget(email_label, 1)
            btn_copy_email = QPushButton(tr('copy'))
            btn_copy_email.setMinimumWidth(84)
            btn_copy_email.setCursor(Qt.PointingHandCursor)
            copy_btn_style = f"QPushButton{{border:none;background:transparent;color:{('#8b949e' if is_dark else '#666')};font-size:11px;border-radius:3px;padding:2px 4px;}}QPushButton:hover{{background:{('#30363d' if is_dark else '#f0f0f0')};color:{('#58a6ff' if is_dark else '#0078D4')};}}"
            btn_copy_email.setStyleSheet(copy_btn_style)
            btn_copy_email.setProperty('copy_text', acc[1])
            btn_copy_email.clicked.connect(self.copy_text)
            email_layout.addWidget(btn_copy_email)
            self.table.setCellWidget(row, 2, email_widget)
            pwd_widget = QWidget()
            pwd_widget.setStyleSheet('QWidget { background: transparent; border: none; }')
            pwd_layout = QHBoxLayout(pwd_widget)
            pwd_layout.setContentsMargins(4, 0, 4, 0)
            pwd_layout.setSpacing(4)
            pwd_label = QLabel('••••••••')
            pwd_label.setStyleSheet(f'QLabel {{ color: {text_secondary}; font-size: 13px; background: transparent; }}')
            pwd_label.setProperty('real_password', acc[2])
            pwd_label.setProperty('is_hidden', True)
            pwd_layout.addWidget(pwd_label, 1)
            btn_toggle_pwd = QPushButton(tr('show'))
            btn_toggle_pwd.setMinimumWidth(66)
            btn_toggle_pwd.setCursor(Qt.PointingHandCursor)
            btn_toggle_pwd.setStyleSheet(copy_btn_style)
            btn_toggle_pwd.setProperty('pwd_label', pwd_label)
            btn_toggle_pwd.clicked.connect(self.toggle_password)
            pwd_layout.addWidget(btn_toggle_pwd)
            btn_copy_pwd = QPushButton(tr('copy'))
            btn_copy_pwd.setMinimumWidth(84)
            btn_copy_pwd.setCursor(Qt.PointingHandCursor)
            btn_copy_pwd.setStyleSheet(copy_btn_style)
            btn_copy_pwd.setProperty('copy_text', acc[2])
            btn_copy_pwd.clicked.connect(self.copy_text)
            pwd_layout.addWidget(btn_copy_pwd)
            self.table.setCellWidget(row, 3, pwd_widget)
            group_item = QTableWidgetItem(tx(acc[3]) if acc[3] == 'Default' else acc[3])
            group_item.setForeground(QColor(text_color))
            group_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            group_item.setData(Qt.UserRole, acc[0])
            self.table.setItem(row, 4, group_item)
            status_text = acc[4]
            status_widget = QWidget()
            status_widget.setStyleSheet('background: transparent; border: none;')
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(0, 0, 0, 0)
            status_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            status_badge = QLabel(tx(status_text))
            status_badge.setAlignment(Qt.AlignCenter)
            badge_style_key = 'badge_info'
            if status_text == 'Normal':
                badge_style_key = 'badge_success'
            elif status_text in ['Error', 'Blocked', 'Failed']:
                badge_style_key = 'badge_error'
            elif status_text in ['Verifying', 'Verification']:
                badge_style_key = 'badge_warning'
            status_badge.setStyleSheet(self.theme_manager.get_theme().get(badge_style_key, ''))
            status_layout.addWidget(status_badge)
            self.table.setCellWidget(row, 5, status_widget)
            type_item = QTableWidgetItem(tx(acc[5]))
            type_item.setForeground(QColor(text_secondary))
            type_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row, 6, type_item)
            has_aws = acc[14] if len(acc) > 14 else 0
            aws_item = QTableWidgetItem(tr('has_aws_code') if has_aws else tr('no_aws_code'))
            aws_item.setTextAlignment(Qt.AlignCenter)
            if has_aws:
                aws_item.setForeground(QColor(success_color))
            else:
                aws_item.setForeground(QColor(text_muted))
            self.table.setItem(row, 7, aws_item)
            ops_widget = QWidget()
            ops_widget.setStyleSheet('background: transparent; border: none;')
            ops_layout = QHBoxLayout(ops_widget)
            ops_layout.setContentsMargins(0, 0, 0, 0)
            ops_layout.setSpacing(6)
            ops_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            btn_view = QPushButton('👁')
            btn_view.setFixedSize(28, 28)
            btn_view.setCursor(Qt.PointingHandCursor)
            view_color = '#58a6ff' if is_dark else '#0078D4'
            view_bg = 'rgba(88,166,255,0.1)' if is_dark else 'rgba(0,120,212,0.1)'
            btn_view.setStyleSheet(f'QPushButton{{color:{view_color};background:transparent;border:none;border-radius:4px;font-size:14px;}}QPushButton:hover{{background:{view_bg};}}')
            btn_view.setToolTip(tr('view'))
            btn_view.setProperty('account_id', acc[0])
            btn_view.clicked.connect(self.view_emails)
            btn_del = QPushButton('🗑')
            btn_del.setFixedSize(28, 28)
            btn_del.setCursor(Qt.PointingHandCursor)
            del_color = '#f85149' if is_dark else '#D13438'
            del_bg = 'rgba(248,81,73,0.1)' if is_dark else 'rgba(209,52,56,0.1)'
            btn_del.setStyleSheet(f'QPushButton{{color:{del_color};background:transparent;border:none;border-radius:4px;font-size:14px;}}QPushButton:hover{{background:{del_bg};}}')
            btn_del.setToolTip(tr('delete'))
            account_id = acc[0]
            btn_del.clicked.connect(lambda checked, aid=account_id: self.delete_single_account(aid))
            btn_more = QPushButton('⋮')
            btn_more.setFixedSize(28, 28)
            btn_more.setCursor(Qt.PointingHandCursor)
            more_color = '#8b949e' if is_dark else '#666'
            more_hover_bg = '#30363d' if is_dark else '#f0f0f0'
            btn_more.setStyleSheet(f'QPushButton{{color:{more_color};background:transparent;border:none;border-radius:4px;font-size:16px;font-weight:bold;}}QPushButton:hover{{background:{more_hover_bg};}}')
            btn_more.setToolTip(tx('More actions'))
            btn_more.setProperty('row', row)
            btn_more.clicked.connect(self.show_more_menu)
            ops_layout.addWidget(btn_view)
            ops_layout.addWidget(btn_del)
            ops_layout.addWidget(btn_more)
            self.table.setCellWidget(row, 8, ops_widget)
        current_count = len(accounts)
        self.stats_count.setText(str(current_count))
        self.page_info.setText(tr('total_records', current_count))
        self.adjust_column_widths()

    def on_group_selected(self, group_name):
        self.current_group = group_name
        self.hide_settings_page()
        self.load_accounts()

    def on_group_filter_changed(self, group_name):
        all_groups_text = tr('all_groups')
        self.current_group = self.group_filter.currentData() or 'All'
        self.load_accounts()

    def show_sort_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        action_default = menu.addAction(tr('sort_default'))
        action_email = menu.addAction(tr('sort_by_email'))
        action_status = menu.addAction(tr('sort_by_status'))
        action_aws = menu.addAction(tr('sort_by_aws'))
        action = menu.exec_(self.btn_sort.mapToGlobal(self.btn_sort.rect().bottomLeft()))
        if action == action_default:
            self.sort_by = 'id'
            self.sort_order = 'DESC'
        elif action == action_email:
            self.sort_by = 'email'
            self.sort_order = 'ASC'
        elif action == action_status:
            self.sort_by = 'status'
            self.sort_order = 'ASC'
        elif action == action_aws:
            self.sort_by = 'has_aws_code'
            self.sort_order = 'DESC'
        else:
            return
        self.load_accounts()

    def open_settings(self):
        self.show_settings_page()

    def show_settings_page(self):
        if not hasattr(self, 'settings_page'):
            self.create_settings_page()
        self.toolbar.hide()
        self.table_card.hide()
        self.header_buttons.hide()
        if hasattr(self, 'dashboard_page'):
            self.dashboard_page.hide()
        if hasattr(self, 'oauth_page'):
            self.oauth_page.hide()
        self.settings_page.show()
        self.title_label.setText(tr('settings'))
        self.subtitle_label.setText(tr('settings_desc'))

    def hide_settings_page(self):
        if hasattr(self, 'settings_page'):
            self.settings_page.hide()
        if hasattr(self, 'dashboard_page'):
            self.dashboard_page.hide()
        if hasattr(self, 'oauth_page'):
            self.oauth_page.hide()
        self.toolbar.show()
        self.table_card.show()
        self.header_buttons.show()
        self.title_label.setText(tr('email_management'))
        self.subtitle_label.setText(tr('manage_all_accounts'))

    def create_settings_page(self):
        from core.i18n import tr, get_language, set_language
        is_dark = self.theme_manager.is_dark()
        self.settings_page = QWidget()
        if is_dark:
            self.settings_page.setStyleSheet('background: #0d1117; border: none;')
        else:
            self.settings_page.setStyleSheet('background: #FFFFFF; border: none;')
        content_layout = self.content.layout()
        content_layout.addWidget(self.settings_page)
        page_layout = QVBoxLayout(self.settings_page)
        page_layout.setContentsMargins(32, 32, 32, 32)
        page_layout.setSpacing(32)
        theme_section = self.create_theme_section()
        page_layout.addWidget(theme_section)
        general_section = self.create_general_section()
        page_layout.addWidget(general_section)
        page_layout.addStretch()
        self.settings_page.hide()

    def create_theme_section(self):
        from core.i18n import tr
        is_dark = self.theme_manager.is_dark()
        section = QWidget()
        section.setStyleSheet('background: transparent;')
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.theme_section_title = QLabel(tr('theme_settings'))
        self.theme_section_title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {self.theme_manager.get_color('text')}; background: transparent;")
        layout.addWidget(self.theme_section_title)
        self.theme_section_desc = QLabel(tr('theme_settings_desc'))
        self.theme_section_desc.setStyleSheet(f"font-size: 13px; color: {self.theme_manager.get_color('text_secondary')}; background: transparent;")
        layout.addWidget(self.theme_section_desc)
        layout.addSpacing(8)
        theme_row = QHBoxLayout()
        theme_row.setSpacing(16)
        self.theme_light_btn = self.create_theme_button('☀️', tr('light_theme'), not is_dark, '#0078D4')
        self.theme_light_btn.clicked.connect(lambda : self.on_theme_select('light'))
        theme_row.addWidget(self.theme_light_btn.container)
        self.theme_dark_btn = self.create_theme_button('🌙', tr('dark_theme'), is_dark, '#1a1b3c')
        self.theme_dark_btn.clicked.connect(lambda : self.on_theme_select('dark'))
        theme_row.addWidget(self.theme_dark_btn.container)
        theme_row.addStretch()
        layout.addLayout(theme_row)
        return section

    def create_theme_button(self, icon, text, selected=False, icon_bg='#0078D4'):
        is_light = icon == '☀️'
        container = QWidget()
        container.setFixedSize(100, 120)
        container.setStyleSheet('background: transparent;')
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        btn = QPushButton()
        btn.setFixedSize(100, 120)
        btn.setCheckable(True)
        btn.setChecked(selected)
        btn.setCursor(Qt.PointingHandCursor)
        btn_layout = QVBoxLayout(btn)
        btn_layout.setAlignment(Qt.AlignCenter)
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 16, 0, 12)
        icon_container = QLabel()
        icon_container.setFixedSize(48, 48)
        icon_container.setAlignment(Qt.AlignCenter)
        if is_light:
            icon_container.setText('☀')
            icon_container.setStyleSheet('\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n                    stop:0 #60A5FA, stop:1 #3B82F6);\n                border-radius: 12px;\n                font-size: 22px;\n                color: white;\n            ')
        else:
            icon_container.setText('🌙')
            icon_container.setStyleSheet('\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n                    stop:0 #1e1b4b, stop:1 #312e81);\n                border-radius: 12px;\n                font-size: 20px;\n            ')
        btn_layout.addWidget(icon_container, 0, Qt.AlignCenter)
        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet(f"font-size: 13px; color: {self.theme_manager.get_color('text')}; background: transparent; font-weight: 500;")
        btn_layout.addWidget(text_label)
        check_label = QLabel('✓')
        check_label.setFixedSize(20, 20)
        check_label.setAlignment(Qt.AlignCenter)
        check_label.setStyleSheet('\n            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n                stop:0 #60A5FA, stop:1 #3B82F6);\n            color: white;\n            border-radius: 10px;\n            font-size: 12px;\n            font-weight: bold;\n        ')
        check_label.setVisible(selected)
        btn.icon_container = icon_container
        btn.text_label = text_label
        btn.check_label = check_label
        btn.container = container
        btn.is_light = is_light
        self._apply_theme_btn_style(btn, selected)
        container_layout.addWidget(btn)
        check_label.setParent(container)
        check_label.move(76, 6)
        check_label.raise_()
        return btn

    def _apply_theme_btn_style(self, btn, selected=False):
        is_dark = self.theme_manager.is_dark()
        if is_dark:
            if selected:
                btn.setStyleSheet('\n                    QPushButton {\n                        background: rgba(59, 130, 246, 0.15);\n                        border: 2px solid #3B82F6;\n                        border-radius: 16px;\n                    }\n                    QPushButton:hover {\n                        background: rgba(59, 130, 246, 0.2);\n                    }\n                ')
            else:
                btn.setStyleSheet('\n                    QPushButton {\n                        background: transparent;\n                        border: none;\n                        border-radius: 16px;\n                    }\n                    QPushButton:hover {\n                        background: rgba(255, 255, 255, 0.05);\n                    }\n                ')
        elif selected:
            btn.setStyleSheet('\n                    QPushButton {\n                        background: rgba(59, 130, 246, 0.08);\n                        border: 2px solid #3B82F6;\n                        border-radius: 16px;\n                    }\n                    QPushButton:hover {\n                        background: rgba(59, 130, 246, 0.12);\n                    }\n                ')
        else:
            btn.setStyleSheet('\n                    QPushButton {\n                        background: transparent;\n                        border: none;\n                        border-radius: 16px;\n                    }\n                    QPushButton:hover {\n                        background: rgba(0, 0, 0, 0.03);\n                    }\n                ')

    def on_theme_select(self, theme):
        self.set_theme(theme)
        is_dark = theme == 'dark'
        self.theme_light_btn.setChecked(not is_dark)
        self.theme_dark_btn.setChecked(is_dark)
        self._apply_theme_btn_style(self.theme_light_btn, not is_dark)
        self._apply_theme_btn_style(self.theme_dark_btn, is_dark)
        if hasattr(self.theme_light_btn, 'check_label'):
            self.theme_light_btn.check_label.setVisible(not is_dark)
        if hasattr(self.theme_dark_btn, 'check_label'):
            self.theme_dark_btn.check_label.setVisible(is_dark)

    def create_general_section(self):
        from core.i18n import tr, get_language
        import os
        section = QWidget()
        section.setStyleSheet('background: transparent;')
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(16)
        self.general_section_title = QLabel(tr('general_settings'))
        self.general_section_title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {self.theme_manager.get_color('text')}; background: transparent;")
        layout.addWidget(self.general_section_title)
        self.general_section_desc = QLabel(tr('general_settings_desc'))
        self.general_section_desc.setStyleSheet(f"font-size: 13px; color: {self.theme_manager.get_color('text_secondary')}; background: transparent;")
        layout.addWidget(self.general_section_desc)
        layout.addSpacing(8)
        self.font_label = QLabel(tr('font_size'))
        self.font_label.setFixedSize(100, 32)
        self.font_label.setStyleSheet(f"color: {self.theme_manager.get_color('text')}; background: transparent; font-size: 14px;")
        self.settings_font_combo = QComboBox()
        self.settings_font_combo.addItems(['11', '12', '13', '14', '15', '16', '18', '20'])
        self.settings_font_combo.setFixedSize(120, 32)
        self.settings_font_combo.setStyleSheet(self.theme_manager.get_theme()['combo'])
        current_font = self.db.get_setting('font_size', '13')
        index = self.settings_font_combo.findText(current_font)
        if index >= 0:
            self.settings_font_combo.setCurrentIndex(index)
        self.settings_font_combo.currentTextChanged.connect(self.on_settings_font_changed)
        font_row = QHBoxLayout()
        font_row.setSpacing(24)
        font_row.addWidget(self.font_label)
        font_row.addWidget(self.settings_font_combo)
        font_row.addStretch()
        layout.addLayout(font_row)
        layout.addSpacing(8)
        self.lang_label = QLabel(tr('language'))
        self.lang_label.setFixedSize(100, 32)
        self.lang_label.setStyleSheet(f"color: {self.theme_manager.get_color('text')}; background: transparent; font-size: 14px;")
        self.settings_lang_combo = QComboBox()
        self.settings_lang_combo.addItem(tr('russian'), 'ru')
        self.settings_lang_combo.addItem(tr('english'), 'en')
        self.settings_lang_combo.setFixedSize(120, 32)
        self.settings_lang_combo.setStyleSheet(self.theme_manager.get_theme()['combo'])
        current_lang = get_language()
        for i in range(self.settings_lang_combo.count()):
            if self.settings_lang_combo.itemData(i) == current_lang:
                self.settings_lang_combo.setCurrentIndex(i)
                break
        self.settings_lang_combo.currentIndexChanged.connect(self.on_settings_lang_changed)
        lang_row = QHBoxLayout()
        lang_row.setSpacing(24)
        lang_row.addWidget(self.lang_label)
        lang_row.addWidget(self.settings_lang_combo)
        lang_row.addStretch()
        layout.addLayout(lang_row)
        layout.addSpacing(8)
        self.data_label = QLabel(tr('data_location'))
        self.data_label.setFixedSize(100, 28)
        self.data_label.setStyleSheet(f"color: {self.theme_manager.get_color('text')}; background: transparent; font-size: 14px;")
        db_path = os.path.abspath(self.db.db_path)
        self.data_path_label = QLabel(db_path)
        self.data_path_label.setFixedHeight(28)
        self.data_path_label.setStyleSheet(f"color: {self.theme_manager.get_color('text_secondary')}; background: transparent; font-size: 13px;")
        self.btn_open_data = QPushButton(tr('open_folder'))
        self.btn_open_data.setFixedHeight(28)
        self.btn_open_data.setCursor(Qt.PointingHandCursor)
        self._apply_link_btn_style(self.btn_open_data)
        self.btn_open_data.clicked.connect(self.open_data_folder)
        data_row = QHBoxLayout()
        data_row.setSpacing(24)
        data_row.addWidget(self.data_label)
        data_row.addWidget(self.data_path_label)
        data_row.addWidget(self.btn_open_data)
        data_row.addStretch()
        layout.addLayout(data_row)
        layout.addSpacing(24)
        self.about_section_title = QLabel(tr('about'))
        self.about_section_title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {self.theme_manager.get_color('text')}; background: transparent;")
        layout.addWidget(self.about_section_title)
        layout.addSpacing(8)
        self.version_label = QLabel(f"{tr('app_name')} v1.3.0")
        self.version_label.setStyleSheet(f"color: {self.theme_manager.get_color('text')}; background: transparent; font-size: 14px;")
        layout.addWidget(self.version_label)
        self.copyright_label = QLabel(tx('Based on Email-Manager (MIT). Russian / English edition.'))
        self.copyright_label.setStyleSheet(f"color: {self.theme_manager.get_color('text_secondary')}; background: transparent; font-size: 12px;")
        layout.addWidget(self.copyright_label)
        return section

    def _apply_link_btn_style(self, btn):
        is_dark = self.theme_manager.is_dark()
        if is_dark:
            btn.setStyleSheet('\n                QPushButton {\n                    background: transparent;\n                    color: #58a6ff;\n                    border: none;\n                    font-size: 13px;\n                    padding: 4px 8px;\n                }\n                QPushButton:hover {\n                    text-decoration: underline;\n                }\n            ')
        else:
            btn.setStyleSheet('\n                QPushButton {\n                    background: transparent;\n                    color: #0078D4;\n                    border: none;\n                    font-size: 13px;\n                    padding: 4px 8px;\n                }\n                QPushButton:hover {\n                    text-decoration: underline;\n                }\n            ')

    def open_data_folder(self):
        import os
        import subprocess
        data_path = os.path.dirname(os.path.abspath(self.db.db_path))
        if os.path.exists(data_path):
            subprocess.Popen(['explorer', data_path])

    def on_settings_font_changed(self, font_size_str):
        font_size = int(font_size_str)
        self.db.set_setting('font_size', font_size_str)
        self.refresh_font_size(font_size)

    def on_settings_lang_changed(self, index):
        from core.i18n import set_language
        lang = self.settings_lang_combo.currentData()
        self.db.set_setting('language', lang)
        set_language(lang)
        self.refresh_language()
        self.refresh_settings_page_text()
        self.sidebar._update_lang_btn_text()

    def refresh_settings_page_text(self):
        from core.i18n import tr, get_language
        if not hasattr(self, 'settings_page'):
            return
        self.title_label.setText(tr('settings'))
        self.subtitle_label.setText(tr('settings_desc'))
        self.theme_section_title.setText(tr('theme_settings'))
        self.theme_section_desc.setText(tr('theme_settings_desc'))
        if hasattr(self.theme_light_btn, 'text_label'):
            self.theme_light_btn.text_label.setText(tr('light_theme'))
        if hasattr(self.theme_dark_btn, 'text_label'):
            self.theme_dark_btn.text_label.setText(tr('dark_theme'))
        self.general_section_title.setText(tr('general_settings'))
        self.general_section_desc.setText(tr('general_settings_desc'))
        self.font_label.setText(tr('font_size'))
        self.lang_label.setText(tr('language'))
        if hasattr(self, 'data_label'):
            self.data_label.setText(tr('data_location'))
        if hasattr(self, 'btn_open_data'):
            self.btn_open_data.setText(tr('open_folder'))
        if hasattr(self, 'about_section_title'):
            self.about_section_title.setText(tr('about'))
        if hasattr(self, 'version_label'):
            self.version_label.setText(f"{tr('app_name')} v1.3.0")
        current_data = self.settings_lang_combo.currentData()
        self.settings_lang_combo.blockSignals(True)
        self.settings_lang_combo.clear()
        self.settings_lang_combo.addItem(tr('russian'), 'ru')
        self.settings_lang_combo.addItem(tr('english'), 'en')
        for i in range(self.settings_lang_combo.count()):
            if self.settings_lang_combo.itemData(i) == current_data:
                self.settings_lang_combo.setCurrentIndex(i)
                break
        self.settings_lang_combo.blockSignals(False)

    def _update_settings_page_theme(self):
        if not hasattr(self, 'settings_page'):
            return
        is_dark = self.theme_manager.is_dark()
        if is_dark:
            self.settings_page.setStyleSheet('background: #0d1117; border: none;')
        else:
            self.settings_page.setStyleSheet('background: #FFFFFF; border: none;')
        self.theme_section_title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {self.theme_manager.get_color('text')}; background: transparent;")
        self.theme_section_desc.setStyleSheet(f"font-size: 13px; color: {self.theme_manager.get_color('text_secondary')}; background: transparent;")
        self.general_section_title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {self.theme_manager.get_color('text')}; background: transparent;")
        self.general_section_desc.setStyleSheet(f"font-size: 13px; color: {self.theme_manager.get_color('text_secondary')}; background: transparent;")
        self.font_label.setStyleSheet(f"color: {self.theme_manager.get_color('text')}; background: transparent; font-size: 14px;")
        self.lang_label.setStyleSheet(f"color: {self.theme_manager.get_color('text')}; background: transparent; font-size: 14px;")
        if hasattr(self, 'data_label'):
            self.data_label.setStyleSheet(f"color: {self.theme_manager.get_color('text')}; background: transparent; font-size: 14px;")
        if hasattr(self, 'data_path_label'):
            self.data_path_label.setStyleSheet(f"color: {self.theme_manager.get_color('text_secondary')}; background: transparent; font-size: 13px;")
        if hasattr(self, 'btn_open_data'):
            self._apply_link_btn_style(self.btn_open_data)
        if hasattr(self, 'about_section_title'):
            self.about_section_title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {self.theme_manager.get_color('text')}; background: transparent;")
        if hasattr(self, 'version_label'):
            self.version_label.setStyleSheet(f"color: {self.theme_manager.get_color('text')}; background: transparent; font-size: 14px;")
        if hasattr(self, 'copyright_label'):
            self.copyright_label.setStyleSheet(f"color: {self.theme_manager.get_color('text_secondary')}; background: transparent; font-size: 12px;")
        self.settings_font_combo.setStyleSheet(self.theme_manager.get_theme()['combo'])
        self.settings_lang_combo.setStyleSheet(self.theme_manager.get_theme()['combo'])
        self.theme_light_btn.setChecked(not is_dark)
        self.theme_dark_btn.setChecked(is_dark)
        self._apply_theme_btn_style(self.theme_light_btn, not is_dark)
        self._apply_theme_btn_style(self.theme_dark_btn, is_dark)
        if hasattr(self.theme_light_btn, 'check_label'):
            self.theme_light_btn.check_label.setVisible(not is_dark)
        if hasattr(self.theme_dark_btn, 'check_label'):
            self.theme_dark_btn.check_label.setVisible(is_dark)
        if hasattr(self.theme_light_btn, 'text_label'):
            self.theme_light_btn.text_label.setStyleSheet(f"font-size: 13px; color: {self.theme_manager.get_color('text')}; background: transparent; font-weight: 500;")
        if hasattr(self.theme_dark_btn, 'text_label'):
            self.theme_dark_btn.text_label.setStyleSheet(f"font-size: 13px; color: {self.theme_manager.get_color('text')}; background: transparent; font-weight: 500;")

    def open_oauth2_dialog(self):
        self.show_oauth_page()

    def show_oauth_page(self):
        from core.i18n import tr
        if not hasattr(self, 'oauth_page'):
            self.create_oauth_page()
        self.toolbar.hide()
        self.table_card.hide()
        self.header_buttons.hide()
        if hasattr(self, 'settings_page'):
            self.settings_page.hide()
        if hasattr(self, 'dashboard_page'):
            self.dashboard_page.hide()
        self.oauth_page.show()
        self.title_label.setText(tx('Manual authorization'))
        self.subtitle_label.setText(tx('Sign in through the browser to authorize OAuth2'))

    def create_oauth_page(self):
        from core.i18n import tr
        from ui.dialogs import ManualOAuth2Thread
        is_dark = self.theme_manager.is_dark()
        self.oauth_page = QWidget()
        if is_dark:
            self.oauth_page.setStyleSheet('background: #0d1117; border: none;')
        else:
            self.oauth_page.setStyleSheet('background: #FFFFFF; border: none;')
        content_layout = self.content.layout()
        content_layout.addWidget(self.oauth_page)
        page_layout = QVBoxLayout(self.oauth_page)
        page_layout.setContentsMargins(32, 32, 32, 32)
        page_layout.setSpacing(20)
        desc_label = QLabel(tx('Click "Start authorization" to open the Microsoft sign-in page.\nSign in to your Outlook account; the app will then obtain the authorization details.'))
        desc_label.setStyleSheet(f"color: {self.theme_manager.get_color('text_secondary')}; font-size: 13px; line-height: 1.6;")
        desc_label.setWordWrap(True)
        page_layout.addWidget(desc_label)
        group_row = QHBoxLayout()
        group_label = QLabel(tx('Import into group:'))
        group_label.setStyleSheet(f"color: {self.theme_manager.get_color('text')}; font-size: 14px;")
        group_row.addWidget(group_label)
        self.oauth_group_combo = QComboBox()
        self.oauth_group_combo.setFixedSize(160, 32)
        self.oauth_group_combo.setStyleSheet(self.theme_manager.get_theme()['combo'])
        for group in self.db.get_all_groups():
            self.oauth_group_combo.addItem(tx(group[1]) if group[1] == 'Default' else group[1], group[1])
        group_row.addWidget(self.oauth_group_combo)
        group_row.addStretch()
        page_layout.addLayout(group_row)
        tip_label = QLabel(tx('💡 Wait for the automatic redirect after sign-in. Do not close the browser manually.'))
        tip_label.setStyleSheet('color: #E67E22; font-size: 12px; padding: 8px 0;')
        page_layout.addWidget(tip_label)
        self.oauth_progress_label = QLabel(tx('Ready'))
        self.oauth_progress_label.setStyleSheet(f"color: {self.theme_manager.get_color('accent')}; font-size: 14px; font-weight: 500;")
        page_layout.addWidget(self.oauth_progress_label)
        result_title = QLabel(tx('Authorization result:'))
        result_title.setStyleSheet(f"color: {self.theme_manager.get_color('text')}; font-size: 14px; font-weight: 500;")
        page_layout.addWidget(result_title)
        self.oauth_result_text = QTextEdit()
        self.oauth_result_text.setReadOnly(True)
        self.oauth_result_text.setMaximumHeight(200)
        if is_dark:
            self.oauth_result_text.setStyleSheet("\n                QTextEdit {\n                    border: 1px solid #30363d;\n                    border-radius: 8px;\n                    background: #161b22;\n                    color: #c9d1d9;\n                    font-size: 12px;\n                    font-family: 'Consolas', 'Microsoft YaHei UI', monospace;\n                    padding: 12px;\n                }\n            ")
        else:
            self.oauth_result_text.setStyleSheet("\n                QTextEdit {\n                    border: 1px solid #E0E0E0;\n                    border-radius: 8px;\n                    background: #FAFAFA;\n                    color: #1A1A1A;\n                    font-size: 12px;\n                    font-family: 'Consolas', 'Microsoft YaHei UI', monospace;\n                    padding: 12px;\n                }\n            ")
        page_layout.addWidget(self.oauth_result_text)
        btn_row = QHBoxLayout()
        self.oauth_btn_start = FluentButton(tx('Start authorization'), 'primary', is_dark=is_dark)
        self.oauth_btn_start.clicked.connect(self._start_oauth)
        btn_row.addWidget(self.oauth_btn_start)
        self.oauth_btn_stop = FluentButton(tx('Stop'), 'default', is_dark=is_dark)
        self.oauth_btn_stop.clicked.connect(self._stop_oauth)
        self.oauth_btn_stop.setEnabled(False)
        btn_row.addWidget(self.oauth_btn_stop)
        btn_row.addStretch()
        page_layout.addLayout(btn_row)
        page_layout.addStretch()
        self.oauth_is_processing = False
        self.oauth_thread = None
        self.oauth_success_count = 0
        self.oauth_page.hide()

    def _start_oauth(self):
        from ui.dialogs import ManualOAuth2Thread
        if self.oauth_is_processing:
            return
        self.oauth_is_processing = True
        self.oauth_btn_start.setEnabled(False)
        self.oauth_btn_stop.setEnabled(True)
        self.oauth_progress_label.setText(tx('Opening browser...'))
        group = self.oauth_group_combo.currentData()
        self.oauth_thread = ManualOAuth2Thread(self.db, group)
        self.oauth_thread.progress.connect(self._on_oauth_progress)
        self.oauth_thread.finished_signal.connect(self._on_oauth_finished)
        self.oauth_thread.start()

    def _stop_oauth(self):
        if self.oauth_thread:
            self.oauth_thread.stop()
        self.oauth_is_processing = False
        self.oauth_btn_start.setEnabled(True)
        self.oauth_btn_stop.setEnabled(False)
        self.oauth_progress_label.setText(tx('Stopped'))

    def _on_oauth_progress(self, message):
        self.oauth_progress_label.setText(message)

    def _on_oauth_finished(self, email, client_id, refresh_token, error):
        self.oauth_is_processing = False
        self.oauth_btn_start.setEnabled(True)
        self.oauth_btn_stop.setEnabled(False)
        if error:
            self.oauth_progress_label.setText(tx('Authorization failed'))
            self.oauth_result_text.append(tx('❌ Failed: {0}', error))
        else:
            self.oauth_progress_label.setText(tx('Authorization successful!'))
            self.oauth_result_text.append(tx('✅ {0} — authorized and saved', email))
            self.oauth_success_count += 1
            self.load_accounts()
            self.sidebar.load_groups()

    def _update_oauth_page_theme(self):
        if not hasattr(self, 'oauth_page'):
            return
        is_dark = self.theme_manager.is_dark()
        if is_dark:
            self.oauth_page.setStyleSheet('background: #0d1117; border: none;')
            self.oauth_result_text.setStyleSheet("\n                QTextEdit {\n                    border: 1px solid #30363d;\n                    border-radius: 8px;\n                    background: #161b22;\n                    color: #c9d1d9;\n                    font-size: 12px;\n                    font-family: 'Consolas', 'Microsoft YaHei UI', monospace;\n                    padding: 12px;\n                }\n            ")
        else:
            self.oauth_page.setStyleSheet('background: #FFFFFF; border: none;')
            self.oauth_result_text.setStyleSheet("\n                QTextEdit {\n                    border: 1px solid #E0E0E0;\n                    border-radius: 8px;\n                    background: #FAFAFA;\n                    color: #1A1A1A;\n                    font-size: 12px;\n                    font-family: 'Consolas', 'Microsoft YaHei UI', monospace;\n                    padding: 12px;\n                }\n            ")
        self.oauth_group_combo.setStyleSheet(self.theme_manager.get_theme()['combo'])
        self.oauth_progress_label.setStyleSheet(f"color: {self.theme_manager.get_color('accent')}; font-size: 14px; font-weight: 500;")
        self.oauth_btn_start.set_dark_mode(is_dark)
        self.oauth_btn_stop.set_dark_mode(is_dark)

    def on_batch_oauth2_completed(self, success_count, fail_count):
        self.load_accounts()
        self.sidebar.load_groups()

    def on_oauth2_completed(self, email, client_id, refresh_token):
        if not email or not refresh_token:
            return
        existing = self.db.get_account_by_email(email)
        if existing:
            reply = QMessageBox.question(self, tx('Account already exists'), tx('Account {0} already exists. Update its OAuth2 credentials?', email), QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.db.update_account_oauth(existing[0], client_id, refresh_token)
                QMessageBox.information(self, tx('Success'), tx('Updated account {0} OAuth2 credentials', email))
                self.load_accounts()
        else:
            self.db.add_account(email=email, password='', group='Default', client_id=client_id, refresh_token=refresh_token)
            QMessageBox.information(self, tx('Success'), tx('Added account {0}', email))
            self.load_accounts()
            self.sidebar.load_groups()

    def filter_accounts(self, text):
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 2)
            if widget:
                label = widget.findChild(QLabel)
                if label:
                    self.table.setRowHidden(row, text.lower() not in label.text().lower())

    def import_accounts(self):
        default_group = None if self.current_group == 'All' else self.current_group
        dialog = ImportDialog(self.db, self, default_group=default_group)
        if dialog.exec_():
            self.load_accounts()
            self.load_group_filter()
            self.sidebar.load_groups()

    def export_accounts(self):
        (path, selected_filter) = QFileDialog.getSaveFileName(self, tr('export_backup'), '', tx('Excel files (*.xlsx);;Text files (*.txt)'))
        if path:
            accounts = self.db.get_all_accounts()
            if path.endswith('.xlsx') or 'xlsx' in selected_filter:
                self.export_to_xlsx(path, accounts)
            else:
                self.export_to_txt(path, accounts)
            QMessageBox.information(self, tr('success'), tr('exported_accounts', len(accounts)))

    def export_to_xlsx(self, path, accounts):
        try:
            import openpyxl
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = tx('Email accounts')
            headers = [tx('Email'), tx('Password'), tx('Group'), tx('Status'), tx('Type'), 'Client ID', 'Refresh Token', tx('Notes')]
            ws.append(headers)
            for acc in accounts:
                row = [acc[1], acc[2], acc[3], acc[4], acc[5], acc[10] if len(acc) > 10 else '', acc[11] if len(acc) > 11 else '', acc[15] if len(acc) > 15 and acc[15] else '']
                ws.append(row)
            ws.column_dimensions['A'].width = 35
            ws.column_dimensions['B'].width = 20
            ws.column_dimensions['C'].width = 15
            ws.column_dimensions['D'].width = 10
            ws.column_dimensions['E'].width = 10
            ws.column_dimensions['F'].width = 40
            ws.column_dimensions['G'].width = 50
            ws.column_dimensions['H'].width = 30
            wb.save(path)
        except ImportError:
            QMessageBox.warning(self, tr('warning'), tx('The openpyxl library is required to export Excel files. Install the complete application bundle.'))

    def export_to_txt(self, path, accounts):
        with open(path, 'w', encoding='utf-8') as f:
            parts = []
            for acc in accounts:
                email = acc[1]
                password = acc[2]
                client_id = acc[10] if len(acc) > 10 and acc[10] else ''
                refresh_token = acc[11] if len(acc) > 11 and acc[11] else ''
                if client_id or refresh_token:
                    part = f'{email}----{password}----{client_id}----{refresh_token}'
                else:
                    part = f'{email}----{password}'
                parts.append(part)
            f.write('$'.join(parts))

    def batch_move_group(self):
        selected = self.get_selected_accounts()
        if not selected:
            QMessageBox.warning(self, tr('warning'), tr('please_select_account'))
            return
        groups = [g[1] for g in self.db.get_all_groups()]
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        for group in groups:
            menu.addAction(group)
        action = menu.exec_(self.btn_move.mapToGlobal(self.btn_move.rect().bottomLeft()))
        if action:
            target_group = action.text()
            for aid in selected:
                self.db.update_account_group(aid, target_group)
            self.load_accounts()
            self.sidebar.load_groups()
            FluentMessageBox.success(self, tr('success'), tr('moved_to_group', len(selected), target_group))

    def get_selected_accounts(self):
        selected = []
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                cb = widget.findChild(QCheckBox)
                if cb and cb.isChecked():
                    selected.append(cb.property('account_id'))
        return selected

    def batch_check_status(self):
        if hasattr(self, 'check_thread') and self.check_thread and self.check_thread.isRunning():
            self.check_thread.stop()
            self.btn_check.setText(tx('Stopping...'))
            self.btn_check.setEnabled(False)
            return
        selected = self.get_selected_accounts()
        accounts = [acc for acc in self.db.get_all_accounts() if acc[0] in selected] if selected else self.db.get_all_accounts()
        if not accounts:
            QMessageBox.warning(self, tr('warning'), tr('no_accounts_to_check'))
            return
        self._check_total = len(accounts)
        self.btn_check.setText(tx('Checking 0/{0} (click to stop)', self._check_total))
        self.check_thread = StatusCheckThread(accounts, self.db)
        self.check_thread.status_updated.connect(self.on_status_updated)
        self.check_thread.aws_updated.connect(self.on_aws_updated)
        self.check_thread.progress_updated.connect(self.on_check_progress)
        self.check_thread.finished_all.connect(self.on_check_finished)
        self.check_thread.start()

    def on_check_progress(self, current, total):
        self.btn_check.setText(tx('Checking {0}/{1} (click to stop)', current, total))

    def on_status_updated(self, account_id, status):
        is_dark = self.theme_manager.is_dark()
        success_color = '#3fb950' if is_dark else '#107C10'
        danger_color = '#f85149' if is_dark else '#D13438'
        if hasattr(self, 'table'):
            for row in range(self.table.rowCount()):
                widget = self.table.cellWidget(row, 0)
                if widget:
                    cb = widget.findChild(QCheckBox)
                    if cb and cb.property('account_id') == account_id:
                        status_widget = self.table.cellWidget(row, 5)
                        if status_widget:
                            badge = status_widget.findChild(QLabel)
                            if badge:
                                label.setText(tx(status))
                                badge_style_key = 'badge_info'
                                if status == 'Normal':
                                    badge_style_key = 'badge_success'
                                elif status in ['Error', 'Blocked', 'Failed']:
                                    badge_style_key = 'badge_error'
                                elif status in ['Verifying', 'Verification']:
                                    badge_style_key = 'badge_warning'
                                badge.setStyleSheet(self.theme_manager.get_theme().get(badge_style_key, ''))
                        break
        if hasattr(self, 'dashboard_page') and self.dashboard_page.isVisible():
            self.refresh_dashboard_realtime()

    def refresh_dashboard_realtime(self):
        total = self.db.get_account_count()
        accounts = self.db.get_all_accounts()
        normal_count = sum((1 for acc in accounts if acc[4] == 'Normal'))
        error_count = sum((1 for acc in accounts if acc[4] == 'Error'))
        unchecked_count = sum((1 for acc in accounts if acc[4] not in ['Normal', 'Error']))
        if hasattr(self, 'dashboard_stat_labels') and len(self.dashboard_stat_labels) >= 4:
            self.dashboard_stat_labels[0].setText(str(total))
            self.dashboard_stat_labels[1].setText(str(normal_count))
            self.dashboard_stat_labels[2].setText(str(error_count))
            self.dashboard_stat_labels[3].setText(str(unchecked_count))
        group_data = self._get_group_data()
        status_data = self._get_status_data()
        is_dark = self.theme_manager.is_dark()
        if is_dark:
            colors = ['#58a6ff', '#3fb950', '#f85149', '#d29922', '#a371f7', '#39c5cf', '#ff7b72', '#79c0ff']
        else:
            colors = ['#0078D4', '#107C10', '#D13438', '#FFB900', '#8764B8', '#00B7C3', '#E74856', '#0099BC']
        if hasattr(self, 'group_pie_chart'):
            self.group_pie_chart.data = group_data
            self.group_pie_chart.update()
        if hasattr(self, 'group_legend_layout'):
            self._update_legend(self.group_legend_layout, group_data, colors)
        if hasattr(self, 'status_pie_chart'):
            self.status_pie_chart.data = status_data
            self.status_pie_chart.update()
        if hasattr(self, 'status_legend_layout'):
            self._update_legend(self.status_legend_layout, status_data, colors)

    def on_aws_updated(self, account_id, has_aws):
        is_dark = self.theme_manager.is_dark()
        success_color = '#3fb950' if is_dark else '#107C10'
        muted_color = '#6e7681' if is_dark else '#999999'
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                cb = widget.findChild(QCheckBox)
                if cb and cb.property('account_id') == account_id:
                    aws_item = self.table.item(row, 7)
                    if aws_item:
                        aws_item.setText(tr('has_aws_code') if has_aws else tr('no_aws_code'))
                        if has_aws:
                            aws_item.setForeground(QColor(success_color))
                        else:
                            aws_item.setForeground(QColor(muted_color))
                    break

    def on_check_finished(self):
        self.btn_check.setEnabled(True)
        self.btn_check.setText(tr('batch_check'))
        FluentMessageBox.success(self, tr('success'), tr('check_complete'))

    def batch_delete(self):
        selected = self.get_selected_accounts()
        if not selected:
            FluentMessageBox.warning(self, tr('warning'), tr('please_select_account'))
            return
        if FluentMessageBox.question(self, tr('confirm'), tr('confirm_delete', len(selected))):
            for aid in selected:
                self.db.delete_account(aid)
            self.load_accounts()

    def batch_send_email(self):
        selected = self.get_selected_accounts()
        if not selected:
            FluentMessageBox.warning(self, tr('warning'), tr('please_select_send_account'))
            return
        accounts = [acc for acc in self.db.get_all_accounts() if acc[0] in selected]
        dialog = BatchSendDialog(accounts, self)
        dialog.exec_()

    def view_emails(self):
        btn = self.sender()
        account_id = btn.property('account_id')
        for acc in self.db.get_all_accounts():
            if acc[0] == account_id:
                dialog = EmailViewDialog(acc, self.db, self)
                dialog.exec_()
                self.load_accounts()
                break

    def delete_single_account(self, account_id=None):
        try:
            if account_id is None:
                btn = self.sender()
                if btn:
                    account_id = btn.property('account_id')
            if not account_id:
                return
            if FluentMessageBox.question(self, tr('confirm'), tr('confirm_delete_single')):
                self.db.delete_account(account_id)
                self.load_accounts()
                self.sidebar.load_groups()
        except Exception as e:
            FluentMessageBox.error(self, tx('Error'), tx('Error deleting account: {0}', str(e)))

    def show_more_menu(self):
        btn = self.sender()
        row = btn.property('row')
        menu = QMenu(self)
        is_dark = self.theme_manager.is_dark()
        menu.setStyleSheet(MENU_STYLE_DARK if is_dark else MENU_STYLE_LIGHT)
        shadow = QGraphicsDropShadowEffect(menu)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50 if is_dark else 30))
        shadow.setOffset(0, 4)
        menu.setGraphicsEffect(shadow)
        action_check_this = menu.addAction(tr('check_this_row'))
        action_check_from = menu.addAction(tr('check_from_row'))
        menu.addSeparator()
        action_check_all = menu.addAction(tr('check_all'))
        action_uncheck_all = menu.addAction(tr('uncheck_all'))
        action = menu.exec_(btn.mapToGlobal(btn.rect().bottomLeft()))
        if action == action_check_this:
            self.check_row(row)
        elif action == action_check_from:
            self.check_from_row(row)
        elif action == action_check_all:
            self.check_all_rows()
        elif action == action_uncheck_all:
            self.uncheck_all_rows()

    def get_row_checkbox(self, row):
        widget = self.table.cellWidget(row, 0)
        return widget.findChild(QCheckBox) if widget else None

    def set_rows_checked(self, rows, checked=True):
        for row in rows:
            cb = self.get_row_checkbox(row)
            if cb:
                cb.setChecked(checked)

    def check_row(self, row):
        self.set_rows_checked([row], True)

    def check_from_row(self, start_row):
        from PyQt5.QtWidgets import QInputDialog
        total = self.table.rowCount() - start_row
        (n, ok) = QInputDialog.getInt(self, tr('check_count_title'), tr('check_count_msg', start_row + 1, total), value=min(10, total), min=1, max=total)
        if ok:
            self.set_rows_checked(range(start_row, min(start_row + n, self.table.rowCount())), True)

    def check_all_rows(self):
        self.set_rows_checked(range(self.table.rowCount()), True)

    def uncheck_all_rows(self):
        self.set_rows_checked(range(self.table.rowCount()), False)

    def copy_text(self):
        btn = self.sender()
        text = btn.property('copy_text')
        if text:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            self.show_toast(tr('copied'))

    def toggle_password(self):
        btn = self.sender()
        pwd_label = btn.property('pwd_label')
        if pwd_label:
            is_hidden = pwd_label.property('is_hidden')
            real_password = pwd_label.property('real_password')
            if is_hidden:
                pwd_label.setText(real_password)
                pwd_label.setProperty('is_hidden', False)
                btn.setText(tr('hide'))
            else:
                pwd_label.setText('••••••••')
                pwd_label.setProperty('is_hidden', True)
                btn.setText(tr('show'))

    def show_toast(self, message):
        from PyQt5.QtWidgets import QToolTip
        from PyQt5.QtCore import QPoint
        QToolTip.showText(self.mapToGlobal(QPoint(self.width() // 2, 50)), message, self, self.rect(), 1500)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_column_widths()

    def showEvent(self, event):
        super().showEvent(event)
        self.adjust_column_widths()

    def adjust_column_widths(self):
        if not hasattr(self, 'table'):
            return
        widths = {0: 44, 1: 50, 2: 300, 3: 300, 4: 140, 5: 140, 6: 95, 7: 60, 8: 120}
        widths[2] += max(0, self.table.viewport().width() - sum(widths.values()) - 2)
        for column, width in widths.items():
            self.table.setColumnWidth(column, width)

    def setup_shortcuts(self):
        QShortcut(QKeySequence('Ctrl+A'), self, self.check_all_rows)
        QShortcut(QKeySequence('Delete'), self, self.on_delete_shortcut)
        QShortcut(QKeySequence('Escape'), self, self.uncheck_all_rows)
        QShortcut(QKeySequence('Ctrl+F'), self, self.focus_search)
        QShortcut(QKeySequence('Ctrl+N'), self, self.import_accounts)
        QShortcut(QKeySequence('Ctrl+Shift+V'), self, self.quick_import_from_clipboard)

    def quick_import_from_clipboard(self):
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text or not text.strip():
            self.show_toast(tx('Clipboard is empty'))
            return
        if '@' not in text or '----' not in text:
            self.show_toast(tx('Invalid clipboard format'))
            return
        dialog = ImportDialog(self.db, self, default_group=None if self.current_group == 'All' else self.current_group)
        dialog.text_edit.setText(text)
        if dialog.exec_():
            self.load_accounts()
            self.load_group_filter()
            self.sidebar.load_groups()

    def on_delete_shortcut(self):
        selected = self.get_selected_accounts()
        if selected:
            self.batch_delete()

    def focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    def toggle_theme(self):
        theme = self.theme_manager.toggle_theme()
        self.apply_theme(theme)

    def set_theme(self, theme_name):
        if theme_name == 'light' and self.theme_manager.is_dark():
            self.toggle_theme()
        elif theme_name == 'dark' and (not self.theme_manager.is_dark()):
            self.toggle_theme()

    def refresh_language(self):
        from PyQt5.QtCore import QTimer, QThread
        if any(isinstance(value, QThread) and value.isRunning() for value in vars(self).values()):
            set_language(self._display_language)
            self.db.set_setting('language', self._display_language)
            if hasattr(self, 'settings_lang_combo'):
                self.settings_lang_combo.blockSignals(True)
                self.settings_lang_combo.setCurrentIndex(self.settings_lang_combo.findData(self._display_language))
                self.settings_lang_combo.blockSignals(False)
            self.sidebar._update_lang_btn_text()
            QMessageBox.information(self, tr('warning'), tx('An operation is in progress. Please wait.'))
            return
        self.db.set_setting('language', get_language())
        QTimer.singleShot(0, self._rebuild_localized_ui)

    def _rebuild_localized_ui(self):
        settings_visible = hasattr(self, 'settings_page') and self.settings_page.isVisible()
        dashboard_visible = hasattr(self, 'dashboard_page') and self.dashboard_page.isVisible()
        oauth_visible = hasattr(self, 'oauth_page') and self.oauth_page.isVisible()
        size = self.size()
        selected_group = self.current_group
        for name in ('settings_page', 'dashboard_page', 'oauth_page', 'drag_overlay'):
            if hasattr(self, name):
                delattr(self, name)
        self.init_ui()
        self.resize(size)
        self.current_group = selected_group
        self.load_accounts()
        self.tray_manager.refresh_language()
        self._display_language = get_language()
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self.adjust_column_widths)
        if settings_visible:
            self.show_settings_page()
        elif dashboard_visible:
            self.show_dashboard_page()
        elif oauth_visible:
            self.show_oauth_page()

    def refresh_font_size(self, font_size):
        self.font_size = font_size
        self._apply_global_style()

    def apply_theme(self, theme):
        is_dark = self.theme_manager.is_dark()
        self._apply_global_style()
        self._apply_content_style()
        self.sidebar.apply_theme(is_dark)
        self.title_label.setStyleSheet(f"font-size: 28px; font-weight: 600; color: {theme['colors']['text']};")
        self.subtitle_label.setStyleSheet(f"font-size: 14px; color: {theme['colors']['text_secondary']}; margin-top: 4px;")
        self.stats_count.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {theme['colors']['accent']};")
        self.stats_text.setStyleSheet(f"font-size: 11px; color: {theme['colors']['text_secondary']};")
        self.search_input.setStyleSheet(theme['input'])
        self.group_filter.setStyleSheet(theme['combo'])
        self.table.setStyleSheet(theme['table'])
        for btn in [self.btn_sort, self.btn_import, self.btn_export, self.btn_move, self.btn_send, self.btn_check, self.btn_delete]:
            btn.set_dark_mode(is_dark)
        self.stats_card.set_dark_mode(is_dark)
        self.toolbar.set_dark_mode(is_dark)
        self.table_card.set_dark_mode(is_dark)
        if hasattr(self, 'settings_page'):
            self._update_settings_page_theme()
        self._update_dashboard_theme()
        self._apply_table_bottom_style()
        self._apply_drag_hint_style()
        self._apply_page_info_style()
        self.load_accounts()

    def open_stats_dialog(self):
        self.show_dashboard_page()

    def show_dashboard_page(self):
        from core.i18n import tr
        if not hasattr(self, 'dashboard_page'):
            self.create_dashboard_page()
        else:
            self._update_dashboard_data()
        self.toolbar.hide()
        self.table_card.hide()
        self.header_buttons.hide()
        if hasattr(self, 'settings_page'):
            self.settings_page.hide()
        if hasattr(self, 'oauth_page'):
            self.oauth_page.hide()
        self.dashboard_page.show()
        self.title_label.setText(tr('dashboard'))
        self.subtitle_label.setText(tr('dashboard_desc'))

    def hide_dashboard_page(self):
        if hasattr(self, 'dashboard_page'):
            self.dashboard_page.hide()

    def create_dashboard_page(self):
        from core.i18n import tr
        from ui.dialogs import PieChartWidget
        is_dark = self.theme_manager.is_dark()
        self.dashboard_page = QWidget()
        if is_dark:
            self.dashboard_page.setStyleSheet('background: #0d1117; border: none;')
        else:
            self.dashboard_page.setStyleSheet('background: #FFFFFF; border: none;')
        content_layout = self.content.layout()
        content_layout.addWidget(self.dashboard_page)
        page_layout = QVBoxLayout(self.dashboard_page)
        page_layout.setContentsMargins(32, 32, 32, 32)
        page_layout.setSpacing(24)
        self._create_stats_cards(page_layout)
        self._create_charts_section(page_layout)
        page_layout.addStretch()
        self.dashboard_page.hide()

    def _create_stats_cards(self, parent_layout):
        is_dark = self.theme_manager.is_dark()
        cards_widget = QWidget()
        cards_widget.setStyleSheet('background: transparent;')
        cards_layout = QHBoxLayout(cards_widget)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(16)
        total = self.db.get_account_count()
        accounts = self.db.get_all_accounts()
        normal_count = sum((1 for acc in accounts if acc[4] == 'Normal'))
        error_count = sum((1 for acc in accounts if acc[4] == 'Error'))
        unchecked_count = sum((1 for acc in accounts if acc[4] not in ['Normal', 'Error']))
        cards_data = [('📊', tx('Total accounts'), str(total), '#0078D4' if not is_dark else '#58a6ff'), ('✅', tx('Working accounts'), str(normal_count), '#107C10' if not is_dark else '#3fb950'), ('⚠️', tx('Accounts with errors'), str(error_count), '#D13438' if not is_dark else '#f85149'), ('❓', tx('Unchecked'), str(unchecked_count), '#FFB900' if not is_dark else '#d29922')]
        self.dashboard_stat_labels = []
        for (icon, title, value, color) in cards_data:
            card = self._create_stat_card(icon, title, value, color)
            cards_layout.addWidget(card)
        cards_layout.addStretch()
        parent_layout.addWidget(cards_widget)

    def _create_stat_card(self, icon, title, value, color):
        is_dark = self.theme_manager.is_dark()
        card = QFrame()
        card.setFixedSize(160, 100)
        if is_dark:
            card.setStyleSheet(f'\n                QFrame {{\n                    background: #161b22;\n                    border: none;\n                    border-radius: 12px;\n                }}\n            ')
        else:
            card.setStyleSheet(f'\n                QFrame {{\n                    background: #FFFFFF;\n                    border: none;\n                    border-radius: 12px;\n                }}\n            ')
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 20 if not is_dark else 40))
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet('font-size: 18px; background: transparent;')
        header.addWidget(icon_label)
        title_label = QLabel(title)
        title_color = '#8b949e' if is_dark else '#616161'
        title_label.setStyleSheet(f'font-size: 12px; color: {title_color}; background: transparent;')
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        layout.addStretch()
        value_label = QLabel(value)
        value_label.setStyleSheet(f'font-size: 28px; font-weight: 600; color: {color}; background: transparent;')
        layout.addWidget(value_label)
        self.dashboard_stat_labels.append(value_label)
        return card

    def _create_charts_section(self, parent_layout):
        from ui.dialogs import PieChartWidget
        is_dark = self.theme_manager.is_dark()
        charts_widget = QWidget()
        charts_widget.setStyleSheet('background: transparent;')
        charts_layout = QHBoxLayout(charts_widget)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        charts_layout.setSpacing(24)
        group_data = self._get_group_data()
        self.group_chart_panel = self._create_chart_panel(tx('Accounts by group'), group_data)
        charts_layout.addWidget(self.group_chart_panel)
        status_data = self._get_status_data()
        self.status_chart_panel = self._create_chart_panel(tx('Accounts by status'), status_data)
        charts_layout.addWidget(self.status_chart_panel)
        charts_layout.addStretch()
        parent_layout.addWidget(charts_widget)

    def _create_chart_panel(self, title, data):
        from ui.dialogs import PieChartWidget
        is_dark = self.theme_manager.is_dark()
        if is_dark:
            colors = ['#58a6ff', '#3fb950', '#f85149', '#d29922', '#a371f7', '#39c5cf', '#ff7b72', '#79c0ff']
        else:
            colors = ['#0078D4', '#107C10', '#D13438', '#FFB900', '#8764B8', '#00B7C3', '#E74856', '#0099BC']
        panel = QFrame()
        panel.setFixedSize(320, 360)
        if is_dark:
            panel.setStyleSheet('\n                QFrame {\n                    background: #161b22;\n                    border: none;\n                    border-radius: 16px;\n                }\n            ')
        else:
            panel.setStyleSheet('\n                QFrame {\n                    background: #FFFFFF;\n                    border: none;\n                    border-radius: 16px;\n                }\n            ')
        shadow = QGraphicsDropShadowEffect(panel)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 15 if not is_dark else 30))
        shadow.setOffset(0, 4)
        panel.setGraphicsEffect(shadow)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        title_label = QLabel(title)
        title_color = '#c9d1d9' if is_dark else '#1A1A1A'
        title_label.setStyleSheet(f'font-size: 16px; font-weight: 600; color: {title_color}; background: transparent;')
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        pie_widget = PieChartWidget(data, colors)
        pie_widget.setFixedSize(160, 160)
        layout.addWidget(pie_widget, 0, Qt.AlignCenter)
        if title == tx('Accounts by group'):
            self.group_pie_chart = pie_widget
            self.group_legend_layout = None
        else:
            self.status_pie_chart = pie_widget
            self.status_legend_layout = None
        legend_widget = QWidget()
        legend_widget.setStyleSheet('background: transparent;')
        legend_layout = QVBoxLayout(legend_widget)
        legend_layout.setContentsMargins(0, 8, 0, 0)
        legend_layout.setSpacing(6)
        if title == tx('Accounts by group'):
            self.group_legend_layout = legend_layout
        else:
            self.status_legend_layout = legend_layout
        self._update_legend(legend_layout, data, colors)
        layout.addWidget(legend_widget)
        layout.addStretch()
        return panel

    def _update_legend(self, layout, data, colors):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        is_dark = self.theme_manager.is_dark()
        total = sum(data.values()) if data else 1
        for (i, (name, count)) in enumerate(data.items()):
            color = colors[i % len(colors)]
            percent = count / total * 100 if total > 0 else 0
            item_widget = QWidget()
            item_widget.setStyleSheet('background: transparent;')
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(8)
            color_block = QLabel()
            color_block.setFixedSize(10, 10)
            color_block.setStyleSheet(f'background: {color}; border-radius: 2px;')
            item_layout.addWidget(color_block)
            name_label = QLabel(tx(name))
            name_color = '#c9d1d9' if is_dark else '#1A1A1A'
            name_label.setStyleSheet(f'color: {name_color}; font-size: 12px; background: transparent;')
            item_layout.addWidget(name_label)
            item_layout.addStretch()
            value_label = QLabel(f'{count} ({percent:.1f}%)')
            value_color = '#8b949e' if is_dark else '#616161'
            value_label.setStyleSheet(f'color: {value_color}; font-size: 12px; background: transparent;')
            item_layout.addWidget(value_label)
            layout.addWidget(item_widget)

    def _get_group_data(self):
        groups = self.db.get_all_groups()
        data = {}
        for group in groups:
            count = len(self.db.get_accounts_by_group(group[1]))
            if count > 0:
                data[group[1]] = count
        return data

    def _get_status_data(self):
        accounts = self.db.get_all_accounts()
        data = {'Normal': 0, 'Error': 0, 'Unchecked': 0}
        for acc in accounts:
            status = acc[4]
            if status in data:
                data[status] += 1
            else:
                data['Unchecked'] += 1
        return {k: v for (k, v) in data.items() if v > 0}

    def _update_dashboard_data(self):
        if hasattr(self, 'dashboard_page'):
            self.dashboard_page.deleteLater()
            delattr(self, 'dashboard_page')
        self.create_dashboard_page()
        self.dashboard_page.show()

    def _update_dashboard_theme(self):
        if hasattr(self, 'dashboard_page'):
            was_visible = self.dashboard_page.isVisible()
            self.dashboard_page.deleteLater()
            delattr(self, 'dashboard_page')
            if was_visible:
                self.create_dashboard_page()
                self.dashboard_page.show()

    def closeEvent(self, event):
        if self.tray_manager and self.tray_manager.tray_icon:
            self.tray_manager.tray_icon.hide()
        event.accept()

    def show_table_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        group_item = self.table.item(row, 4)
        if not group_item:
            return
        account_id = group_item.data(Qt.UserRole)
        from PyQt5.QtWidgets import QMenu, QWidgetAction
        menu = QMenu(self)
        is_dark = self.theme_manager.is_dark()
        danger_color = '#f85149' if is_dark else '#E53935'
        if is_dark:
            menu.setStyleSheet(f'\n                QMenu {{\n                    background: #21262d;\n                    border: none;\n                    border-radius: 12px;\n                    padding: 8px 4px;\n                }}\n                QMenu::item {{\n                    padding: 10px 40px 10px 16px;\n                    color: #c9d1d9;\n                    border-radius: 6px;\n                    margin: 2px 6px;\n                    font-size: 13px;\n                }}\n                QMenu::item:selected {{\n                    background: #30363d;\n                    color: #FFFFFF;\n                }}\n                QMenu::item[data-danger="true"] {{\n                    color: {danger_color};\n                }}\n                QMenu::separator {{\n                    height: 1px;\n                    background: #30363d;\n                    margin: 6px 16px;\n                }}\n            ')
        else:
            menu.setStyleSheet(f'\n                QMenu {{\n                    background: #FFFFFF;\n                    border: none;\n                    border-radius: 12px;\n                    padding: 8px 4px;\n                }}\n                QMenu::item {{\n                    padding: 10px 40px 10px 16px;\n                    color: #333333;\n                    border-radius: 6px;\n                    margin: 2px 6px;\n                    font-size: 13px;\n                }}\n                QMenu::item:selected {{\n                    background: #F0F0F0;\n                    color: #333333;\n                }}\n                QMenu::separator {{\n                    height: 1px;\n                    background: #EEEEEE;\n                    margin: 6px 16px;\n                }}\n            ')
        shadow = QGraphicsDropShadowEffect(menu)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 50 if is_dark else 30))
        shadow.setOffset(0, 6)
        menu.setGraphicsEffect(shadow)
        action_detail = menu.addAction(tx('⊙  Details'))
        action_detail.triggered.connect(lambda : self.show_account_detail(account_id))
        action_view = menu.addAction(tx('✉  View messages'))
        action_view.triggered.connect(lambda : self.view_account_emails(account_id))
        action_export = menu.addAction(tx('📋  Export information'))
        action_export.triggered.connect(lambda : self.export_single_account(account_id))
        menu.addSeparator()
        delete_widget = QWidget()
        delete_widget.setStyleSheet('background: transparent;')
        delete_layout = QHBoxLayout(delete_widget)
        delete_layout.setContentsMargins(16, 10, 40, 10)
        delete_label = QLabel(tx('<span style="color:{0};">🗑  Delete</span>', danger_color))
        delete_label.setStyleSheet(f'color: {danger_color}; font-size: 13px; background: transparent;')
        delete_layout.addWidget(delete_label)
        delete_action = QWidgetAction(menu)
        delete_action.setDefaultWidget(delete_widget)
        delete_account_id = account_id

        def do_delete():
            menu.close()
            self.delete_single_account(delete_account_id)
        delete_action.triggered.connect(do_delete)
        delete_widget.mousePressEvent = lambda e: do_delete()
        delete_widget.setCursor(Qt.PointingHandCursor)
        menu.addAction(delete_action)
        menu.exec_(self.table.viewport().mapToGlobal(pos))

    def show_account_detail(self, account_id):
        accounts = self.db.get_all_accounts()
        account = None
        for acc in accounts:
            if acc[0] == account_id:
                account = acc
                break
        if not account:
            QMessageBox.warning(self, tx('Error'), tx('Account not found'))
            return
        dialog = AccountDetailDialog(account, self.theme_manager, self)
        dialog.exec_()

    def export_single_account(self, account_id):
        accounts = self.db.get_all_accounts()
        account = None
        for acc in accounts:
            if acc[0] == account_id:
                account = acc
                break
        if not account:
            QMessageBox.warning(self, tx('Error'), tx('Account not found'))
            return
        email = account[1] if len(account) > 1 else ''
        password = account[2] if len(account) > 2 else ''
        client_id = account[10] if len(account) > 10 and account[10] else ''
        refresh_token = account[11] if len(account) > 11 and account[11] else ''
        export_text = f'{email}----{password}----{client_id}----{refresh_token}'
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(export_text)
        QMessageBox.information(self, tx('Notice'), tx('Account information copied to clipboard'))

    def view_account_emails(self, account_id):
        accounts = self.db.get_all_accounts()
        account = None
        for acc in accounts:
            if acc[0] == account_id:
                account = acc
                break
        if account:
            from ui.dialogs import EmailViewDialog
            dialog = EmailViewDialog(account, self.db, self)
            dialog.exec_()

    def on_cell_double_clicked(self, row, col):
        if col == 8:
            self.edit_remark(row)

    def edit_remark(self, row):
        item = self.table.item(row, 8)
        if not item:
            return
        current_remark = item.text()
        account_id = item.data(Qt.UserRole)
        editor = QLineEdit(self.table)
        editor.setText(current_remark)
        editor.setProperty('row', row)
        editor.setProperty('account_id', account_id)
        editor.setProperty('original', current_remark)
        is_dark = self.theme_manager.is_dark()
        if is_dark:
            editor.setStyleSheet('\n                QLineEdit {\n                    padding: 4px 8px;\n                    border: 2px solid #58a6ff;\n                    border-radius: 4px;\n                    background: #0d1117;\n                    color: #c9d1d9;\n                    font-size: 13px;\n                }\n            ')
        else:
            editor.setStyleSheet('\n                QLineEdit {\n                    padding: 4px 8px;\n                    border: 2px solid #0078D4;\n                    border-radius: 4px;\n                    background: #FFFFFF;\n                    color: #1A1A1A;\n                    font-size: 13px;\n                }\n            ')
        editor.returnPressed.connect(lambda : self.save_remark(editor))
        editor.installEventFilter(self)
        self.table.setCellWidget(row, 8, editor)
        editor.setFocus()
        editor.selectAll()

    def save_remark(self, editor):
        row = editor.property('row')
        account_id = editor.property('account_id')
        new_remark = editor.text().strip()
        self.db.update_account_remark(account_id, new_remark)
        self.table.removeCellWidget(row, 8)
        is_dark = self.theme_manager.is_dark()
        text_color = '#8b949e' if is_dark else '#666666'
        item = QTableWidgetItem(new_remark)
        item.setForeground(QColor(text_color))
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        item.setToolTip(tx('Double-click to edit notes'))
        item.setData(Qt.UserRole, account_id)
        self.table.setItem(row, 8, item)
        self.show_toast(tr('remark_saved'))

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if isinstance(obj, QLineEdit) and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                row = obj.property('row')
                account_id = obj.property('account_id')
                original = obj.property('original')
                self.table.removeCellWidget(row, 8)
                is_dark = self.theme_manager.is_dark()
                text_color = '#8b949e' if is_dark else '#666666'
                item = QTableWidgetItem(original)
                item.setForeground(QColor(text_color))
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                item.setToolTip(tx('Double-click to edit notes'))
                item.setData(Qt.UserRole, account_id)
                self.table.setItem(row, 8, item)
                return True
        return super().eventFilter(obj, event)
