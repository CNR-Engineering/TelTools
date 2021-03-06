import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAction, QApplication, QComboBox, QGridLayout, QGroupBox, QHBoxLayout,
                             QInputDialog, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton,
                             QSpacerItem, QStyle, QTabWidget, QVBoxLayout, QWidget)
import sys

from pyteltools.conf import settings
from pyteltools.slf import Serafin

from .util import ColorMapCanvas, LoadMeshDialog, MapViewer, PlotViewer, PolygonMapCanvas, PyTelToolWidget, \
    TimeSliderIndexOnly as TimeSlider, open_polygons, SerafinInputTab


class SimpleTimeSelection(QWidget):
    def __init__(self, label='Reference frame index'):
        super().__init__()
        self.refIndex = QLineEdit('', self)
        self.refIndex.setMaximumWidth(60)
        self.refSlider = TimeSlider(self.refIndex)
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel(label))
        hlayout.addWidget(self.refIndex)
        hlayout.addWidget(self.refSlider)
        hlayout.setAlignment(Qt.AlignLeft)
        hlayout.addStretch()
        hlayout.setSpacing(10)
        self.setLayout(hlayout)
        self.refIndex.editingFinished.connect(self.refSlider.enterIndexEvent)

    def initRef(self, nb_frames):
        self.refSlider.reinit(nb_frames, 0)
        self.refIndex.setText(str(1))

    def clearText(self):
        self.refIndex.clear()


class DoubleTimeSelection(QWidget):
    def __init__(self):
        super().__init__()
        self.refIndex = QLineEdit('', self)
        self.refIndex.setMaximumWidth(60)
        self.testIndex = QLineEdit('', self)
        self.testIndex.setMaximumWidth(60)

        self.refSlider = TimeSlider(self.refIndex)
        self.testSlider = TimeSlider(self.testIndex)

        mainLayout = QVBoxLayout()

        hlayout = QHBoxLayout()
        lb = QLabel('Reference frame index')
        lb.setFixedWidth(100)
        hlayout.addWidget(lb)
        hlayout.addWidget(self.refIndex)
        hlayout.addWidget(self.refSlider)
        hlayout.setAlignment(Qt.AlignLeft)
        hlayout.addStretch()
        hlayout.setSpacing(10)
        mainLayout.addLayout(hlayout)
        hlayout = QHBoxLayout()

        lb = QLabel('Test frame index')
        lb.setFixedWidth(100)
        hlayout.addWidget(lb)
        hlayout.addWidget(self.testIndex)
        hlayout.addWidget(self.testSlider)
        hlayout.setAlignment(Qt.AlignLeft)
        hlayout.addStretch()
        hlayout.setSpacing(10)
        mainLayout.addLayout(hlayout)
        self.setLayout(mainLayout)

        self.refIndex.editingFinished.connect(self.refSlider.enterIndexEvent)
        self.testIndex.editingFinished.connect(self.testSlider.enterIndexEvent)

    def initRef(self, nb_frames):
        self.refSlider.reinit(nb_frames, 0)
        self.refIndex.setText(str(1))

    def initTest(self, nb_frames):
        self.testSlider.reinit(nb_frames, nb_frames-1)
        self.testIndex.setText(str(nb_frames))

    def clearText(self):
        self.refIndex.clear()
        self.testIndex.clear()


