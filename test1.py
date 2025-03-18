import math
from PyQt5.QtCore import QPropertyAnimation, QSequentialAnimationGroup, QPointF, QEasingCurve

def animate_moving_object(self, path):
    """
    Hàm này nhận vào danh sách path chứa các điểm (x, y) (đại diện cho tâm đối tượng)
    và tạo animation di chuyển moving_obj dọc theo các điểm đó.
    """
    # Kiểm tra xem moving_obj đã tồn tại hay chưa
    if not hasattr(self, 'moving_obj'):
        return

    # Tạo một nhóm animation để nối các animation nhỏ lại
    animation_group = QSequentialAnimationGroup()

    # Tính offset: vị trí của đối tượng trong scene được xác định từ góc trên bên trái.
    # Trong khi đó, các điểm đường đi thường đại diện cho tâm của đối tượng.
    center_offset = QPointF(self.moving_obj.boundingRect().width() / 2,
                            self.moving_obj.boundingRect().height() / 2)

    # Lấy vị trí tâm hiện tại của moving_obj
    current_center = self.moving_obj.pos() + center_offset

    # Nếu điểm đầu tiên của đường đi không trùng với vị trí hiện tại, thêm vào đầu danh sách
    if len(path) == 0:
        return
    if current_center != QPointF(path[0][0], path[0][1]):
        path = [(current_center.x(), current_center.y())] + path

    # Duyệt qua từng đoạn của đường đi
    for i in range(1, len(path)):
        # Tính toán giá trị bắt đầu và kết thúc của animation:
        # Lưu ý: chúng ta trừ đi center_offset để setPos cho đúng (vì pos() là góc trên bên trái)
        start_point = QPointF(path[i-1][0], path[i-1][1]) - center_offset
        end_point = QPointF(path[i][0], path[i][1]) - center_offset

        animation = QPropertyAnimation(self.moving_obj, b"pos")
        animation.setStartValue(start_point)
        animation.setEndValue(end_point)

        # Tính khoảng cách giữa 2 điểm để xác định thời gian animation (ví dụ: 5ms cho mỗi đơn vị khoảng cách)
        distance = math.hypot(path[i][0] - path[i-1][0], path[i][1] - path[i-1][1])
        duration = int(distance * 5)  # Bạn có thể điều chỉnh hệ số này tùy ý
        animation.setDuration(duration)

        # (Tùy chọn) Sử dụng easing curve cho chuyển động mượt mà
        animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Thêm animation vào nhóm
        animation_group.addAnimation(animation)

    # Để tránh bị garbage collected, bạn có thể lưu animation_group vào thuộc tính của MainWindow
    self.current_animation = animation_group

    # Bắt đầu animation
    animation_group.start()

