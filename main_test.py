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
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            print(f"Chọn điểm: ({scene_pos.x()}, {scene_pos.y()})")
            self.selected_points = scene_pos.x(), scene_pos.y()
            
           # Gọi callback nếu đã được thiết lập
            if self.pointsSelectedCallback:
                    self.pointsSelectedCallback(self.selected_points)
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
        #setup các nút di chuyển
        self.uic.SetUp.clicked.connect(self.add_moving_item)
        self.uic.Goal.clicked.connect(self.add_goal_item)
        self.uic.Up.clicked.connect(self.move_up)
        self.uic.Down.clicked.connect(self.move_down)
        self.uic.Left.clicked.connect(self.move_left)
        self.uic.Right.clicked.connect(self.move_right)
        self.uic.Clock.clicked.connect(self.rotate_clockwise)
        self.uic.ReClock.clicked.connect(self.rotate_counterclockwise)
        self.uic.Select.clicked.connect(self.find_path)
        self.uic.Load_dxf.clicked.connect(self.load_dxf_file)
        
        # tạo graphics trên widget
        layout = QtWidgets.QVBoxLayout(self.uic.widget)
        self.graphicsView = CustomGraphicsView(self.uic.widget)
        layout.addWidget(self.graphicsView)
        self.scene = QtWidgets.QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        # self.graphicsView.pointsSelectedCallback = self.processSelectedPoints
        self.is_goal_active = False
        self.moving_obj_unactive = True
        self.is_setup_active = False  # Track the state of the SetUp button
        self.selected_goal = None
        self.current_circle = None
        self.path_points = []
        self.path_lines = []

    def load_dxf_file(self):
        # Hộp thoại chọn file DXF
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_win, "Chọn file DXF", "", "DXF Files (*.dxf)"
        )
        if file_path:
            self.Mapprocessing = MapProcessing(file_path)
            self.Mapprocessing.workingCoordinates()

        self.draw_dxf()

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
        proportion = min(float(950/(self.Mapprocessing.max_x - self.Mapprocessing.min_x)), 
                         float(700/(self.Mapprocessing.max_y - self.Mapprocessing.min_y)))
        self.graphicsView.scale(proportion,proportion)
    

    def show(self):
        self.main_win.show()

    def add_moving_item(self):  
        self.is_setup_active = not self.is_setup_active   
        self.is_goal_active = False 
        self.uic.Goal.setStyleSheet("")  
        self.graphicsView.pointsSelectedCallback = None     
        # Change the button color based on the state
        if self.is_setup_active:
            self.uic.SetUp.setStyleSheet("background-color: blue;")  # Change to blue
            # Create an instance of MovingCompositeObject
            if self.moving_obj_unactive:
                self.moving_obj = MovingCompositeObject()
                # Add moving_obj to the scene
                self.scene.addItem(self.moving_obj)
        self.moving_obj_unactive = False
        self.moving_obj.setMovable(True)
        if not self.is_setup_active:
            self.uic.SetUp.setStyleSheet("")
            self.moving_obj.setMovable(False)
           
    def move_up(self):
        if self.is_setup_active:
            if hasattr(self, 'moving_obj'):
                self.moving_obj.setPos(self.moving_obj.pos() + QPointF(0, -100))  # Move up by 10 units

    def move_down(self):
        if self.is_setup_active:
            if hasattr(self, 'moving_obj'):
                self.moving_obj.setPos(self.moving_obj.pos() + QPointF(0, 100))  # Move down by 10 units

    def move_left(self):
        if self.is_setup_active:
            if hasattr(self, 'moving_obj'):
                self.moving_obj.setPos(self.moving_obj.pos() + QPointF(-100, 0))  # Move left by 10 units

    def move_right(self):
        if self.is_setup_active:
            if hasattr(self, 'moving_obj'):
                self.moving_obj.setPos(self.moving_obj.pos() + QPointF(100, 0))  # Move right by 10 units

    def rotate_clockwise(self):
        if self.is_setup_active:
            if hasattr(self, 'moving_obj'):
                self.moving_obj.setRotation(self.moving_obj.rotation() - 10)  # Rotate clockwise by 10 degrees

    def rotate_counterclockwise(self):
        if self.is_setup_active:
            if hasattr(self, 'moving_obj'):
                self.moving_obj.setRotation(self.moving_obj.rotation() + 10)  # Rotate counterclockwise by 10 degrees
    
    def add_goal_item(self):
        self.is_goal_active = not self.is_goal_active
        self.is_setup_active = False   
        self.moving_obj.setMovable(False)
        self.uic.SetUp.setStyleSheet("") 
        if self.is_goal_active:
            self.uic.Goal.setStyleSheet("background-color: blue;")
            self.graphicsView.pointsSelectedCallback = self.processSelectedPoints
        else:
            self.uic.Goal.setStyleSheet("")
            self.graphicsView.pointsSelectedCallback = None 

    def processSelectedPoints(self, points):
        if self.current_circle:
            self.scene.removeItem(self.current_circle)

        self.selected_goal = points  
        self.current_circle = self.scene.addEllipse(self.selected_goal[0]-250, self.selected_goal[1]-250, 500, 500, QPen(Qt.green, 20))
        print(f"Selected goal: {self.selected_goal}")
            
    def find_path(self):
        self.is_goal_active = False
        self.uic.Goal.setStyleSheet("") 
        self.is_setup_active = False
        self.uic.SetUp.setStyleSheet("")
        self.graphicsView.pointsSelectedCallback = None 
        if hasattr(self, 'moving_obj') and self.selected_goal:
            start = (self.moving_obj.pos().x() + self.moving_obj.boundingRect().width() / 2,
                     self.moving_obj.pos().y() + self.moving_obj.boundingRect().height() / 2)
            self.path_points = self.Mapprocessing.dijkstra_shortest_path(start, self.selected_goal)
            self.path_points = self.remove_collinear_points(self.path_points,start,self.selected_goal)
            print(f"Path: {self.path_points}")
            self.display_path(self.path_points)

    def display_path(self, path):  
         # Xóa đường cũ trước khi vẽ đường mới
        for line in getattr(self, 'path_lines', []):
            self.scene.removeItem(line)
        self.path_lines = []  # Xóa danh sách cũ 
        pen_path = QPen(Qt.darkGreen, 20)
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            line =  self.scene.addLine(x1, y1, x2, y2, pen_path)
            self.path_lines.append(line)

    def remove_collinear_points(self,path,start,end):
        if len(path) < 3:
            return path  # Nếu có ít hơn 3 điểm thì không cần xử lý
        
        optimized_path = [path[0]]  # Giữ điểm đầu tiên
        for i in range(1, len(path) - 1):
            x1, y1 = path[i - 1]
            x2, y2 = path[i]
            x3, y3 = path[i + 1]

            # Kiểm tra nếu 3 điểm thẳng hàng bằng cách so sánh hệ số góc
            if (x2 - x1) * (y3 - y2) != (y2 - y1) * (x3 - x2):
                optimized_path.append((x2, y2))  # Giữ lại điểm không nằm trên đoạn thẳng

        optimized_path.append(end)  # Giữ điểm cuối cùng
        optimized_path[0] = start
        return optimized_path  
    
if __name__ =="__main__":
        app = QApplication(sys.argv)
        main_win = MainWindow()
        main_win.show()
        sys.exit(app.exec())