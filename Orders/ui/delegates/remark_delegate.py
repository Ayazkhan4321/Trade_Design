from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt


class RemarkDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()

        painter.setPen(Qt.gray)
        painter.drawText(option.rect, Qt.AlignCenter, "✎")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == event.MouseButtonRelease:
            row = index.row()
            print(f"Edit remark for row {row}")
            return True
        return False
