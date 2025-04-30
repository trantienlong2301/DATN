from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QPainter, QBrush, QPen, QPolygonF
import sys
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsObject

class Coordinate(QGraphicsObject):
    def __init__(self, length=800):
        super().__init__()
        # Cho phép di chuyển và chọn
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        # Độ dài mũi tên theo trục X và Y
        self.axis_length = length
        self.arrow_size = 100
    
        self.flag = False  # cho phép di chuyển

    def setMovable(self, movable: bool):
        self.flag = movable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, movable)

    def boundingRect(self):
        # Vùng chứa hai mũi tên: từ (0, -axis_length) đến (axis_length, 0)
        return QRectF(-self.arrow_size/2, -self.axis_length, self.axis_length + self.arrow_size/2, self.axis_length + self.arrow_size/2)

    def paint(self, painter: QPainter, option, widget=None):
        # Thiết lập bút vẽ
        pen = QPen(Qt.red, 20)
        painter.setPen(pen)

        # Vẽ trục Ox: mũi tên ngang
        painter.drawLine(0, 0, self.axis_length, 0)
        # Mũi tên Ox
        arrow_x = QPolygonF([
            QPointF(self.axis_length, 0),
            QPointF(self.axis_length - self.arrow_size, -self.arrow_size/2),
            QPointF(self.axis_length - self.arrow_size, self.arrow_size/2)
        ])
        painter.setBrush(QBrush(Qt.red))
        painter.drawPolygon(arrow_x)

        # Vẽ trục Oy: mũi tên dọc lên
        pen = QPen(Qt.blue, 20)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.blue))
        painter.drawLine(0, 0, 0, -self.axis_length)
        # Mũi tên Oy
        arrow_y = QPolygonF([
            QPointF(0, -self.axis_length),
            QPointF(-self.arrow_size/2, -self.axis_length + self.arrow_size),
            QPointF(self.arrow_size/2, -self.axis_length + self.arrow_size)
        ])
        painter.drawPolygon(arrow_y)

    def hoverEnterEvent(self, event):
        if self.flag:
            self.setCursor(Qt.OpenHandCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self.flag:
            self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if self.flag:
            self.setCursor(Qt.ClosedHandCursor)
            self._startPos = event.scenePos()
            self._itemPos = self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.flag and hasattr(self, '_startPos'):
            delta = event.scenePos() - self._startPos
            self.setPos(self._itemPos + delta)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.flag:
            self.setCursor(Qt.OpenHandCursor)
            self.print_position()
        super().mouseReleaseEvent(event)

    def print_position(self):
        print('Coordinate position: x = {0}, y = {1}'.format(self.pos().x() ,
                                                       self.pos().y()  ))

class GraphicView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setSceneRect(-300, -300, 600, 600)

        self.axes = Coordinate(length=250)
        self.scene.addItem(self.axes)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = GraphicView()
    view.show()
    sys.exit(app.exec_())
