import sys, os
from speech_ui import Ui_MainWindow
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar, QFileDialog
from azure.cognitiveservices.speech import SpeechConfig, audio, SpeechSynthesizer, ResultReason, CancellationReason
import json
from winsound import Beep
from os.path import expanduser


__config = dict()
__azure = dict()


def load_files():
    global __config, __azure
    try:
        with open("config.json", 'r', encoding="utf-8") as _f:
            __config = json.loads(_f.read())
    except:
        print("Error reading config file. Make sure config.json is at ./")
    try:
        with open(os.path.join(os.path.dirname(__file__), ".res/azure.json"), 'r', encoding="utf-8") as _f:
            __azure = json.loads(_f.read())
    except:
        print("Error reading Azure file. Make sure azure.json is at ./.res/")
        exit(1)


def save_config():
    global __config
    with open("config.json", 'w', encoding="utf-8") as _f:
        try:
            _f.write(json.dumps(__config, indent="  "))
            return True
        except:
            return False


def set_config(element, new_value):
    global __config
    # ToDo: Validity check?
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
        # set title, icon and size
        self.setWindowTitle("Text-to-Speech from Azure")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), ".res/icon.ico")))
        # set button actions
        self.statusBar().showMessage("Loading...")
        self.init_settings()
        self.statusBar().showMessage("Ready.")
        self.ui.btnReadAloud.clicked.connect(self.btnReadAloud_clicked)
        self.ui.txtKey.textChanged.connect(self.txtKey_changed)
        self.ui.btnSaveSettings.clicked.connect(self.btnSave_clicked)
        self.ui.cmbRegion.currentIndexChanged.connect(self.cmbRegion_changed)
        self.ui.txtMain.textChanged.connect(self.txtMain_changed)
        self.ui.cmbVoice.currentIndexChanged.connect(self.cmbVoice_changed)
        self.ui.btnRec.clicked.connect(self.btnRec_clicked)

    def init_settings(self):
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
        if speech(
            key=self.ui.txtKey.text().strip(),
            region=self.ui.cmbRegion.currentData(),
            voice=self.ui.cmbVoice.currentData(),
            text=self.ui.txtMain.toPlainText().strip(),
            callback=self.statusBar(),
            file=_file_name[0]
        ):
            if self.settings_changed():
                self.ui.btnSaveSettings.setEnabled(True)
        self.can_read(False)

    def btnReadAloud_clicked(self):
        if speech(
            key=self.ui.txtKey.text().strip(),
            region=self.ui.cmbRegion.currentData(),
            voice=self.ui.cmbVoice.currentData(),
            text=self.ui.txtMain.toPlainText().strip(),
            callback=self.statusBar()
        ):
            if self.settings_changed():
                self.ui.btnSaveSettings.setEnabled(True)
        self.can_read(False)

    def btnSave_clicked(self):
        if self.validate_settings():
            set_config("SPEECH_KEY", self.ui.txtKey.text().strip())
            set_config("SPEECH_REGION", self.ui.cmbRegion.currentData())
            set_config("SPEECH_VOICE", self.ui.cmbVoice.currentData())
            if save_config():
                self.settings_changed(False)
                self.ui.btnSaveSettings.setEnabled(False)

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
        if changed is None:
            return self.windowTitle()[0] == '*'  # ToDo: Use a variable for this instead of checking for the Asterix

        if changed:
            if self.windowTitle()[0] != '*':
                self.setWindowTitle('*' + self.windowTitle())
        else:
            if self.windowTitle()[0] == '*':
                self.setWindowTitle(self.windowTitle()[1:])
            self.ui.lblKey.setStyleSheet("color: black;")
            self.ui.lblRegion.setStyleSheet("color: black;")
            self.ui.lblVoice.setStyleSheet("color: black;")

    def txtMain_changed(self):
        self.validate_read()

    def can_read(self, value: bool = None):
        if value is None:
            return self.ui.btnReadAloud.isEnabled()
        else:
            self.ui.btnReadAloud.setEnabled(value)
            self.ui.btnRec.setEnabled(value)

    def validate_settings(self):
        if self.ui.txtKey.text().strip() and self.ui.cmbRegion.currentData() and self.ui.cmbVoice.currentData():
            if len(self.ui.txtMain.toPlainText().strip()) != 0:
                return True
        return False

    def validate_read(self):
        if not self.can_read():
            if self.validate_settings():
                self.can_read(True)


_app = QApplication([])
_window = GUI()
_window.show()


# ToDo: Read through another function and always save file to disk
# Todo: Show how much characters are left in Azure plan?

def speech(key, region, voice, text, callback: QStatusBar, file=None):
    speech_config = SpeechConfig(
        subscription=key,
        region=region
    )
    speech_config.speech_synthesis_voice_name = voice
    callback.showMessage("Reading...")
    audio_config = audio.AudioOutputConfig(
        use_default_speaker=not file,  # ToDo: allow choice of device
        filename=None if not file else file  # ToDo: Ask for filename
    )
    speech_synthesizer = SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    _speech = speech_synthesizer.speak_text_async(text).get()
    if _speech.reason == ResultReason.SynthesizingAudioCompleted:
        callback.showMessage("Speech synthesized.")
        return True
    elif _speech.reason == ResultReason.Canceled:
        callback.showMessage("Speech synthesis canceled: {}".format(_speech.cancellation_details.reason))
        if _speech.cancellation_details.reason == CancellationReason.Error:
            if _speech.cancellation_details.error_details:
                callback.showMessage("Error details: {}".format(_speech.cancellation_details.error_details))
        Beep(880, 500)
        return False


sys.exit(_app.exec())
