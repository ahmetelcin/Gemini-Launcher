# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Gemini Launcher v1.0
#
# Description:
# This application is a desktop utility designed for quick access to Google
# Gemini. It runs in the background, resides as an icon in the system tray,
# and can be invoked via a global keyboard shortcut.
#
# Required Libraries:
# PyQt6, PyQt6-WebEngine, pynput, pywin32, Pillow
# -----------------------------------------------------------------------------

import sys
from pynput import keyboard
from pathlib import Path
import os
import configparser

try:
    import winshell
    from win32com.client import Dispatch
except ImportError:
    winshell = None

from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, QMenu,
                             QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton)
from PyQt6.QtGui import QIcon, QAction, QKeyEvent
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QStandardPaths

# --- APPLICATION INFO ---
APP_VERSION = "1.0"

# --- PATH MANAGEMENT ---
APP_DATA_ROAMING_PATH = Path(os.getenv('APPDATA')) / "GeminiLauncher"
APP_DATA_LOCAL_PATH = Path(os.getenv('LOCALAPPDATA')) / "GeminiLauncher"
APP_DATA_ROAMING_PATH.mkdir(parents=True, exist_ok=True)
APP_DATA_LOCAL_PATH.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = APP_DATA_ROAMING_PATH / "config.ini"
PROFILE_DATA_PATH = APP_DATA_LOCAL_PATH / "gemini_profile_data"

if getattr(sys, 'frozen', False):
    BASE_PATH = Path(sys._MEIPASS)
else:
    BASE_PATH = Path(__file__).parent
ICON_PATH = BASE_PATH / "icon.svg"

# --- CONFIGURATION MANAGEMENT ---
config = configparser.ConfigParser()


def load_config():
    if not CONFIG_FILE.exists():
        config['Settings'] = {'hotkey': '<alt>+<space>', 'autostart': 'false'}
        save_config()
    config.read(CONFIG_FILE, encoding='utf-8')
    return config


def save_config():
    with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
        config.write(configfile)


# --- AUTOSTART MANAGEMENT ---
def manage_autostart(enable):
    if not winshell: return
    startup_folder = winshell.startup()
    shortcut_path = os.path.join(startup_folder, "GeminiLauncher.lnk")
    if not getattr(sys, 'frozen', False): return
    exe_path = sys.executable
    if enable:
        if not os.path.exists(shortcut_path):
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path)
            shortcut.save()
    else:
        if os.path.exists(shortcut_path): os.remove(shortcut_path)


# --- SETTINGS WINDOW ---
class SettingsWindow(QWidget):
    settings_saved = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.layout = QVBoxLayout(self)
        self.hotkey_label = QLabel("Set New Hotkey:")
        self.layout.addWidget(self.hotkey_label)
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("Click here and press keys to record...")
        self.hotkey_input.setText(config.get('Settings', 'hotkey'))
        self.hotkey_input.installEventFilter(self)
        self.layout.addWidget(self.hotkey_input)
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.save_button);
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)
        self.save_button.clicked.connect(self.save);
        self.cancel_button.clicked.connect(self.close)

    def eventFilter(self, source, event):
        if source is self.hotkey_input and event.type() == QKeyEvent.Type.KeyPress:
            key, mods = event.key(), event.modifiers()
            key_str, mod_str = self.qt_key_to_pynput(key), self.qt_mods_to_pynput(mods)
            if key_str: self.hotkey_input.setText("+".join(mod_str + [key_str])); return True
        return super().eventFilter(source, event)

    def qt_mods_to_pynput(self, mods):
        mod_map = {Qt.KeyboardModifier.ControlModifier: "<ctrl>", Qt.KeyboardModifier.AltModifier: "<alt>",
                   Qt.KeyboardModifier.ShiftModifier: "<shift>", Qt.KeyboardModifier.MetaModifier: "<cmd>"}
        return [mod_map[mod] for mod in mod_map if mods & mod]

    def qt_key_to_pynput(self, key):
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z: return chr(key).lower()
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9: return chr(key)
        return {Qt.Key.Key_Space: 'space', Qt.Key.Key_Return: 'enter'}.get(key)

    def save(self):
        config.set('Settings', 'hotkey', self.hotkey_input.text())
        save_config();
        self.settings_saved.emit();
        self.close()


# --- ABOUT WINDOW ---
class AboutWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.setFixedSize(380, 220)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(f"Gemini Launcher v{APP_VERSION}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")

        author_label = QLabel("Developer: Ahmet Elçin")
        author_label.setStyleSheet("margin-bottom: 15px;")

        disclaimer_label = QLabel(
            "This software is provided 'as is' and the developer\ncannot be held responsible for any issues that may arise\nfrom the use of the program.")
        disclaimer_label.setWordWrap(True)
        disclaimer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disclaimer_label.setStyleSheet("font-size: 11px; color: #888;")

        ok_button = QPushButton("OK")
        ok_button.setFixedWidth(100)
        ok_button.clicked.connect(self.close)

        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(disclaimer_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)


