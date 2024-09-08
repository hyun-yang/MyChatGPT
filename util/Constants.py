from enum import Enum, auto


class Constants:
    # Application Title
    APPLICATION_TITLE = "MyChatGPT"

    # Setting file name
    SETTINGS_FILENAME = "settings.ini"

    # App Style
    FUSION = 'Fusion'

    # API Call User Stop
    MODEL_PREFIX = "Model: "
    ELAPSED_TIME = "Elapsed Time: "
    FINISH_REASON = "Finish Reason: "

    FORCE_STOP = "Force Stop"
    NORMAL_STOP = "stop"
    RESPONSE_TIME = " | Response Time : "

    # Claude Model List
    CLAUDE_MODEL_LIST_SECTION = "Claude_Model_List"
    CLAUDE_MODEL_LIST = [
        "claude-3-5-sonnet-20240620",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]

    # Ollama Model List
    OLLAMA_MODEL_LIST_SECTION = "Ollama_Model_List"
    OLLAMA_MODEL_LIST = [
        # The list of Ollama models is retrieved from the settings.ini file.
    ]

    # Database
    DATABASE_NAME = "mychatgpt.db"
    SQLITE_DATABASE = "QSQLITE"

    CHAT_MAIN_TABLE = "chat_main"
    CHAT_DETAIL_TABLE = "chat_detail"

    IMAGE_MAIN_TABLE = "image_main"
    IMAGE_DETAIL_TABLE = "image_detail"
    IMAGE_FILE_TABLE = "image_files"

    IMAGE_DETAIL_TABLE_ID_NAME = "image_detail_"

    VISION_MAIN_TABLE = "vision_main"
    VISION_DETAIL_TABLE = "vision_detail"
    VISION_FILE_TABLE = "vision_files"

    VISION_DETAIL_TABLE_ID_NAME = "vision_detail_"
    VISION_IMAGE_EXTENSION = "png"

    TTS_MAIN_TABLE = "tts_main"
    TTS_DETAIL_TABLE = "tts_detail"

    STT_MAIN_TABLE = "stt_main"
    STT_DETAIL_TABLE = "stt_detail"

    CHAT_PROMPT_TABLE = "prompt"

    NEW_CHAT = "New Chat"
    NEW_IMAGE = "New Image"
    NEW_VISION = "New Vision"
    NEW_TTS = "New TTS"
    NEW_STT = "New STT"

    # Image
    DALLE2 = "dall-e-2"
    DALLE3 = "dall-e-3"
    DALLE_CREATE = "Create"
    DALLE_EDIT = "Edit"
    DALLE_VARIATION = "Variation"
    DALLE_CREATION_TYPE = [DALLE_CREATE, DALLE_EDIT, DALLE_VARIATION]

    DALLE_EDIT_FILES_COUNT = 2  # Image/Edit case : two files needed, original image file and masked image file

    DALLE3_SIZE_LIST = [
        "1024x1024", "1792x1024", "1024x1792"
    ]

    DALLE2_SIZE_LIST = [
        "256x256", "512x512", "1024x1024"
    ]

    DALLE_QUALITY_LIST = [
        "standard",
        "hd"
    ]

    DALLE_STYLE_LIST = [
        "vivid",
        "natural"
    ]

    RESPONSE_FORMAT_B64_JSON = "b64_json"
    SCALE_RATIO = 1.1

    # Vision
    VISION_MODEL_LIST = ["gpt-4o", "gpt-4-turbo", "gpt-4-vision-preview", "gpt-4-1106-vision-preview"]

    VISION_DETAIL_LIST = [
        "auto",
        "high",
        "low"
    ]

    THUMBNAIL_LIST_MAX_COLUMN = 3  # Vision : 3 images per row

    # TTS
    TTS_MODEL_LIST = ["tts-1", "tts-1-hd"]
    TTS_VOICE_LIST = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    TTS_OUTPUT_FORMAT_LIST = ["mp3", "opus", "aac", "flac"]
    TTS_FILETYPE_LIST = ["txt", "pdf", "docx"]

    TTS_PLAYER_WIDTH = 500
    TTS_PLAYER_HEIGHT = 150
    TTS_4K_LIMIT = 4096

    # STT
    STT_MODEL_LIST = ["whisper-1"]
    STT_RESPONSE_FORMAT_LIST = ["json", "text", "srt", "verbose_json", "vtt"]
    STT_FORMAT_LIST = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
    STT_TIMESTAMP_GRANULARITIES = ["segment", "word"]
    STT_LANGUAGE_LIST = {
        'English': 'en',
        'Korean': 'ko',
        'Japanese': 'ja',
        'German': 'de',
        'Chinese': 'zh',
        'Italian': 'it',
        'Spanish': 'es',
        'French': 'fr',
        'Hindi': 'hi',
        'Russian': 'ru'
    }

    ABOUT_TEXT = (
        "<b>MyChatGPT</b><br>"
        "Version: 1.0.0<br><br>"
        "Author: Hayden Yang(양 현석)<br>"
        "Github: <a href='https://github.com/hyun-yang'>https://github.com/hyun-yang</a><br><br>"
        "Contact: iamyhs@gmail.com<br>"
    )

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise ValueError(f"Cannot reassign constant '{name}'")
        self.__dict__[name] = value


