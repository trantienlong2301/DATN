import sys
import math, socket, json, time, struct
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from Mapping import MapProcessing
import ezdxf
from gui1 import Ui_MainWindow
from PyQt5.QtGui import QPen, QPolygonF, QFont
from PyQt5.QtCore import Qt, QPointF, QPropertyAnimation, QSequentialAnimationGroup, QPointF, QEasingCurve, QTimer
from AddMovingObject import MovingCompositeObject

def recvall(sock, n):
    """Nhận đủ n byte từ socket."""
    data = b""
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None  # Nếu kết nối bị đóng
        data += packet
    return data

class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_points = []
        self.pointsSelectedCallback = None  
    
    def eraseSelected_points (self):
        self.selected_points = []
    def mousePressEvent(self, event):
        
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())

            if self.pointsSelectedCallback:
                print(f"Chọn điểm: ({scene_pos.x()}, {scene_pos.y()})")
                self.selected_points.append([scene_pos.x(), scene_pos.y()])
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
        self.uic.animated.clicked.connect(self.animate_moving_object1)
        self.uic.continue_2.clicked.connect(self.resume_next_segment)
        # tạo graphics trên widget
        layout = QtWidgets.QVBoxLayout(self.uic.widget)
        self.graphicsView = CustomGraphicsView(self.uic.widget)
        layout.addWidget(self.graphicsView)
        self.scene = QtWidgets.QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        self.is_goal_active = False
        self.moving_obj_unactive = True
        self.is_setup_active = False  # Track the state of the SetUp button
        self.selected_goals = None
        self.current_circle = None
        self.path_points = []
        self.path_lines = []
        self.select_count = 0

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
        proportion = min(float((self.uic.widget.width()-50)/(self.Mapprocessing.max_x - self.Mapprocessing.min_x)), 
                         float((self.uic.widget.height()-50)/(self.Mapprocessing.max_y - self.Mapprocessing.min_y)))
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
            self.graphicsView.eraseSelected_points()
            self.uic.Goal.setStyleSheet("background-color: blue;")
            self.graphicsView.pointsSelectedCallback = self.processSelectedPoints
        else:
            self.uic.Goal.setStyleSheet("")
            self.graphicsView.pointsSelectedCallback = None 

    def processSelectedPoints(self, points_list):
        # Xóa tất cả các hình tròn cũ
        for circle in getattr(self, "current_circles", []):
            self.scene.removeItem(circle)
        
        # Lưu danh sách điểm được chọn
        self.selected_goals = points_list  
        
        # Danh sách mới để lưu các hình tròn
        self.current_circles = []
        
        # Vẽ hình tròn tại từng điểm trong danh sách
        for point in points_list:
            circle = self.scene.addEllipse(
                point[0] - 250,  # X tọa độ góc trên bên trái
                point[1] - 250,  # Y tọa độ góc trên bên trái
                500, 500,  # Chiều rộng và chiều cao (hình tròn có đường kính 500)
                QPen(Qt.green, 20)  # Màu viền xanh lá và độ dày 20px
            )
            self.current_circles.append(circle)  # Lưu lại để xóa sau này
        
            
    def find_path(self):
        if self.selected_goals is None:
            print("chưa chọn điểm đích")
        else:
            print(f"Selected goals: {self.selected_goals}")
        
            self.is_goal_active = False
            self.uic.Goal.setStyleSheet("") 
            self.is_setup_active = False
            self.uic.SetUp.setStyleSheet("")
            self.graphicsView.pointsSelectedCallback = None 
            self.graphicsView.eraseSelected_points()
            if hasattr(self, 'moving_obj') and self.selected_goals:
                start = (self.moving_obj.pos().x() + self.moving_obj.boundingRect().width() / 2,
                        self.moving_obj.pos().y() + self.moving_obj.boundingRect().height() / 2)
                self.path_points.append(self.Mapprocessing.dijkstra_shortest_path(start, self.selected_goals[0]))
                for i in range(len(self.selected_goals) -1):
                    inter_path = self.Mapprocessing.dijkstra_shortest_path(self.selected_goals[i],self.selected_goals[i+1])
                    self.path_points.append(inter_path)
                print(f"Path: {self.path_points}")
                self.display_path(self.path_points)

    def display_path(self, path_points):  
         # Xóa đường cũ trước khi vẽ đường mới
        for line in getattr(self, 'path_lines', []):
            self.scene.removeItem(line)
        self.path_lines = []  # Xóa danh sách cũ 
        pen_path = QPen(Qt.darkGreen, 50)
        for i in range(len(path_points)):
            path = path_points[i]
 
            for j in range(len(path)-1):
                
                x1, y1 = path[j]
                x2, y2 = path[j + 1]
                line =  self.scene.addLine(x1, y1, x2, y2, pen_path)
                self.path_lines.append(line)

    def resume_next_segment(self):
        if self.resume_timer is not None:
            self.resume_timer.stop()  # Dừng timer nếu đang chạy
            self.resume_timer = None
        if self.next_segment_callback:
            self.next_segment_callback()
            self.next_segment_callback = None

    def animate_moving_object(self):
            segments = self.path_points
            if not hasattr(self, 'moving_obj') or len(segments) == 0:#Kiểm tra nếu không có moving_obj hoặc segments trống thì thoát hàm
                return
            # Tính offset để đảm bảo moving_obj được căn giữa theo boundingRect
            center_offset = QPointF(self.moving_obj.boundingRect().width() / 2,
                                    self.moving_obj.boundingRect().height() / 2)
            # Các biến dùng để điều khiển việc chuyển sang đoạn tiếp theo
            self.resume_timer = None
            self.next_segment_callback = None
            def animate_segment(seg_index):
                if seg_index >= len(segments):
                    return  # Đã hết các đoạn, dừng animation

                segment = segments[seg_index]
                # Nếu đoạn không đủ điểm để di chuyển, chuyển sang đoạn kế
                if len(segment) < 2:
                    wait_for_resume(seg_index + 1)
                    return
            # Định nghĩa hàm di chuyển từng bước
                def move_step(index):
                    if index >= len(segment):
                         # Khi hoàn thành đoạn, tạm dừng 5s hoặc chờ nhấn nút để chuyển sang đoạn tiếp theo
                        wait_for_resume(seg_index + 1)
                        return  # Kết thúc hàm

                    start_point = QPointF(segment[index - 1][0], segment[index - 1][1]) - center_offset
                    end_point = QPointF(segment[index][0], segment[index][1]) - center_offset
                    d_total = math.hypot(segment[index][0] - segment[index - 1][0], segment[index][1] - segment[index - 1][1])
                    target_angle = math.degrees(math.atan2(segment[index][1] - segment[index - 1][1],segment[index][0] - segment[index - 1][0]))
                    a = 500
                    alpha = 25
                    segment_start = start_point
                    initial_angle = self.moving_obj.rotation()

                    def step_angle():
                        current_angle = self.moving_obj.rotation()
                        angle_diff = target_angle - current_angle
                        # Xác định hướng xoay: 1 nếu tăng, -1 nếu giảm
                        sign = 1 if angle_diff > 0 else -1
                        d_total_angle = abs(target_angle - initial_angle)
                        d_travelled_angle = abs(current_angle - initial_angle)
                        d_remaining_angle = abs(target_angle - current_angle)

                        # Nếu góc cần xoay quá nhỏ, hoàn thành xoay và chuyển sang di chuyển
                        if d_remaining_angle < 1:
                            self.moving_obj.setRotation(target_angle)
                            step()  # bắt đầu chuyển động
                            return

                        # Tính vận tốc góc mong muốn theo ba pha: gia tốc, tốc độ không đổi, giảm tốc
                        v_desired_angle = min(math.sqrt(2 * alpha * d_travelled_angle) if d_travelled_angle > 0 else 1,
                                            50,
                                            math.sqrt(2 * alpha * d_remaining_angle))
                        angular_step = v_desired_angle * 0.1

                        if d_remaining_angle <= angular_step:
                            self.moving_obj.setRotation(target_angle)
                            step()  # chuyển sang bước di chuyển khi đã xoay đủ
                        else:
                            new_angle = current_angle + sign * angular_step
                            self.moving_obj.setRotation(new_angle)
                            QTimer.singleShot(100, step_angle)

                    def step():
                        current_pos = self.moving_obj.pos()
                        d_travelled = math.hypot(current_pos.x() - segment_start.x(), current_pos.y() - segment_start.y())
                        d_remain = d_total - d_travelled
                        v_desired = min(math.sqrt(2 * a * d_travelled) if d_travelled > 0 else 50,
                                    1000,
                                    math.sqrt(2 * a * d_remain) if d_remain > 0 else 50)
                        direction = (end_point - current_pos)
                        distance = math.hypot(direction.x(), direction.y())
                        if distance != 0:
                            unit_direction = QPointF(direction.x() / distance, direction.y() / distance)
                        else:
                            unit_direction = QPointF(0, 0)
                        move_distance = v_desired * 0.1
                        if d_remain <= move_distance:
                            self.moving_obj.setPos(end_point)
                            move_step(index + 1)
                        else:
                            new_pos = current_pos + QPointF(unit_direction.x() * move_distance,
                                                            unit_direction.y() * move_distance)
                            self.moving_obj.setPos(new_pos)
                            QTimer.singleShot(100, step)
                    step_angle()  # Bắt đầu animation

                move_step(1)  # Bắt đầu từ điểm thứ hai
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

    def animate_moving_object1(self):
        segments = self.path_points
        if not hasattr(self, 'moving_obj') or len(segments) == 0:#Kiểm tra nếu không có moving_obj hoặc segments trống thì thoát hàm
            return

        HOST = "192.168.1.38"  # Địa chỉ IP của ESP32
        PORT = 80              # Cổng mà ESP32 đang lắng nghe
        # Tạo socket TCP
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        print("Đã kết nối đến ESP32")
        
        center_offset = QPointF(self.moving_obj.boundingRect().width() / 2,
                                self.moving_obj.boundingRect().height() / 2)
        # Các biến dùng để điều khiển việc chuyển sang đoạn tiếp theo
        self.resume_timer = None
        self.next_segment_callback = None

        # Định nghĩa hàm di chuyển từng bước
        def animate_segment(seg_index):
            if (abs(self.moving_obj.pos().x() + center_offset.x() - self.path_points[-1][-1][0]) < 10) and (abs(self.moving_obj.pos().y() + center_offset.y() - self.path_points[-1][-1][1]) < 10) :
                client.close()
                print(" da dong ket noi.")
            if seg_index >= len(segments): 
                return  # Đã hết các đoạn, dừng animation

            segment = segments[seg_index]
            # Nếu đoạn không đủ điểm để di chuyển, chuyển sang đoạn kế
            if len(segment) < 2:
                wait_for_resume(seg_index + 1)
                return
            def move_step(index):
                if index >= len(segment):
                    # Khi hoàn thành đoạn, tạm dừng 5s hoặc chờ nhấn nút để chuyển sang đoạn tiếp theo
                    wait_for_resume(seg_index + 1)
                    return  # Kết thúc animation

                start_point = QPointF(segment[index - 1][0], segment[index - 1][1]) - center_offset
                end_point = QPointF(segment[index][0], segment[index][1]) - center_offset
                d_total = math.hypot(segment[index][0] - segment[index - 1][0], segment[index][1] - segment[index - 1][1])
                target_angle = math.degrees(math.atan2(segment[index][1] - segment[index - 1][1],segment[index][0] - segment[index - 1][0]))
                print("start: ",start_point)
                print("end: ",end_point)
                a = 500
                alpha = 25
                segment_start = start_point
                initial_angle = self.moving_obj.rotation()

                def step_angle():
                    current_angle = self.moving_obj.rotation()
                    angle_diff = target_angle - current_angle
                    # Xác định hướng xoay: 1 nếu tăng, -1 nếu giảm
                    sign = 1 if angle_diff > 0 else -1
                    d_total_angle = abs(target_angle - initial_angle)
                    d_travelled_angle = abs(current_angle - initial_angle)
                    d_remaining_angle = abs(target_angle - current_angle)

                    # Nếu góc cần xoay quá nhỏ, hoàn thành xoay và chuyển sang di chuyển
                    if d_remaining_angle < 1:
                        self.moving_obj.setRotation(target_angle)
                        step()  # bắt đầu chuyển động
                        return

                    # Tính vận tốc góc mong muốn theo ba pha: gia tốc, tốc độ không đổi, giảm tốc
                    v_desired_angle = min(math.sqrt(2 * alpha * d_travelled_angle) if d_travelled_angle > 0 else 1,
                                        50,
                                        math.sqrt(2 * alpha * d_remaining_angle))
                    angular_step = v_desired_angle * 0.1

                    if d_remaining_angle <= angular_step:
                        self.moving_obj.setRotation(target_angle)
                        step()  # chuyển sang bước di chuyển khi đã xoay đủ
                    else:
                        new_angle = current_angle + sign * angular_step
                        self.moving_obj.setRotation(new_angle)
                        QTimer.singleShot(100, step_angle)

                def step():
                    current_pos = self.moving_obj.pos()
                    d_travelled = math.hypot(current_pos.x() - segment_start.x(), current_pos.y() - segment_start.y())
                    d_remain = d_total - d_travelled
                    v_desired = min(math.sqrt(2 * a * d_travelled) if d_travelled > 0 else 50,
                                1000,
                                math.sqrt(2 * a * d_remain) if d_remain > 0 else 50)
                    direction = (end_point - current_pos)
                    distance = math.hypot(direction.x(), direction.y())

                    if distance != 0:
                        v_x = v_desired * direction.x()/distance
                        v_y = v_desired * direction.y()/distance
                    else:
                        v_x = 0
                        v_y = 0

                    control_data = {
                    "v_x": v_x,
                    "v_y": v_y,
                    "start": [start_point.x(),start_point.y()],
                    "goal":  [end_point.x(),end_point.y()]
                    }
                    json_data = json.dumps(control_data)
                    client.sendall((json_data + "\n").encode('utf-8'))
                    print(" da gui:", json_data)
                    try:
                        client.settimeout(5.0)
                        header = recvall(client, 4)
                        if header is None:
                            print("Kết nối bị đóng khi nhận header.")

                        # Giải mã header theo network byte order ("!I" định dạng số nguyên 4 byte)
                        msg_length = struct.unpack("!I", header)[0]

                        # Nhận nội dung JSON theo độ dài vừa có được
                        json_payload = recvall(client, msg_length)
                        if json_payload is None:
                            print("Kết nối bị đóng khi nhận payload.")

                        response_data = json.loads(json_payload.decode("utf-8"))
                        print("Vị trí hiện tại của robot:")
                        print("  x =", response_data["x"])
                        print("  y =", response_data["y"])
                        self.moving_obj.setPos(QPointF(response_data["x"], response_data["y"]))
                        
                    except socket.timeout:
                        print(" Khong nhan phan hoi.")

                    move_distance = v_desired * 0.2
                    if d_remain <= move_distance:
                        self.moving_obj.setPos(end_point)
                        move_step(index + 1)
                    else:
                        QTimer.singleShot(200, step)
                step_angle()  # Bắt đầu animation

            move_step(1)  # Bắt đầu từ điểm thứ hai
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

        
    
if __name__ =="__main__":
        app = QApplication(sys.argv)
        main_win = MainWindow()
        main_win.show()
        sys.exit(app.exec())