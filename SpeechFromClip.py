from azure.cognitiveservices.speech import SpeechConfig, audio, SpeechSynthesizer, ResultReason, CancellationReason
import pyperclip as clipboard
import json
from winsound import Beep
from subprocess import call
from platform import system
from os import startfile
from datetime import datetime


with open("config.json", 'r', encoding="utf-8") as _f:
    __config = json.loads(_f.read())
    if "OUT_FILE" not in __config:
        __config["OUT_FILE"] = False
    elif __config["OUT_FILE"] == True:  # check if True, not if not False:
        __config["OUT_FILE"] = "AzSpeech %s.wav" % datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if "READ_FILE" not in __config:
        __config["READ_FILE"] = False


speech_config = SpeechConfig(
    subscription=__config['SPEECH_KEY'],
    region=__config['SPEECH_REGION']
)
speech_config.speech_synthesis_voice_name = __config['SPEECH_VOICE']

audio_config = audio.AudioOutputConfig(
    use_default_speaker=not (__config["OUT_FILE"]),
    filename=None if not __config["OUT_FILE"] else __config["OUT_FILE"]
)
speech_synthesizer = SpeechSynthesizer(
    speech_config=speech_config,
    audio_config=audio_config
)


def open_file(file):
    # cf. https://stackoverflow.com/questions/434597
    if system() == 'Darwin':  # macOS
        call(('open', file))
    elif system() == 'Windows':  # Windows
        startfile(file)
    else:  # linux variants
        call(('xdg-open', file))
    pass


if __name__ == "__main__":
    _speech = speech_synthesizer.speak_text_async(clipboard.paste().strip()).get()
    if _speech.reason == ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized.")
        if __config["READ_FILE"] and __config["OUT_FILE"]:
            open_file(__config["OUT_FILE"])
        exit(0)
    elif _speech.reason == ResultReason.Canceled:
        print("Speech synthesis canceled: {}".format(_speech.cancellation_details.reason))
        if _speech.cancellation_details.reason == CancellationReason.Error:
            if _speech.cancellation_details.error_details:
                print("Error details: {}".format(_speech.cancellation_details.error_details))
    Beep(880, 500)
    input()
    exit(1)
