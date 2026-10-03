from core.i18n import tx
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject
import os
TRAY_MENU_STYLE = '\n    QMenu {\n        background: #FFFFFF;\n        border: 1px solid #E0E0E0;\n        border-radius: 6px;\n        padding: 4px;\n    }\n    QMenu::item {\n        padding: 8px 20px;\n        color: #1A1A1A;\n        border-radius: 4px;\n    }\n    QMenu::item:selected {\n        background: #E5F1FB;\n        color: #0078D4;\n    }\n'

class SystemTrayManager(QObject):

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.tray_icon = None
        self.setup_tray()

    def setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray_icon = QSystemTrayIcon(self.main_window)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(self.main_window.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.setToolTip(tx('Email Manager'))
        menu = QMenu()
        menu.setStyleSheet(TRAY_MENU_STYLE)
        action_show = menu.addAction(tx('Show main window'))
        action_show.triggered.connect(self.show_window)
        menu.addSeparator()
        action_quit = menu.addAction(tx('Quit'))
        action_quit.triggered.connect(self.quit_app)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()
        elif reason == QSystemTrayIcon.Trigger:
            self.show_window()

    def refresh_language(self):
        if self.tray_icon:
            self.tray_icon.setToolTip(tx('Email Manager'))
            actions = self.tray_icon.contextMenu().actions()
            actions[0].setText(tx('Show main window'))
            actions[-1].setText(tx('Quit'))

    def show_window(self):
        self.main_window.show()
        self.main_window.showNormal()
        self.main_window.activateWindow()
        self.main_window.raise_()

    def quit_app(self):
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()

    def hide_to_tray(self):
        self.main_window.hide()
        if self.tray_icon:
            self.tray_icon.showMessage(tx('Email Manager'), tx('The application was minimized to the system tray'), QSystemTrayIcon.Information, 2000)

    def is_available(self):
        return self.tray_icon is not None and self.tray_icon.isVisible()
