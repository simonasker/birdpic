#!/usr/bin/env python3

import sys

from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import skimage.draw

COMPACTNESS = 35
N_SEGMENTS = 200
THRESHOLD = 30

CURSOR_COLOR = 'black'
START_COLOR = [255, 255, 255]
START_RADIUS = 5


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
        # TODO Add a min and a max size
        delta = 5
        if event.button == 'up':
            self.radius += delta
        if event.button == 'down':
            self.radius -= delta
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

        hbox = QtGui.QHBoxLayout()
        vbox = QtGui.QVBoxLayout()

        vbox.addWidget(self.canvas)
        vbox.addWidget(self.toolbar)

        hbox.addLayout(vbox)
        hbox.addWidget(self.render_area)
        self.main.setLayout(hbox)

    def on_click(self, event):
        self.rgb = list(self.img[int(event.ydata), int(event.xdata)])
        rr, cc = skimage.draw.circle(event.xdata, event.ydata, 3)
        print(self.img[rr, cc])
        self.repaint()

    def on_scroll(self, event):
        self.repaint()

    def paintEvent(self, event):
        self.canvas.draw()


class RenderArea(QtGui.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setMinimumWidth(100)

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        col = QtGui.QColor(*self.parent.rgb)
        qp.fillRect(0, 0, 100, 100, col)
        qp.end()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
