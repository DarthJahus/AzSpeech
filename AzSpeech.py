from sys import exit as sys_exit
from speech_ui import Ui_MainWindow
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar, QFileDialog
from azure.cognitiveservices.speech import SpeechConfig, audio, SpeechSynthesizer, ResultReason, CancellationReason
from json import loads as j_loads, dumps as j_dumps
from os.path import expanduser, dirname, join as path_join
from threading import Thread


__config = dict()
__azure = dict()
__speech_thread = Thread()


def load_files():
    global __config, __azure
    try:
        with open("config.json", 'r', encoding="utf-8") as _f:
            __config = j_loads(_f.read())
    except:
        print("Error reading config file. Make sure config.json is at ./")
    try:
        with open(path_join(dirname(__file__), ".res/azure.json"), 'r', encoding="utf-8") as _f:
            __azure = j_loads(_f.read())
    except:
        raise FileNotFoundError(f"Error reading Azure file. Make sure azure.json is at {dirname(__file__)}/.res/")


def save_config():
    global __config
    with open("config.json", 'w', encoding="utf-8") as _f:
        try:
            _f.write(j_dumps(__config, indent="  "))
            return True
        except:
            return False


def set_config(element, new_value):
    global __config
    __config[element] = new_value


def get_config(element, default):
    global __config
    if element in __config:
        return __config[element]
    return default


def get_azure(element):
    global __azure
    if element in __azure:
        return __azure[element]


class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # Loading...
        self.setWindowTitle("Text-to-Speech from Azure")
        self.setWindowIcon(QIcon(path_join(dirname(__file__), ".res/icon.ico")))
        self.statusBar().showMessage("Loading...")
        self.init_settings()
        self.statusBar().showMessage("Ready.")
        self.b_settings_changed = False
        # set button actions
        self.ui.btnReadAloud.clicked.connect(self.btnReadAloud_clicked)
        self.ui.txtKey.textChanged.connect(self.txtKey_changed)
        self.ui.btnSaveSettings.clicked.connect(self.btnSave_clicked)
        self.ui.cmbRegion.currentIndexChanged.connect(self.cmbRegion_changed)
        self.ui.txtMain.textChanged.connect(self.txtMain_changed)
        self.ui.cmbVoice.currentIndexChanged.connect(self.cmbVoice_changed)
        self.ui.btnRec.clicked.connect(self.btnRec_clicked)
        self.ui.btnStop.clicked.connect(self.btnStop_clicked)

    def init_settings(self):
        self.ui.btnStop.setVisible(False)
        load_files()
        self.can_read(False)
        # populate regions and voices
        for _region in get_azure("regions"):
            self.ui.cmbRegion.addItem(_region["regionName"], _region["regionCode"])
        for _voice in get_azure("voices"):
            self.ui.cmbVoice.addItem(
                "%s %s" % (_voice["voiceName"], "♀" if _voice["voiceSex"].lower() == "male" else "♂"),
                _voice["voiceCode"]
            )
        # set defaults
        self.ui.txtKey.setText(get_config("SPEECH_KEY", None))
        self.ui.cmbRegion.setCurrentIndex(self.ui.cmbRegion.findData(get_config("SPEECH_REGION", None)))
        self.ui.cmbVoice.setCurrentIndex(self.ui.cmbVoice.findData(get_config("SPEECH_VOICE", None)))

    def btnRec_clicked(self):
        _file_name = QFileDialog.getSaveFileName(self, "Save as...", expanduser("~"), "Waveform audio (*.wav)")
        try:
            # interesting talk: https://stackoverflow.com/questions/9532499
            open(_file_name[0], 'w')
        except:
            _file_name = ("rec.wav", "*.wav")
        speech(
            key=self.ui.txtKey.text().strip(),
            region=self.ui.cmbRegion.currentData(),
            voice=self.ui.cmbVoice.currentData(),
            text=self.ui.txtMain.toPlainText().strip(),
            callback=self.statusBar(),
            file=_file_name[0]
        )
        self.can_read(False)

    def set_reading(self, value: bool, status, success: bool = None):
        self.ui.btnStop.setVisible(value)
        self.ui.btnRec.setVisible(not value)
        self.ui.btnReadAloud.setVisible(not value)
        self.statusBar().showMessage(status)
        self.ui.txtKey.setEnabled(not value)
        self.ui.cmbRegion.setEnabled(not value)
        self.ui.cmbVoice.setEnabled(not value)
        self.ui.txtMain.setEnabled(not value)
        if not value:
            if success:
                if self.settings_changed():
                    self.ui.btnSaveSettings.setEnabled(True)

    def btnReadAloud_clicked(self):
        speech(
            key=self.ui.txtKey.text().strip(),
            region=self.ui.cmbRegion.currentData(),
            voice=self.ui.cmbVoice.currentData(),
            text=self.ui.txtMain.toPlainText().strip(),
            callback=self.set_reading
        )
        self.can_read(False)

    def btnSave_clicked(self):
        if self.pre_validate_settings():
            set_config("SPEECH_KEY", self.ui.txtKey.text().strip())
            set_config("SPEECH_REGION", self.ui.cmbRegion.currentData())
            set_config("SPEECH_VOICE", self.ui.cmbVoice.currentData())
            if save_config():
                self.settings_changed(False)

    def txtKey_changed(self):
        self.ui.lblKey.setStyleSheet("color: red;")
        self.settings_changed(True)
        self.validate_read()

    def cmbRegion_changed(self):
        self.ui.lblRegion.setStyleSheet("color: red;")
        self.settings_changed(True)
        self.validate_read()

    def cmbVoice_changed(self):
        self.ui.lblVoice.setStyleSheet("color: red;")
        self.settings_changed(True)
        self.validate_read()

    def settings_changed(self, changed: bool = None):
        self.ui.btnSaveSettings.setEnabled(False)
        if changed is None:
            return self.b_settings_changed
        if changed:
            if self.windowTitle()[0] != '*':
                self.setWindowTitle('*' + self.windowTitle())
            self.b_settings_changed = True
        else:
            if self.windowTitle()[0] == '*':
                self.setWindowTitle(self.windowTitle()[1:])
            self.ui.lblKey.setStyleSheet("color: black;")
            self.ui.lblRegion.setStyleSheet("color: black;")
            self.ui.lblVoice.setStyleSheet("color: black;")
            self.b_settings_changed = False

    def txtMain_changed(self):
        self.validate_read()

    def can_read(self, value: bool = None):
        if value is None:
            return self.ui.btnReadAloud.isEnabled()
        else:
            self.ui.btnReadAloud.setEnabled(value)
            self.ui.btnRec.setEnabled(value)

    def pre_validate_settings(self):
        if self.ui.txtKey.text().strip() and self.ui.cmbRegion.currentData() and self.ui.cmbVoice.currentData():
            if len(self.ui.txtMain.toPlainText().strip()) != 0:
                return True
        return False

    def validate_read(self):
        if not self.can_read():
            if self.pre_validate_settings():
                self.can_read(True)

    def btnStop_clicked(self):
        stop_speech()


