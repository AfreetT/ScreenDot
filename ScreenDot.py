import sys
import os
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QCheckBox, QFileDialog

class Overlay(QWidget):
    EnterSignal = pyqtSignal()

    def __init__(self, screen_width, screen_height):
        super().__init__()

        # Set the window attributes for a transparent overlay
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.dot_color = QColor(255, 0, 0)
        self.dot_size = 50 #Size of crosshair, in pixels

        #Read size of the screen
        self.screen_width = screen_width
        self.screen_height = screen_height

        try:
            self.LoadPosition()
        except:
            self.pos_w = 0.5
            self.pos_h = 0.5

        #Calculate the position of down-left egde of the window
        self.pixel_pos_w = int(self.pos_w * self.screen_width - 0.5 * self.dot_size) 
        self.pixel_pos_h = int(self.pos_h * self.screen_height - 0.5 * self.dot_size)
        
        #Set the geometry
        self.setGeometry(self.pixel_pos_w, self.pixel_pos_h, self.dot_size, self.dot_size )
        self.dot_position = (self.width() // 2, self.height() // 2)

        self.move_dot_on_click = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw a transparent background
        if(self.move_dot_on_click):
            painter.fillRect(self.rect(), QColor(0, 0, 0, 127))

        half_size = self.dot_size // 2

        # Draw the dot in the middle of the screen
        painter.setPen(QPen(self.dot_color, 2))
        painter.drawEllipse(self.dot_position[0] - half_size,
                             self.dot_position[1] - half_size,
                             self.dot_size, self.dot_size)

        painter.drawLine(self.dot_position[0] - half_size, self.dot_position[1],
                         self.dot_position[0] + half_size, self.dot_position[1])

        painter.drawLine(self.dot_position[0], self.dot_position[1] - half_size,
                         self.dot_position[0], self.dot_position[1] + half_size)

    def WindowForNewCrosshair(self):
        self.setGeometry(0, 0, self.screen_width, self.screen_height )
        self.dot_position = ( int(self.pos_w * self.screen_width), int(self.pos_h * self.screen_height) )

    def RecalculateGeometry(self, screen_width = None, screen_height = None):
        if(screen_width):
            self.screen_width = screen_width
        if(screen_height):
            self.screen_height = screen_height

        self.pixel_pos_w = int(self.pos_w * self.screen_width - 0.5 * self.dot_size) 
        self.pixel_pos_h = int(self.pos_h * self.screen_height - 0.5 * self.dot_size)
        self.setGeometry(self.pixel_pos_w, self.pixel_pos_h, self.dot_size, self.dot_size )
        self.dot_position = (self.width() // 2, self.height() // 2)

    def mousePressEvent(self, event):
        if self.move_dot_on_click:
            # Move the dot to the clicked position
            self.dot_position = (event.pos().x(), event.pos().y())
            
            self.pos_w = self.dot_position[0] / self.screen_width
            self.pos_h = self.dot_position[1] / self.screen_height
            self.pixel_pos_w = int(self.dot_position[0] - 0.5 * self.dot_size)
            self.pixel_pos_h = int(self.dot_position[1] - 0.5 * self.dot_size)

            self.update()

    def keyPressEvent(self, qKeyEvent):
        if(not self.move_dot_on_click): 
            return

        if(qKeyEvent.key() == Qt.Key_Escape):
            self.move_dot_on_click = False
            self.LoadPosition()
            self.RecalculateGeometry()
            self.EnterSignal.emit()

        if(qKeyEvent.key() == Qt.Key_Return): 
            self.move_dot_on_click = False
            self.setGeometry(self.pixel_pos_w, self.pixel_pos_h, self.dot_size, self.dot_size )
            self.dot_position = (self.width() // 2, self.height() // 2)
            self.SavePosition()
            self.EnterSignal.emit()

        

    def SavePosition(self, f_name = None):
        if(not f_name):
            f_name = "./LastPosition.txt"
        f = open(f_name, "w")
        f.write(f"{self.pos_w}\t{self.pos_h}")
        f.close()

    def LoadPosition(self, f_name = None):
        if(not f_name):
            f_name = "./LastPosition.txt"
        f = open(f_name, "r")
        pos = f.read()
        f.close()

        pos = pos.split('\t')
        self.pos_w = float(pos[0])
        self.pos_h = float(pos[1])

class MainWindow(QWidget):
    def __init__(self, screen_width = 1920, screen_height = 1080):
        super().__init__()

        self.overlay = Overlay(screen_width, screen_height)
        self.overlay.show()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Overlay Menu')
        self.setGeometry(100, 100, 200, 100)

        layout = QVBoxLayout()

        toggle_button = QPushButton('Toggle Overlay', self)
        toggle_button.clicked.connect(self.toggle_overlay)
        layout.addWidget(toggle_button)

        self.move_dot_checkbox = QPushButton('Move Crosshair on Click', self)
        self.move_dot_checkbox.clicked.connect(self.toggle_move_dot)
        layout.addWidget(self.move_dot_checkbox)

        load_button = QPushButton('Load position', self)
        load_button.clicked.connect(self.LoadPosition)
        layout.addWidget(load_button)

        save_button = QPushButton('Save position', self)
        save_button.clicked.connect(self.SavePosition)
        layout.addWidget(save_button)

        self.setLayout(layout)

        self.overlay.EnterSignal.connect(self.UpdateText)

    def toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()

    def toggle_move_dot(self, state):
        if(not self.overlay.move_dot_on_click):
            self.overlay.move_dot_on_click = True
            self.move_dot_checkbox.setText("Press Enter key to stop the edit")
            self.overlay.WindowForNewCrosshair()

    def UpdateText(self):
        self.move_dot_checkbox.setText("Move Crosshair on Click")

    def closeEvent(self, event):
        self.overlay.close()
        event.accept()

    def LoadPosition(self):
        f_name = QFileDialog.getOpenFileName(self, 'Load position', 
                            os.getcwd(),"TXT Files (*.txt)")[0]

        if(f_name):
            self.overlay.LoadPosition(f_name = f_name)
            self.overlay.RecalculateGeometry()

    def SavePosition(self):
        f_name = QFileDialog.getSaveFileName(self, 'Load position', 
                            os.getcwd(),"TXT Files (*.txt)")[0]

        if(f_name):
            if(f_name[:-4] != ".txt"):
                f_name += ".txt"
            self.overlay.SavePosition(f_name = f_name)


if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setApplicationName("Crosshair Overlay")
    screen = app.primaryScreen().size()
    win = MainWindow(screen_width = screen.width(), screen_height = screen.height() )
    win.show()

    sys.exit(app.exec_())