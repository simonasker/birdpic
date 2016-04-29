#!/usr/bin/env python3

import sys
import os

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
        self.reset(ax)

    def reset(self, ax):
        self.ax = ax
        self.x, self.y = 0, 0
        self.radius = START_RADIUS

        self.lx1 = ax.axhline(color=CURSOR_COLOR)
        self.lx2 = ax.axhline(color=CURSOR_COLOR)
        self.ly1 = ax.axvline(color=CURSOR_COLOR)
        self.ly2 = ax.axvline(color=CURSOR_COLOR)

    def mouse_move(self, event):
        if event.inaxes:
            self.x, self.y = int(event.xdata), int(event.ydata)
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
        self.setWindowTitle('Untitled')
        self.statusBar()

        self.figure, self.ax = plt.subplots()
        self.cursor = Cursor(self.figure.axes[0])
        self.file_index = 0
        self.file_names = ['/home/simon/git/birdpic/nelicourvi.jpg']
        # self.img = mpimg.imread(self.file_names[self.file_index])
        # plt.imshow(self.img)
        self.reset_figure()

        self.genus_items = [
            'foo',
            'bar',
            'baz',
        ]
        self.species_items = self.genus_items
        self.ssp_items = self.genus_items
        self.field_items = self.genus_items

        self.mean = [0, 0, 0]
        self.median = [0, 0, 0]
        self.var = [0, 0, 0]
        self.std = [0, 0, 0]

        self.rgb = START_COLOR

        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.figure.canvas.mpl_connect('button_press_event', self.on_click)
        self.figure.canvas.mpl_connect(
            'motion_notify_event', self.cursor.mouse_move)
        self.figure.canvas.mpl_connect(
            'scroll_event', self.cursor.mouse_scroll)
        self.figure.canvas.mpl_connect('scroll_event', self.on_scroll)

        plt_vbox = QtGui.QVBoxLayout()

        plt_vbox.addWidget(self.canvas)
        plt_vbox.addWidget(self.toolbar)

        side_panel_vbox = self.create_side_panel()

        main_hbox = QtGui.QHBoxLayout()
        main_hbox.addLayout(plt_vbox)
        main_hbox.addLayout(side_panel_vbox)

        self.main.setLayout(main_hbox)

    def create_menubar(self):
        openFile = QtGui.QAction(QtGui.QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new file')
        openFile.triggered.connect(self.showDialog)

        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        menubar = self.menuBar()

        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)
        fileMenu.addAction(exitAction)

    def create_side_panel(self):
        layout = QtGui.QVBoxLayout()

        self.render_area = RenderArea(self)
        layout.addWidget(self.render_area)

        self.genus_hbox = QtGui.QHBoxLayout()
        self.genus_label = QtGui.QLabel('Genus:')
        self.genus_edit = QtGui.QComboBox(self)
        self.genus_edit.addItems(self.genus_items)
        self.genus_hbox.addWidget(self.genus_label)
        self.genus_hbox.addWidget(self.genus_edit)
        layout.addLayout(self.genus_hbox)
        self.species_hbox = QtGui.QHBoxLayout()
        self.species_label = QtGui.QLabel('Species:')
        self.species_edit = QtGui.QComboBox(self)
        self.species_edit.addItems(self.species_items)
        self.species_hbox.addWidget(self.species_label)
        self.species_hbox.addWidget(self.species_edit)
        layout.addLayout(self.species_hbox)
        self.ssp_hbox = QtGui.QHBoxLayout()
        self.ssp_label = QtGui.QLabel('SSP:')
        self.ssp_edit = QtGui.QComboBox(self)
        self.ssp_edit.addItems(self.ssp_items)
        self.ssp_hbox.addWidget(self.ssp_label)
        self.ssp_hbox.addWidget(self.ssp_edit)
        layout.addLayout(self.ssp_hbox)
        self.field_hbox = QtGui.QHBoxLayout()
        self.field_label = QtGui.QLabel('Field:')
        self.field_edit = QtGui.QComboBox(self)
        self.field_edit.addItems(self.field_items)
        self.field_hbox.addWidget(self.field_label)
        self.field_hbox.addWidget(self.field_edit)
        layout.addLayout(self.field_hbox)

        self.display_area = QtGui.QTextEdit(self)
        self.display_area.setReadOnly(True)
        self.display_area.setFixedWidth(200)
        self.display_area.setFontFamily('monospace')
        layout.addWidget(self.display_area)

        self.save_button = QtGui.QPushButton('Save', self)
        self.save_button.clicked.connect(self.save)
        layout.addWidget(self.save_button)

        self.prev_next_hbox = QtGui.QHBoxLayout()
        self.prev_button = QtGui.QPushButton('<', self)
        self.prev_button.clicked.connect(self.prev_file)
        self.prev_next_hbox.addWidget(self.prev_button)
        self.next_button = QtGui.QPushButton('>', self)
        self.next_button.clicked.connect(self.next_file)
        self.prev_next_hbox.addWidget(self.next_button)
        layout.addLayout(self.prev_next_hbox)

        return layout

    def reset_figure(self):
        self.figure.clear()
        self.img = mpimg.imread(self.file_names[self.file_index])
        plt.imshow(self.img)
        self.cursor.reset(self.figure.axes[0])
        self.repaint()

    def showDialog(self):
        self.file_names = QtGui.QFileDialog.getOpenFileNames(
            self, 'Open file', '/home/simon/git/birdpic', '*.jpg *.png')
        # TODO Do some error checking here
        self.file_index = 0
        self.reset_figure()

    def next_file(self):
        if self.file_index < len(self.file_names) - 1:
            self.file_index += 1
        self.reset_figure()

    def prev_file(self):
        if self.file_index > 0:
            self.file_index -= 1
        self.reset_figure()

    def save(self):
        print('Saving...')

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
            'genus: {:>15}\n'
            'species: {:>15}\n'
            'ssp: {:>15}\n'
            'field: {:>15}\n'
            'mean: {:>20}\n'
            'median: {:>18}\n'
            'var: {:>20}\n'
            'std: {:>20}\n'
            'file: {}/{}\n'
            'filename: {}\n'
            'cursor: ({}, {})\n'
            'sample size: {}\n'

        ).format(
            self.genus_edit.currentText(),
            self.species_edit.currentText(),
            self.ssp_edit.currentText(),
            self.field_edit.currentText(),
            str(list(map(int, self.mean))),
            str(list(map(int, self.median))),
            str(list(map(int, self.var))),
            str(list(map(int, self.std))),
            self.file_index + 1,
            len(self.file_names),
            os.path.basename(self.file_names[self.file_index]),
            self.cursor.x,
            self.cursor.y,
            (self.cursor.radius * 2) ** 2,
        ))

    def on_scroll(self, event):
        self.repaint()

    def paintEvent(self, event):
        self.canvas.draw()
        self.update_text()


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
