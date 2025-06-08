from PyQt5 import QtWidgets, uic

class InputDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("input_dialog.ui", self)  # nạp giao diện dialog

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui2.ui", self)  # nạp giao diện chính

        # Kết nối QAction trong toolbar
        self.actionInputValues.triggered.connect(self.show_input_dialog)

    def show_input_dialog(self):
        dialog = InputDialog()
        if dialog.exec_():  # hiển thị dialog và đợi người dùng OK
            # Lấy giá trị từ spinbox
            speed = dialog.spinSpeed.value()
            angle = dialog.spinAngle.value()
            print(f"Tốc độ: {speed}, Góc: {angle}")

app = QtWidgets.QApplication([])
window = MainWindow()
window.show()
app.exec_()
