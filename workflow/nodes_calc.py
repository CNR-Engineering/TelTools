from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from workflow.Node import Node, OneInOneOutNode, TwoInOneOutNode
from slf import Serafin
from slf.volume import TruncatedTriangularPrisms, VolumeCalculator
from slf.flux import TriangularVectorField, FluxCalculator
import slf.misc as operations
from gui.util import ConditionDialog


class ComputeMaxNode(OneInOneOutNode):
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Calculations'
        self.label = 'Compute\nMax'
        self.out_port.data_type = 'slf'
        self.in_port.data_type = 'slf'
        self.state = Node.READY
        self.data = None

    def reconfigure(self):
        super().reconfigure()
        self.state = Node.READY
        self.reconfigure_downward()

    def configure(self):
        super().configure()
        self.state = Node.READY
        self.reconfigure_downward()

    def save(self):
        return '|'.join([self.category, self.name(), str(self.index()),
                         str(self.pos().x()), str(self.pos().y()), ''])

    def load(self, options):
        self.state = Node.READY

    def run(self):
        success = super().run_upward()
        if not success:
            self.state = Node.FAIL
            self.update()
            self.message = 'Failed: input failed.'
            return
        input_data = self.in_port.mother.parentItem().data

        if input_data.operator is not None:
            self.state = Node.FAIL
            self.update()
            if input_data.operator == operations.MAX:
                self.message = 'Failed: the input data is already the result of Compute Max.'
                return
            else:
                self.message = 'Failed: the input data is already the result of another computation.'
                return

        self.data = input_data.copy()
        self.data.operator = operations.MAX
        self.state = Node.SUCCESS
        self.update()
        self.message = 'Successful.'


class ComputeMinNode(OneInOneOutNode):
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Calculations'
        self.label = 'Compute\nMin'
        self.out_port.data_type = 'slf'
        self.in_port.data_type = 'slf'
        self.state = Node.READY
        self.data = None

    def reconfigure(self):
        super().reconfigure()
        self.state = Node.READY
        self.reconfigure_downward()

    def configure(self):
        super().configure()
        self.state = Node.READY
        self.reconfigure_downward()

    def save(self):
        return '|'.join([self.category, self.name(), str(self.index()),
                         str(self.pos().x()), str(self.pos().y()), ''])

    def load(self, options):
        self.state = Node.READY

    def run(self):
        success = super().run_upward()
        if not success:
            self.state = Node.FAIL
            self.update()
            self.message = 'Failed: input failed.'
            return
        input_data = self.in_port.mother.parentItem().data

        if input_data.operator is not None:
            self.state = Node.FAIL
            self.update()
            if input_data.operator == operations.MIN:
                self.message = 'Failed: the input data is already the result of Compute Min.'
                return
            else:
                self.message = 'Failed: the input data is already the result of another computation.'
                return

        self.data = input_data.copy()
        self.data.operator = operations.MIN
        self.state = Node.SUCCESS
        self.update()
        self.message = 'Successful.'


class ComputeMeanNode(OneInOneOutNode):
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Calculations'
        self.label = 'Compute\nMean'
        self.out_port.data_type = 'slf'
        self.in_port.data_type = 'slf'
        self.state = Node.READY
        self.data = None

    def reconfigure(self):
        super().reconfigure()
        self.state = Node.READY
        self.reconfigure_downward()

    def configure(self):
        super().configure()
        self.state = Node.READY
        self.reconfigure_downward()

    def save(self):
        return '|'.join([self.category, self.name(), str(self.index()),
                         str(self.pos().x()), str(self.pos().y()), ''])

    def load(self, options):
        self.state = Node.READY

    def run(self):
        success = super().run_upward()
        if not success:
            self.state = Node.FAIL
            self.update()
            self.message = 'Failed: input failed.'
            return
        input_data = self.in_port.mother.parentItem().data

        if input_data.operator is not None:
            self.state = Node.FAIL
            self.update()
            if input_data.operator == operations.MEAN:
                self.message = 'Failed: the input data is already the result of Compute Mean.'
                return
            else:
                self.message = 'Failed: the input data is already the result of another computation.'
                return

        self.data = input_data.copy()
        self.data.operator = operations.MEAN
        self.state = Node.SUCCESS
        self.update()
        self.message = 'Successful.'


