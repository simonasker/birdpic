#!/usr/bin/env python3

import sys

from PyQt4 import QtGui
# from PyQt4 import QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np

# import skimage.draw

COMPACTNESS = 35
N_SEGMENTS = 200
THRESHOLD = 30

CURSOR_COLOR = 'black'
START_COLOR = [255, 255, 255]
START_RADIUS = 10
MIN_RADIUS = 0
MAX_RADIUS = 50
RADIUS_SCROLL_DELTA = 5


class Cursor(object):
    def __init__(self, ax):
        self.ax = ax
        self.x, self.y = 0, 0
        self.radius = START_RADIUS

        self.lx1 = ax.axhline(color=CURSOR_COLOR)
        self.lx2 = ax.axhline(color=CURSOR_COLOR)
        self.ly1 = ax.axvline(color=CURSOR_COLOR)
        self.ly2 = ax.axvline(color=CURSOR_COLOR)

    def mouse_move(self, event):
        if event.inaxes:
            self.x, self.y = event.xdata, event.ydata
            self.update()

    def mouse_scroll(self, event):
        if event.button == 'up' and self.radius < MAX_RADIUS:
            self.radius += RADIUS_SCROLL_DELTA
        if event.button == 'down' and self.radius > MIN_RADIUS:
            self.radius -= RADIUS_SCROLL_DELTA
        self.update()

    def update(self):
        self.lx1.set_ydata(self.y - self.radius)
        self.lx2.set_ydata(self.y + self.radius)
        self.ly1.set_xdata(self.x - self.radius)
        self.ly2.set_xdata(self.x + self.radius)


class Example(QtGui.QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.main = QtGui.QWidget()
        self.setCentralWidget(self.main)

        self.figure, self.ax = plt.subplots()
        self.img = mpimg.imread('nelicourvi.jpg')
        plt.imshow(self.img)

        self.rgb = START_COLOR

        self.display_text = 'This is shit\nHello'
        self.species_edit = QtGui.QLineEdit(self)
        self.field_edit = QtGui.QLineEdit(self)

        self.display_area = QtGui.QTextEdit(self)
        self.display_area.setReadOnly(True)
        self.display_area.setTextBackgroundColor(QtGui.QColor(200, 200, 200))

        self.display_area.setText('hello')
        self.display_area.setFixedWidth(200)

        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.render_area = RenderArea(self)

        self.cursor = Cursor(self.ax)

        self.figure.canvas.mpl_connect('button_press_event', self.on_click)
        self.figure.canvas.mpl_connect(
            'motion_notify_event', self.cursor.mouse_move)
        self.figure.canvas.mpl_connect(
            'scroll_event', self.cursor.mouse_scroll)
        self.figure.canvas.mpl_connect('scroll_event', self.on_scroll)

        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        self.setWindowTitle('Untitled')

        plt_vbox = QtGui.QVBoxLayout()
        plt_vbox.addWidget(self.canvas)
        plt_vbox.addWidget(self.toolbar)

        side_panel_vbox = QtGui.QVBoxLayout()
        side_panel_vbox.addWidget(self.render_area)
        side_panel_vbox.addWidget(self.species_edit)
        side_panel_vbox.addWidget(self.field_edit)
        side_panel_vbox.addWidget(self.display_area)

        main_hbox = QtGui.QHBoxLayout()
        main_hbox.addLayout(plt_vbox)
        main_hbox.addLayout(side_panel_vbox)

        self.main.setLayout(main_hbox)

    def on_click(self, event):
        x, y = int(event.xdata), int(event.ydata)
        radius = self.cursor.radius
        if radius <= 0:
            selected = self.img[y:y+1, x:x+1]
        else:
            x1, x2 = x - radius + 2, x + radius + 2
            y1, y2 = y - radius + 2, y + radius + 2
            selected = self.img[y1:y2, x1:x2]
        a, b, _ = selected.shape
        rgbs = selected.reshape((a * b, 3))
        self.mean = np.mean(rgbs, axis=0)
        self.median = np.median(rgbs, axis=0)
        self.var = np.var(rgbs, axis=0)
        self.std = np.std(rgbs, axis=0)
        self.rgb = list(map(int, self.mean))
        self.update_text()
        self.repaint()

    def update_text(self):
        self.display_area.setText((
            'mean: {}\n'
            'median: {}\n'
            'var: {}\n'
            'std: {}\n'
        ).format(
            list(map(int, self.mean)),
            list(map(int, self.median)),
            list(map(int, self.var)),
            list(map(int, self.std)),
        ))

    def on_scroll(self, event):
        self.repaint()

    def paintEvent(self, event):
        self.canvas.draw()


class RenderArea(QtGui.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedSize(200, 50)

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        col = QtGui.QColor(*self.parent.rgb)
        qp.fillRect(0, 0, self.width(), self.height(), col)
        qp.end()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
