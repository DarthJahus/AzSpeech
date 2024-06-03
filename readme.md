# AzSpeech

Simple Azure Text-to-speech.

You can copy text, call script, hear the speech. This simple.

A GUI is available, if using clipboard is not what you want.

## `config.json` example:

    {
        "SPEECH_KEY": "bdxxxxxxxxxxxxxxxxxxxxxxxxxxxxa5",
        "SPEECH_REGION": "eastus",
        "SPEECH_VOICE": "en-US-EmmaMultilingualNeural",
        "OUT_FILE": false,
        "READ_FILE": false
    }

- `SPEECH_KEY`: Your Azure service key.
- `SPEECH_REGION`: Region your Azure service runs in.
- `SPEECH_VOICE`: Voice name.
- `OUT_FILE`:
  - if `false`, the speech will be read through the default sound device;
  - You can set `OUT_FILE` to the name of the output file (example: `rec.wav`);
  - if `true`, the speech will be saved to a file named `AzSpeech %Y-%m-%d_%H-%M-%S.wav` (example: `AzSpeech 2024-06-03_18-22-04.wav`).
- `READ_FILE`: set `true` if you want the saved file to be opened with the default program for `.wav` format (example: Media Player).

Note:
 - In `.res/azure.json`, you will find a list of regions (this list may be outdated. Make sure to set the correct region for your service).
 - `.res/azure.json` lists some Multilingual Neural voices. These are the *best*, and the most fit for most languages.
 - Microsoft Azure offers many other voices. Check out [Language and voice support for the Speech service](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts) on Microsoft Learn for a comprehensive list.
 - In a production environment, you should use the API to get a list of regions / voices, instead of a static file.