class ArrivalDurationNode(OneInOneOutNode):
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Calculations'
        self.label = 'Compute\nArrival\nDuration'
        self.out_port.data_type = 'csv'
        self.in_port.data_type = 'slf'
        self.in_data = None
        self.data = None

        self.conditions = []
        self.table = []
        self.time_unit = 'second'
        self.new_conditions = []
        self.new_options = tuple()

        self.units = ['second', 'minute', 'hour', 'day', 'percentage']
        self.condition_table = None
        self.unit_box = None

    def get_option_panel(self):
        add_button = QPushButton('Add new condition')
        add_button.setFixedSize(135, 50)

        self.condition_table = QTableWidget()
        self.condition_table.setColumnCount(3)
        self.condition_table .setHorizontalHeaderLabels(['Condition', 'Arrival', 'Duration'])
        vh = self.condition_table .verticalHeader()
        vh.setSectionResizeMode(QHeaderView.Fixed)
        vh.setDefaultSectionSize(20)
        hh = self.condition_table .horizontalHeader()
        hh.setDefaultSectionSize(150)
        self.condition_table.setMaximumHeight(500)
        self.condition_table.cellChanged.connect(self._check_name)

        self.unit_box = QComboBox()
        for unit in self.units:
            self.unit_box.addItem(unit)
        self.unit_box.setCurrentIndex(self.units.index(self.time_unit))
        self.unit_box.setFixedHeight(30)
        self.unit_box.setMaximumWidth(150)

        self.new_conditions = self.conditions[:]
        if self.conditions:
            for line in self.table:
                row = self.condition_table.rowCount()
                self.condition_table.insertRow(row)
                condition_item = QTableWidgetItem(line[0])
                condition_item.setFlags(Qt.ItemIsEditable)
                self.condition_table.setItem(row, 0, condition_item)
                self.condition_table.setItem(row, 1, QTableWidgetItem(line[1]))
                self.condition_table.setItem(row, 2, QTableWidgetItem(line[2]))

        option_panel = QWidget()
        layout = QVBoxLayout()
        hlayout = QHBoxLayout()

        hlayout.addItem(QSpacerItem(50, 10))
        hlayout.addWidget(add_button)
        hlayout.setAlignment(add_button, Qt.AlignLeft)
        hlayout.addStretch()
        lb = QLabel('Double click on the cells to edit Arrival / Duration variable names')
        hlayout.addWidget(lb)
        hlayout.setAlignment(lb, Qt.AlignBottom | Qt.AlignRight)
        layout.addLayout(hlayout)
        layout.addItem(QSpacerItem(1, 5))
        layout.addWidget(self.condition_table)
        layout.addItem(QSpacerItem(1, 10))
        hlayout = QHBoxLayout()
        hlayout.addItem(QSpacerItem(50, 10))
        hlayout.addWidget(QLabel('Time unit'))
        hlayout.addWidget(self.unit_box, Qt.AlignLeft)
        hlayout.addStretch()
        hlayout.setAlignment(Qt.AlignLeft)
        layout.addLayout(hlayout)
        option_panel.setLayout(layout)
        add_button.clicked.connect(self._add)
        option_panel.destroyed.connect(self._select)
        return option_panel

    def _current_names(self, ignore_row, ignore_column):
        names = []
        for row in range(self.condition_table.rowCount()):
            for column in range(1, 3):
                if row == ignore_row and column == ignore_column:
                    continue
                item = self.condition_table.item(row, column)
                if item is not None:
                    names.append(item.text())
        return names

    def _current_conditions(self):
        conditions = []
        for row in range(self.condition_table.rowCount()):
            conditions.append(self.condition_table.item(row, 0).text())
        return conditions

    def _check_name(self, row, column):
        if column == 1 or column == 2:
            name = self.condition_table.item(row, column).text()
            if len(name) < 2 or len(name) > 16:
                QMessageBox.critical(None, 'Error', 'The variable names should be between 2 and 16 characters!',
                                     QMessageBox.Ok)
            elif ',' in name or '|' in name:
                QMessageBox.critical(None, 'Error', 'The variable names should not contain comma or vertical bar.',
                                     QMessageBox.Ok)
            elif name in self._current_names(row, column):
                QMessageBox.critical(None, 'Error', 'Duplicated name.',
                                     QMessageBox.Ok)
            else:
                return
            # back to default
            condition = self.condition_table.item(row, 0).text()
            condition_tight = operations.tighten_expression(condition)
            if column == 1:
                self.condition_table.setItem(row, column, QTableWidgetItem(('A ' + condition_tight)[:16]))
            else:
                self.condition_table.setItem(row, column, QTableWidgetItem(('D ' + condition_tight)[:16]))

    def _add(self):
        parent_node = self.in_port.mother.parentItem()
        available_vars = [var for var in parent_node.data.header.var_IDs if var in parent_node.data.selected_vars]
        available_var_names = [parent_node.data.selected_vars_names[var][0] for var in available_vars]

        dlg = ConditionDialog(available_vars, available_var_names)
        value = dlg.exec_()
        if value == QDialog.Rejected:
            return
        condition = str(dlg.condition)
        if condition in self._current_conditions():
            QMessageBox.critical(None, 'Error', 'This condition is already added!',
                                 QMessageBox.Ok)
            return
        condition_tight = operations.tighten_expression(condition)
        self.new_conditions.append(dlg.condition)

        row = self.condition_table.rowCount()
        self.condition_table.insertRow(row)
        condition_item = QTableWidgetItem(condition)
        condition_item.setFlags(Qt.ItemIsEditable)
        self.condition_table.setItem(row, 0, condition_item)
        self.condition_table.setItem(row, 1, QTableWidgetItem(('A ' + condition_tight)[:16]))
        self.condition_table.setItem(row, 2, QTableWidgetItem(('D ' + condition_tight)[:16]))

    def _select(self):
        table = []
        for row in range(self.condition_table.rowCount()):
            row_condition = []
            for j in range(3):
                row_condition.append(self.condition_table.item(row, j).text())
            table.append(row_condition)
        time_unit = self.unit_box.currentText()
        self.new_options = (self.new_conditions, table, time_unit)

    def _current_needed_vars(self):
        vars = set()
        for condition in self.conditions:
            expression = condition.expression
            for item in expression:
                if item[0] == '[':
                    vars.add(item[1:-1])
        return vars

    def _reset(self):
        self.in_data = self.in_port.mother.parentItem().data
        if not self.conditions:
            self.state = Node.NOT_CONFIGURED
            self.reconfigure_downward()
            self.update()
            return
        available_vars = [var for var in self.in_data.selected_vars if var in self.in_data.header.var_IDs]
        current_vars = self._current_needed_vars()
        if all([var in available_vars for var in current_vars]):
            self.state = Node.READY
        else:
            self.state = Node.NOT_CONFIGURED
            self.conditions = []
            self.table = []
        self.reconfigure_downward()
        self.update()

    def add_link(self, link):
        self.links.add(link)

        if not self.in_port.has_mother():
            return
        parent_node = self.in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            if parent_node.state != Node.SUCCESS:
                return
        self._reset()

    def reconfigure(self):
        super().reconfigure()
        if self.in_port.has_mother():
            parent_node = self.in_port.mother.parentItem()
            if parent_node.ready_to_run():
                parent_node.run()
                if parent_node.state == Node.SUCCESS:
                    self._reset()
                    return
        self.in_data = None
        self.state = Node.NOT_CONFIGURED
        self.reconfigure_downward()
        self.update()

    def configure(self):
        if not self.in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return

        parent_node = self.in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        self._reset()
        if super().configure():
            self.conditions, self.table, self.time_unit = self.new_options
        self.reconfigure_downward()

    def save(self):
        table = []
        for line in self.table:
            for j in range(3):
                table.append(line[j])
        return '|'.join([self.category, self.name(), str(self.index()),
                         str(self.pos().x()), str(self.pos().y()),
                         ','.join(map(repr, self.conditions)), ','.join(table), self.time_unit])

    def load(self, options):
        conditions, table, time_unit = options
        table = table.split(',')
        for i in range(int(len(table)/3)):
            line = []
            for j in range(3):
                line.append(table[3*i+j])
            self.table.append(line)
        conditions = conditions.split(',')
        for i, condition in zip(range(len(self.table)), conditions):
            literal = self.table[i][0]
            condition = condition.split()
            expression = condition[:-2]
            comparator = condition[-2]
            threshold = float(condition[-1])
            self.conditions.append(operations.Condition(expression, literal, comparator, threshold))
        self.time_unit = time_unit

    def run(self):
        #TODO TODO
        success = super().run_upward()
        if not success:
            self.state = Node.FAIL
            self.update()
            self.message = 'Failed: input failed.'
            return
        self.state = Node.FAIL
        self.update()
        self.message = 'Failed: not implemented yet.'

        # self.in_data = self.in_port.mother.parentItem().data
        #
        # self.state = Node.SUCCESS
        # self.update()
        # self.message = 'Successful.'


