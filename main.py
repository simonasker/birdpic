#!/usr/bin/env python3

import sys

from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
import matplotlib.pyplot as plt

from skimage import io, segmentation, color

COMPACTNESS = 35
N_SEGMENTS = 200
THRESHOLD = 30


class Example(QtGui.QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.main = QtGui.QWidget()
        self.setCentralWidget(self.main)

        self.figure = plt.figure()
        self.img = io.imread('nelicourvi.jpg')
        labels1 = segmentation.slic(
            self.img, compactness=COMPACTNESS, n_segments=N_SEGMENTS)
        out1 = color.label2rgb(labels1, self.img, kind='overlay')
        plt.imshow(out1)

        self.rgb = [255, 255, 255]

        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.render_area = RenderArea(self)

        self.figure.canvas.mpl_connect('button_press_event', self.on_click)
        self.figure.canvas.mpl_connect('motion_notify_event', self.on_move)

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
        self.repaint()

    def on_move(self, event):
        pass


class RenderArea(QtGui.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setMinimumWidth(100)

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        color = QtGui.QColor(*self.parent.rgb)
        qp.fillRect(0, 0, 100, 100, color)
        qp.end()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
