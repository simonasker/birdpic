#!/usr/bin/env python3

import sys
import os
import json
import csv

from PyQt4 import QtGui
from PyQt4 import QtCore
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

DISPLAY_PYPLOT_TOOLBAR = False


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
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)
        self.cursor = Cursor(self.figure.axes[0])
        self.file_index = 0
        self.files = []

        self.mean = [0, 0, 0]
        self.median = [0, 0, 0]
        self.var = [0, 0, 0]
        self.std = [0, 0, 0]
        self.sample_size = 0
        self.point_x = 0
        self.point_y = 0

        self.rgb = START_COLOR

        plt_vbox = QtGui.QVBoxLayout()
        self.canvas = FigureCanvasQTAgg(self.figure)
        plt_vbox.addWidget(self.canvas)
        if DISPLAY_PYPLOT_TOOLBAR:
            self.toolbar = NavigationToolbar2QT(self.canvas, self)
            plt_vbox.addWidget(self.toolbar)

        side_panel_vbox = self.create_side_panel()

        self.load_species_data()
        self.load_field_data()

        self.create_menubar()

        main_hbox = QtGui.QHBoxLayout()
        main_hbox.addLayout(plt_vbox)
        main_hbox.addLayout(side_panel_vbox)

        self.main.setLayout(main_hbox)
        self.connect_mouse_events()

    def load_species_data(self):
        with open('species.json') as f:
            self.species_data = json.load(f)
        genus = list(self.species_data.keys())
        self.genus_edit.addItems(genus)
        self.select_genus(genus[0])

    def load_field_data(self):
        with open('fields.csv') as f:
            lines = f.readlines()
        for l in lines:
            fid, accr, name = l.strip().split(',')
            self.field_edit.addItem(name)

    def connect_mouse_events(self):
        self.figure.canvas.mpl_connect(
            'motion_notify_event', self.cursor.mouse_move)
        self.figure.canvas.mpl_connect(
            'scroll_event', self.cursor.mouse_scroll)

        self.figure.canvas.mpl_connect(
            'button_press_event', self.on_click)
        self.figure.canvas.mpl_connect(
            'scroll_event', self.on_scroll)
        self.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_move)

    def create_menubar(self):
        openFile = QtGui.QAction(QtGui.QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new file')
        openFile.triggered.connect(self.showDialog)

        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        select_species = QtGui.QAction(
            QtGui.QIcon('open.png'), 'Select species', self)
        select_species.setStatusTip('Select species')
        select_species.triggered.connect(self.show_species_dialog)

        menubar = self.menuBar()

        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)
        fileMenu.addAction(exitAction)
        fileMenu.addSeparator()
        fileMenu.addAction(select_species)

    def select_genus(self, event):
        self.genus = event
        self.species_edit.clear()
        species = list(self.species_data[self.genus].keys())
        self.species_edit.addItems(species)
        self.select_species(species[0])

    def select_species(self, event):
        self.species = event
        self.ssp_edit.clear()
        subspecies = self.species_data[self.genus][self.species]
        self.ssp_edit.addItems(subspecies)
        self.ssp = subspecies[0]

    def create_side_panel(self):
        layout = QtGui.QVBoxLayout()

        self.render_area = RenderArea(self)
        layout.addWidget(self.render_area)

        self.file_label = QtGui.QLabel('')
        layout.addWidget(self.file_label)

        self.species_group = QtGui.QGroupBox('Species')
        self.species_group_vbox = QtGui.QVBoxLayout()

        self.genus_hbox = QtGui.QHBoxLayout()
        self.genus_label = QtGui.QLabel('Genus:')
        self.genus_edit = QtGui.QComboBox(self)
        self.genus_edit.activated[str].connect(self.select_genus)
        self.genus_hbox.addWidget(self.genus_label)
        self.genus_hbox.addWidget(self.genus_edit)
        self.species_group_vbox.addLayout(self.genus_hbox)

        self.species_hbox = QtGui.QHBoxLayout()
        self.species_label = QtGui.QLabel('Species:')
        self.species_edit = QtGui.QComboBox(self)
        self.species_edit.activated[str].connect(self.select_species)
        self.species_hbox.addWidget(self.species_label)
        self.species_hbox.addWidget(self.species_edit)
        self.species_group_vbox.addLayout(self.species_hbox)

        self.ssp_hbox = QtGui.QHBoxLayout()
        self.ssp_label = QtGui.QLabel('SSP:')
        self.ssp_edit = QtGui.QComboBox(self)
        self.ssp_hbox.addWidget(self.ssp_label)
        self.ssp_hbox.addWidget(self.ssp_edit)
        self.species_group_vbox.addLayout(self.ssp_hbox)

        self.sp_button = QtGui.QPushButton('Select species', self)
        self.sp_button.clicked.connect(self.show_species_dialog)
        self.species_group_vbox.addWidget(self.sp_button)

        self.species_group.setLayout(self.species_group_vbox)
        layout.addWidget(self.species_group)

        self.field_hbox = QtGui.QHBoxLayout()
        self.field_label = QtGui.QLabel('Field:')
        self.field_edit = QtGui.QComboBox(self)
        self.field_hbox.addWidget(self.field_label)
        self.field_hbox.addWidget(self.field_edit)
        layout.addLayout(self.field_hbox)

        self.display_area = QtGui.QTextEdit(self)
        self.display_area.setReadOnly(True)
        self.display_area.setFixedWidth(200)
        self.display_area.setCurrentFont(QtGui.QFont('Courier New', 8))
        layout.addWidget(self.display_area)

        self.save_button = QtGui.QPushButton('Save', self)
        self.save_button.clicked.connect(self.save)
        layout.addWidget(self.save_button)

        self.prev_next_hbox = QtGui.QHBoxLayout()
        self.prev_button = QtGui.QPushButton('<', self)
        self.prev_button.clicked.connect(self.prev_file)
        self.prev_next_hbox.addWidget(self.prev_button)

        self.filenum_label = QtGui.QLabel('')
        self.prev_next_hbox.addWidget(self.filenum_label)

        self.next_button = QtGui.QPushButton('>', self)
        self.next_button.clicked.connect(self.next_file)
        self.prev_next_hbox.addWidget(self.next_button)
        layout.addLayout(self.prev_next_hbox)

        return layout

    def reset_figure(self):
        self.figure.clear()
        self.img = mpimg.imread(self.files[self.file_index])
        plt.imshow(self.img)
        self.cursor.reset(self.figure.axes[0])
        self.figure.axes[0].get_xaxis().set_visible(False)
        self.figure.axes[0].get_yaxis().set_visible(False)
        self.repaint()

    def show_species_dialog(self):
        dlg = SpeciesDialog(self)
        if dlg.exec_():
            print(dlg.species)

    def showDialog(self):
        self.files = QtGui.QFileDialog.getOpenFileNames(
            self, 'Open file', '/home/simon/git/birdpic', '*.jpg *.png')
        # TODO Do some error checking here
        self.file_index = 0
        self.reset_figure()

    def next_file(self):
        if self.file_index < len(self.files) - 1:
            self.file_index += 1
        self.reset_figure()

    def prev_file(self):
        if self.file_index > 0:
            self.file_index -= 1
        self.reset_figure()

    def get_file_name(self):
        if len(self.files) == 0:
            return 'No file open'
        else:
            return os.path.basename(self.files[self.file_index])

    def save(self):
        print('Saving...')

    def on_move(self, event):
        self.repaint()

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
        self.sample_size = (self.cursor.radius * 2) ** 2
        self.point_x = x
        self.point_y = y
        self.update_text()
        self.repaint()

    def on_scroll(self, event):
        self.repaint()

    def update_text(self):
        result = ""
        display_items = [
            ('genus', self.genus_edit.currentText()),
            ('species', self.species_edit.currentText()),
            ('ssp', self.ssp_edit.currentText()),
            ('field', self.field_edit.currentText()),
            ('mean', str(list(map(int, self.mean)))),
            ('median', str(list(map(int, self.median)))),
            ('std', str(list(map(int, self.std)))),
            ('point', '({}, {})'.format(self.point_x, self.point_y)),
            ('size', self.sample_size),
        ]
        total_w = 25
        for (k, v) in display_items:
            s = '{}:{:>{}}\n'.format(str(k), str(v), total_w - len(str(k)))
            result += s
        self.display_area.setText(result)

    def paintEvent(self, event):
        self.canvas.draw()
        self.update_text()
        self.file_label.setText(self.get_file_name())
        self.filenum_label.setText('{}/{}'.format(
            self.file_index + 1 if len(self.files) > 0 else 0,
            len(self.files),
        ))


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


class SpeciesDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.button = QtGui.QPushButton('this is a button')
        self.button.clicked.connect(self.set_species)

        self.proxy_model = QtGui.QSortFilterProxyModel()
        self.proxy_model.setDynamicSortFilter(True)

        self.create_model()
        self.insert_data()

        self.proxy_model.setSourceModel(self.model)

        self.list_view = QtGui.QTreeView()
        self.list_view.setRootIsDecorated(False)
        self.list_view.setAlternatingRowColors(True)
        self.list_view.setSortingEnabled(True)
        self.list_view.setModel(self.proxy_model)

        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(self.list_view)
        main_layout.addWidget(self.button)
        self.setLayout(main_layout)

        self.setWindowTitle('Select species')
        self.resize(800, 500)

    def create_model(self):
        heading = [
            'Taxon',
            'First name',
            'Last name',
            'Genus',
            'Species',
            'Subspecies',
        ]
        self.model = QtGui.QStandardItemModel(0, len(heading), self)
        for i in range(len(heading)):
            self.model.setHeaderData(i, QtCore.Qt.Horizontal, heading[i])

    def insert_data(self):
        with open('species.csv', newline='') as csvfile:
            species = csv.reader(csvfile, delimiter=',')
            for row in species:
                self.model.insertRow(0)
                for i, c in enumerate(row):
                    if i == 0:
                        c = int(c)
                    self.model.setData(self.model.index(0, i), c)

    def set_species(self):
        self.species = 42
        self.accept()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
