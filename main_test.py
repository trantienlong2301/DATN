import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from Mapping import MapProcessing
import ezdxf
from gui1 import Ui_MainWindow
from PyQt5.QtGui import QPen, QPolygonF, QFont
from PyQt5.QtCore import Qt, QPointF
from AddMovingObject import MovingCompositeObject

class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_points = []
        self.pointsSelectedCallback = None  # Callback để gửi 2 điểm khi chọn xong

   

    def wheelEvent(self, event):
        # Phóng to hoặc thu nhỏ bản đồ
        factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        self.scale(factor, factor)

class MainWindow:
    def __init__(self):
        #setup mainwindow bằng gui1
        self.main_win = QMainWindow()
        self.uic = Ui_MainWindow()
        self.uic.setupUi(self.main_win)
        #setup các nút di chuyển
        self.uic.SetUp.clicked.connect(self.add_moving_item)
        self.uic.Up.clicked.connect(self.move_up)
        self.uic.Down.clicked.connect(self.move_down)
        self.uic.Left.clicked.connect(self.move_left)
        self.uic.Right.clicked.connect(self.move_right)
        self.uic.Clock.clicked.connect(self.rotate_clockwise)
        self.uic.ReClock.clicked.connect(self.rotate_counterclockwise)
        
        # tạo graphics trên widget
        layout = QtWidgets.QVBoxLayout(self.uic.widget)
        self.graphicsView = CustomGraphicsView(self.uic.widget)
        layout.addWidget(self.graphicsView)
        self.scene = QtWidgets.QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        

        # mở file dxf
        self.load_dxf_file()
        self.draw_dxf()
        proportion = min(float(600/(self.Mapprocessing.max_x - self.Mapprocessing.min_x)), 
                         float(600/(self.Mapprocessing.max_y - self.Mapprocessing.min_y)))
        self.graphicsView.scale(proportion,proportion)
        
        # self.graphicsView.pointsSelectedCallback = self.processSelectedPoints

    def load_dxf_file(self):
        # Hộp thoại chọn file DXF
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_win, "Chọn file DXF", "", "DXF Files (*.dxf)"
        )
        if file_path:
            self.Mapprocessing = MapProcessing(file_path)
            self.Mapprocessing.workingCoordinates()

    def draw_dxf(self):
        if self.Mapprocessing.dwg is None:
            print(f"Lỗi khi đọc file DXF")
            return
        pen_line = QPen(Qt.black, 20)
        for segment in self.Mapprocessing.line_points:
            # Mỗi segment là danh sách gồm 2 tuple (x, y)
            x1, y1 = segment[0]
            x2, y2 = segment[1]
            self.scene.addLine(x1, y1, x2, y2, pen_line)
        pen_poly = QPen(Qt.red, 20)
        for polyline in self.Mapprocessing.lwpolyline_points:
            # Chuyển đổi list các tuple thành QPolygonF
            polygon = QPolygonF([QPointF(x, y) for (x, y) in polyline])
            self.scene.addPolygon(polygon, pen_poly)
        font = QFont("Arial", 160)
        for text, coord in self.Mapprocessing.marked_points.items():
            text_item = self.scene.addText(text, font)
            text_item.setDefaultTextColor(Qt.blue)
            # Đặt vị trí dựa trên giá trị x, y đã cho
            text_item.setPos(coord['x'], coord['y'])
    
    

    def show(self):
        self.main_win.show()

    def add_moving_item(self):
    # Tạo một instance của MovingCompositeObject
        self.moving_obj = MovingCompositeObject()
        # Thêm moving_obj vào scene
        self.scene.addItem(self.moving_obj)

    def move_up(self):
        if hasattr(self, 'moving_obj'):
            self.moving_obj.setPos(self.moving_obj.pos() + QPointF(0, -100))  # Move up by 10 units

    def move_down(self):
        if hasattr(self, 'moving_obj'):
            self.moving_obj.setPos(self.moving_obj.pos() + QPointF(0, 100))  # Move down by 10 units

    def move_left(self):
        if hasattr(self, 'moving_obj'):
            self.moving_obj.setPos(self.moving_obj.pos() + QPointF(-100, 0))  # Move left by 10 units

    def move_right(self):
        if hasattr(self, 'moving_obj'):
            self.moving_obj.setPos(self.moving_obj.pos() + QPointF(100, 0))  # Move right by 10 units

    def rotate_clockwise(self):
        if hasattr(self, 'moving_obj'):
            self.moving_obj.setRotation(self.moving_obj.rotation() + 10)  # Rotate clockwise by 10 degrees

    def rotate_counterclockwise(self):
        if hasattr(self, 'moving_obj'):
            self.moving_obj.setRotation(self.moving_obj.rotation() - 10)  # Rotate counterclockwise by 10 degrees

if __name__ =="__main__":
        app = QApplication(sys.argv)
        main_win = MainWindow()
        main_win.show()
        sys.exit(app.exec())