class UI:
    FILE = "File"
    VIEW = "View"
    HELP = "Help"

    UI = "UI"
    FOUNDS = "founds"
    NOT_FOUND = "not found"
    METHOD = "Method "

    CHAT = "Chat"
    CHAT_TIP = "Chat"
    CHAT_LIST = "Chat List"

    IMAGE = "Image"
    IMAGE_TIP = "Image"
    IMAGE_LIST = "Image List"

    VISION = "Vision"
    VISION_TIP = "Vision"
    VISION_LIST = "Vision List"

    STT = "STT"
    STT_TIP = "STT"
    STT_LIST = "STT List"

    TTS = "TTS"
    TTS_TIP = "TTS"
    TTS_LIST = "TTS List"
    TTS_TEXT = "text"
    TTS_SRT = "srt"
    TTS_VTT = "vtt"

    SETTING = "Setting"
    SETTING_TIP = "Setting"

    CLOSE = "Close"
    CLOSE_TIP = "Exit App"

    ABOUT = "About..."
    ABOUT_TIP = "About"

    ADD = "Add"
    DELETE = "Delete"
    RENAME = "Rename"
    STOP = "Stop"
    SAVE = "Save"
    COPY = "Copy"
    PLAY = "Play"
    PAUSE = "Pause"
    ZOOM_IN = "+Zoom"
    ZOOM_OUT = "-Zoom"
    CLEAR_ALL = "Clear All"
    COPY_ALL = "Copy All"
    RELOAD_ALL = "Reload All"
    OK = "Ok"
    CANCEL = "Cancel"

    IMAGE_FILTER = "Images (*.png)"
    IMAGE_PNG_EXTENSION = ".png"
    IMAGE_PNG = "PNG"
    IMAGE_SIZE_ERROR_MESSAGE = "It should be a png file and its size should be less than 4MB."

    FILE_READ_IN_BINARY_MODE = 'rb'
    UTF_8 = "utf-8"

    CHAT_PROMPT_PLACEHOLDER = "Enter your prompt here."
    SEARCH_PROMPT_PLACEHOLDER = "Enter your search term."
    SEARCH_PROMPT_DB_PLACEHOLDER = "Search..."
    SELECT_FILE_AND_PROMPT_PLACEHOLDER = "Select file and enter your prompt(optional)"
    IMAGE_EDIT_PROMPT_PLACEHOLDER = (
        "Please select two files.\nThe first file should be the original image file. "
        " \nAnd the second file should be the image file with the mask applied.  "
        " \nThen enter the prompt")

    TTS_PROMPT_PLACEHOLDER = "Enter your text or select file"
    TTS_FILE_NOT_FOUND = "The file was not found."
    TTS_FILE_ERROR = "An error occurred:"
    TTS_FILE_ENCODING_ERROR = "Could not decode the file with encoding"
    TTS_CHARACTER_LIMIT_TITLE = "TTS 4096 characters limit"
    TTS_CHARACTER_LIMIT_INFO_MESSAGE = "The maximum length for the TTS string is 4096 characters"

    VISION_PROMPT_PLACEHOLDER = ("Prompts can be very helpful for correcting specific words or "
                                 " acronyms that the model may misrecognize in the audio")

    TITLE = "Title"
    PROMPT = "Prompt"

    EXIT_APPLICATION_TITLE = "Exit Application"
    EXIT_APPLICATION_MESSAGE = "Are you sure you want to exit?"

    WARNING_TITLE = "Warning"
    WARNING_API_KEY_SETTING_MESSAGE = "Please set the API key in Setting->AI Provider."
    WARNING_TITLE_NO_ROW_SELECT_MESSAGE = "No row selected for saving."
    WARNING_TITLE_NO_ROW_DELETE_MESSAGE = "No row selected for deletion."
    WARNING_TITLE_SELECT_FILE_MESSAGE = "Select file first."
    WARNING_TITLE_SELECT_FILE_AND_PROMPT_MESSAGE = "Select file and enter your prompt."
    WARNING_TITLE_NO_PROMPT_MESSAGE = "Enter your prompt."

    SAVE_IMAGE_TITLE = "Save Image"
    SAVE_IMAGE_FILTER = "PNG Files (*.png);;All Files (*)"

    STT_FILTER = "Speech (*.mp3 *.mp4 *.mpeg *.mpga *.m4a *.wav *.webm)"
    VISION_IMAGE_FILTER = "Images (*.png *.jpeg *.jpg *.webp *.gif)"

    TEXT_FILTER = "Text (*.txt)"
    PDF_FILTER = "PDF (*.pdf)"
    WORD_FILTER = "Word (*.docx)"

    CONFIRM_DELETION_TITLE = "Confirm Deletion"
    CONFIRM_DELETION_ROW_MESSAGE = "Are you sure you want to delete the selected row?"
    CONFIRM_DELETION_CHAT_MESSAGE = "Are you sure you want to delete this chat?"
    CONFIRM_DELETION_IMAGE_MESSAGE = "Are you sure you want to delete this image?"
    CONFIRM_DELETION_VISION_MESSAGE = "Are you sure you want to delete this vision?"
    CONFIRM_DELETION_TTS_MESSAGE = "Are you sure you want to delete this tts?"
    CONFIRM_DELETION_STT_MESSAGE = "Are you sure you want to delete this stt?"
    CONFIRM_CHOOSE_CHAT_MESSAGE = "Choose chat first to delete"
    CONFIRM_CHOOSE_IMAGE_MESSAGE = "Choose image first to delete"
    CONFIRM_CHOOSE_VISION_MESSAGE = "Choose vision first to delete"
    CONFIRM_CHOOSE_TTS_MESSAGE = "Choose tts first to delete"
    CONFIRM_CHOOSE_STT_MESSAGE = "Choose stt first to delete"

    LABEL_ENTER_NEW_NAME = "Enter new name:"

    FAILED_TO_OPEN_FILE = "Failed to open file: "
    FILE_NOT_EXIST = "File does not exist: "
    MEDIA_NOT_LOADED = "Media is not loaded yet."

    AUDIO_SELECT_FOLDER = "Select Folder"
    AUDIO_SAVE = "Save Audio"

    UNSUPPORTED_FILE_TYPE = "Unsupported file type"

    SETTINGS = "Settings"
    SETTINGS_PIXEL = "px"

    ICON_FILE_ERROR = "Error: The icon file"
    ICON_FILE_NOT_EXIST = "does not exist."

    ITEM_ICON_SIZE = 32
    ITEM_EXTRA_SIZE = 20
    ITEM_PADDING = 5

    QSPLITTER_LEFT_WIDTH = 200
    QSPLITTER_RIGHT_WIDTH = 800
    QSPLITTER_HANDLEWIDTH = 3

    PROGRESS_BAR_STYLE = """
            QProgressBar{
                border: 1px grey;
                border-radius: 5px;            
            }
    
            QProgressBar::chunk {
                background-color: lightgreen;
                width: 10px;
                margin: 1px;
            }
            """

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise ValueError(f"Cannot reassign constant '{name}'")
        self.__dict__[name] = value