class ComputeVolumeNode(TwoInOneOutNode):
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Calculations'
        self.label = 'Compute\nVolume'
        self.out_port.data_type = 'csv'
        self.first_in_port.data_type = 'slf'
        self.second_in_port.data_type = 'polygon'
        self.in_data = None
        self.data = None

        self.first_var = None
        self.second_var = None
        self.sup_volume = False
        self.new_options = tuple()

        self.first_var_box = None
        self.second_var_box = None
        self.sup_volume_box = None

    def get_option_panel(self):
        self.first_var_box = QComboBox()
        self.first_var_box.setFixedSize(400, 30)
        self.second_var_box = QComboBox()
        self.second_var_box.setFixedSize(400, 30)
        self.sup_volume_box = QCheckBox('Compute positive and negative volumes (slow)', None)

        self.second_var_box.addItem('0')
        self.second_var_box.addItem('Initial values of the first variable')

        available_vars = [var for var in self.in_data.header.var_IDs if var in self.in_data.selected_vars]
        for var_ID, var_name in zip(self.in_data.header.var_IDs, self.in_data.header.var_names):
            if var_ID not in available_vars:
                continue
            self.first_var_box.addItem(var_ID + ' (%s)' % var_name.decode('utf-8').strip())
            self.second_var_box.addItem(var_ID + ' (%s)' % var_name.decode('utf-8').strip())
        if self.first_var is not None:
            self.first_var_box.setCurrentIndex(available_vars.index(self.first_var))
        if self.second_var is not None:
            if self.second_var == VolumeCalculator.INIT_VALUE:
                self.second_var_box.setCurrentIndex(1)
            else:
                self.second_var_box.setCurrentIndex(2 + available_vars.index(self.second_var))
        self.sup_volume_box.setChecked(self.sup_volume)

        option_panel = QWidget()
        glayout = QGridLayout()
        glayout.addWidget(QLabel('     Select the principal variable'), 1, 1)
        glayout.addWidget(self.first_var_box, 1, 2)
        glayout.addWidget(QLabel('     Select a variable to subtract (optional)'), 2, 1)
        glayout.addWidget(self.second_var_box, 2, 2)
        glayout.addWidget(QLabel('     Positive / negative volumes'), 3, 1)
        glayout.addWidget(self.sup_volume_box, 3, 2)
        option_panel.setLayout(glayout)
        option_panel.destroyed.connect(self._select)
        return option_panel

    def _select(self):
        first_var = self.first_var_box.currentText().split('(')[0][:-1]
        second_var = self.second_var_box.currentText()
        if second_var == '0':
            second_var = None
        elif '(' in second_var:
            second_var = second_var.split('(')[0][:-1]
        else:
            second_var = VolumeCalculator.INIT_VALUE
        sup_volume = self.sup_volume_box.isChecked()
        self.new_options = (first_var, second_var, sup_volume)

    def _reset(self):
        self.in_data = self.first_in_port.mother.parentItem().data
        if self.first_var is None:
            return
        available_vars = [var for var in self.in_data.selected_vars if var in self.in_data.header.var_IDs]
        if self.first_var not in available_vars:
            self.first_var = None
            self.state = Node.NOT_CONFIGURED
        elif self.state == Node.NOT_CONFIGURED:
            self.state = Node.READY
        if self.second_var is not None and self.second_var != VolumeCalculator.INIT_VALUE:
            if self.second_var not in available_vars:
                self.second_var = None
                self.state = Node.NOT_CONFIGURED
        self.reconfigure_downward()
        self.update()

    def add_link(self, link):
        self.links.add(link)

        if not self.first_in_port.has_mother():
            return
        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            if parent_node.state != Node.SUCCESS:
                return
        self._reset()

    def reconfigure(self):
        super().reconfigure()
        if self.first_in_port.has_mother():
            parent_node = self.first_in_port.mother.parentItem()
            if parent_node.ready_to_run():
                parent_node.run()
                if parent_node.state == Node.SUCCESS:
                    self._reset()
                    return
        self.in_data = None
        self.state = Node.NOT_CONFIGURED
        self.reconfigure_downward()
        self.update()

    def configure(self):
        if not self.first_in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return

        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        self._reset()
        if super().configure():
            self.first_var, self.second_var, self.sup_volume = self.new_options
        self.reconfigure_downward()

    def save(self):
        first = '' if self.first_var is None else self.first_var
        second = '' if self.second_var is None else self.second_var
        return '|'.join([self.category, self.name(), str(self.index()),
                         str(self.pos().x()), str(self.pos().y()),
                         first, second, str(int(self.sup_volume))])

    def load(self, options):
        first, second, sup = options
        if first:
            self.first_var = first
        if second:
            self.second_var = second
        self.sup_volume = bool(int(sup))

    def run(self):
        success = super().run_upward()
        if not success:
            self.state = Node.FAIL
            self.update()
            self.message = 'Failed: input failed.'
            return

        self.progress_bar.setVisible(True)
        self.in_data = self.first_in_port.mother.parentItem().data
        polygons = self.second_in_port.mother.parentItem().data
        polygon_names = ['Polygon %d' % (i+1) for i in range(len(polygons))]
        if self.sup_volume:
            volume_type = VolumeCalculator.POSITIVE
        else:
            volume_type = VolumeCalculator.NET

        mesh = TruncatedTriangularPrisms(self.in_data.header, False)

        if self.in_data.has_index:
            mesh.index = self.in_data.index
            mesh.triangles = self.in_data.triangles
        else:
            self.construct_mesh(mesh)
            self.in_data.has_index = True
            self.in_data.index = mesh.index
            self.in_data.triangles = mesh.triangles

        with Serafin.Read(self.in_data.filename, self.in_data.language) as resin:
            resin.header = self.in_data.header
            resin.time = self.in_data.time

            calculator = VolumeCalculator(volume_type, self.first_var, self.second_var, resin,
                                          polygon_names, polygons, 1)
            calculator.time_indices = self.in_data.selected_time_indices
            calculator.mesh = mesh
            calculator.construct_weights()

            self.data = [calculator.get_csv_header()]

            for i, time_index in enumerate(calculator.time_indices):
                i_result = [str(calculator.input_stream.time[time_index])]
                values = calculator.read_values_in_frame(time_index)

                for j in range(len(calculator.polygons)):
                    weight = calculator.weights[j]
                    volume = calculator.volume_in_frame_in_polygon(weight, values, calculator.polygons[j])
                    if calculator.volume_type == VolumeCalculator.POSITIVE:
                        for v in volume:
                            i_result.append('%.6f' % v)
                    else:
                        i_result.append('%.6f' % volume)
                self.data.append(i_result)

                self.progress_bar.setValue(100 * (i+1) / len(calculator.time_indices))
                QApplication.processEvents()

        self.state = Node.SUCCESS
        self.update()
        self.message = 'Successful.'
        self.progress_bar.setVisible(False)


