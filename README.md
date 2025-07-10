# MyChatGPT
The ultimate PyQt6 application featuring the power of OpenAI, Google Gemini, Claude, and various open-source AI models.

It delivers outstanding capabilities for Chat, Image, Vision, Text-To-Speech(TTS) and Speech-To-Text(STT).


## What's New 

- Enhanced Chat Capabilities: 
Utilize a variety of file formats, including documents, images, audio, and video files. (Please note: Ensure the selected model supports these formats for optimal performance.)
  - OpenAI Supported File Types
    - Document: 'pdf', 'doc', 'docx', 'pptx'
    - Image: 'jpeg', 'jpg', 'png', 'gif', 'webp'
    - Text: Plain text format files
  
  - Claude Supported File Types
    - Document: 'pdf', 'rtf', 'docx', 'doc', 'epub'
    - Image: 'jpeg', 'jpg', 'png', 'gif', 'webp'
    - Text: Plain text format files
 
  - Gemini Supported File Types
    - Document: 'pdf', 'rtf', 'doc', 'docx', 'dot', 'dotx', 'hwp', 'hwpx'  
    - Image: 'jpeg', 'jpg', 'png', 'gif', 'webp'
    - Video: 'x-flv', 'quicktime', 'mpeg', 'mpegs', 'mpg', 'mp4', 'webm', 'wmv', '3gpp'
    - Audio: 'x-aac', 'flac', 'mp3', 'm4a', 'mpeg', 'mpga', 'mp4', 'opus', 'pcm', 'wav', 'webm'
    - Text: Plain text format files
    - Note: Some file types are only supported for Google AI Pro or Google AI Ultra subscribers. Learn how to upgrade to Google AI Pro or Ultra.
      - The link at https://support.google.com/gemini/answer/14903178?hl=en says that hwp/hwpx files are supported, but when tested, the following error occurs.
      - This is the detailed error message when tested with the two MIME types: application/vnd.hancom.hwp and application/x-hwp.
       ```
        400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'Unable to submit request because it has a mimeType parameter with value application/vnd.hancom.hwp, which is not supported. Update the mimeType and try again. Learn more: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini', 'status': 'INVALID_ARGUMENT'}}
        400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'Unable to submit request because it has a mimeType parameter with value application/x-hwp, which is not supported. Update the mimeType and try again. Learn more: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini', 'status': 'INVALID_ARGUMENT'}}
       ```
      
  - Ollama Supported File Types
    - Image: 'jpeg', 'jpg', 'png', 'gif', 'webp'
    - Text: Plain text format files


- MCP (Model Context Protocol) Integration: 
Experience the power of advanced AI with the integration of Claude, OpenAI, Gemini and Ollama enabling richer and more context-aware conversations.
  - Windows, Mac, Ubuntu: Update/install your system with the latest npx and upx.
    - Mac: If you have installed the latest npx and upx, however if it still doesn't work, install the coreutils package using the following command:  
    ```
    brew install coreutils
    ```


- Powerful Workflows: 
Unlock new possibilities with the Orchestrator-Worker and Evaluator-Optimizer workflows, designed to streamline processes and enhance efficiency in interactions.
  - Reference Link [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)


- Reasoning/Thinking Feature:
  - Support the 'reasoning/thinking' feature of OpenAI, Gemini and Claude. Please note that you need to select a model that supports this 'reasoning/thinking' feature.


### Evaluator-Optimizer and Orchestrator-Worker Workflows Prompt Sample

- Evaluator-Optimizer Prompt sample

```markdown
1) Evaluator Prompt

Evaluate this following code implementation for:
1. code correctness
2. time complexity
3. style and best practices

You should be evaluating only and not attemping to solve the task.
Only output "PASS" if all criteria are met and you have no further suggestions for improvements.
Output your evaluation concisely in the following format.

<evaluation>PASS, NEEDS_IMPROVEMENT, or FAIL</evaluation>
<feedback>
What needs improvement and why.
</feedback>


2) Generator Prompt

Your goal is to complete the task based on <user input>. If there are feedback 
from your previous generations, you should reflect on them to improve your solution

Output your answer concisely in the following format: 

It MUST have <thoughts> and <response> Tag.

<thoughts>
[Your understanding of the task and feedback and how you plan to improve]
</thoughts>

<response>
[Your code implementation here]
</response>


3) Task Prompt

<user input>
Implement a Stack with:
1. push(x)
2. pop()
3. getMin()
All operations should be O(1).
</user input>
```


