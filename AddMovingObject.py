from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QPainter, QBrush
import sys
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsObject

class MovingCompositeObject(QGraphicsObject):
    def __init__(self):
        super().__init__()
        # Cho phép nhận các sự kiện hover và đánh dấu là có thể di chuyển, chọn được.
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        
        # Định nghĩa tọa độ và kích thước cho các hình, theo hệ tọa độ cục bộ của đối tượng.
        self.rect1 = QRectF(0, 0, 500, 300)      # Hình chữ nhật thứ nhất
        self.rect2 = QRectF(300, 100, 100, 100)    # Hình chữ nhật thứ hai
        self.rect3 = QRectF(100, -100, 300, 100)   # Hình tròn thứ nhất
        self.rect4 = QRectF(100, 300, 300, 100)    # Hình tròn thứ hai
 # Hình tròn thứ hai
        
        # Đặt màu sắc cho từng hình (có thể tùy chỉnh theo ý muốn)
        self.rect1_color = Qt.GlobalColor.blue
        self.rect2_color = Qt.GlobalColor.green
        self.rect3_color = Qt.GlobalColor.red
        self.rect4_color = Qt.GlobalColor.yellow

        # Thiết lập điểm gốc quay là tâm của boundingRect()
        self.setTransformOriginPoint(self.boundingRect().center())
        
        self.flag = False
    
    def setMovable(self, movable: bool):
        self.flag = movable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, movable)

    def boundingRect(self):
        """
        Phương thức này trả về vùng chứa (bounding rectangle) của toàn bộ đối tượng.
        Vùng này phải bao bọc đủ 4 hình (hai hình chữ nhật và hai hình tròn).
        """
        return QRectF(0, -100, 500, 500)

    def paint(self, painter: QPainter, option, widget=None):
        """
        Phương thức paint sẽ được gọi để vẽ các hình trong đối tượng.
        Chúng ta sử dụng QPainter để vẽ từng hình với màu sắc đã định nghĩa.
        """
        # Vẽ hình chữ nhật thứ nhất
        painter.setBrush(QBrush(self.rect1_color))
        painter.drawRect(self.rect1)
        
        # Vẽ hình chữ nhật thứ hai
        painter.setBrush(QBrush(self.rect2_color))
        painter.drawRect(self.rect2)
        
        # Vẽ hình tròn thứ nhất (drawEllipse vẽ hình elip dựa trên hình chữ nhật bao quanh)
        painter.setBrush(QBrush(self.rect3_color))
        painter.drawRect(self.rect3)
        
        # Vẽ hình tròn thứ hai
        painter.setBrush(QBrush(self.rect4_color))
        painter.drawRect(self.rect4)

    def hoverEnterEvent(self, event):
        """
        Khi con trỏ chuột di chuyển vào vùng của đối tượng,
        thay đổi hình con trỏ thành hình bàn tay mở.
        """
        if self.flag:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """
        Khi con trỏ chuột rời khỏi đối tượng, khôi phục hình con trỏ mặc định.
        """
        if self.flag:
            self.unsetCursor()
        super().hoverLeaveEvent(event)
       
    def mousePressEvent(self, event):
        """
        Khi nhấn chuột, đổi con trỏ thành hình bàn tay nắm chặt,
        và lưu lại vị trí ban đầu của chuột và của đối tượng.
        """
        if self.flag:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self._startPos = event.scenePos()  # Vị trí chuột ban đầu trong scene
            self._itemPos = self.pos()          # Vị trí hiện tại của đối tượng
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """
        Khi kéo chuột, tính toán sự thay đổi vị trí của chuột so với vị trí ban đầu
        và cập nhật vị trí của đối tượng tương ứng.
        """
        if self.flag:
            if hasattr(self, '_startPos'):
                delta = event.scenePos() - self._startPos
                self.setPos(self._itemPos + delta)
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """
        Khi nhả chuột, thay đổi con trỏ trở lại hình bàn tay mở và in ra vị trí mới của đối tượng.
        """
        if self.flag:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.print_position()
        super().mouseReleaseEvent(event)
        
    def print_position(self):
        print('New position: x = {0}, y = {1}'.format(self.pos().x() + self.boundingRect().width() / 2,
                                                       self.pos().y() + self.boundingRect().height() / 2  ))
class GraphicView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)       
        self.setSceneRect(0, 0, 3000, 3000)

        self.moveObject = MovingCompositeObject()
        # self.moveObject2 = MovingObject(100, 100, 100)
        self.scene.addItem(self.moveObject)
        
        # self.scene.addItem(self.moveObject2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = GraphicView()
    view.show()
    sys.exit(app.exec_())