import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from Mapping import MapProcessing
import ezdxf
from gui1 import Ui_MainWindow
from PyQt5.QtGui import QPen, QPolygonF, QFont
from PyQt5.QtCore import Qt, QPointF

class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_points = []
        self.pointsSelectedCallback = None  # Callback để gửi 2 điểm khi chọn xong

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            print(f"Chọn điểm: ({scene_pos.x()}, {scene_pos.y()})")
            self.selected_points.append((scene_pos.x(), scene_pos.y()))
            
            pen = QPen(Qt.green, 50)
            self.scene().addEllipse(scene_pos.x()-250, scene_pos.y()-250, 500, 500, pen)
            
            if len(self.selected_points) == 2:
                print("Đã chọn đủ 2 điểm:", self.selected_points)
                # Gọi callback nếu đã được thiết lập
                if self.pointsSelectedCallback:
                    self.pointsSelectedCallback(self.selected_points[0], self.selected_points[1])
                self.selected_points = []  # Reset danh sách để chọn lại
        super().mousePressEvent(event)

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
        
        self.graphicsView.pointsSelectedCallback = self.processSelectedPoints

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
    
    def processSelectedPoints(self, start, end):
        # Đây là hàm nhận 2 điểm được chọn từ CustomGraphicsView
        print(f"Điểm đầu: {start}, Điểm cuối: {end}")
        # Giả sử bạn có hàm tìm đường đi trong MapProcessing
        path = self.Mapprocessing.dijkstra_shortest_path(start, end)
        print("Đường đi tìm được:", path)
        self.display_path(path)
    
    def display_path(self,path):
        pen_path = QPen(Qt.darkGreen, 20)
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            self.scene.addLine(x1, y1, x2, y2, pen_path)


    def show(self):
        self.main_win.show()

if __name__ =="__main__":
        app = QApplication(sys.argv)
        main_win = MainWindow()
        main_win.show()
        sys.exit(app.exec())