class ComputeFluxNode(TwoInOneOutNode):
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Calculations'
        self.label = 'Compute\nFlux'
        self.out_port.data_type = 'csv'
        self.first_in_port.data_type = 'slf'
        self.second_in_port.data_type = 'polyline 2d'
        self.in_data = None
        self.data = None

        self.flux_options = ''
        self.new_options = ''

        self.flux_type_box = None

    def get_option_panel(self):
        option_panel = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(QLabel('     Select the flux to compute'))
        layout.addWidget(self.flux_type_box)
        option_panel.setLayout(layout)
        option_panel.destroyed.connect(self._select)
        return option_panel

    def _select(self):
        self.new_options = self.flux_type_box.currentText()

    def _prepare_flux_options(self, available_vars, available_var_names):
        self.flux_type_box = QComboBox()
        self.flux_type_box.setFixedSize(400, 30)
        if 'U' in available_vars and 'V' in available_vars:
            if 'H' in available_vars:
                self.flux_type_box.addItem('Liquid flux (m3/s): (U, V, H)')
                for name in available_var_names:
                    str_name = name.decode('utf-8').strip()
                    if 'TRACEUR' in str_name or 'TRACER' in str_name:
                        self.flux_type_box.addItem('Solid flux (kg/s): (U, V, H, %s)' % str_name)
        if 'I' in available_vars and 'J' in available_vars:
            self.flux_type_box.addItem('Liquid flux (m3/s): (I, J)')
        if 'H' in available_vars and 'M' in available_vars:
            self.flux_type_box.addItem('Liquid flux (m3/s): (M, H)')
        if 'Q' in available_vars:
            self.flux_type_box.addItem('Liquid flux (m3/s): (Q)')

        if 'QSX' in available_vars and 'QSY' in available_vars:
            self.flux_type_box.addItem('Solid flux TOTAL (m3/s): (QSX, QSY)')
        if 'QS' in available_vars:
            self.flux_type_box.addItem('Solid flux TOTAL (m3/s): (QS)')
        if 'QSBLX' in available_vars and 'QSBLY' in available_vars:
            self.flux_type_box.addItem('Solid flux BEDLOAD (m3/s): (QSBLX, QSBLY)')
        if 'QSBL' in available_vars:
            self.flux_type_box.addItem('Solid flux BEDLOAD (m3/s): (QSBL)')
        if 'QSSUSPX' in available_vars and 'QSSUSPY' in available_vars:
            self.flux_type_box.addItem('Solid flux SUSPENSION (m3/s): (QSSUSPX, QSSUSPY)')
        if 'QSSUSP' in available_vars:
            self.flux_type_box.addItem('Solid flux SUSPENSION (m3/s): (QSSUSP)')

        for name in available_var_names:
            str_name = name.decode('utf-8').strip()
            if 'QS CLASS' in str_name:
                self.flux_type_box.addItem('Solid flux TOTAL (m3/s): (%s)' % str_name)
            if 'QS BEDLOAD CL' in str_name:
                self.flux_type_box.addItem('Solid flux BEDLOAD (m3/s): (%s)' % str_name)
            if 'QS SUSP. CL' in str_name:
                self.flux_type_box.addItem('Solid flux SUSPENSION (m3/s): (%s)' % str_name)

        return self.flux_type_box.count() > 0

    def _reset(self):
        self.in_data = self.first_in_port.mother.parentItem().data
        if self.flux_options:
            for i in range(self.flux_type_box.count()):
                text = self.flux_type_box.itemText(i)
                if text == self.flux_options:
                    self.flux_type_box.setCurrentIndex(i)
                    self.state = Node.READY
                    self.update()
                    return
            self.state = Node.NOT_CONFIGURED
        else:
            self.state = Node.READY
        self.reconfigure_downward()
        self.update()

    def add_link(self, link):
        self.links.add(link)

        if not self.first_in_port.has_mother():
            return
        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            if parent_node.state != Node.SUCCESS:
                return
        available_vars = [var for var in parent_node.data.header.var_IDs if var in parent_node.data.selected_vars]
        available_var_names = [parent_node.data.selected_vars_names[var][0] for var in available_vars]
        has_options = self._prepare_flux_options(available_vars, available_var_names)
        if has_options:
            self._reset()
        else:
            self.state = Node.NOT_CONFIGURED
            self.update()

    def reconfigure(self):
        super().reconfigure()
        if self.first_in_port.has_mother():
            parent_node = self.first_in_port.mother.parentItem()
            if parent_node.ready_to_run():
                parent_node.run()
                if parent_node.state == Node.SUCCESS:
                    available_vars = [var for var in parent_node.data.header.var_IDs
                                      if var in parent_node.data.selected_vars]
                    available_var_names = [parent_node.data.selected_vars_names[var][0] for var in available_vars]
                    has_options = self._prepare_flux_options(available_vars, available_var_names)
                    if has_options:
                        self._reset()
                        return
        self.in_data = None
        self.state = Node.NOT_CONFIGURED
        self.reconfigure_downward()
        self.update()

    def configure(self):
        if not self.first_in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return

        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        available_vars = [var for var in parent_node.data.header.var_IDs if var in parent_node.data.selected_vars]
        available_var_names = [parent_node.data.selected_vars_names[var][0] for var in available_vars]
        has_options = self._prepare_flux_options(available_vars, available_var_names)
        if not has_options:
            QMessageBox.critical(None, 'Error', 'No flux is computable from the input file.',
                                 QMessageBox.Ok)
            return
        self._reset()
        if super().configure():
            self.flux_options = self.new_options
        self.reconfigure_downward()

    def save(self):
        return '|'.join([self.category, self.name(), str(self.index()),
                         str(self.pos().x()), str(self.pos().y()),
                         self.flux_options])

    def load(self, options):
        self.flux_options = options[0]

    def run(self):
        success = super().run_upward()
        if not success:
            self.state = Node.FAIL
            self.update()
            self.message = 'Failed: input failed.'
            return

        self.progress_bar.setVisible(True)
        self.in_data = self.first_in_port.mother.parentItem().data
        sections = self.second_in_port.mother.parentItem().data
        section_names = ['Section %d' % (i+1) for i in range(len(sections))]

        var_IDs = list(self.flux_options.split(':')[1].split('(')[1][:-1].split(', '))
        nb_vars = len(var_IDs)
        if nb_vars == 1:
            flux_type = FluxCalculator.LINE_INTEGRAL
        elif nb_vars == 2:
            if var_IDs[0] == 'M':
                flux_type = FluxCalculator.DOUBLE_LINE_INTEGRAL
            else:
                flux_type = FluxCalculator.LINE_FLUX
        elif nb_vars == 3:
            flux_type = FluxCalculator.AREA_FLUX
        else:
            flux_type = FluxCalculator.MASS_FLUX
        pass
        mesh = TriangularVectorField(self.in_data.header, False)

        if self.in_data.has_index:
            mesh.index = self.in_data.index
            mesh.triangles = self.in_data.triangles
        else:
            self.construct_mesh(mesh)
            self.in_data.has_index = True
            self.in_data.index = mesh.index
            self.in_data.triangles = mesh.triangles

        with Serafin.Read(self.in_data.filename, self.in_data.language) as resin:
            resin.header = self.in_data.header
            resin.time = self.in_data.time

            calculator = FluxCalculator(flux_type, var_IDs,
                                        resin, section_names, sections, 1)
            calculator.time_indices = self.in_data.selected_time_indices
            calculator.mesh = mesh
            calculator.construct_intersections()

            self.data = [['time'] + section_names]

            for i, time_index in enumerate(calculator.time_indices):
                i_result = [str(calculator.input_stream.time[time_index])]
                values = []
                for var_ID in calculator.var_IDs:
                    values.append(calculator.input_stream.read_var_in_frame(time_index, var_ID))

                for j in range(len(calculator.sections)):
                    intersections = calculator.intersections[j]
                    flux = calculator.flux_in_frame(intersections, values)
                    i_result.append('%.6f' % flux)
                self.data.append(i_result)

                self.progress_bar.setValue(100 * (i+1) / len(calculator.time_indices))
                QApplication.processEvents()

        self.state = Node.SUCCESS
        self.update()
        self.message = 'Successful.'
        self.progress_bar.setVisible(False)