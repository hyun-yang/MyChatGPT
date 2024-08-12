# MyChatGPT
이 프로그램은 PyQt6 애플리케이션으로, OpenAI, Google Gemini, Claude 및 다양한 오픈 소스 AI 모델의 강력한 기능을 제공합니다.

이 애플리케이션은 채팅, 이미지, 비전, 텍스트-음성 변환(TTS) 및 음성-텍스트 변환(STT) 기능을 지원합니다.

## 필수 조건
시작하기 전에 다음 요구 사항을 충족했는지 확인하세요:

1. Python:

    Python 3.8 이상이 설치되어 있는지 확인하세요. 공식 Python 웹사이트에서 다운로드 할 수 있습니다. 

```bash
  python --version
```    

2. pip:

   Python의 패키지 설치 도구인 pip가 설치되어 있는지 확인하세요.


3. Git:

   버전 관리를 위해 Git이 설치되어 있는지 확인하세요. 공식 Git 웹사이트에서 다운로드 할 수 있습니다.


4. 가상 환경:

   프로젝트 의존성을 관리하기 위해 가상 환경을 사용하는 것이 권장됩니다.
   
   venv를 사용하여 가상 환경을 생성할 수 있습니다:

```bash
  python -m venv venv
```    

```bash
  source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

5. IDE/코드 편집기:

   원하는 IDE 또는 코드 편집기를 사용하세요. 인기 있는 옵션으로는 PyCharm, VSCode, Eclipse 등이 있습니다.


6. PlantUML: 

    PlantUML은 UML 다이어그램을 생성하는 데 사용됩니다. 

    공식 PlantUML 웹사이트 또는 PyCharm 플러그인, Xcode 확장에서 PlantUML을 다운로드하세요.


## 빠른 설치

1. 저장소 복사

```bash
git clone https://github.com/hyun-yang/MyChatGPT.git
```

2. pip를 사용하여 설치:

```bash
pip install -r requirements.txt
```
가상 환경(venv)을 사용하는 경우, 다음 명령어를 사용하세요

```bash
python -m pip install -r requirements.txt
```

3. main.py 실행

```bash
python main.py
```

4. API Key 설정하기
   * 'Setting' 메뉴를 열고 API Key를 설정합니다.  
   * Ollama 를 사용하기전에 [Ollama](https://ollama.com/) 앱을 인스톨 한 후 사용하고 싶은 모델을 다운로드 합니다. 


5. 재 실행

```bash
python main.py
```

## 데모
[MyChatGPT Demo - OpenAI, Gemini, Claude, Ollama-English](https://www.youtube.com/watch?v=KCdJH2MLwWM)

[MyChatGPT Demo - OpenAI, Gemini, Claude, Ollama-Korean](https://www.youtube.com/watch?v=KCdJH2MLwWM)

## 요구 사항

* Python version >= 3.10
* PyQt6
* API Key (OpenAI, Google Gemini, Claude)


## 기능

* OpenAI, Google Gemini, Claude 지원 
* Ollama 라이브러리를 사용한 오픈 소스 AI 모델 지원
* 채팅, 이미지, 비전, TTS 및 STT 생성 지원

## 실행 파일 만들기

```bash
pyinstaller --add-data "ico/*.svg:ico" --add-data "ico/*.png:ico" --add-data "splash/pyqt-small.png:splash" --icon="ico/app.ico" --windowed --onefile main.py
```
### 실행 파일 아이콘 문제
Windows에서 실행 파일을 생성한 후, .exe 파일의 이름을 변경하여 아이콘이 제대로 표시되도록 하세요.


## 알려진 문제
## Ubuntu 문제
### Ubuntu 운영 체제에서 프로그램을 실행/디버깅하는 동안 아래의 오류 메시지가 발생하면, [Fix] 섹션에 설명된 대로 해결하세요

qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.

qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.

This application failed to start because no Qt platform plugin could be initialized.

Reinstalling the application may fix this problem.

### 해결 방법

다음 라이브러리를 설치한 후 다시 실행하세요.

```bash
sudo apt-get install -y libxcb-cursor-dev
```

## 세그먼트 오류 문제 - Ubuntu 
### 앱을 닫을 때 위의 오류 메시지가 발생하면 - Ubuntu 및 Mac

### 해결 방법
Use pyinstaller==6.5.0 

requirements.txt를 참조하세요 

### 관련 링크
[PyQT6.5.X fails with to start on macOS (segmentation fault)](https://github.com/pyinstaller/pyinstaller/issues/7789)

[Segment fault when packed with pyinstaller on linux](https://github.com/pyglet/pyglet/issues/1049)

## check_gcp_environment_no_op.cc:29] ALTS: Linux 및 Windows 이외의 플랫폼은 지원되지 않음 문제 - Mac
### 앱을 닫을 때 위의 오류 메시지가 발생하면 - Ubuntu 및 Mac

### 해결 방법
Use grpcio==1.64.1

requirements.txt를 참조하세요

### 관련 링크
[Suppress logs with google.cloud.workflows client instantiation](https://github.com/googleapis/google-cloud-python/issues/12902)

## 라이센스
MIT 라이센스에 따라 배포됩니다.