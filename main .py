import sys
import math, socket, json, time, struct, threading
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QDialog
from Mapping import MapProcessing
import ezdxf
from gui2 import Ui_MainWindow
from PyQt5.QtGui import QPen, QPolygonF, QFont
from PyQt5.QtCore import Qt, QPointF, QThread, QPointF, pyqtSignal, QTimer, QObject
from AddMovingObject import MovingCompositeObject
from AddCoordinate import Coordinate
from Trajectory_Tracking import State,PurePursuit,rotation
from InputDiaglog import Ui_Dialog

class InputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)  # nạp giao diện từ .ui
        self.ui.Chieu_rong.setRange(0,1000)
        self.ui.Chieu_rong.setValue(245)
        self.ui.Ban_kinh.setValue(33)
        self.ui.Vmax.setValue(0.1)
        self.ui.pushButton.clicked.connect(self.accept)


    def get_values(self):
        # Lấy dữ liệu từ các spinbox, ví dụ:
        return {
            "Ban_kinh": self.ui.Ban_kinh.value(),
            "Chieu_rong": self.ui.Chieu_rong.value(),
            "Vmax": self.ui.Vmax.value()
        }
    
class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.selected_points = []
        self.flagAddLine = None
        self.pointsSelectedCallback = None  
        self.gridHighlightCallback = None
        self.rightMouseCallback = None
    def eraseSelected_points (self):
        self.selected_points = []

    def mousePressEvent(self, event):        
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            if self.pointsSelectedCallback and self.flagAddLine is None:
                print(f"Chọn điểm: ({scene_pos.x()}, {scene_pos.y()})")
                self.selected_points.append([scene_pos.x(), scene_pos.y()])
                self.pointsSelectedCallback(self.selected_points)
            if self.pointsSelectedCallback and self.flagAddLine:
                self.pointsSelectedCallback(scene_pos)
        if event.button() == Qt.RightButton:
            if self.rightMouseCallback:
                self.rightMouseCallback()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        if self.gridHighlightCallback:
            self.gridHighlightCallback(scene_pos)
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        # Phóng to hoặc thu nhỏ bản đồ
        factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        self.scale(factor, factor)

class TrackingWorker(QObject):
    position_signal = pyqtSignal(float, float, float)
    finished = pyqtSignal()

    def __init__(self, camera, convert_func):
        super().__init__()
        self.camera = camera
        self.convert_func = convert_func
        self.running = True

    def run(self):
        buffer = ""
        prev_receive_time = None
        while self.running:
            try:
                data = self.camera.recv(1024).decode()
                buffer += data  # Nối thêm dữ liệu nhận được

                if '\n' in buffer:
                    lines = buffer.split('\n')       # Tách tất cả dòng hoàn chỉnh
                    last_line = lines[-2] if len(lines) >= 2 else None  # dòng cuối hoàn chỉnh
                    buffer = lines[-1]               # giữ lại phần chưa hoàn chỉnh

                    if last_line:
                        print("Received from server:", last_line)
                        parts = last_line.strip().split(',')
                        if len(parts) == 6:
                            receive_time = int(time.time() * 1000)
                            if prev_receive_time is not None:
                                interval = receive_time - prev_receive_time
                                print("Interval:", interval)
                            prev_receive_time = receive_time

                            x = float(parts[0])
                            y = float(parts[1])
                            z = float(parts[2])
                            pitch = float(parts[3])
                            yaw = float(parts[4])
                            roll = float(parts[5])

                            x_gui, y_gui, angle = self.convert_func(x, z, yaw)
                            self.position_signal.emit(x_gui, y_gui, angle)
            except Exception as e:
                print(f"Lost connection: {e}")
                break
        self.finished.emit()