- Orchestrator-Worker Prompt sample

```markdown
1) Orchestrator Prompt

Analyze the following user question and break it down into 2 or 3 related sub-questions:

Respond in the following format:
{
    "analysis": "Provide a detailed explanation of your understanding of the user question and the rationale behind the sub-questions you created.",
    "tasks": [
        {
            "task": "Sub-question 1",
            "description": "Explain the intent and main point of this sub-question."
        },
        {
            "task": "Sub-question 2",
            "description": "Explain the intent and main point of this sub-question."
        }
        // Include additional sub-questions as necessary
    ]
}
Generate a maximum of 2 or 3 sub-questions.

User question: {user_query}


2) Worker Prompt

Addressing the sub-questions derived from the following user question.

Original question: {user_query}  
Sub-question: {task}

Explanation: {description}

Provide a thorough and detailed response that addresses the sub-question.


3) Aggregator Prompt

Provide a final response that summarize the questions and responses below.

- The responses to the sub-questions should be as comprehensive and detailed as possible.
- The final report should be presented in a comprehensive manner using Markdown format.

User's original question:
{user_query}

Sub-questions and final responses:

```


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

## Quick Demo
[MyChatGPT Demo-ENG](https://youtu.be/oLN8wS8gwwc)

[MyChatGPT Demo-KOR](https://youtu.be/HuFUf5ldb_Q)


## Requirements

* Python version >= 3.10
* PyQt6
* API Key (OpenAI, Google Gemini, Claude)


## Feature

* Support OpenAI, Google Gemini, Claude 
* Support Open-source AI models using Ollama library
* Support Chat, Image, Vision, TTS, and STT generation

## Ollama Model List
Ollama currently do not have a method to retrieve the list of supported models, 
so you need to open the **settings.ini** file and add them manually as shown below.

If you are using Ollama, make sure to check the following three things:

1) Install [Ollama](https://ollama.com/).
2) Download the model you wish to use.
3) Open the settings.ini file and add the name of the model.

```
Open 'settings.ini' file then add model list.

...
[Ollama_Model_List]
llama3.1=true
gemma2=true
gemma2:27b=true
codegemma=true
...
```

## Create executable file

```bash
pyinstaller --add-data "ico/*.svg:ico" --add-data "ico/*.png:ico" --add-data "splash/pyqt-small.png:splash" --icon="ico/app.ico" --windowed --onefile main.py
```

## Screenshots

* First Run

![first-run-screenshot](https://github.com/user-attachments/assets/317e3b12-980f-4946-9704-20cbcaa4f071)

* Setting
![setting_screenshot](https://github.com/user-attachments/assets/c035a534-d58e-45d5-a2b7-6c3aa6c8a95e)


* MCP 

![mcp_claude](https://github.com/user-attachments/assets/508767de-2e8a-4034-ad7c-e91676359f4c)

![mcp_openai](https://github.com/user-attachments/assets/bddbead2-6d82-4363-8477-ed51d872d13b)

![mcp_gemini](https://github.com/user-attachments/assets/fc481e42-ce76-4db4-a3ed-a853e2108f91)

![openai_mcp2](https://github.com/user-attachments/assets/0bb4372a-4ccf-4c5a-b379-7d00ac0e59a3)


* Evaluator / Orchestrator
![evaluator](https://github.com/user-attachments/assets/178507ab-d3e8-470b-8ffe-49e9a363fa66)

![orchestrator](https://github.com/user-attachments/assets/77d803cc-ef3c-4de8-bb5a-18c091cb7ad7)


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


* Ollama Model List (You need to manually add models and make sure to download the model you wish to use beforehand)
![ollama_model_list_screenshot](https://github.com/user-attachments/assets/f7397692-d8df-419e-bd76-903e8e8c1263)


## UML Diagram

* Main Class Diagram
![main_class_screenshot_small](https://github.com/user-attachments/assets/73ccd686-8480-41dd-9288-41f01bc5cff2)


* Main Sequence Diagram
![main_sequence_screenshot_small](https://github.com/user-attachments/assets/f239d07f-db05-4b79-ac21-40f992a72e13)


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