_app = QApplication([])
_window = GUI()
_window.show()


class SpeechThread(Thread):
    def __init__(self, speech_synthesizer, text, callback):
        super().__init__()
        self.speech_synthesizer = speech_synthesizer
        self.text = text
        self.callback = callback
        self.stopped = False

    def run(self):
        _speech = self.speech_synthesizer.speak_text_async(self.text).get()
        if _speech.reason == ResultReason.SynthesizingAudioCompleted:
            self.callback(False, "Speech synthesis completed." if not self.stopped else "Speech stopped!", success=True)
        elif _speech.reason == ResultReason.Canceled:
            self.callback(False, "Speech synthesis canceled: {}".format(_speech.cancellation_details.reason))
            if _speech.cancellation_details.reason == CancellationReason.Error:
                if _speech.cancellation_details.error_details:
                    self.callback(False, "Error: {}".format(_speech.cancellation_details.error_details), success=False)

    def stop(self):
        self.stopped = True
        self.speech_synthesizer.stop_speaking_async()


def speech(key, region, voice, text, callback, file=None):
    global __speech_thread

    speech_config = SpeechConfig(
        subscription=key,
        region=region
    )
    speech_config.speech_synthesis_voice_name = voice
    callback(True, "Reading...", False)
    audio_config = audio.AudioOutputConfig(
        use_default_speaker=not file,  # ToDo: allow choice of device
        filename=None if not file else file  # ToDo: Ask for filename
    )
    speech_synthesizer = SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    __speech_thread = SpeechThread(speech_synthesizer, text, callback)
    __speech_thread.start()


def stop_speech():
    global __speech_thread
    __speech_thread.stop()
    __speech_thread.join()


sys_exit(_app.exec())
