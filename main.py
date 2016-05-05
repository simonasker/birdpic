#!/usr/bin/env python3

import sys
import os
import csv
import collections

from PyQt4 import QtGui
from PyQt4 import QtCore

# from PySide import QtGui
# from PySide import QtCore
# import matplotlib
# matplotlib.use('Qt4Agg')
# matplotlib.rcParams['backend.qt4'] = 'PySide'

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np

# import skimage.color

SPECIES_FILE = 'data/ploceide_taxon.csv'
PLUMREG_FILE = 'data/plumreg.csv'


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


class Sample(object):
    def __init__(self):
        self.data = collections.OrderedDict()
        self.data['genus'] = ''
        self.data['species'] = ''
        self.data['subspecies'] = ''
        self.data['plumreg'] = ''
        self.data['sex'] = ''
        self.data['age'] = ''
        self.data['imgfile'] = ''
        self.data['imgsrc'] = ''
        self.data['imgtype'] = ''
        self.data['x'] = 0
        self.data['y'] = 0
        self.data['size'] = 0
        self.data['r_mean'] = 0
        self.data['g_mean'] = 0
        self.data['b_mean'] = 0
        self.data['r_std'] = 0
        self.data['g_std'] = 0
        self.data['b_std'] = 0
        self.data['r_min'] = 0
        self.data['g_min'] = 0
        self.data['b_min'] = 0
        self.data['r_max'] = 0
        self.data['g_max'] = 0
        self.data['b_max'] = 0

    def get_csv_head(self):
        return ','.join(map(str, self.data.keys()))

    def get_csv(self):
        return ','.join(map(str, self.data.values()))

    def get_display(self):
        items = [
            'rgb_mean',
            'rgb_std',
            'rgb_min',
            'rgb_max',
        ]
        result = []
        for item in items:
            value = 0
            result.append((item, value))
        return result


