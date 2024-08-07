import os

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import QWidget, QLabel, QSizePolicy, QSlider, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout, \
    QGroupBox

from util.Constants import Constants, UI
from util.Utility import Utility


class AudioPlayerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(Constants.TTS_PLAYER_WIDTH, Constants.TTS_PLAYER_HEIGHT)
        self.mediaPlayer = QMediaPlayer()
        self.audioOutput = QAudioOutput()
        self.mediaPlayer.setAudioOutput(self.audioOutput)
        self.mediaPlayer.mediaStatusChanged.connect(self.on_media_status_changed)
        self.isMediaLoaded = False
        self.initialize_ui()

    def initialize_ui(self):
        self.audioLabel = QLabel("00:00")
        self.audioLabel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.audioLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progressSlider = QSlider(Qt.Orientation.Horizontal)
        self.playButton = QPushButton(QIcon(Utility.get_icon_path('ico', 'control.png')), UI.PLAY)
        self.stopButton = QPushButton(QIcon(Utility.get_icon_path('ico', 'control-stop-square.png')), UI.STOP)
        self.playButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.playButton)
        buttonLayout.addWidget(self.stopButton)

        self.playButton.clicked.connect(self.play_audio)
        self.stopButton.clicked.connect(self.stop_audio)
        self.mediaPlayer.positionChanged.connect(self.on_position_changed)
        self.mediaPlayer.durationChanged.connect(self.on_duration_changed)
        self.progressSlider.sliderMoved.connect(self.set_audio_position)

        layout = QGridLayout()
        layout.addWidget(self.audioLabel, 0, 0, 1, 2)
        layout.addWidget(self.progressSlider, 1, 0, 1, 2)
        layout.addWidget(self.playButton, 2, 0)
        layout.addWidget(self.stopButton, 2, 1)

        groupBox = QGroupBox()
        groupBox.setLayout(layout)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(groupBox)

        self.setLayout(layout)

    def set_audio_file(self, filepath):
        if not os.path.isfile(filepath):
            print(f"{UI.FILE_NOT_EXIST} {filepath}")
            return
        self.filepath = filepath
        self.mediaPlayer.setSource(QUrl.fromLocalFile(filepath))
        self.audioOutput.setVolume(1)

    def play_audio(self):
        if self.isMediaLoaded:
            if self.mediaPlayer.mediaStatus() == QMediaPlayer.MediaStatus.EndOfMedia:
                self.mediaPlayer.setPosition(0)
            self.mediaPlayer.play()
            self.update_playbutton_state(isPlaying=True)
        else:
            print(f"{UI.MEDIA_NOT_LOADED}")

    def pause_audio(self):
        self.mediaPlayer.pause()
        self.update_playbutton_state(isPlaying=False)

    def stop_audio(self):
        self.mediaPlayer.stop()
        self.reset_player_ui()

    def on_position_changed(self, position):
        self.progressSlider.setValue(position)
        self.update_label(position)

    def on_duration_changed(self, duration):
        self.progressSlider.setRange(0, duration)

    def set_audio_position(self, position):
        self.mediaPlayer.setPosition(position)

    def update_label(self, milliseconds):
        seconds = int((milliseconds / 1000) % 60)
        minutes = int((milliseconds / (1000 * 60)) % 60)
        self.audioLabel.setText(f"{minutes:02}:{seconds:02}")

    def update_playbutton_state(self, isPlaying):
        if isPlaying:
            self.playButton.setText(UI.PAUSE)
            self.playButton.setIcon(QIcon(Utility.get_icon_path('ico', 'control-pause.png')))
            self.playButton.clicked.disconnect()
            self.playButton.clicked.connect(self.pause_audio)
        else:
            self.playButton.setText(UI.PLAY)
            self.playButton.setIcon(QIcon(Utility.get_icon_path('ico', 'control.png')))
            self.playButton.clicked.disconnect()
            self.playButton.clicked.connect(self.play_audio)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.isMediaLoaded = True
            self.playButton.setEnabled(True)
            self.stopButton.setEnabled(True)
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.reset_player_ui()
        elif status == QMediaPlayer.MediaStatus.NoMedia:
            self.isMediaLoaded = False
            self.playButton.setEnabled(False)
            self.stopButton.setEnabled(False)

    def reset_player_ui(self):
        self.progressSlider.setValue(0)
        self.update_label(0)
        self.update_playbutton_state(isPlaying=False)
        self.mediaPlayer.stop()
        self.mediaPlayer.setPosition(0)

    def clean_audio_player_widget(self):
        self.mediaPlayer.stop()