class MainWindow:
    def __init__(self):
        #setup mainwindow bằng gui1
        self.main_win = QMainWindow()
        self.uic = Ui_MainWindow()
        self.uic.setupUi(self.main_win)
        self.dialog = InputDialog()

        # Tạo spacer trái
        left_spacer = QtWidgets.QWidget()
        left_spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        # Tạo spacer phải
        right_spacer = QtWidgets.QWidget()
        right_spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        # Thêm vào toolbar
        self.uic.toolBar_2.addWidget(left_spacer)

        # Thêm các action giữa hai spacer
        self.uic.toolBar_2.addAction(self.uic.actionSimulate)
        self.uic.toolBar_2.addAction(self.uic.actionStart)
        self.uic.toolBar_2.addAction(self.uic.actionContinue)

        self.uic.toolBar_2.addWidget(right_spacer)

        self.uic.actionOpen.triggered.connect(self.load_dxf_file)
        self.uic.actionAddGoal.triggered.connect(self.add_goal_item)
        self.uic.actionAddLine.triggered.connect(self.AddLine)
        self.uic.actionTrim.triggered.connect(self.EraseLine)
        self.uic.actionSelect.triggered.connect(self.Select)
        self.uic.actionSimulate.triggered.connect(self.Simulate)
        self.uic.actionStart.triggered.connect(self.Start)
        self.uic.actionContinue.triggered.connect(self.resume_next_segment)
        self.uic.actioncoordinate.triggered.connect(self.AddCoordinate)
        self.uic.actionrobot.triggered.connect(self.AddObject)
        self.uic.actionInput.triggered.connect(self.Show_input_diaglog)
        self.uic.actionconnect.triggered.connect(self.connect)
        self.uic.actiontracking.triggered.connect(self.tracking)
        self.uic.actionstop.triggered.connect(self.stop)
        # tạo graphics trên widget
        layout = QtWidgets.QVBoxLayout()
        self.graphicsView = CustomGraphicsView(self.uic.Screen)
        layout.addWidget(self.graphicsView)
        self.uic.Screen.setLayout(layout)

        self.scene = QtWidgets.QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        self.uic.VelLeft.setStyleSheet("QLabel { background-color: rgba(255, 255, 255, 0); color: black; }")
        self.uic.VelRight.setStyleSheet("QLabel { background-color: rgba(255, 255, 255, 0); color: black; }")
        self.uic.Angle.setStyleSheet("QLabel { background-color: rgba(255, 255, 255, 0); color: black; }")
        self.uic.VelLeft.raise_()
        self.uic.VelRight.raise_()
        self.uic.Angle.raise_()
        # Thiết lập callback cho sự kiện di chuyển chuột
        self.current_highlighted_point = None  
        self.current_highlighted_line_erase = None # Đối tượng đang được highlight
        self.current_highlighted_line_add = None
        self.grid_point_item = []
        self.selected_goals = None
        self.current_circle = None
        self.line_items = []
        self.path = []
        self.flags = {
            "AddGoal" : False,
            "AddLine" : False,
            "EraseLine" : False,
            "Simulate" : False,
            "Start" : False,
            "AddObject": False,
            "AddCoordinate": False
        }
        self.Wright = 0
        self.Wleft = 0
        self.robot1 =0
        self.robot2 = 0
        self.robot3 = 0
        self.ban_kinh = 33
        self.chieu_rong = 245
        self.speed = 0.1
        self.esp32 = None
        self.camera = None


    def Show_input_diaglog(self):
        if self.dialog.exec_():  # hiện cửa sổ và đợi OK
            values = self.dialog.get_values()
            self.ban_kinh = values["Ban_kinh"]
            self.chieu_rong = values["Chieu_rong"]
            self.speed = values["Vmax"]
            print("Giá trị đã nhập:", self.ban_kinh, self.chieu_rong, self.speed)
        if hasattr(self, 'moving_obj'):
            pos = self.moving_obj.pos()
            self.scene.removeItem(self.moving_obj)
            self.moving_obj = MovingCompositeObject(self.chieu_rong)
            self.scene.addItem(self.moving_obj)
            self.moving_obj.setPos(pos)


    def display_button_color(self,button):
        for key in self.flags:
            if key == button:
                self.flags[key] = not self.flags[key]
            else:
                self.flags[key] = False
        
        self.resetCallback()
        self.resetFlag(button)

    def resetCallback(self):
        self.graphicsView.pointsSelectedCallback = None  
        self.graphicsView.gridHighlightCallback = None
        self.graphicsView.rightMouseCallback = None

    def resetFlag(self,button):
        if button == "AddObject":
            if hasattr(self, "moving_obj"): 
                self.moving_obj.setMovable(True)
        else:
            if hasattr(self, "moving_obj"): 
                self.moving_obj.setMovable(False)

        if button == "AddCoordinate":
            if hasattr(self, "coordinate"): 
                self.coordinate.setMovable(True)
        else:
            if hasattr(self, "coordinate"):
                self.coordinate.setMovable(False)

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
        self.scene.clear()
        if hasattr(self, 'moving_obj'):
            del self.moving_obj
        if hasattr(self, 'coordinate'):
            del self.coordinate
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
        self.draw_grid()
        proportion = min(float((self.uic.Screen.width()-50)/(self.Mapprocessing.max_x - self.Mapprocessing.min_x)), 
                         float((self.uic.Screen.height()-50)/(self.Mapprocessing.max_y - self.Mapprocessing.min_y)))
        self.graphicsView.scale(proportion,proportion)  

    def AddObject(self):  
        self.display_button_color("AddObject")
        if hasattr(self, "chieu_rong"):
            D = self.chieu_rong
        else:
            D = 300
        if not hasattr(self, "moving_obj"):          
            self.moving_obj = MovingCompositeObject(D)
        # Add moving_obj to the scene
            self.scene.addItem(self.moving_obj)           
       
    def AddCoordinate(self):  
            self.display_button_color("AddCoordinate") 
            if not hasattr(self, "coordinate"):          
                self.coordinate = Coordinate()
            # Add moving_obj to the scene
                self.scene.addItem(self.coordinate)
                # self.scene.addEllipse(
                #     self.coordinate.pos().x() - 250,  # X tọa độ góc trên bên trái
                #     self.coordinate.pos().y() - 250,  # Y tọa độ góc trên bên trái
                #     500, 500,  # Chiều rộng và chiều cao (hình tròn có đường kính 500)
                #     QPen(Qt.green, 20)  # Màu viền xanh lá và độ dày 20px
                # )

    def draw_grid(self):
        #Vẽ lưới (grid) được tạo bởi MapProcessing lên scene."""
        if not hasattr(self, 'Mapprocessing'):
            return

        # Tạo bút vẽ cho lưới với đường nét đứt, màu xám
        pen_grid = QPen(Qt.gray, 2, Qt.DashLine)
        self.grid_point_item = self.Mapprocessing.gridalter
        # Giả sử mỗi ô có kích thước 200x200 như đã sử dụng khi tạo lưới,
        # vẽ một hình chữ nhật cho mỗi ô.
        for cell in self.Mapprocessing.gridalter:
            x, y = cell
            if (x+200,y+200)  in self.Mapprocessing.gridalter:
                rect = QtCore.QRectF(x, y, 200, 200)
            else:
                continue
            self.scene.addRect(rect, pen_grid)

    def highlightGridPoint(self, scene_pos):
        if not hasattr(self, 'Mapprocessing') or not hasattr(self, 'grid_point_item'):
            return
        
        min_distance = float('inf')
        nearest_index = -1
        
        # Tìm điểm có khoảng cách nhỏ nhất đến vị trí chuột
        for i, point in enumerate(self.grid_point_item):
            # Giả sử mỗi điểm trong grid là tọa độ trung tâm của ô
            distance = math.hypot(scene_pos.x() - point[0], scene_pos.y() - point[1])
            if distance < min_distance:
                min_distance = distance
                nearest_index = i

        if nearest_index != -1:
            # Reset lại điểm đã được highlight trước đó nếu có
            if self.current_highlighted_point is not None:
                self.scene.removeItem(self.current_highlighted_point)
                self.current_highlighted_point = None

            # Highlight điểm mới: thay đổi màu sang vàng (có thể thay đổi kích thước nếu muốn)
            circle = self.scene.addEllipse(
                self.grid_point_item[nearest_index][0] - 100,  # X tọa độ góc trên bên trái
                self.grid_point_item[nearest_index][1] - 100,  # Y tọa độ góc trên bên trái
                200, 200,  # Chiều rộng và chiều cao (hình tròn có đường kính 500)
                QPen(Qt.green, 20)  # Màu viền xanh lá và độ dày 20px
            )
            self.current_highlighted_point = circle 

    def show(self):
        self.main_win.show()
           
    def add_goal_item(self):
        self.display_button_color("AddGoal")
        if self.flags["AddGoal"]:
            self.graphicsView.eraseSelected_points()
            self.graphicsView.flagAddLine = None
            self.graphicsView.gridHighlightCallback = self.highlightGridPoint
            self.graphicsView.pointsSelectedCallback = self.processSelectedPoints

    def processSelectedPoints(self, points_list):
        # Xóa tất cả các hình tròn cũ
        for circle in getattr(self, "current_circles", []):
            self.scene.removeItem(circle)
        # Lưu danh sách điểm được chọn
        self.selected_goals = []
        for point in points_list:
            self.selected_goals.append(self.Mapprocessing.findClosestGridCenter(point)) 
        
        # Danh sách mới để lưu các hình tròn
        self.current_circles = []
        
        # Vẽ hình tròn tại từng điểm trong danh sách
        for point in self.selected_goals:
            circle = self.scene.addEllipse(
                point[0] - 150,  # X tọa độ góc trên bên trái
                point[1] - 150,  # Y tọa độ góc trên bên trái
                300, 300,  # Chiều rộng và chiều cao (hình tròn có đường kính 500)
                QPen(Qt.green, 20)  # Màu viền xanh lá và độ dày 20px
            )
            self.current_circles.append(circle)  # Lưu lại để xóa sau này
        
    def highlightPathLine(self, scene_pos):
        # Kiểm tra xem self.path_lines có tồn tại và không rỗng không
        if not hasattr(self, 'line_items') or len(self.line_items) == 0:
            return
        
        min_distance = float('inf')
        nearest_line = None
        
        # Tìm đoạn thẳng gần nhất với vị trí chuột
        for line in self.line_items:
            x1, y1 = line.line().p1().x(), line.line().p1().y()
            x2, y2 = line.line().p2().x(), line.line().p2().y()
            
            # Tính khoảng cách từ điểm chuột đến đoạn thẳng
            distance = self.distanceToLine(scene_pos, x1, y1, x2, y2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_line = line
        
        # Ngưỡng khoảng cách để highlight (ví dụ: 50 pixel)
        if min_distance < 50:
            # Xóa highlight cũ nếu có
            if self.current_highlighted_line_erase is not None:
                self.current_highlighted_line_erase.setPen(QPen(Qt.darkGreen, 50))  # Màu gốc
            
            # Highlight đoạn thẳng gần nhất
            nearest_line.setPen(QPen(Qt.yellow, 50))  # Màu vàng để highlight
            self.current_highlighted_line_erase = nearest_line

        else:
            # Nếu không có đoạn thẳng nào gần, xóa highlight cũ
            if self.current_highlighted_line_erase is not None:
                self.current_highlighted_line_erase.setPen(QPen(Qt.darkGreen, 50))
                self.current_highlighted_line_erase = None

    def removePathLine(self, scene_pos):
            # Kiểm tra xem self.path_lines có tồn tại và không rỗng không
            if not hasattr(self, 'line_items') or len(self.line_items) == 0:
                return
            
            min_distance = float('inf')
            nearest_line = None
            
            # Tìm đoạn thẳng gần nhất với vị trí chuột
            for line in self.line_items:
                x1, y1 = line.line().p1().x(), line.line().p1().y()
                x2, y2 = line.line().p2().x(), line.line().p2().y()
                
                # Tính khoảng cách từ điểm chuột đến đoạn thẳng
                distance = self.distanceToLine(scene_pos, x1, y1, x2, y2)
                if distance < min_distance:
                    min_distance = distance
                    nearest_line = line
            
            # Ngưỡng khoảng cách để highlight (ví dụ: 50 pixel)
            if min_distance < 50:
                # Xóa highlight cũ nếu có
                self.scene.removeItem(nearest_line)
                self.line_items.remove(nearest_line)

    def distanceToLine(self, point, x1, y1, x2, y2):
        import math
        
        # Vector từ điểm đầu đến điểm cuối của đoạn thẳng
        line_vec = [x2 - x1, y2 - y1]
        # Vector từ điểm đầu đến điểm chuột
        point_vec = [point.x() - x1, point.y() - y1]
        
        # Tính độ dài đoạn thẳng
        line_len = math.hypot(line_vec[0], line_vec[1])
        if line_len == 0:
            return math.hypot(point_vec[0], point_vec[1])
        
        # Tính projection scalar
        proj = (point_vec[0] * line_vec[0] + point_vec[1] * line_vec[1]) / (line_len ** 2)
        
        if proj < 0:
            closest = [x1, y1]  # Điểm gần nhất là điểm đầu
        elif proj > 1:
            closest = [x2, y2]  # Điểm gần nhất là điểm cuối
        else:
            closest = [x1 + proj * line_vec[0], y1 + proj * line_vec[1]]  # Điểm trên đoạn thẳng
        
        # Tính khoảng cách Euclidean từ điểm chuột đến điểm gần nhất
        dx = point.x() - closest[0]
        dy = point.y() - closest[1]
        return math.hypot(dx, dy)

    def EraseLine(self):
        self.display_button_color("EraseLine")
        if self.flags["EraseLine"]:
            self.graphicsView.flagAddLine = True
            self.graphicsView.gridHighlightCallback = self.highlightPathLine
            self.graphicsView.pointsSelectedCallback = self.removePathLine

    def AddLine(self):
        self.display_button_color("AddLine")
        if self.flags["AddLine"]:
            self.versus = []
            self.point1 = None
            self.graphicsView.flagAddLine = True
            self.graphicsView.gridHighlightCallback = self.LineCallback
            self.graphicsView.pointsSelectedCallback = self.AddlineCallback
            self.graphicsView.rightMouseCallback = self.finishCallback
    
    def finishCallback(self):
        self.point1 = None
        self.versus = []
        self.scene.removeItem(self.current_highlighted_line_add)
        self.current_highlighted_line_add = None
    
    def LineCallback(self,scene_pos):
        if not hasattr(self, 'Mapprocessing') or not hasattr(self, 'grid_point_item'):
            return
        
        min_distance = float('inf')
        nearest_index = -1
        pen_path = QPen(Qt.darkGreen, 50)
        # Tìm điểm có khoảng cách nhỏ nhất đến vị trí chuột
        for i, point in enumerate(self.grid_point_item):
            # Giả sử mỗi điểm trong grid là tọa độ trung tâm của ô
            distance = math.hypot(scene_pos.x() - point[0], scene_pos.y() - point[1])
            if distance < min_distance:
                min_distance = distance
                nearest_index = i
        
        if nearest_index != -1:
            # Reset lại điểm đã được highlight trước đó nếu có
            if self.current_highlighted_point is not None:
                self.scene.removeItem(self.current_highlighted_point)
                self.current_highlighted_point = None

            # Highlight điểm mới: thay đổi màu sang vàng (có thể thay đổi kích thước nếu muốn)
            circle = self.scene.addEllipse(
                self.grid_point_item[nearest_index][0] - 100,  # X tọa độ góc trên bên trái
                self.grid_point_item[nearest_index][1] - 100,  # Y tọa độ góc trên bên trái
                200, 200,  # Chiều rộng và chiều cao (hình tròn có đường kính 500)
                QPen(Qt.green, 20)  # Màu viền xanh lá và độ dày 20px
            )
            self.current_highlighted_point = circle 
        if self.point1 is not None:
            if self.current_highlighted_line_add is not None:
                self.scene.removeItem(self.current_highlighted_line_add)
                self.current_highlighted_line_add = None

            line = self.scene.addLine(
                self.point1[0],self.point1[1],
                self.grid_point_item[nearest_index][0],self.grid_point_item[nearest_index][1],
                pen_path
            )
            self.current_highlighted_line_add = line

    def AddlineCallback(self, scene_pos):
        if not hasattr(self, 'Mapprocessing') or not hasattr(self, 'grid_point_item'):
            return
        
        min_distance = float('inf')
        nearest_index = -1
        pen_path = QPen(Qt.darkGreen, 50)
        # Tìm điểm có khoảng cách nhỏ nhất đến vị trí chuột
        for i, point in enumerate(self.grid_point_item):
            # Giả sử mỗi điểm trong grid là tọa độ trung tâm của ô
            distance = math.hypot(scene_pos.x() - point[0], scene_pos.y() - point[1])
            if distance < min_distance:
                min_distance = distance
                nearest_index = i

        if nearest_index != -1:
            self.versus.append(self.grid_point_item[nearest_index])
            self.point1 = self.grid_point_item[nearest_index]
            #print(self.grid_point_item[i])
            if len(self.versus) == 2:
                line =  self.scene.addLine(self.versus[0][0], self.versus[0][1], self.versus[1][0],self.versus[1][1], pen_path)
                self.line_items.append(line)
                del self.versus[0]

    def Select(self):
        if not self.line_items:
            return
        self.path_points = []
        inter_path = []
        path_line = self.line_items
        start = self.selected_goals[0]
        end = self.selected_goals[-1]
        for line in path_line:
            (x1,y1) = (line.line().p1().x(),line.line().p1().y())
            (x2,y2) = (line.line().p2().x(),line.line().p2().y())
            if (x1,y1) not in inter_path:
                inter_path.append((x1,y1))
            if (x2,y2) not in inter_path:
                inter_path.append((x2,y2))
        length = len(inter_path)
        inter_path2 = [[] for _ in range(length)]
        for line in path_line:
            x1, y1 = line.line().p1().x(), line.line().p1().y()
            x2, y2 = line.line().p2().x(), line.line().p2().y()
            try:
                i1 = inter_path.index((x1, y1))
                i2 = inter_path.index((x2, y2))
            except ValueError:
                continue
            if (x2, y2) not in inter_path2[i1]:
                inter_path2[i1].append((x2, y2))
            if (x1, y1) not in inter_path2[i2]:
                inter_path2[i2].append((x1, y1))
        # Hàm DFS để tìm đường đi từ start đến end trên đồ thị các điểm
        def dfs(current, end, path, visited):
            if current == end:
                return path
            visited.add(current)
            # Tìm index của current trong inter_path để lấy các điểm kề
            try:
                index = inter_path.index(current)
            except ValueError:
                return None
            for neighbor in inter_path2[index]:
                if neighbor not in visited:
                    result = dfs(neighbor, end, path + [neighbor], visited)
                    if result is not None:
                        return result
            return None

        # Tìm đường đi (danh sách các điểm nối liền)
        path_mid = dfs(start, end, [start], set())
        if path_mid is None:
            print("Không tìm được đường đi từ start đến end.")
            return

        
        #     return new_path
        self.path = []
        mid = []
        for point in path_mid:
            mid.append(point)
            if point in self.selected_goals:
                self.path.append(mid)
                mid = [point]
        # Nếu còn phần dư, thêm vào cuối
        if mid:
            self.path.append(mid)
        del self.path[0] 
        del self.path[-1]
        print("Cập nhật self.path_points:", self.path_points)
        print("Cập nhật self.path_points:", self.path)

    def resume_next_segment(self):
        if self.resume_timer is not None:
            self.resume_timer.stop()  # Dừng timer nếu đang chạy
            self.resume_timer = None
        if self.next_segment_callback:
            self.next_segment_callback()
            self.next_segment_callback = None

    def densify_path(self,path, step=200):
            if step <= 0:
                raise ValueError("Step phải > 0")

            new_path = []
            n = len(path)
            if n == 0:
                return new_path
            new_path.append(path[0])

            for i in range(n - 1):
                x0, y0 = path[i]
                x1, y1 = path[i+1]
                # độ dài đoạn thẳng
                dx = x1 - x0
                dy = y1 - y0
                dist = math.hypot(dx, dy)
                # số bước chèn thêm (loại bỏ đầu/cuối)
                num = max(int(math.floor(dist / step)), 1)
                # vector đơn vị hướng từ p0 sang p1
                ux = dx / dist
                uy = dy / dist

                # tạo các điểm cách đều
                for k in range(1, num):
                    px = x0 + ux * step * k
                    py = y0 + uy * step * k
                    new_path.append((px, py))

                # thêm điểm cuối đoạn (là điểm góc của path gốc)
                new_path.append((x1, y1))

            return new_path
    
    def Simulate(self):
            self.display_button_color("Simulate")
            segments = self.path 
            if not hasattr(self, 'moving_obj') or not hasattr(self, 'ban_kinh') or len(segments)  == 0:#Kiểm tra nếu không có moving_obj hoặc segments trống thì thoát hàm
                self.display_button_color("Simulate")
                print("error")
                return
            # Các biến dùng để điều khiển việc chuyển sang đoạn tiếp theo
            self.state = State(self.ban_kinh,self.chieu_rong)
            self.resume_timer = None
            self.next_segment_callback = None
            def animate_segment(seg_index):
                if seg_index >= len(segments):
                    self.display_button_color("Simulate")
                    return  # Đã hết các đoạn, dừng animation

                segment = segments[seg_index]
                # Nếu đoạn không đủ điểm để di chuyển, chuyển sang đoạn kế
                if len(segment) < 2:
                    wait_for_resume(seg_index + 1)
                    return
                start_point = self.moving_obj.pos()
                self.point1x,self.point1y = start_point.x(),start_point.y()
                
            # Định nghĩa hàm di chuyển từng bước
                def move_step(index):
                    if index >= len(segment):
                         # Khi hoàn thành đoạn, tạm dừng 5s hoặc chờ nhấn nút để chuyển sang đoạn tiếp theo
                        wait_for_resume(seg_index + 1)
                        return  # Kết thúc hàm
                    start_point = self.moving_obj.pos()
                    self.point1x,self.point1y = start_point.x(),start_point.y()
                    end_point = QPointF(segment[index][0], segment[index][1])
                    target_angle = math.degrees(math.atan2(segment[index][1] - segment[index - 1][1],segment[index][0] - segment[index - 1][0])) 
                    path = [segment[index-1],segment[index]]
                    densified_segment = self.densify_path(path,200)
                    self.PurePursuit = PurePursuit(densified_segment,500,100)
                    def step():
                        current_pos = self.moving_obj.pos()
                        self.scene.addLine(
                            self.point1x,self.point1y,
                            current_pos.x(),current_pos.y(),
                            QPen(Qt.red, 30)
                        )
                        self.point1x,self.point1y = current_pos.x(),current_pos.y()
                        current_angle = self.moving_obj.rotation()
                        d_travelled = math.hypot(current_pos.x() - start_point.x(), current_pos.y() - start_point.y())
                        d_remain = math.hypot(current_pos.x() - end_point.x(), current_pos.y() - end_point.y()) -100
                        if d_remain < 30:
                            self.uic.VelRight.setText(f"Wright: 0 rad/s")
                            self.uic.VelLeft.setText(f"Wleft: 0 rad/s")
                            move_step(index+1)
                        else:
                            v_desired = min(math.sqrt(2 * 500 * d_travelled) if d_travelled > 0 else 50,
                                        10*self.speed,
                                        math.sqrt(2 * 500 * d_remain) if d_remain > 0 else 50)
                            angle,velRight,velLeft =self.PurePursuit.control([current_pos.x(),current_pos.y(),math.radians(current_angle)],v_desired)
                            self.Wright = velRight/self.state.R
                            self.Wleft = velLeft/self.state.R
                            velx,vely,velang = self.state.velocity(math.radians(self.moving_obj.rotation()),self.Wright,self.Wleft)
                            velang = math.degrees(velang)
                            newPos = current_pos + QPointF(velx*0.1,vely*0.1)
                            newAngle = current_angle + velang * 0.1
                            self.uic.VelRight.setText(f"Wright: {self.Wright:.2f} rad/s")
                            self.uic.VelLeft.setText(f"Wleft: {self.Wleft:.2f} rad/s")
                            self.uic.Angle.setText(f"Angle: {-newAngle:.2f} deg")
                            self.moving_obj.setPos(newPos)
                            self.moving_obj.setRotation(newAngle)
                            QTimer.singleShot(100,step)
                    def step_angle():
                        self.rotation = rotation(target_angle,5)
                        current_angle = self.moving_obj.rotation()
                        current_angle = current_angle - int(current_angle/360)*360
                        if current_angle <= -180: 
                            current_angle = 360 - current_angle
                        if current_angle > 180:
                            current_angle = -360 + current_angle
                        current_pos = self.moving_obj.pos()
                        testkey = abs(current_angle - target_angle)
                        print("test: ", testkey)
                        print("current_pos: ", current_angle)
                        print("target_angle:" ,target_angle)
                        if testkey < 10:
                            self.Wleft = 0
                            self.Wright = 0
                            self.uic.VelRight.setText(f"Wright: 0 rad/s")
                            self.uic.VelLeft.setText(f"Wleft: 0 rad/s")
                            step()
                        else:
                            self.Wleft, self.Wright = self.rotation.control(current_angle)
                            velx,vely,velang = self.state.velocity(math.radians(self.moving_obj.rotation()),self.Wright,self.Wleft)
                            velang = math.degrees(velang)
                            newPos = current_pos + QPointF(velx*0.1,vely*0.1)
                            newAngle = current_angle + velang * 0.1
                            newAngle = int(newAngle)
                            self.uic.VelRight.setText(f"Wright: {self.Wright:.2f} rad/s")
                            self.uic.VelLeft.setText(f"Wleft: {self.Wleft:.2f} rad/s")
                            self.uic.Angle.setText(f"Angle: {-newAngle:.2f} deg")
                            self.moving_obj.setPos(newPos)
                            self.moving_obj.setRotation(newAngle)
                            QTimer.singleShot(100,step_angle)
                    step_angle()
                move_step(1)
                  

            def wait_for_resume(next_seg_index):
                # Lưu lại callback chuyển sang đoạn tiếp theo
                self.next_segment_callback = lambda: animate_segment(next_seg_index)
                # Sử dụng QTimer để đợi 5 giây
                self.resume_timer = QTimer()
                self.resume_timer.setSingleShot(True)
                self.resume_timer.timeout.connect(self.next_segment_callback)
                self.resume_timer.start(5000)

            # Bắt đầu animate với đoạn đầu tiên
            animate_segment(0)

    def stop(self):
        if self.esp32 is not None:
            msg = f"0,0\n"
            self.esp32.sendall(msg.encode())
            self.esp32.close()
            self.esp32 = None
        

    def Start(self):

        def send_data():
            dem = 0
            while self.flag:
                    dem +=1
                    left_speed = int(-self.Wright *17.54)
                    right_speed = int(self.Wleft *17.54)
                    msg = f"{left_speed},{right_speed}\n"
                    print(f"📤 Gửi: {msg.strip()}")
                    print(f"Đã gửi lúc {time.time()}")
                    self.esp32.sendall(msg.encode())
                    time.sleep(0.01)

        segments = self.path
        if not hasattr(self, 'moving_obj')  or len(segments) == 0:#Kiểm tra nếu không có moving_obj hoặc segments trống thì thoát hàm
            self.display_button_color("Simulate")
            print("error")
            return
        
       # Các biến dùng để điều khiển việc chuyển sang đoạn tiếp theo
        self.state = State(self.ban_kinh,self.chieu_rong)
        self.flag = True
        self.resume_timer = None
        self.next_segment_callback = None
        # Định nghĩa hàm di chuyển từng bước
        def animate_segment(seg_index):
            if (abs(self.moving_obj.pos().x()  - self.path[-1][-1][0]) < 100) and (abs(self.moving_obj.pos().y() - self.path[-1][-1][1]) < 100) :
                self.flag = False
                print(" completed.")

            if seg_index >= len(segments):
                self.display_button_color("Simulate")
                self.flag =False
                return  # Đã hết các đoạn, dừng animation

            segment = segments[seg_index]
            # Nếu đoạn không đủ điểm để di chuyển, chuyển sang đoạn kế
            if len(segment) < 2:
                wait_for_resume(seg_index + 1)
                return
            
            start_point = self.moving_obj.pos()
            self.point1x,self.point1y = start_point.x(),start_point.y()

            def move_step(index):
                if index >= len(segment):
                     # Khi hoàn thành đoạn, tạm dừng 5s hoặc chờ nhấn nút để chuyển sang đoạn tiếp theo
                    wait_for_resume(seg_index + 1)
                    return  # Kết thúc hàm
                start_point = self.moving_obj.pos()
                self.point1x,self.point1y = start_point.x(),start_point.y()
                end_point = QPointF(segment[index][0], segment[index][1])
                target_angle = math.degrees(math.atan2(segment[index][1] - segment[index - 1][1],segment[index][0] - segment[index - 1][0])) 
                path = [segment[index-1],segment[index]]
                densified_segment = self.densify_path(path,200)
                self.PurePursuit = PurePursuit(densified_segment,500,100)
                def step():
                    current_pos = self.moving_obj.pos()
                    self.scene.addLine(
                        self.point1x,self.point1y,
                        current_pos.x(),current_pos.y(),
                        QPen(Qt.red, 30)
                    )
                    self.point1x,self.point1y = current_pos.x(),current_pos.y()
                    current_angle = self.moving_obj.rotation()
                    d_travelled = math.hypot(current_pos.x() - start_point.x(), current_pos.y() - start_point.y())
                    d_remain = math.hypot(current_pos.x() - end_point.x(), current_pos.y() - end_point.y()) -100
                    if d_remain < 50:
                        self.uic.VelRight.setText(f"Wright: 0 rad/s")
                        self.uic.VelLeft.setText(f"Wleft: 0 rad/s")
                        self.Wleft =0
                        self.Wright = 0
                        move_step(index+1)
                    else:
                        v_desired = self.speed
                        angle,velRight,velLeft =self.PurePursuit.control([current_pos.x(),current_pos.y(),math.radians(current_angle)],v_desired)
                        self.Wright = velRight/self.state.R
                        self.Wleft = velLeft/self.state.R
                        self.uic.VelRight.setText(f"Wright: {self.Wright:.2f} rad/s")
                        self.uic.VelLeft.setText(f"Wleft: {self.Wleft:.2f} rad/s")
                        QTimer.singleShot(10,step)
                
                def step_angle():
                    self.rotation = rotation(target_angle,1)
                    current_angle = self.moving_obj.rotation()
                    testkey = abs(current_angle - target_angle)
                    if testkey < 20:
                        self.Wleft = 0
                        self.Wright = 0
                        self.uic.VelRight.setText(f"Wright: 0 rad/s")
                        self.uic.VelLeft.setText(f"Wleft: 0 rad/s")
                        step()
                    else:
                        self.Wleft, self.Wright = self.rotation.control(current_angle)
                        self.uic.VelRight.setText(f"Wright: {self.Wright:.2f} rad/s")
                        self.uic.VelLeft.setText(f"Wleft: {self.Wleft:.2f} rad/s")
                        QTimer.singleShot(10,step_angle)
                step_angle()
            move_step(1)
                

        def wait_for_resume(next_seg_index):
            # Lưu lại callback chuyển sang đoạn tiếp theo
            self.next_segment_callback = lambda: animate_segment(next_seg_index)
            # Sử dụng QTimer để đợi 5 giây
            self.resume_timer = QTimer()
            self.resume_timer.setSingleShot(True)
            self.resume_timer.timeout.connect(self.next_segment_callback)
            self.resume_timer.start(5000)

        # Bắt đầu animate với đoạn đầu tiên
        animate_segment(0)
        t_send = threading.Thread(target=send_data, daemon=True)
        t_send.start()


    def converCoordinate(self, x, z, angle):
        if hasattr(self, 'coordinate'):
            toa_do1, toa_do2 = self.coordinate.pos().x(), self.coordinate.pos().y()
            robot1 = toa_do1 - z
            robot2 = toa_do2 + x
            robot3 = -angle
            return robot1, robot2, robot3
        else:
            return x,z,angle

    def connect(self):
        if self.camera is None:
            self.thread = QThread()
            self.uic.actionconnect.setEnabled(False)
            # Gắn một function xử lý trực tiếp vào thread
            def do_connect():
                # ESP32
                while True:
                    try:
                        print(" Đang kết nối ESP32...")
                        self.esp32 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.esp32.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                        self.esp32.settimeout(10)
                        self.esp32.connect(('192.168.158.56', 1234))
                        self.esp32.settimeout(0)
                        print(" Đã kết nối ESP32.")
                        break
                    except Exception as e:
                        print(f"ESP32 lỗi: {e}")
                        time.sleep(2)

                # Camera
                while True:
                    try:
                        print(" Đang kết nối Camera...")
                        self.camera = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.camera.connect(('192.168.158.102', 8000))
                        print(" Đã kết nối Camera.")
                        break
                    except Exception as e:
                        print(f" Camera lỗi: {e}")
                        time.sleep(2)
                self.thread.quit() 
                # Thoát sau khi xong

            self.thread.run = do_connect  # Gắn hàm xử lý vào QThread
            self.thread.finished.connect(lambda: self.uic.actionconnect.setEnabled(True))
            self.thread.start()
        else:
            # self.esp32.close()
            self.camera.close()
            print("đã ngắt kết nối")

            self.esp32 = None
            self.camera = None

    def tracking(self):
        self.uic.actiontracking.setEnabled(False)

        self.threadposition = QThread()
        self.worker = TrackingWorker(
            camera=self.camera,
            convert_func=self.converCoordinate
        )
        self.worker.moveToThread(self.threadposition)

        # Kết nối tín hiệu
        self.threadposition.started.connect(self.worker.run)
        self.worker.position_signal.connect(self.update_robot_position)
        self.worker.finished.connect(self.threadposition.quit)
        self.worker.finished.connect(lambda: self.uic.actiontracking.setEnabled(True))
        self.threadposition.finished.connect(self.worker.deleteLater)
        self.threadposition.finished.connect(self.threadposition.deleteLater)

        self.threadposition.start()

    def update_robot_position(self, x, y, angle):
        self.robot1, self.robot2, self.robot3 = x, y, angle
        self.moving_obj.setPos(QPointF(x, y))
        self.moving_obj.setRotation(angle)
        self.uic.Angle.setText(f"Angle: {self.robot3} deg")


    def Start2(self):
        def send_data():
            dem = 0
            while self.flag:
                    dem +=1
                    left_speed = int(-self.Wright *17.54)
                    right_speed = int(self.Wleft *17.54)
                    msg = f"{left_speed},{right_speed}\n"
                    print(f"📤 Gửi: {msg.strip()}")
                    print(f"Đã gửi lúc {time.time()}")
                    self.esp32.sendall(msg.encode())
                    time.sleep(0.01)

        segments = self.path
        if not hasattr(self, 'moving_obj')  or len(segments) == 0:#Kiểm tra nếu không có moving_obj hoặc segments trống thì thoát hàm
            self.display_button_color("Simulate")
            print("error")
            return
        
       # Các biến dùng để điều khiển việc chuyển sang đoạn tiếp theo
        self.state = State(self.ban_kinh,self.chieu_rong)
        self.flag = True
        self.resume_timer = None
        self.next_segment_callback = None
        # Định nghĩa hàm di chuyển từng bước
        def animate_segment(seg_index):
            if (abs(self.moving_obj.pos().x()  - self.path[-1][-1][0]) < 100) and (abs(self.moving_obj.pos().y() - self.path[-1][-1][1]) < 100) :
                self.flag = False
                print(" completed.")

            if seg_index >= len(segments):
                self.display_button_color("Simulate")
                self.flag =False
                return  # Đã hết các đoạn, dừng animation

            segment = segments[seg_index]
            # Nếu đoạn không đủ điểm để di chuyển, chuyển sang đoạn kế
            if len(segment) < 2:
                wait_for_resume(seg_index + 1)
                return
            
            start_point = self.moving_obj.pos()
            self.point1x,self.point1y = start_point.x(),start_point.y()

            def move_step(index):
                if index >= len(segment):
                     # Khi hoàn thành đoạn, tạm dừng 5s hoặc chờ nhấn nút để chuyển sang đoạn tiếp theo
                    wait_for_resume(seg_index + 1)
                    return  # Kết thúc hàm
                start_point = self.moving_obj.pos()
                self.point1x,self.point1y = start_point.x(),start_point.y()
                end_point = QPointF(segment[index][0], segment[index][1])
                path = segment
                densified_segment = self.densify_path(path,200)
                self.PurePursuit = PurePursuit(densified_segment,500,100)
                def step():
                    current_pos = self.moving_obj.pos()
                    self.scene.addLine(
                        self.point1x,self.point1y,
                        current_pos.x(),current_pos.y(),
                        QPen(Qt.red, 30)
                    )
                    self.point1x,self.point1y = current_pos.x(),current_pos.y()
                    current_angle = self.moving_obj.rotation()
                    d_travelled = math.hypot(current_pos.x() - start_point.x(), current_pos.y() - start_point.y())
                    d_remain = math.hypot(current_pos.x() - end_point.x(), current_pos.y() - end_point.y()) -100
                    if d_remain < 100:
                        self.uic.VelRight.setText(f"Wright: 0 rad/s")
                        self.uic.VelLeft.setText(f"Wleft: 0 rad/s")
                        self.Wleft =0
                        self.Wright = 0
                        move_step(index+1)
                    else:
                        v_desired = self.speed 
                        _,velRight,velLeft =self.PurePursuit.control([current_pos.x(),current_pos.y(),math.radians(current_angle)],v_desired)
                        self.Wright = velRight/self.state.R
                        self.Wleft = velLeft/self.state.R
                        self.uic.VelRight.setText(f"Wright: {self.Wright:.2f} rad/s")
                        self.uic.VelLeft.setText(f"Wleft: {self.Wleft:.2f} rad/s")
                        QTimer.singleShot(10,step)
                
                
                step()
            move_step(1)
                

        def wait_for_resume(next_seg_index):
            # Lưu lại callback chuyển sang đoạn tiếp theo
            self.next_segment_callback = lambda: animate_segment(next_seg_index)
            # Sử dụng QTimer để đợi 5 giây
            self.resume_timer = QTimer()
            self.resume_timer.setSingleShot(True)
            self.resume_timer.timeout.connect(self.next_segment_callback)
            self.resume_timer.start(5000)

        # Bắt đầu animate với đoạn đầu tiên
        animate_segment(0)
        t_send = threading.Thread(target=send_data, daemon=True)
        t_send.start()

        
    
if __name__ =="__main__":
        app = QApplication(sys.argv)
        main_win = MainWindow()
        main_win.show()
        sys.exit(app.exec())