class Example(QtGui.QMainWindow):
    def __init__(self):
        super().__init__()
        styleName = 'Cleanlooks'
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create(styleName))

        # self.originalPalette = QtGui.QApplication.palette()
        # QtGui.QApplication.setPalette(self.originalPalette)
        QtGui.QApplication.setPalette(
            QtGui.QApplication.style().standardPalette())
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
        # TODO For testing, remove
        self.files = ['img/tux.png']

        self.data = []

        self.sample = Sample()

        plt_vbox = QtGui.QVBoxLayout()
        self.canvas = FigureCanvasQTAgg(self.figure)
        plt_vbox.addWidget(self.canvas)
        if DISPLAY_PYPLOT_TOOLBAR:
            self.toolbar = NavigationToolbar2QT(self.canvas, self)
            plt_vbox.addWidget(self.toolbar)

        self.load_plumreg_data()

        side_panel_vbox = self.create_side_panel()

        self.create_menubar()

        main_hbox = QtGui.QHBoxLayout()
        main_hbox.addLayout(plt_vbox)
        main_hbox.addLayout(side_panel_vbox)

        self.main.setLayout(main_hbox)
        self.connect_mouse_events()

    def load_plumreg_data(self):
        self.plumregs = []
        with open(PLUMREG_FILE) as f:
            lines = f.readlines()
        for l in lines:
            index, accr, name = l.strip().split(',')
            self.plumregs.append((accr, name))

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

        save_action = QtGui.QAction(QtGui.QIcon('save.png'), 'Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Save data to file')
        save_action.triggered.connect(self.save)

        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        menubar = self.menuBar()

        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)
        fileMenu.addAction(save_action)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)

    def create_side_panel(self):
        layout = QtGui.QVBoxLayout()

        self.render_area = RenderArea(self)
        layout.addWidget(self.render_area)

        self.file_label = QtGui.QLabel('')
        layout.addWidget(self.file_label)

        self.species_group = QtGui.QGroupBox('Species')
        self.species_group_vbox = QtGui.QVBoxLayout()

        self.ssp_label = QtGui.QLabel('No species selected')
        self.species_group_vbox.addWidget(self.ssp_label)

        self.sp_button = QtGui.QPushButton('Select species', self)
        self.sp_button.clicked.connect(self.show_species_dialog)
        self.species_group_vbox.addWidget(self.sp_button)

        self.species_group.setLayout(self.species_group_vbox)
        layout.addWidget(self.species_group)

        grid = QtGui.QGridLayout()
        comboboxes = [
            ('plumreg', 'Plumage region', [n for a, n in self.plumregs]),
            ('sex', 'Sex', [
                'M',
                'F',
                '?',
            ]),
            ('age', 'Age', [
                'Pullus',
                'Juvenile',
                'Subadult',
                'Adult',
                'Unknown',
            ]),
            ('imgsrc', 'Image source', [
                'HBW',
                'Flickr',
                'Ecco',
                'Other',
            ]),
            ('imgtype', 'Image type', [
                'Painting',
                'Photo',
            ]),
        ]
        self.boxes = {}

        i = 0
        for cb, label, items in comboboxes:
            cb_label = QtGui.QLabel(label)
            self.boxes[cb] = QtGui.QComboBox(self)
            self.boxes[cb].addItems(items)
            self.boxes[cb].currentIndexChanged.connect(self.combo_change)
            grid.addWidget(cb_label, i, 0, QtCore.Qt.AlignRight)
            grid.addWidget(self.boxes[cb], i, 1)
            i += 1
        # Initialize the combo box sample fields
        self.combo_change()
        layout.addLayout(grid)

        self.display_area = QtGui.QTextEdit(self)
        self.display_area.setReadOnly(True)
        # self.display_area.setCurrentFont(QtGui.QFont('Courier New', 8))
        self.display_area.setFontFamily('Monospace')
        layout.addWidget(self.display_area)

        self.insert_button = QtGui.QPushButton('Insert', self)
        self.insert_button.clicked.connect(self.insert)
        layout.addWidget(self.insert_button)

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

    def combo_change(self, *args):
        self.sample.data['sex'] = self.boxes['sex'].currentText().lower()
        self.sample.data['age'] = self.boxes['age'].currentText().lower()
        self.sample.data['imgsrc'] = self.boxes['imgsrc'].currentText().lower()
        self.sample.data['imgtype'] = (
            self.boxes['imgtype'].currentText().lower())
        plumreg_accr = self.plumregs[self.boxes['plumreg'].currentIndex()][0]
        self.sample.data['plumreg'] = plumreg_accr.lower()

    def reset_figure(self):
        self.sample.data['imgfile'] = os.path.basename(
            self.files[self.file_index])
        self.figure.clear()
        self.img = mpimg.imread(self.files[self.file_index])
        plt.imshow(self.img)
        self.cursor.reset(self.figure.axes[0])
        self.figure.axes[0].get_xaxis().set_visible(False)
        self.figure.axes[0].get_yaxis().set_visible(False)
        self.repaint()

    def show_species_dialog(self):
        dlg = SimpleSpeciesDialog(self)
        if dlg.exec_():
            self.sample.data['genus'] = dlg.ssp[0]
            self.sample.data['species'] = dlg.ssp[1]
            self.sample.data['subspecies'] = dlg.ssp[2]
            self.ssp_label.setText(' '.join(dlg.ssp))

    def showDialog(self):
        self.files = QtGui.QFileDialog.getOpenFileNames(
            self, 'Open file', os.getcwd(), '*.jpg *.png')
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

    def insert(self):
        print(self.sample.get_csv_head())
        print(self.sample.get_csv())

    def save(self):
        suggested_file = os.path.join(os.getcwd(), 'test.txt')
        file_name = QtGui.QFileDialog.getSaveFileName(
            self, 'Save to file', suggested_file)

        self.col_heads = ['taxon', 'size']
        with open(file_name, 'w') as f:
            col_heads = ','.join(self.col_heads)
            f.write('{}\n'.format(col_heads))
            for d in self.data:
                sample = ','.join(d)
                f.write('{}\n'.format(sample))
        self.data = []

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

        # selected = skimage.color.rgb2lab(selected)
        a, b, c = selected.shape
        rgbs = selected.reshape((a * b, c))

        rgb_mean = list(np.mean(rgbs, axis=0))[:3]
        rgb_std = list(np.std(rgbs, axis=0))[:3]
        rgb_min = [np.amin(rgbs[:, i]) for i in range(3)]
        rgb_max = [np.amax(rgbs[:, i]) for i in range(3)]

        self.sample.data['r_mean'] = rgb_mean[0]
        self.sample.data['g_mean'] = rgb_mean[1]
        self.sample.data['b_mean'] = rgb_mean[2]

        self.sample.data['r_std'] = rgb_std[0]
        self.sample.data['g_std'] = rgb_std[1]
        self.sample.data['b_std'] = rgb_std[2]

        self.sample.data['r_min'] = rgb_min[0]
        self.sample.data['g_min'] = rgb_min[1]
        self.sample.data['b_min'] = rgb_min[2]

        self.sample.data['r_max'] = rgb_max[0]
        self.sample.data['g_max'] = rgb_max[1]
        self.sample.data['b_max'] = rgb_max[2]


        self.sample.data['size'] = (self.cursor.radius * 2) ** 2
        self.sample.data['x'] = x
        self.sample.data['y'] = y
        self.update_text()
        self.repaint()

    def on_scroll(self, event):
        self.repaint()

    def update_text(self):
        result = ""
        display_items = self.sample.get_display()
        total_w = 33
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

        def f(x): return int(x * 255)
        col = QtGui.QColor(
            f(self.parent.sample.data['r_mean']),
            f(self.parent.sample.data['g_mean']),
            f(self.parent.sample.data['b_mean']),
        )
        qp.fillRect(0, 0, self.width(), self.height(), col)
        qp.end()


class SimpleSpeciesDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QtGui.QVBoxLayout()
        grid = QtGui.QGridLayout()

        genus_label = QtGui.QLabel('Genus')
        grid.addWidget(genus_label, 0, 0, QtCore.Qt.AlignRight)
        self.genus_edit = QtGui.QLineEdit()
        grid.addWidget(self.genus_edit, 0, 1)

        sp_label = QtGui.QLabel('Species')
        grid.addWidget(sp_label, 1, 0, QtCore.Qt.AlignRight)
        self.sp_edit = QtGui.QLineEdit()
        grid.addWidget(self.sp_edit, 1, 1)

        ssp_label = QtGui.QLabel('Subspecies')
        grid.addWidget(ssp_label, 2, 0, QtCore.Qt.AlignRight)
        self.ssp_edit = QtGui.QLineEdit()
        grid.addWidget(self.ssp_edit, 2, 1)

        main_layout.addLayout(grid)

        self.button = QtGui.QPushButton('Select')
        self.button.clicked.connect(self.select)
        main_layout.addWidget(self.button)

        self.setLayout(main_layout)

        self.setWindowTitle('Select species')
        self.setFixedWidth(250)

    def select(self):
        self.ssp = (
            self.genus_edit.text(),
            self.sp_edit.text(),
            self.ssp_edit.text(),
        )
        self.accept()


class SpeciesDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.headings = [
            'Taxon ID',
            'First name',
            'Last name',
            'Genus',
            'Species',
            'Subspecies',
            'Taxon Code',
            'S&A Tax Order',
            'Crook 64 Order',
        ]

        self.proxy_model = QtGui.QSortFilterProxyModel()
        self.proxy_model.setDynamicSortFilter(True)

        self.create_model()
        self.insert_data()

        self.proxy_model.setSourceModel(self.model)

        main_layout = QtGui.QVBoxLayout()

        filter_hbox = QtGui.QHBoxLayout()
        filter_label = QtGui.QLabel('Filter')
        filter_hbox.addWidget(filter_label)

        self.filter_pattern_edit = QtGui.QLineEdit()
        self.filter_pattern_edit.textChanged.connect(self.filter_changed)
        filter_hbox.addWidget(self.filter_pattern_edit)
        main_layout.addLayout(filter_hbox)

        self.filter_column_box = QtGui.QComboBox(self)
        for h in self.headings:
            self.filter_column_box.addItem(h)
        self.filter_column_box.currentIndexChanged.connect(
            self.proxy_model.setFilterKeyColumn)
        filter_hbox.addWidget(self.filter_column_box)

        self.list_view = QtGui.QTreeView()
        self.list_view.setRootIsDecorated(False)
        self.list_view.setAlternatingRowColors(True)
        self.list_view.setSortingEnabled(True)
        self.list_view.setModel(self.proxy_model)
        self.list_view.doubleClicked.connect(self.select)
        self.list_view.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        main_layout.addWidget(self.list_view)

        self.button = QtGui.QPushButton('Select')
        self.button.clicked.connect(self.select)
        main_layout.addWidget(self.button)
        self.setLayout(main_layout)

        self.setWindowTitle('Select species')
        self.resize(1000, 500)

    def select(self, event):
        indexes = self.list_view.selectedIndexes()
        if indexes:
            self.taxon = indexes[0].data()
            self.accept()

    def filter_changed(self):
        pattern = self.filter_pattern_edit.text()
        regex = QtCore.QRegExp(pattern, QtCore.Qt.CaseInsensitive, 0)
        self.proxy_model.setFilterRegExp(regex)

    def create_model(self):
        self.model = QtGui.QStandardItemModel(0, len(self.headings), self)
        for i in range(len(self.headings)):
            self.model.setHeaderData(i, QtCore.Qt.Horizontal, self.headings[i])

    def insert_data(self):
        with open(SPECIES_FILE, newline='') as csvfile:
            species = csv.reader(csvfile, delimiter=',')
            for row in species:
                self.model.insertRow(0)
                for i, c in enumerate(row):
                    if i == 0:
                        c = int(c)
                    self.model.setData(self.model.index(0, i), c)


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
