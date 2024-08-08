# MyChatGPT
The ultimate PyQt6 application featuring the power of OpenAI, Google Gemini, Claude, and various open-source AI models.

It delivers outstanding capabilities for Chat, Image, Vision, Text-To-Speech(TTS) and Speech-To-Text(STT).

## Quick Install

1. With pip:

```bash
pip install -r requirements.txt
```
Or 

```bash
python -m pip install -r requirements.txt
```

2. Run main.py

```bash
python main.py
```

## Quick Demo
[MyChatGPT Demo - OpenAI, Gemini, Claude, Ollama-English](https://www.youtube.com/watch?v=KCdJH2MLwWM)

[MyChatGPT Demo - OpenAI, Gemini, Claude, Ollama-Korean](https://www.youtube.com/watch?v=KCdJH2MLwWM)

## Requirements

* Python version >= 3.10
* PyQt6
* API Key (OpenAI, Google Gemini, Claude)


## Feature

* Support OpenAI, Google Gemini, Claude 
* Support Open-source AI models using Ollama library
* Support Chat, Image, Vision, TTS, and STT generation

## Create executable file

```bash
pyinstaller --add-data "ico/*.svg:ico" --add-data "ico/*.png:ico" --add-data "splash/pyqt-small.png:splash" --icon="ico/app.ico" --windowed --onefile main.py
```
### Tip
After you generate the executable file on Windows, change the name of the .exe file to make its icon show up properly.


## Known Issue
## Ubuntu Issue
### If you encounter the error message below while running/debugging the program on the Ubuntu operating system, please resolve it as described in the [Fix] section

qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.

qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.

This application failed to start because no Qt platform plugin could be initialized.

Reinstalling the application may fix this problem.

### Fix

Install following library then re-run it

```bash
sudo apt-get install -y libxcb-cursor-dev
```

## Segment fault error issue - Ubuntu 
### If you encounter the error message above when closing the app - Ubuntu and Mac

### Fix
Use pyinstaller==6.5.0 

Refer requirements.txt 

### Related links
[PyQT6.5.X fails with to start on macOS (segmentation fault)](https://github.com/pyinstaller/pyinstaller/issues/7789)

[Segment fault when packed with pyinstaller on linux](https://github.com/pyglet/pyglet/issues/1049)

## check_gcp_environment_no_op.cc:29] ALTS: Platforms other than Linux and Windows are not supported issue - Mac
### If you encounter the error message above when closing the app - Ubuntu and Mac

### Fix
Use grpcio==1.64.1

Refer requirements.txt

### Related links
[Suppress logs with google.cloud.workflows client instantiation](https://github.com/googleapis/google-cloud-python/issues/12902)

## License
Distributed under the MIT License.