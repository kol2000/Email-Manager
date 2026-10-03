from core.i18n import tx
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow

def main():
    os.environ['QT_FONT_DPI'] = '96'
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    from ui.localization import StandardLabels, LocalizedLayout
    app.standard_labels = StandardLabels(app)
    app.installTranslator(app.standard_labels)
    app.localized_layout = LocalizedLayout(app)
    app.installEventFilter(app.localized_layout)
    window = MainWindow()
    window.show()
    if '--smoke-test' in sys.argv:
        from PyQt5.QtCore import QTimer

        def finish_smoke_test():
            import json
            from core.i18n import get_language
            output = os.environ['EMAIL_MANAGER_SMOKE_OUTPUT']
            window.grab().save(output + '.png')
            with open(output + '.json', 'w', encoding='utf-8') as handle:
                json.dump({'window_visible': window.isVisible(), 'language': get_language(), 'title': window.windowTitle()}, handle)
            app.quit()
        QTimer.singleShot(1500, finish_smoke_test)
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()