class MODEL_CONSTANTS:
    MODEL = "model"

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise ValueError(f"Cannot reassign constant '{name}'")
        self.__dict__[name] = value


class MODEL_MESSAGE:
    MODEL_UNSUPPORTED = "Unsupported LLM:"
    MODEL_UNSUPPORTED_TYPE = "Unsupported model type"
    THREAD_RUNNING = "Previous thread is still running!"
    THREAD_FINISHED = "Thread has been finished"
    INVALID_CREATION_TYPE = "Invalid creation type: "
    UNEXPECTED_ERROR = "An unexpected error occurred: "
    AUTHENTICATION_FAILED_OPENAI = "Authentication failed. The OpenAI API key is not valid."
    AUTHENTICATION_FAILED_GEMINI = "Authentication failed. The Gemini API key is not valid."
    AUTHENTICATION_FAILED_CLAUDE = "Authentication failed. The Claude API key is not valid."

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise ValueError(f"Cannot reassign constant '{name}'")
        self.__dict__[name] = value


class DATABASE_MESSAGE:
    DATABASE_TITLE_ERROR = "Database Error"
    DATABASE_FETCH_ERROR = "Failed to fetch prompt from the database."
    DATABASE_ADD_ERROR = "Failed to add new row from the database."
    DATABASE_DELETE_ERROR = "Failed to delete row from the database."
    DATABASE_UPDATE_ERROR = "Failed to update row from the database."

    DATABASE_CHAT_CREATE_TABLE_ERROR = "Failed to create chat_main table: "
    DATABASE_CHAT_ADD_ERROR = "Failed to add chat main: "
    DATABASE_CHAT_UPDATE_ERROR = "Failed to update chat main: "
    DATABASE_CHAT_MAIN_ENTRY_SUCCESS = "Successfully deleted chat main entry with id: "
    DATABASE_CHAT_MAIN_ENTRY_FAIL = "Failed to delete chat main entry with id "

    DATABASE_CHAT_DETAIL_CREATE_TABLE_ERROR = "Failed to create chat detail table for chat_main_id "
    DATABASE_CHAT_DETAIL_INSERT_ERROR = "Failed to insert chat detail: "
    DATABASE_CHAT_DETAIL_DELETE_ERROR = "Failed to delete chat detail table "
    DATABASE_CHAT_DETAIL_FETCH_ERROR = "Failed to fetch chat details for chat_main_id"

    DATABASE_PROMPT_CREATE_TABLE_ERROR = "Failed to create prompt table: "
    DATABASE_PROMPT_ADD_ERROR = "Failed to add prompt: "
    DATABASE_PROMPT_UPDATE_ERROR = "Failed to update prompt: "
    DATABASE_PROMPT_DELETE_SUCCESS = "Successfully deleted prompt with id: "
    DATABASE_PROMPT_DELETE_FAIL = "Failed to delete prompt with id "

    DATABASE_IMAGE_CREATE_TABLE_ERROR = "Failed to create image_main table: "
    DATABASE_IMAGE_ADD_ERROR = "Failed to add image main: "
    DATABASE_IMAGE_UPDATE_ERROR = "Failed to update image main: "
    DATABASE_IMAGE_DELETE_SUCCESS = "Successfully deleted image main entry with id: "
    DATABASE_IMAGE_DELETE_FAIL = "Failed to delete image main entry with id "

    DATABASE_IMAGE_DETAIL_CREATE_TABLE_ERROR = "Failed to create image_detail table: "
    DATABASE_IMAGE_DETAIL_INSERT_ERROR = "Failed to insert image detail: "
    DATABASE_IMAGE_DETAIL_DELETE_ERROR = "Failed to delete image detail table "
    DATABASE_IMAGE_DETAIL_FETCH_ERROR = "Failed to fetch image details for image_main_id"

    DATABASE_IMAGE_DETAIL_FILE_CREATE_TABLE_ERROR = "Failed to create image detail file table: "
    DATABASE_IMAGE_DETAIL_FILE_INSERT_ERROR = "Failed to insert image detail file: "
    DATABASE_IMAGE_DETAIL_FILE_DELETE_ERROR = "Failed to delete image detail file table "
    DATABASE_IMAGE_DETAIL_FILE_FETCH_ERROR = "Failed to fetch image detail file for image_main_id "
    DATABASE_IMAGE_DETAIL_FILE_NO_RECORD_ERROR = "No record found for image_detail_id "

    DATABASE_VISION_CREATE_TABLE_ERROR = "Failed to create vision_main table: "
    DATABASE_VISION_ADD_ERROR = "Failed to add vision main: "
    DATABASE_VISION_UPDATE_ERROR = "Failed to update vision main: "
    DATABASE_VISION_MAIN_ENTRY_SUCCESS = "Successfully deleted vision main entry with id: "
    DATABASE_VISION_MAIN_ENTRY_FAIL = "Failed to delete vision main entry with id "

    DATABASE_VISION_DETAIL_CREATE_TABLE_ERROR = "Failed to create vision_detail table: "
    DATABASE_VISION_DETAIL_INSERT_ERROR = "Failed to insert vision detail: "
    DATABASE_VISION_DETAIL_DELETE_ERROR = "Failed to delete vision detail table "
    DATABASE_VISION_DETAIL_FETCH_ERROR = "Failed to fetch vision details for vision_main_id"

    DATABASE_VISION_DETAIL_FILE_CREATE_TABLE_ERROR = "Failed to create vision detail file table: "
    DATABASE_VISION_DETAIL_FILE_INSERT_ERROR = "Failed to insert vision detail file: "
    DATABASE_VISION_DETAIL_FILE_DELETE_ERROR = "Failed to delete vision detail file table "
    DATABASE_VISION_DETAIL_FILE_FETCH_ERROR = "Failed to fetch vision detail file for vision_detail_id "
    DATABASE_VISION_DETAIL_FILE_NO_RECORD_ERROR = "No record found for vision_detail_id "

    DATABASE_TTS_CREATE_TABLE_ERROR = "Failed to create tts_main table: "
    DATABASE_TTS_ADD_ERROR = "Failed to add tts main: "
    DATABASE_TTS_UPDATE_ERROR = "Failed to update tts main: "
    DATABASE_TTS_MAIN_ENTRY_SUCCESS = "Successfully deleted tts main entry with id: "
    DATABASE_TTS_MAIN_ENTRY_FAIL = "Failed to delete tts main entry with id "

    DATABASE_TTS_DETAIL_CREATE_TABLE_ERROR = "Failed to create tts_detail table: "
    DATABASE_TTS_DETAIL_INSERT_ERROR = "Failed to insert tts detail: "
    DATABASE_TTS_DETAIL_DELETE_ERROR = "Failed to delete tts detail table "
    DATABASE_TTS_DETAIL_FETCH_ERROR = "Failed to fetch tts details for tts_main_id "

    DATABASE_STT_CREATE_TABLE_ERROR = "Failed to create stt_main table: "
    DATABASE_STT_ADD_ERROR = "Failed to add stt main: "
    DATABASE_STT_UPDATE_ERROR = "Failed to update stt main: "
    DATABASE_STT_MAIN_ENTRY_SUCCESS = "Successfully deleted stt main entry with id: "
    DATABASE_STT_MAIN_ENTRY_FAIL = "Failed to delete stt main entry with id "

    DATABASE_STT_DETAIL_CREATE_TABLE_ERROR = "Failed to create stt_detail table: "
    DATABASE_STT_DETAIL_INSERT_ERROR = "Failed to insert stt detail: "
    DATABASE_STT_DETAIL_DELETE_ERROR = "Failed to delete stt detail table "
    DATABASE_STT_DETAIL_FETCH_ERROR = "Failed to fetch stt details for stt_main_id"

    DATABASE_RETRIEVE_DATA_FAIL = "Failed to retrieve data from "
    DATABASE_DELETE_TABLE_SUCCESS = "Successfully deleted table: "
    DATABASE_EXECUTE_QUERY_ERROR = "Failed to execute query: "

    DATABASE_FAILED_OPEN = "Failed to open database."
    DATABASE_ENABLE_FOREIGN_KEY = "Failed to enable foreign key: "
    DATABASE_PRAGMA_FOREIGN_KEYS_ON = "PRAGMA foreign_keys = ON;"

    NEW_TITLE = "New Title"
    NEW_PROMPT = "New Prompt"


class AIProviderName(Enum):
    OPENAI = 'OpenAI'
    CLAUDE = 'Claude'
    GEMINI = 'Gemini'
    OLLAMA = 'Ollama'


class MainWidgetIndex(Enum):
    CHAT_WIDGET = auto()
    IMAGE_WIDGET = auto()
    VISION_WIDGET = auto()
    TTS_WIDGET = auto()
    STT_WIDGET = auto()


def get_ai_provider_names():
    return [ai_provider.value for ai_provider in AIProviderName]
