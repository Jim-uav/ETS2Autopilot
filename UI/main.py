from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5 import QtCore
from UI.ui_main import Ui_MainWindow
from UI.settings import SettingsUI
from UI.sequence import SequenceUI
from database import Settings, Data
from thread_controller import ControllerThread
from thread_autopilot import AutopilotThread
from thread_recording import RecordingThread
from thread_training import TrainingThread
import sys


class MainUI(object):
    def __init__(self):
        self.window = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)

        # Register other windows
        self.settings_ui = SettingsUI()
        self.sequence_ui = SequenceUI()

        # Define thread variables
        self.thread_controller = None
        self.thread_training = None
        self.thread_autopilot = None
        self.thread_recording = None

        # Register buttons and stuff
        self.ui.actionSettings.triggered.connect(self.settings_ui.show)
        self.ui.actionExit.triggered.connect(sys.exit)
        self.ui.actionAbout.triggered.connect(self.show_info)

        self.ui.b_sequenceApply.clicked.connect(self.append_sequence_changes)
        self.ui.b_sequenceDetails.clicked.connect(self.show_sequence_details)
        self.ui.b_sequenceDelete.clicked.connect(self.delete_selected_sequence)
        self.ui.sequence_list.clicked.connect(self.fill_sequence_data_fields)

        self.ui.b_mode.clicked.connect(self.enter_mode)

        self.fill_sequence_list()

        # Try to start controller thread
        if Settings().get_value(Settings.CONTROLLER) is not None and Settings().get_value(Settings.VJOY_DEVICE) is not None:
            self.thread_controller = ControllerThread()
            self.thread_controller.start()

    def show(self):
        self.window.show()

    def hide(self):
        pass

    def show_info(self):
        """
        actionAbout:
        Show window with program info.
        """
        pass

    def _get_selected_sequence(self):
        selection_list = self.ui.sequence_list.selectedIndexes()
        if len(selection_list) > 0:
            return selection_list[0].data(QtCore.Qt.UserRole)
        else:
            return None

    def fill_sequence_list(self):
        """
        Fill sequence_list with data.
        """
        data = Data()
        sequence_list = self.ui.sequence_list

        model = QStandardItemModel(sequence_list)
        sequences = data.get_sequence_list()
        if len(sequences) > 0:
            for sequence in sequences:
                item = QStandardItem(sequence[1])
                item.setEditable(False)
                item.setData(str(sequence[0]), QtCore.Qt.UserRole)
                model.appendRow(item)
        sequence_list.setModel(model)

    def fill_sequence_data_fields(self):
        """
        Set text of e_country and choose right cb_roadtype.
        """
        sid = self._get_selected_sequence()
        if sid:
            sequence_data = Data().get_sequence_data(sid)
            if sequence_data:
                code = Data().get_country_code(sequence_data[1])
                self.ui.e_country.setText(code)
                self.ui.cb_roadtype.setCurrentIndex(sequence_data[2]+1)

    def append_sequence_changes(self):
        """
        b_sequenceApply:
        Update data of selected sequence.
        """
        sid = self._get_selected_sequence()
        code = self.ui.e_country.text()
        road_type = self.ui.cb_roadtype.currentIndex()-1
        Data().update_sequence(sid, code, road_type)

    def delete_selected_sequence(self):
        """
        b_sequenceDelete:
        Delete the selected sequence.
        """
        sid = self._get_selected_sequence()
        Data().delete_sequence(sid)
        self.fill_sequence_list()

    def show_sequence_details(self):
        """
        b_sequenceDetails:
        Show window with all images of the selected sequence.
        """
        sid = self._get_selected_sequence()
        if sid:
            self.sequence_ui.set_sequence_id(sid)
            self.sequence_ui.show()

    def fill_front_image(self):
        """
        Fill image_front.
        """
        pass

    def fill_steering_wheel(self):
        """
        Fill steering_wheel.
        """
        pass

    def enter_mode(self):
        """
        b_mode:
        Starts the autopilot, recording or training.
        """
        rb_autopilot = self.ui.mode_autopilot.isChecked()
        rb_recording = self.ui.mode_recording.isChecked()
        rb_training = self.ui.mode_training.isChecked()

        # Start the controller thread if it is not running
        if self.thread_controller is None:
            self.thread_controller = ControllerThread()
            self.thread_controller.start()
        else:
            if not self.thread_controller.is_running():
                self.thread_controller.start()

        # Start mode specific thread
        if rb_autopilot:
            self.thread_autopilot = AutopilotThread()
            self.thread_autopilot.start()
        elif rb_recording:
            self.thread_recording = RecordingThread()
            self.thread_recording.start()
        elif rb_training:
            self.thread_training = TrainingThread()
            self.thread_training.start()

        # Deactivate radio boxes while on mode is active
        self.ui.mode_autopilot.setEnabled(False)
        self.ui.mode_training.setEnabled(False)
        self.ui.mode_recording.setEnabled(False)

        self.ui.b_mode.clicked.connect(self.leave_mode)
        self.ui.b_mode.setText("Stop")

    def leave_mode(self):
        """
        b_mode:
        Stops the autopilot, recording or training.
        """
        rb_autopilot = self.ui.mode_autopilot.isChecked()
        rb_recording = self.ui.mode_recording.isChecked()
        rb_training = self.ui.mode_training.isChecked()

        # Stop mode specific thread
        if rb_autopilot:
            self.thread_autopilot.stop()
        elif rb_recording:
            self.thread_recording.stop()
        elif rb_training:
            self.thread_training.stop()

        self.ui.mode_autopilot.setEnabled(True)
        self.ui.mode_training.setEnabled(True)
        self.ui.mode_recording.setEnabled(True)

        self.ui.b_mode.clicked.connect(self.enter_mode)
        self.ui.b_mode.setText("Start")
