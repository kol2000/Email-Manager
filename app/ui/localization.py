"""Qt standard labels and layout adjustments for longer Russian captions."""
from PyQt5.QtCore import QObject, QEvent, QTimer, QTranslator
from PyQt5.QtWidgets import QAbstractButton, QLabel, QDialog, QMainWindow
from core.i18n import get_language

class StandardLabels(QTranslator):
    LABELS = {
        '&Yes': 'Да', '&No': 'Нет', 'Yes': 'Да', 'No': 'Нет',
        'OK': 'ОК', 'Cancel': 'Отмена', '&Cancel': 'Отмена',
        'Close': 'Закрыть', '&Close': 'Закрыть', 'Save': 'Сохранить',
        '&Save': 'Сохранить', 'Open': 'Открыть', '&Open': 'Открыть',
        'Apply': 'Применить', 'Help': 'Справка', 'Reset': 'Сбросить',
        'Retry': 'Повторить', 'Ignore': 'Пропустить', 'Abort': 'Прервать',
        'Discard': 'Не сохранять', 'Yes to &All': 'Да для всех',
        'N&o to All': 'Нет для всех', 'Restore Defaults': 'По умолчанию',
    }
    def translate(self, context, sourceText, disambiguation=None, n=-1):
        if get_language() == 'ru':
            return self.LABELS.get(sourceText, '')
        return ''

class LocalizedLayout(QObject):
    def eventFilter(self, watched, event):
        if event.type() == QEvent.Show and isinstance(watched, (QDialog, QMainWindow)):
            QTimer.singleShot(0, lambda: self.fit(watched))
        return False

    def fit(self, window):
        try:
            for button in window.findChildren(QAbstractButton):
                text = button.text()
                if len(text) > 2:
                    required = max(button.sizeHint().width(), button.fontMetrics().horizontalAdvance(text.replace('&', '')) + 48)
                    if button.maximumWidth() < required:
                        button.setMaximumWidth(required)
                    button.setMinimumWidth(max(button.minimumWidth(), required))
            for label in window.findChildren(QLabel):
                if label.minimumWidth() == label.maximumWidth() and label.text() and '<' not in label.text():
                    width = label.fontMetrics().horizontalAdvance(label.text()) + 8
                    if width > label.width() and width < 400:
                        label.setFixedWidth(width)
        except RuntimeError:
            pass  # The window may have been closed before the queued update.