class InputTab(SerafinInputTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.ref_data = None
        self.test_data = None
        self.ref_mesh = None

        self.polygons = []
        self.selected_polygon = None
        self.ref_mesh = None
        self.polygon_added = False   # is the intersection between the mesh and the selected polygon calculated?

        # initialize the map for locating polygons
        canvas = PolygonMapCanvas()
        self.map = MapViewer(canvas)
        self.has_map = False

        self._initWidgets()
        self._setLayout()
        self._bindEvents()

    def _initWidgets(self):
        # create the button open the reference file
        self.btnOpen.setText('Load\nReference')

        # create the button open the test file
        self.btnOpenTest = QPushButton('Load\nTest', self, icon=self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.btnOpenTest.setToolTip('<b>Open</b> a Serafin file')
        self.btnOpenTest.setFixedSize(105, 50)
        self.btnOpenTest.setEnabled(False)

        # create the button open the polygon file
        self.btnOpenPolygon = QPushButton('Load polygons\n(optional)', self,
                                          icon=self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.btnOpenPolygon.setToolTip('<b>Open</b> a .i2s or .shp file')
        self.btnOpenPolygon.setFixedSize(135, 50)
        self.btnOpenPolygon.setEnabled(False)

        # create the button for locating polygons on map
        self.locatePolygons = QPushButton('Locate polygons\non map',
                                          icon=self.style().standardIcon(QStyle.SP_DialogHelpButton))
        self.locatePolygons.setToolTip('<b>Open</b> a map with polygons')
        self.locatePolygons.setFixedSize(135, 50)
        self.locatePolygons.setEnabled(False)

        # create some text fields displaying the IO files info
        self.testNameBox = QLineEdit()
        self.testNameBox.setReadOnly(True)
        self.testNameBox.setFixedHeight(30)
        self.testNameBox.setMinimumWidth(600)
        self.testSummaryTextBox = QPlainTextEdit()
        self.testSummaryTextBox.setReadOnly(True)
        self.testSummaryTextBox.setMinimumHeight(40)
        self.testSummaryTextBox.setMaximumHeight(50)
        self.testSummaryTextBox.setMinimumWidth(600)
        self.polygonNameBox = QPlainTextEdit()
        self.polygonNameBox.setReadOnly(True)
        self.polygonNameBox.setFixedHeight(50)
        self.polygonNameBox.setMinimumWidth(600)

        # create combo box widgets for choosing the variable
        self.varBox = QComboBox()
        self.varBox.setFixedSize(400, 30)

        # create combo box widgets for choosing the polygon
        self.polygonBox = QComboBox()
        self.polygonBox.setFixedSize(400, 30)

    def _bindEvents(self):
        self.btnOpen.clicked.connect(self.btnOpenRefEvent)
        self.btnOpenTest.clicked.connect(self.btnOpenTestEvent)
        self.btnOpenPolygon.clicked.connect(self.btnOpenPolygonEvent)
        self.locatePolygons.clicked.connect(self.locatePolygonsEvent)
        self.polygonBox.currentTextChanged.connect(self.selectPolygonEvent)
        self.map.closeEvent = lambda event: self.locatePolygons.setEnabled(True)

    def _setLayout(self):
        mainLayout = QVBoxLayout()
        mainLayout.addItem(QSpacerItem(10, 20))
        mainLayout.setSpacing(15)

        hlayout = QHBoxLayout()
        hlayout.setAlignment(Qt.AlignLeft)
        hlayout.addItem(QSpacerItem(50, 1))
        hlayout.addWidget(self.btnOpen)
        hlayout.addWidget(self.btnOpenTest)
        hlayout.addItem(QSpacerItem(30, 1))
        hlayout.addWidget(self.langBox)
        hlayout.addItem(QSpacerItem(30, 1))
        hlayout.addWidget(self.btnOpenPolygon)
        hlayout.addWidget(self.locatePolygons)
        hlayout.setSpacing(10)
        mainLayout.addLayout(hlayout)
        mainLayout.addItem(QSpacerItem(10, 10))

        glayout = QGridLayout()
        glayout.addWidget(QLabel('     Reference'), 1, 1)
        glayout.addWidget(self.inNameBox, 1, 2)
        glayout.addWidget(QLabel('     Summary'), 2, 1)
        glayout.addWidget(self.summaryTextBox, 2, 2)
        glayout.addWidget(QLabel('     Test'), 3, 1)
        glayout.addWidget(self.testNameBox, 3, 2)
        glayout.addWidget(QLabel('     Summary'), 4, 1)
        glayout.addWidget(self.testSummaryTextBox, 4, 2)
        glayout.addWidget(QLabel('     Polygons'), 5, 1)
        glayout.addWidget(self.polygonNameBox, 5, 2)
        glayout.setAlignment(Qt.AlignLeft)
        glayout.setVerticalSpacing(10)

        mainLayout.addLayout(glayout)
        mainLayout.addItem(QSpacerItem(10, 10))

        glayout = QGridLayout()
        glayout.addWidget(QLabel('     Select the variable to compare'), 1, 1)
        glayout.addWidget(self.varBox, 1, 2)
        glayout.addWidget(QLabel('     Select the comparison domain'), 2, 1)
        glayout.addWidget(self.polygonBox, 2, 2)
        glayout.setSpacing(10)
        mainLayout.addLayout(glayout)
        mainLayout.setAlignment(glayout, Qt.AlignTop | Qt.AlignLeft)

        mainLayout.addItem(QSpacerItem(30, 15))
        mainLayout.addWidget(QLabel('   Message logs'))
        mainLayout.addWidget(self.logTextBox.widget)
        self.setLayout(mainLayout)
        self.setLayout(mainLayout)

    def _reinitRef(self):
        self.reset()
        self.ref_mesh = None
        self.ref_data = None
        self.polygon_added = False
        self.selected_polygon = None
        self.polygons = []

        self.test_data = None
        self.testSummaryTextBox.clear()
        self.testNameBox.clear()
        self.polygonNameBox.clear()
        self.varBox.clear()
        self.polygonBox.clear()
        self.btnOpenTest.setEnabled(False)
        self.btnOpenPolygon.setEnabled(False)
        self.locatePolygons.setEnabled(False)

        self.map.hide()
        self.has_map = False
        self.parent.reset()

    def _reinitTest(self, filename):
        self.test_data = None
        self.testNameBox.setText(filename)
        self.testSummaryTextBox.clear()
        self.varBox.clear()

    def locatePolygonsEvent(self):
        if not self.has_map:
            self.map.canvas.reinitFigure(self.ref_mesh, self.polygons,
                                         ['Polygon %d' % (i+1) for i in range(len(self.polygons))])
            self.has_map = True
        self.locatePolygons.setEnabled(False)
        self.map.show()

    def selectPolygonEvent(self, text):
        if not text:
            return
        elif text == 'Entire mesh':
            self.selected_polygon = None
        else:
            polygon_index = int(text.split()[1]) - 1
            self.selected_polygon = self.polygons[polygon_index]
        self.polygon_added = False

    def btnOpenRefEvent(self):
        canceled, filename = super().open_event()
        if canceled:
            return

        self._reinitRef()
        success, data = self.read_2d(filename)
        if not success:
            return

        self.ref_data = data

        # record the mesh
        self.parent.inDialog()
        meshLoader = LoadMeshDialog('comparison', self.ref_data.header)
        self.ref_mesh = meshLoader.run()
        self.parent.outDialog()
        if meshLoader.thread.canceled:
            self.summaryTextBox.clear()
            self.ref_data = None
            return

        self.parent.add_reference()

        self.btnOpenTest.setEnabled(True)
        self.btnOpenPolygon.setEnabled(True)
        self.polygonBox.addItem('Entire mesh')

    def btnOpenTestEvent(self):
        canceled, filename = super().open_event()
        if canceled:
            return

        self._reinitTest(filename)
        success, data = self.read_2d(filename, update=False)
        if not success:
            return

        # check if the mesh is identical to the reference
        if not self.ref_data.header.same_2d_mesh(data.header):
            QMessageBox.critical(self, 'Error', 'The mesh is not identical to the reference.', QMessageBox.Ok)
            return

        # check if the test file has common variables with the reference file
        common_vars = [(var_ID, var_names) for var_ID, var_names
                       in zip(self.ref_data.header.var_IDs, self.ref_data.header.var_names)
                       if var_ID in data.header.var_IDs]
        if not common_vars:
            QMessageBox.critical(self, 'Error', 'No common variable with the reference file.', QMessageBox.Ok)
            return

        self.test_data = data
        self.testNameBox.setText(filename)
        self.testSummaryTextBox.appendPlainText(self.test_data.header.summary())

        self.parent.add_test()

        for var_ID, var_name in common_vars:
            self.varBox.addItem(var_ID + ' (%s)' % var_name.decode(Serafin.SLF_EIT).strip())

    def btnOpenPolygonEvent(self):
        success, filename, polygons = open_polygons()
        if not success:
            return

        self.polygons = polygons
        self.map.close()
        self.map.has_figure = False

        self.polygonNameBox.clear()
        self.polygonNameBox.appendPlainText(filename + '\n' + 'The file contains {} polygon{}.'.format(
            len(self.polygons), 's' if len(self.polygons) > 1 else ''))

        self.polygonBox.clear()
        self.polygonBox.addItem('Entire mesh')
        for i in range(len(self.polygons)):
            self.polygonBox.addItem('Polygon %d' % (i+1))
        self.locatePolygons.setEnabled(True)


class ComputeErrorsTab(QWidget):
    def __init__(self, inputTab):
        super().__init__()
        self.input = inputTab
        self.timeSelection = DoubleTimeSelection()
        self.btnCompute = QPushButton('Compute', icon=self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.btnCompute.setFixedSize(105, 50)
        self.resultTextBox = QPlainTextEdit()

        self.btnCompute.clicked.connect(self.btnComputeEvent)

        mainLayout = QVBoxLayout()
        mainLayout.addItem(QSpacerItem(10, 10))
        mainLayout.addWidget(self.timeSelection)
        mainLayout.addItem(QSpacerItem(10, 10))
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.btnCompute)
        hlayout.setAlignment(self.btnCompute, Qt.AlignTop)
        hlayout.setAlignment(Qt.AlignHCenter)
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.resultTextBox)
        hlayout.addItem(QSpacerItem(10, 1))
        hlayout.addLayout(vlayout)
        mainLayout.addLayout(hlayout)
        self.setLayout(mainLayout)

        self.template = '=== Comparison between Ref (frame {}) and Test (frame {}) ===\n'\
                        'MSD  (Mean signed deviation)         \t{:<30}\n' \
                        'MAD  (Mean absolute deviation)       \t{:<30}\n' \
                        'RMSD (Root mean square deviation)    \t{:<30}\n'

    def add_reference(self):
        self.timeSelection.initRef(self.input.ref_data.header.nb_frames)

    def add_test(self):
        self.timeSelection.initTest(self.input.test_data.header.nb_frames)

    def reset(self):
        self.timeSelection.clearText()
        self.resultTextBox.clear()

    def btnComputeEvent(self):
        ref_time = int(self.timeSelection.refIndex.text()) - 1
        test_time = int(self.timeSelection.testIndex.text()) - 1
        selected_variable = self.input.varBox.currentText().split('(')[0][:-1]

        try:
            with Serafin.Read(self.input.ref_data.filename, self.input.ref_data.language) as input_stream:
                input_stream.header = self.input.ref_data.header
                input_stream.time = self.input.ref_data.time
                ref_values = input_stream.read_var_in_frame(ref_time, selected_variable)

            with Serafin.Read(self.input.test_data.filename, self.input.test_data.language) as input_stream:
                input_stream.header = self.input.test_data.header
                input_stream.time = self.input.test_data.time
                test_values = input_stream.read_var_in_frame(test_time, selected_variable)
        except (Serafin.SerafinRequestError, Serafin.SerafinValidationError) as e:
            QMessageBox.critical(None, 'Serafin Error', e.message, QMessageBox.Ok, QMessageBox.Ok)
            return

        values = test_values - ref_values
        msd = self.input.ref_mesh.mean_signed_deviation(values)
        mad = self.input.ref_mesh.mean_absolute_deviation(values)
        rmsd = self.input.ref_mesh.root_mean_square_deviation(values)
        self.resultTextBox.appendPlainText(self.template.format(ref_time+1, test_time+1, msd, mad, rmsd))


class ErrorEvolutionTab(QWidget):
    def __init__(self, inputTab):
        super().__init__()
        self.input = inputTab

        # set up a custom plot viewer
        self.plotViewer = PlotViewer()
        self.plotViewer.exitAct.setEnabled(False)
        self.plotViewer.menuBar.setVisible(False)
        self.plotViewer.toolBar.addAction(self.plotViewer.xLabelAct)
        self.plotViewer.toolBar.addSeparator()
        self.plotViewer.toolBar.addAction(self.plotViewer.yLabelAct)
        self.plotViewer.toolBar.addSeparator()
        self.plotViewer.toolBar.addAction(self.plotViewer.titleAct)
        self.plotViewer.canvas.figure.canvas.mpl_connect('motion_notify_event', self.plotViewer.mouseMove)

        # put it in a group box to get a nice border
        gb = QGroupBox()
        ly = QHBoxLayout()
        ly.addWidget(self.plotViewer)
        gb.setLayout(ly)
        gb.setStyleSheet('QGroupBox {border: 8px solid rgb(108, 122, 137); border-radius: 6px }')
        gb.setMaximumWidth(900)
        gb.setMinimumWidth(600)

        # create the reference time selection widget
        self.timeSelection = SimpleTimeSelection()
        self.btnCompute = QPushButton('Compute', icon=self.style().standardIcon(QStyle.SP_DialogApplyButton))

        # create the compute button
        self.btnCompute.setFixedSize(105, 50)
        self.btnCompute.clicked.connect(self.btnComputeEvent)

        # set layout
        mainLayout = QVBoxLayout()
        mainLayout.addItem(QSpacerItem(10, 10))
        mainLayout.addWidget(self.timeSelection)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.btnCompute)
        hlayout.addWidget(gb, Qt.AlignRight)
        hlayout.setAlignment(self.btnCompute, Qt.AlignTop)
        hlayout.setAlignment(Qt.AlignHCenter)
        hlayout.setSpacing(10)
        mainLayout.addLayout(hlayout)
        self.setLayout(mainLayout)

    def add_reference(self):
        self.timeSelection.initRef(self.input.ref_data.header.nb_frames)

    def add_test(self):
        pass

    def reset(self):
        self.timeSelection.clearText()
        self.plotViewer.defaultPlot()
        self.plotViewer.current_title = 'Evolution of MAD (mean absolute deviation)'
        self.plotViewer.current_ylabel = 'MAD'
        self.plotViewer.current_xlabel = 'Time (second)'

    def btnComputeEvent(self):
        ref_time = int(self.timeSelection.refIndex.text()) - 1
        selected_variable = self.input.varBox.currentText().split('(')[0][:-1]

        mad = []
        try:
            with Serafin.Read(self.input.ref_data.filename, self.input.ref_data.language) as input_stream:
                input_stream.header = self.input.ref_data.header
                input_stream.time = self.input.ref_data.time
                ref_values = input_stream.read_var_in_frame(ref_time, selected_variable)

            with Serafin.Read(self.input.test_data.filename, self.input.test_data.language) as input_stream:
                input_stream.header = self.input.test_data.header
                input_stream.time = self.input.test_data.time
                for i in range(len(self.input.test_data.time)):
                    values = input_stream.read_var_in_frame(i, selected_variable) - ref_values
                    mad.append(self.input.ref_mesh.mean_absolute_deviation(values))
        except (Serafin.SerafinRequestError, Serafin.SerafinValidationError) as e:
            QMessageBox.critical(None, 'Serafin Error', e.message, QMessageBox.Ok, QMessageBox.Ok)
            return
        self.plotViewer.plot(self.input.test_data.time, mad)


class ErrorDistributionTab(QWidget):
    def __init__(self, inputTab):
        super().__init__()
        self.input = inputTab
        self.ewsd = None
        self.xlim = None
        self.ylim = None

        # set up a custom plot viewer
        self.plotViewer = PlotViewer()
        self.plotViewer.exitAct.setEnabled(False)
        self.plotViewer.menuBar.setVisible(False)
        self.XLimitsAct = QAction('Change X limits', self, triggered=self.changeXlimits, enabled=False,
                                  icon=self.style().standardIcon(QStyle.SP_DialogNoButton))
        self.YLimitsAct = QAction('Change Y limits', self, triggered=self.changeYlimits, enabled=False,
                                  icon=self.style().standardIcon(QStyle.SP_DialogNoButton))

        self.plotViewer.toolBar.addAction(self.XLimitsAct)
        self.plotViewer.toolBar.addAction(self.YLimitsAct)
        self.plotViewer.toolBar.addSeparator()
        self.plotViewer.toolBar.addAction(self.plotViewer.xLabelAct)
        self.plotViewer.toolBar.addSeparator()
        self.plotViewer.toolBar.addAction(self.plotViewer.yLabelAct)
        self.plotViewer.toolBar.addSeparator()
        self.plotViewer.toolBar.addAction(self.plotViewer.titleAct)

        # put it in a group box to get a nice border
        gb = QGroupBox()
        ly = QHBoxLayout()
        ly.addWidget(self.plotViewer)
        gb.setLayout(ly)
        gb.setStyleSheet('QGroupBox {border: 8px solid rgb(108, 122, 137); border-radius: 6px }')
        gb.setMinimumWidth(600)

        # create the reference time selection widget
        self.timeSelection = DoubleTimeSelection()

        # create the compute button
        self.btnCompute = QPushButton('Compute', icon=self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.btnCompute.setFixedSize(105, 50)
        self.btnCompute.clicked.connect(self.btnComputeEvent)

        # create the color map button
        self.btnColorMap = QPushButton('2D View', icon=self.style().standardIcon(QStyle.SP_DialogHelpButton))
        self.btnColorMap.setFixedSize(105, 50)
        self.btnColorMap.clicked.connect(self.btnColorMapEvent)
        self.btnColorMap.setEnabled(False)

        # initialize the map for 2D view
        canvas = ColorMapCanvas()
        self.map = MapViewer(canvas)
        self.has_map = False
        self.map.closeEvent = lambda event: self.btnColorMap.setEnabled(True)

        # create the stats box
        self.resultBox = QPlainTextEdit()
        self.resultBox.setMinimumWidth(400)
        self.resultBox.setMaximumWidth(600)

        # set layout
        mainLayout = QVBoxLayout()
        mainLayout.addItem(QSpacerItem(10, 10))
        mainLayout.addWidget(self.timeSelection)
        vlayout = QVBoxLayout()
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.btnColorMap)
        hlayout.addWidget(self.btnCompute)
        hlayout.setSpacing(10)
        vlayout.addLayout(hlayout)
        vlayout.setAlignment(hlayout, Qt.AlignTop | Qt.AlignRight)
        vlayout.addItem(QSpacerItem(10, 10))
        vlayout.addWidget(self.resultBox)
        vlayout.setAlignment(Qt.AlignHCenter)
        hlayout = QHBoxLayout()
        hlayout.addLayout(vlayout)
        hlayout.addWidget(gb, Qt.AlignHCenter)
        hlayout.setSpacing(10)
        mainLayout.addLayout(hlayout)
        self.setLayout(mainLayout)

        # template for text output
        self.template = '=== EWSD distribution between Ref (frame {}) and Test (frame {}) ===\n'\
                        'Mean         \t{:<30}\n' \
                        'Variance     \t{:<30}\n' \
                        'Min          \t{:<30}\n' \
                        'Quartile 25  \t{:<30}\n' \
                        'Median       \t{:<30}\n' \
                        'Quartile 75  \t{:<30}\n' \
                        'Max          \t{:<30}\n'

    def add_reference(self):
        self.timeSelection.initRef(self.input.ref_data.header.nb_frames)

    def add_test(self):
        self.timeSelection.initTest(self.input.test_data.header.nb_frames)

    def reset(self):
        self.ewsd = None
        self.xlim = None
        self.ylim = None
        self.has_map = False
        self.timeSelection.clearText()
        self.resultBox.clear()
        self.plotViewer.defaultPlot()
        self.plotViewer.current_title = 'Distribution of EWSD (element-wise signed deviation)'
        self.plotViewer.current_ylabel = 'Frequency'
        self.plotViewer.current_xlabel = 'EWSD'
        self.XLimitsAct.setEnabled(False)
        self.YLimitsAct.setEnabled(False)
        self.btnColorMap.setEnabled(False)

    def changeXlimits(self):
        value, ok = QInputDialog.getText(self, 'Change X limits',
                                         'Enter the new X limits',
                                         text=', '.join(map(lambda x: '{:+f}'.format(x),
                                                            self.plotViewer.canvas.axes.get_xlim())))
        if not ok:
            return
        try:
            xmin, xmax = map(float, value.split(','))
        except ValueError:
            QMessageBox.critical(self, 'Error', 'Invalid input.', QMessageBox.Ok)
            return

        self.xlim = xmin, xmax
        self.updateHistogram()
        self.has_map = False

    def changeYlimits(self):
        value, ok = QInputDialog.getText(self, 'Change Y limits',
                                         'Enter the new Y limits',
                                         text=', '.join(map(lambda x: '{:+f}'.format(x),
                                                            self.plotViewer.canvas.axes.get_ylim())))
        if not ok:
            return
        try:
            self.ylim = tuple(map(float, value.split(',')))
        except ValueError:
            QMessageBox.critical(self, 'Error', 'Invalid input.', QMessageBox.Ok)
            return

        self.plotViewer.canvas.axes.set_ylim(self.ylim)
        self.plotViewer.canvas.draw()

    def updateStats(self, ref_time, test_time):
        ewsd = np.array(list(self.ewsd.values()))
        quantile25, median, quantile75 = np.percentile(ewsd, [25, 50, 75])
        self.resultBox.appendPlainText(self.template.format(ref_time+1, test_time+1,
                                                            np.mean(ewsd), np.var(ewsd, ddof=1),
                                                            np.min(ewsd), quantile25, median,
                                                            quantile75, np.max(ewsd)))

    def updateHistogram(self):
        ewsd = list(self.ewsd.values())
        if self.xlim is not None:
            ewsd = list(filter(lambda x: self.xlim[0] <= x <= self.xlim[1], ewsd))

        weights = np.ones_like(ewsd) / self.input.ref_mesh.nb_triangles_inside  # make frequency histogram

        self.plotViewer.canvas.axes.clear()
        self.plotViewer.canvas.axes.grid(linestyle='dotted')

        self.plotViewer.canvas.axes.hist(ewsd, bins=settings.NB_BINS_EWSD, weights=weights, histtype='bar', color='g',
                                         edgecolor='k', alpha=0.5)
        self.plotViewer.canvas.axes.set_xlabel(self.plotViewer.current_xlabel)
        self.plotViewer.canvas.axes.set_ylabel(self.plotViewer.current_ylabel)
        self.plotViewer.canvas.axes.set_title(self.plotViewer.current_title)

        if self.ylim is not None:
            self.plotViewer.canvas.axes.set_ylim(self.ylim)

        self.plotViewer.canvas.draw()

        self.btnColorMap.setEnabled(True)
        self.XLimitsAct.setEnabled(True)
        self.YLimitsAct.setEnabled(True)

    def btnComputeEvent(self):
        self.xlim = None
        self.ylim = None
        self.has_map = False

        ref_time = int(self.timeSelection.refIndex.text()) - 1
        test_time = int(self.timeSelection.testIndex.text()) - 1
        selected_variable = self.input.varBox.currentText().split('(')[0][:-1]

        try:
            with Serafin.Read(self.input.ref_data.filename, self.input.ref_data.language) as input_stream:
                input_stream.header = self.input.ref_data.header
                input_stream.time = self.input.ref_data.time
                ref_values = input_stream.read_var_in_frame(ref_time, selected_variable)

            with Serafin.Read(self.input.test_data.filename, self.input.test_data.language) as input_stream:
                input_stream.header = self.input.test_data.header
                input_stream.time = self.input.test_data.time
                test_values = input_stream.read_var_in_frame(test_time, selected_variable)
        except (Serafin.SerafinRequestError, Serafin.SerafinValidationError) as e:
            QMessageBox.critical(None, 'Serafin Error', e.message, QMessageBox.Ok, QMessageBox.Ok)
            return

        values = test_values - ref_values
        self.ewsd = self.input.ref_mesh.element_wise_signed_deviation(values)

        self.updateStats(ref_time, test_time)
        self.updateHistogram()

    def btnColorMapEvent(self):
        if not self.has_map:
            reply = QMessageBox.question(self, 'Show distribution in 2D',
                                         'This may take some time. Are you sure to proceed?',
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
            selected_variable = self.input.varBox.currentText().split('(')[0][:-1]
            self.map.canvas.reinitFigure(self.input.ref_mesh, self.ewsd, selected_variable,
                                         self.xlim, self.input.ref_mesh.polygon)
            self.has_map = True
        self.btnColorMap.setEnabled(False)
        self.map.show()


class BSSTab(QWidget):
    def __init__(self, inputTab):
        super().__init__()
        self.input = inputTab
        self.timeSelection = DoubleTimeSelection()
        self.initSelection = SimpleTimeSelection('Initial state index')

        # set up a custom plot viewer
        self.has_figure = False
        self.plotViewer = PlotViewer()
        self.plotViewer.exitAct.setEnabled(False)
        self.plotViewer.menuBar.setVisible(False)
        self.plotViewer.toolBar.addAction(self.plotViewer.xLabelAct)
        self.plotViewer.toolBar.addSeparator()
        self.plotViewer.toolBar.addAction(self.plotViewer.yLabelAct)
        self.plotViewer.toolBar.addSeparator()
        self.plotViewer.toolBar.addAction(self.plotViewer.titleAct)
        self.plotViewer.canvas.figure.canvas.mpl_connect('motion_notify_event', self.plotViewer.mouseMove)
        self.initSelection.refIndex.textChanged.connect(self.reinitFigure)
        self.timeSelection.refIndex.textChanged.connect(self.reinitFigure)

        self.btnEvolution = QPushButton('BSS evolution', icon=self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.btnEvolution.setFixedSize(105, 50)

        self.btnCompute = QPushButton('Compute', icon=self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.btnCompute.setFixedSize(105, 50)
        self.resultTextBox = QPlainTextEdit()

        self.btnCompute.clicked.connect(self.btnComputeEvent)
        self.btnEvolution.clicked.connect(self.btnEvolutionEvent)

        mainLayout = QVBoxLayout()
        mainLayout.addItem(QSpacerItem(10, 10))
        mainLayout.addWidget(self.timeSelection)
        mainLayout.addWidget(self.initSelection)
        mainLayout.addItem(QSpacerItem(10, 10))
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.btnEvolution)
        hlayout.addWidget(self.btnCompute)
        hlayout.setAlignment(self.btnEvolution, Qt.AlignTop)
        hlayout.setAlignment(self.btnCompute, Qt.AlignTop)
        hlayout.setAlignment(Qt.AlignHCenter)
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.resultTextBox)
        hlayout.addItem(QSpacerItem(10, 1))
        hlayout.addLayout(vlayout)
        mainLayout.addLayout(hlayout)
        self.setLayout(mainLayout)

        self.template = '===\nComparison between Ref (frame {}) and Test (frame {})\n' \
                        'with respect to Init (frame {})\n===\n' \
                        'BSS\t{:<30}\n'

    def add_reference(self):
        self.timeSelection.initRef(self.input.ref_data.header.nb_frames)

    def add_test(self):
        self.timeSelection.initTest(self.input.test_data.header.nb_frames)
        self.initSelection.initRef(self.input.test_data.header.nb_frames)

    def reset(self):
        self.timeSelection.clearText()
        self.resultTextBox.clear()
        self.has_figure = False
        self.plotViewer.defaultPlot()
        self.plotViewer.current_title = 'Evolution of BSS'
        self.plotViewer.current_ylabel = 'BSS'
        self.plotViewer.current_xlabel = 'Time (second)'

    def reinitFigure(self):
        self.has_figure = False

    def btnEvolutionEvent(self):
        if not self.has_figure:
            all_bss = []
            ref_time = int(self.timeSelection.refIndex.text()) - 1

            init_time = int(self.initSelection.refIndex.text()) - 1
            selected_variable = self.input.varBox.currentText().split('(')[0][:-1]

            try:
                with Serafin.Read(self.input.ref_data.filename, self.input.ref_data.language) as input_stream:
                    input_stream.header = self.input.ref_data.header
                    input_stream.time = self.input.ref_data.time
                    ref_values = input_stream.read_var_in_frame(ref_time, selected_variable)

                with Serafin.Read(self.input.test_data.filename, self.input.test_data.language) as input_stream:
                    input_stream.header = self.input.test_data.header
                    input_stream.time = self.input.test_data.time
                    init_values = input_stream.read_var_in_frame(init_time, selected_variable)
                    ref_volume = self.input.ref_mesh.quadratic_volume(ref_values - init_values)

                    for index in range(len(self.input.test_data.time)):
                        test_values = input_stream.read_var_in_frame(index, selected_variable)

                        test_volume = self.input.ref_mesh.quadratic_volume(test_values - ref_values)
                        if test_volume == 0 and ref_volume == 0:
                            bss = 1
                        else:
                            with np.errstate(divide='ignore'):
                                bss = 1 - test_volume / ref_volume
                        all_bss.append(bss)
            except (Serafin.SerafinRequestError, Serafin.SerafinValidationError) as e:
                QMessageBox.critical(None, 'Serafin Error', e.message, QMessageBox.Ok, QMessageBox.Ok)
                return

            self.plotViewer.plot(self.input.test_data.time, all_bss)
        self.plotViewer.show()

    def btnComputeEvent(self):
        ref_time = int(self.timeSelection.refIndex.text()) - 1
        test_time = int(self.timeSelection.testIndex.text()) - 1
        init_time = int(self.initSelection.refIndex.text()) - 1
        selected_variable = self.input.varBox.currentText().split('(')[0][:-1]

        try:
            with Serafin.Read(self.input.ref_data.filename, self.input.ref_data.language) as input_stream:
                input_stream.header = self.input.ref_data.header
                input_stream.time = self.input.ref_data.time
                ref_values = input_stream.read_var_in_frame(ref_time, selected_variable)

            with Serafin.Read(self.input.test_data.filename, self.input.test_data.language) as input_stream:
                input_stream.header = self.input.test_data.header
                input_stream.time = self.input.test_data.time
                test_values = input_stream.read_var_in_frame(test_time, selected_variable)
                init_values = input_stream.read_var_in_frame(init_time, selected_variable)
        except (Serafin.SerafinRequestError, Serafin.SerafinValidationError) as e:
            QMessageBox.critical(None, 'Serafin Error', e.message, QMessageBox.Ok, QMessageBox.Ok)
            return

        test_volume = self.input.ref_mesh.quadratic_volume(test_values - ref_values)
        ref_volume = self.input.ref_mesh.quadratic_volume(ref_values - init_values)
        if test_volume == 0 and ref_volume == 0:
            bss = 1
        else:
            with np.errstate(divide='ignore'):
                bss = 1 - test_volume / ref_volume
        self.resultTextBox.appendPlainText(self.template.format(ref_time+1, test_time+1, init_time+1, bss))


class CompareResultsGUI(PyTelToolWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumWidth(800)
        self.setWindowTitle('Compare two results on identical meshes')

        self.tab = QTabWidget()
        self.tab.setStyleSheet('QTabBar::tab { height: 40px; min-width: 150px; }')

        self.input = InputTab(self)
        errorEvolutionTab = ErrorEvolutionTab(self.input)
        computeErrorTab = ComputeErrorsTab(self.input)
        errorDistributionTab = ErrorDistributionTab(self.input)
        bssTab = BSSTab(self.input)

        self.tab.addTab(self.input, 'Input')
        self.tab.addTab(computeErrorTab, 'MSD/MAD/RMSD')
        self.tab.addTab(errorEvolutionTab, 'MAD evolution')
        self.tab.addTab(errorDistributionTab, 'EWSD distribution')
        self.tab.addTab(bssTab, 'BSS')

        for i in range(1, 5):
            self.tab.setTabEnabled(i, False)
        self.tab.currentChanged.connect(self.switch_tab)

        self.resultTabs = [errorEvolutionTab, computeErrorTab, errorDistributionTab, bssTab]

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.tab)
        self.setLayout(mainLayout)

    def switch_tab(self, index):
        if index == 0:
            pass
        else:
            if not self.input.polygon_added:
                self.input.ref_mesh.add_polygon(self.input.selected_polygon)
                self.input.polygon_added = True

    def reset(self):
        for i, tab in enumerate(self.resultTabs):
            tab.reset()
            self.tab.setTabEnabled(i+1, False)

    def add_reference(self):
        for tab in self.resultTabs:
            tab.add_reference()

    def add_test(self):
        for i, tab in enumerate(self.resultTabs):
            tab.add_test()
            self.tab.setTabEnabled(i+1, True)
        if self.input.ref_data.filename == self.input.test_data.filename:
            self.tab.setTabEnabled(4, False)


def exception_hook(exctype, value, traceback):
    """!
    @brief Needed for suppressing traceback silencing in newer version of PyQt5
    """
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


if __name__ == '__main__':
    # suppress explicitly traceback silencing
    sys._excepthook = sys.excepthook
    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    widget = CompareResultsGUI()
    widget.show()
    app.exec_()
