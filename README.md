# MyChatGPT
The ultimate PyQt6 application featuring the power of OpenAI, Google Gemini, Claude, and various open-source AI models.

It delivers outstanding capabilities for Chat, Image, Vision, Text-To-Speech(TTS) and Speech-To-Text(STT).

## Prerequisites
Before you begin, ensure you have met the following requirements:

1. Python:

    Make sure you have Python 3.10 or later installed. You can download it from the official Python website.

```bash
  python --version
```    

2. pip:

   Ensure you have pip installed, which is the package installer for Python.


3. Git:

   Ensure you have Git installed for version control. You can download it from the official Git website.


4. Virtual Environment:

    It is recommended to use a virtual environment to manage your project dependencies.

    You can create a virtual environment using venv:

```bash
  python -m venv venv
```    

```bash
  source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

5. IDE/Code Editor:

   Use an IDE or code editor of your choice. Popular options include PyCharm, VSCode, and Eclipse.


6. PlantUML: 

    PlantUML is used for generating UML diagrams. 

    Download PlantUML from the official PlantUML website or PyCharm plugin, Xcode extension.


## Quick Install

1. Clone repository

```bash
git clone https://github.com/hyun-yang/MyChatGPT.git
```

2. With pip:

```bash
pip install -r requirements.txt
```
Or virtual environment(venv), use this command

```bash
python -m pip install -r requirements.txt
```

3. Run main.py

```bash
python main.py
```

4. Configure API Key
   * Open 'Setting' menu and set API key.  
   * For Ollama, you can use any key and need to install [Ollama](https://ollama.com/) and download model you want to use.  


5. Re-run main.py

```bash
python main.py
```

## Quick Demo - will update the demo shortly
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
### Icon issue
After you generate the executable file on Windows, change the name of the .exe file to make its icon show up properly.

## Screenshots

* Setting
![setting_screenshot](https://github.com/user-attachments/assets/856aebeb-38c0-44ae-914c-a729a037343b)


* Chat
![chat_screenshot](https://github.com/user-attachments/assets/50d1ac1e-a782-42dd-89fa-7477e0abda3e)


* Image
![image_screenshot](https://github.com/user-attachments/assets/0141b799-b09b-428c-b58e-7a6269e1d3e1)


* Vision
![vision_screenshot](https://github.com/user-attachments/assets/a5b164ac-906b-45ee-8e2e-9578dc576d43)


* TTS
![tts_screenshot](https://github.com/user-attachments/assets/34643d6d-63e3-4717-848e-bdc3dde5e698)


* STT
![stt_screenshot](https://github.com/user-attachments/assets/73ba987a-1c9e-4be6-9c10-cfe79f279a19)



## UML Diagram

* Main Class Diagram
![main_class_screenshot_small](https://github.com/user-attachments/assets/a2d90e47-65ac-440c-8ff1-7f419b211ac6)


* Main Sequence Diagram
![main_sequence_screenshot_small](https://github.com/user-attachments/assets/89073c70-59e3-4cbf-b3d1-97d7c59e981c)


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