# --- MAIN WINDOW ---
class GeminiApp(QMainWindow):
    toggle_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.profile = QWebEngineProfile("persistent_gemini_profile", self)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.profile.setCachePath(str(PROFILE_DATA_PATH));
        self.profile.setPersistentStoragePath(str(PROFILE_DATA_PATH))
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.toggle_signal.connect(self.toggle_visibility)
        self.setWindowTitle("Gemini Launcher")
        self.browser = QWebEngineView(self.profile)
        self.browser.setUrl(QUrl("https://gemini.google.com"))
        self.setCentralWidget(self.browser)
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.set_normal_mode()

    def set_normal_mode(self):
        self.setGeometry(400, 200, 900, 650)

    def set_small_mode(self):
        self.setGeometry(500, 300, 600, 450)

    def closeEvent(self, event):
        event.ignore(); self.hide()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            w, h = 450, 700;
            screen = QApplication.primaryScreen().geometry()
            x, y = (screen.width() - w) // 2, int(screen.height() * 0.3)
            self.setGeometry(x, y, w, h)
            self.show();
            self.raise_();
            self.activateWindow()

    def reset_page(self):
        self.browser.setUrl(QUrl("https://gemini.google.com"))


# --- MAIN CONTROLLER CLASS ---
class AppController:
    def __init__(self, app):
        self.app = app
        self.config = load_config()
        self.window = GeminiApp()
        self.settings_window = None
        self.about_window = None
        self.hotkey_listener = None
        self.actions = {}
        self.setup_tray_icon()
        self.start_hotkey_listener()
        manage_autostart(self.config.getboolean('Settings', 'autostart'))
        self.app.aboutToQuit.connect(self.cleanup)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon()
        self.menu = QMenu()
        icon = QIcon(str(ICON_PATH))
        self.tray_icon.setIcon(icon);
        self.tray_icon.setToolTip("Gemini Launcher")

        self.actions['open_normal'] = QAction("Open Gemini (Normal)")
        self.actions['open_small'] = QAction("Open in Small Mode")
        self.actions['reset'] = QAction("Go to Home (Reset)")
        self.actions['settings'] = QAction("Settings...")
        self.actions['about'] = QAction("About...")
        self.actions['autostart'] = QAction("Start with Windows")
        self.actions['autostart'].setCheckable(True)
        self.actions['autostart'].setChecked(self.config.getboolean('Settings', 'autostart'))
        if not winshell:
            self.actions['autostart'].setEnabled(False)
            self.actions['autostart'].setToolTip("The 'pywin32' library is required for this feature.")
        self.actions['exit'] = QAction("Exit")

        self.menu.addActions([self.actions['open_normal'], self.actions['open_small']])
        self.menu.addSeparator()
        self.menu.addActions([self.actions['reset'], self.actions['settings'], self.actions['about']])
        self.menu.addSeparator()
        self.menu.addAction(self.actions['autostart'])
        self.menu.addSeparator()
        self.menu.addAction(self.actions['exit'])
        self.tray_icon.setContextMenu(self.menu)

        self.actions['open_normal'].triggered.connect(self.show_normal_window)
        self.actions['open_small'].triggered.connect(self.show_small_window)
        self.actions['reset'].triggered.connect(self.window.reset_page)
        self.actions['settings'].triggered.connect(self.open_settings)
        self.actions['about'].triggered.connect(self.open_about)
        self.actions['autostart'].triggered.connect(self.toggle_autostart)
        self.actions['exit'].triggered.connect(self.app.quit)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.setVisible(True)

    def show_normal_window(self):
        self.window.set_normal_mode();
        self.window.show();
        self.window.raise_();
        self.window.activateWindow()

    def show_small_window(self):
        self.window.set_small_mode();
        self.window.show();
        self.window.raise_();
        self.window.activateWindow()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger: self.window.toggle_signal.emit()

    def open_settings(self):
        if self.settings_window is None or not self.settings_window.isVisible():
            self.settings_window = SettingsWindow();
            self.settings_window.settings_saved.connect(self.restart_hotkey_listener)
            self.settings_window.show()

    def open_about(self):
        if self.about_window is None or not self.about_window.isVisible():
            self.about_window = AboutWindow()
            self.about_window.show()

    def toggle_autostart(self, checked):
        self.config.set('Settings', 'autostart', str(checked).lower());
        save_config();
        manage_autostart(checked)

    def restart_hotkey_listener(self):
        if self.hotkey_listener and self.hotkey_listener.is_alive(): self.hotkey_listener.stop()
        self.start_hotkey_listener()

    def start_hotkey_listener(self):
        self.config = load_config()
        hotkey_str = self.config.get('Settings', 'hotkey', fallback='<alt>+<space>')

        def on_activate():
            try:
                self.window.toggle_signal.emit()
            except:
                pass

        try:
            self.hotkey_listener = keyboard.GlobalHotKeys({hotkey_str: on_activate});
            self.hotkey_listener.start()
        except Exception as e:
            print(f"Could not set hotkey: {e}")

    def cleanup(self):
        if self.hotkey_listener: self.hotkey_listener.stop()


# --- APPLICATION START ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    controller = AppController(app)
    sys.exit(app.exec())

