from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QMouseEvent, QPen, QColor

class CustomGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()

        # Tạo một scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Biến lưu hình tròn hiện tại
        self.current_circle = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:  # Chỉ xử lý khi click chuột trái
            scene_pos = self.mapToScene(event.pos())  # Lấy tọa độ trong scene

            # Xóa hình tròn cũ nếu có
            if self.current_circle:
                self.scene.removeItem(self.current_circle)

            # Vẽ hình tròn mới
            pen = QPen(QColor("blue"))  # Viền màu xanh
            self.current_circle = self.scene.addEllipse(scene_pos.x() - 250, scene_pos.y() - 250, 
                                                         500, 500, pen)

        super().mousePressEvent(event)  # Gọi hàm gốc để không ảnh hưởng các sự kiện khác

if __name__ == "__main__":
    app = QApplication([])
    view = CustomGraphicsView()
    view.setSceneRect(0, 0, 800, 600)  # Thiết lập kích thước scene
    view.show()
    app.exec_()
