from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsItem
from PyQt5.QtGui import QPen

class GridLine(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, pen):
        super().__init__(x1, y1, x2, y2)
        self.setPen(pen)
        # Ensure the item is neither selectable nor movable
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setZValue(-1000)

    def mousePressEvent(self, event):
        # Explicitly ignore all mouse events
        event.ignore()

    def mouseReleaseEvent(self, event):
        event.ignore()

    def mouseMoveEvent(self, event):
        event.ignore()

    def itemChange(self, change, value):
        # Prevent any changes to selection state
        if change == QGraphicsItem.ItemSelectedChange:
            return False
        return super().itemChange(change, value)