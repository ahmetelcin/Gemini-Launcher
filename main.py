# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Gemini Launcher v1.2
#
# Description:
# This application is a desktop utility designed for quick access to Google
# Gemini. It runs in the background, resides as an icon in the system tray,
# and can be invoked via a global keyboard shortcut.
#
# Required Libraries:
# PyQt6, PyQt6-WebEngine, pynput, pywin32, Pillow, winshell
# -----------------------------------------------------------------------------

import sys
from pynput import keyboard
from pathlib import Path
import os
import configparser
import threading
import webbrowser

try:
    import winshell
    from win32com.client import Dispatch
except ImportError:
    winshell = None

from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, QMenu,
                             QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QCheckBox, QGroupBox, QToolBar, QSizePolicy)
from PyQt6.QtGui import QIcon, QAction, QKeyEvent, QClipboard
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QStandardPaths, QTimer, QSize

# --- APPLICATION INFO ---
APP_VERSION = "1.2"

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

# Try different icon formats (ico works best for system tray)
if (BASE_PATH / "icon.ico").exists():
    ICON_PATH = BASE_PATH / "icon.ico"
elif (BASE_PATH / "icon.png").exists():
    ICON_PATH = BASE_PATH / "icon.png"
elif (BASE_PATH / "icon.svg").exists():
    ICON_PATH = BASE_PATH / "icon.svg"
else:
    ICON_PATH = BASE_PATH / "icon.ico"  # Default, even if not exists

# --- CONFIGURATION MANAGEMENT ---
config = configparser.ConfigParser()


def load_config():
    if not CONFIG_FILE.exists():
        config['Settings'] = {
            'hotkey': '<alt>+<space>', 
            'autostart': 'false',
            'clipboard_hotkey': '<ctrl>+<shift>+g',
            'auto_paste_clipboard': 'false',
            'minimize_to_tray': 'true',
            'notifications_enabled': 'true'
        }
        config['Window'] = {'width': '450', 'height': '700', 'x': '-1', 'y': '-1'}
        save_config()
    config.read(CONFIG_FILE, encoding='utf-8')
    # Ensure Window section exists for older configs
    if 'Window' not in config:
        config['Window'] = {'width': '450', 'height': '700', 'x': '-1', 'y': '-1'}
        save_config()
    # Ensure x, y exist for older configs
    if 'x' not in config['Window']:
        config.set('Window', 'x', '-1')
        config.set('Window', 'y', '-1')
        save_config()
    # Ensure new settings exist for older configs
    if 'clipboard_hotkey' not in config['Settings']:
        config.set('Settings', 'clipboard_hotkey', '<ctrl>+<shift>+g')
        save_config()
    if 'auto_paste_clipboard' not in config['Settings']:
        config.set('Settings', 'auto_paste_clipboard', 'false')
        save_config()
    if 'minimize_to_tray' not in config['Settings']:
        config.set('Settings', 'minimize_to_tray', 'true')
        save_config()
    if 'notifications_enabled' not in config['Settings']:
        config.set('Settings', 'notifications_enabled', 'true')
        save_config()
    if 'zoom' not in config['Window']:
        config.set('Window', 'zoom', '1.0')
        save_config()
    return config


def save_config():
    with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
        config.write(configfile)


# --- UTILITY FUNCTIONS ---
def check_internet_connection():
    """Check if there's an internet connection"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


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
        self.setMinimumWidth(400)
        self.layout = QVBoxLayout(self)
        
        # --- Hotkeys Group ---
        hotkeys_group = QGroupBox("Hotkeys")
        hotkeys_layout = QVBoxLayout(hotkeys_group)
        
        # Main hotkey
        self.hotkey_label = QLabel("Toggle Window Hotkey:")
        hotkeys_layout.addWidget(self.hotkey_label)
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("Click here and press keys to record...")
        self.hotkey_input.setText(config.get('Settings', 'hotkey'))
        self.hotkey_input.installEventFilter(self)
        hotkeys_layout.addWidget(self.hotkey_input)
        
        # Clipboard hotkey
        self.clipboard_hotkey_label = QLabel("Send Selection to Gemini Hotkey:")
        hotkeys_layout.addWidget(self.clipboard_hotkey_label)
        self.clipboard_hotkey_input = QLineEdit()
        self.clipboard_hotkey_input.setPlaceholderText("Click here and press keys to record...")
        self.clipboard_hotkey_input.setText(config.get('Settings', 'clipboard_hotkey', fallback='<ctrl>+<shift>+g'))
        self.clipboard_hotkey_input.installEventFilter(self)
        hotkeys_layout.addWidget(self.clipboard_hotkey_input)
        
        self.layout.addWidget(hotkeys_group)
        
        # --- Behavior Group ---
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)
        
        # Auto-paste clipboard checkbox
        self.auto_paste_checkbox = QCheckBox("Auto-paste clipboard content when opening")
        self.auto_paste_checkbox.setChecked(config.getboolean('Settings', 'auto_paste_clipboard', fallback=False))
        behavior_layout.addWidget(self.auto_paste_checkbox)
        
        # Minimize to tray checkbox
        self.minimize_to_tray_checkbox = QCheckBox("Minimize to system tray instead of taskbar")
        self.minimize_to_tray_checkbox.setChecked(config.getboolean('Settings', 'minimize_to_tray', fallback=True))
        behavior_layout.addWidget(self.minimize_to_tray_checkbox)
        
        # Notifications checkbox
        self.notifications_checkbox = QCheckBox("Show notifications when Gemini responds")
        self.notifications_checkbox.setChecked(config.getboolean('Settings', 'notifications_enabled', fallback=True))
        behavior_layout.addWidget(self.notifications_checkbox)
        
        self.layout.addWidget(behavior_group)
        
        # --- Buttons ---
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)
        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.close)
        
        # Track which input is being edited
        self.current_hotkey_input = None

    def eventFilter(self, source, event):
        if event.type() == QKeyEvent.Type.KeyPress:
            # Check if source is one of our hotkey inputs
            if source is self.hotkey_input or (hasattr(self, 'clipboard_hotkey_input') and source is self.clipboard_hotkey_input):
                key, mods = event.key(), event.modifiers()
                key_str, mod_str = self.qt_key_to_pynput(key), self.qt_mods_to_pynput(mods)
                if key_str: 
                    source.setText("+".join(mod_str + [key_str]))
                    return True
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
        config.set('Settings', 'clipboard_hotkey', self.clipboard_hotkey_input.text())
        config.set('Settings', 'auto_paste_clipboard', str(self.auto_paste_checkbox.isChecked()).lower())
        config.set('Settings', 'minimize_to_tray', str(self.minimize_to_tray_checkbox.isChecked()).lower())
        config.set('Settings', 'notifications_enabled', str(self.notifications_checkbox.isChecked()).lower())
        save_config()
        self.settings_saved.emit()
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
    clipboard_signal = pyqtSignal(str)
    open_settings_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.profile = QWebEngineProfile("persistent_gemini_profile", self)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.profile.setCachePath(str(PROFILE_DATA_PATH));
        self.profile.setPersistentStoragePath(str(PROFILE_DATA_PATH))
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.toggle_signal.connect(self.toggle_visibility)
        self.clipboard_signal.connect(self.open_with_text)
        self.setWindowTitle("Gemini Launcher")
        self.browser = QWebEngineView(self.profile)
        self.browser.setUrl(QUrl("https://gemini.google.com"))
        self.setCentralWidget(self.browser)
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        
        # Enable clipboard access and optimize WebEngine settings
        from PyQt6.QtWebEngineCore import QWebEngineSettings
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanPaste, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        
        # Open external links in default browser
        self.browser.page().setUrlRequestInterceptor(None)  # Clear any interceptor
        self.browser.page().newWindowRequested.connect(self.handle_new_window)
        
        # Inject clipboard fix when page loads
        self.browser.loadFinished.connect(self.inject_clipboard_fix)
        
        # Track if window should show in taskbar (alt-tab)
        self.show_in_taskbar = True
        
        # --- Custom Toolbar with Icon Buttons ---
        self.toolbar = QToolBar("Mode Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(16, 16))
        self.toolbar.setStyleSheet("""
            QToolBar {
                background: #202020;
                border: none;
                padding: 2px 5px;
                spacing: 3px;
            }
            QPushButton {
                background: transparent;
                color: #aaa;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #333;
                color: #fff;
            }
            QPushButton:pressed {
                background: #444;
            }
        """)
        
        # LEFT SIDE: Mode buttons
        self.btn_normal = QPushButton("\u25a0")  # Small square icon
        self.btn_normal.setToolTip("Normal Size (450×700)")
        self.btn_normal.clicked.connect(self.set_normal_mode)
        self.toolbar.addWidget(self.btn_normal)
        
        self.btn_wide = QPushButton("\u25ac")  # Wide rectangle icon
        self.btn_wide.setToolTip("Wide Mode (800×700)")
        self.btn_wide.clicked.connect(self.set_wide_mode)
        self.toolbar.addWidget(self.btn_wide)
        
        self.btn_maximize = QPushButton("\u25a1")  # Empty square icon
        self.btn_maximize.setToolTip("Maximize")
        self.btn_maximize.clicked.connect(self.set_maximized_mode)
        self.toolbar.addWidget(self.btn_maximize)
        
        # Spacer to push right buttons to right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)
        
        # RIGHT SIDE: Actions and Settings
        self.btn_zoom_out = QPushButton("\u2212")  # Minus sign
        self.btn_zoom_out.setToolTip("Zoom Out (Ctrl -)")
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        self.toolbar.addWidget(self.btn_zoom_out)
        
        self.btn_zoom_in = QPushButton("+")  # Plus sign
        self.btn_zoom_in.setToolTip("Zoom In (Ctrl +)")
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.toolbar.addWidget(self.btn_zoom_in)
        
        self.btn_zoom_reset = QPushButton("\u25cb")  # Circle/reset icon
        self.btn_zoom_reset.setToolTip("Reset Zoom (Ctrl 0)")
        self.btn_zoom_reset.clicked.connect(self.reset_zoom)
        self.toolbar.addWidget(self.btn_zoom_reset)
        
        self.btn_refresh = QPushButton("\u21bb")  # Refresh icon
        self.btn_refresh.setToolTip("Refresh Page (F5)")
        self.btn_refresh.clicked.connect(self.refresh_page)
        self.toolbar.addWidget(self.btn_refresh)
        
        self.btn_export = QPushButton("\u2913")  # Download/export icon
        self.btn_export.setToolTip("Export Chat")
        self.btn_export.clicked.connect(self.export_chat)
        self.toolbar.addWidget(self.btn_export)
        
        self.btn_tray_toggle = QPushButton("\u2b07")  # Down arrow (tray mode)
        self.btn_tray_toggle.setToolTip("Tray Mode: ON (always on top, hidden from Alt+Tab)")
        self.btn_tray_toggle.setCheckable(True)
        self.btn_tray_toggle.setChecked(True)  # Default: tray mode on
        self.btn_tray_toggle.clicked.connect(self.toggle_taskbar_visibility)
        self.toolbar.addWidget(self.btn_tray_toggle)
        
        self.btn_settings = QPushButton("\u2699")  # Gear icon
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.clicked.connect(self.open_settings_signal.emit)
        self.toolbar.addWidget(self.btn_settings)
        
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        # Load saved custom window size and position
        self.custom_width = config.getint('Window', 'width', fallback=450)
        self.custom_height = config.getint('Window', 'height', fallback=700)
        self.custom_x = config.getint('Window', 'x', fallback=-1)
        self.custom_y = config.getint('Window', 'y', fallback=-1)
        
        # Debounce timer for saving window geometry
        self.save_geometry_timer = QTimer(self)
        self.save_geometry_timer.setSingleShot(True)
        self.save_geometry_timer.timeout.connect(self.save_geometry_to_config)
        
        # Track last page content for notification
        self.last_content_length = 0
        self.page_monitor_timer = QTimer(self)
        self.page_monitor_timer.timeout.connect(self.check_for_response)
        self.page_monitor_timer.start(10000)  # Check every 10 seconds
        
        self.set_normal_mode()
        
        # Load saved zoom level
        saved_zoom = config.getfloat('Window', 'zoom', fallback=1.0)
        self.browser.setZoomFactor(saved_zoom)
    
    def check_for_response(self):
        """Check if Gemini has responded (for notifications)"""
        if not config.getboolean('Settings', 'notifications_enabled', fallback=True):
            return
        if not self.isVisible():
            # Only check when window is hidden
            def callback(content_length):
                if content_length > self.last_content_length + 100:  # Significant change
                    self.show_notification("Gemini", "New response received!")
                self.last_content_length = content_length
            
            self.browser.page().runJavaScript(
                "document.body.innerText.length",
                callback
            )
    
    def show_notification(self, title, message):
        """Show a system tray notification"""
        # Will be called from AppController which has access to tray_icon
        pass
    
    def handle_new_window(self, request):
        """Handle new window requests - open external links in default browser"""
        url = request.requestedUrl().toString()
        # If it's not a gemini URL, open in external browser
        if 'gemini.google.com' not in url:
            webbrowser.open(url)
        else:
            # Navigate to the URL in the current browser
            self.browser.setUrl(request.requestedUrl())
    
    def inject_clipboard_fix(self):
        """Inject JavaScript to fix clipboard copy in embedded browser"""
        js_code = """
        (function() {
            // Override clipboard API for embedded browser compatibility
            if (!window._clipboardFixApplied) {
                window._clipboardFixApplied = true;
                
                // Create a helper function to copy text
                window.copyToClipboard = function(text) {
                    const textarea = document.createElement('textarea');
                    textarea.value = text;
                    textarea.style.position = 'fixed';
                    textarea.style.left = '-9999px';
                    document.body.appendChild(textarea);
                    textarea.select();
                    try {
                        document.execCommand('copy');
                        console.log('Copied to clipboard via fallback');
                    } catch (e) {
                        console.error('Copy failed:', e);
                    }
                    document.body.removeChild(textarea);
                };
                
                // Override navigator.clipboard.writeText
                if (navigator.clipboard) {
                    const originalWriteText = navigator.clipboard.writeText.bind(navigator.clipboard);
                    navigator.clipboard.writeText = function(text) {
                        return originalWriteText(text).catch(function() {
                            window.copyToClipboard(text);
                            return Promise.resolve();
                        });
                    };
                }
                
                // Add click listener for copy buttons
                document.addEventListener('click', function(e) {
                    const btn = e.target.closest('button');
                    if (btn) {
                        const svg = btn.querySelector('svg');
                        const ariaLabel = btn.getAttribute('aria-label') || '';
                        if (ariaLabel.toLowerCase().includes('copy') || 
                            ariaLabel.toLowerCase().includes('kopyala')) {
                            // Find the code block
                            const codeBlock = btn.closest('div')?.querySelector('code, pre');
                            if (codeBlock) {
                                window.copyToClipboard(codeBlock.innerText);
                            }
                        }
                    }
                }, true);
            }
        })();
        """
        self.browser.page().runJavaScript(js_code)
    
    def refresh_page(self):
        """Refresh the current page"""
        self.browser.reload()
    
    def save_zoom(self):
        """Save current zoom level to config"""
        config.set('Window', 'zoom', str(self.browser.zoomFactor()))
        save_config()
    
    def zoom_in(self):
        """Zoom in on the page"""
        current_zoom = self.browser.zoomFactor()
        new_zoom = min(current_zoom + 0.1, 3.0)
        self.browser.setZoomFactor(new_zoom)
        self.save_zoom()
    
    def zoom_out(self):
        """Zoom out on the page"""
        current_zoom = self.browser.zoomFactor()
        new_zoom = max(current_zoom - 0.1, 0.5)
        self.browser.setZoomFactor(new_zoom)
        self.save_zoom()
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.browser.setZoomFactor(1.0)
        self.save_zoom()
    
    def export_chat(self):
        """Export the current chat to a text file"""
        from PyQt6.QtWidgets import QFileDialog
        from datetime import datetime
        
        def callback(text):
            if text:
                # Get save file path
                default_name = f"gemini_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Export Chat", default_name, "Text Files (*.txt);;All Files (*)"
                )
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text)
        
        # Get the chat text content
        self.browser.page().runJavaScript(
            "document.body.innerText",
            callback
        )

    def set_maximized_mode(self):
        """Set window to maximized (fills screen but shows taskbar)"""
        self.showMaximized()

    def set_normal_mode(self):
        """Set window to GPT-like normal size"""
        self.showNormal()
        w, h = 450, 700
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - w) // 2
        y = int(screen.height() * 0.30)  # Higher on screen
        self.setGeometry(x, y, w, h)
    
    def set_wide_mode(self):
        """Set window to wide mode"""
        self.showNormal()
        w, h = 1100, 700
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - w) // 2
        y = int(screen.height() * 0.15)
        self.setGeometry(x, y, w, h)
    
    def toggle_taskbar_visibility(self, checked):
        """Toggle whether the window shows in taskbar/alt-tab and stays on top"""
        self.show_in_taskbar = not checked
        was_visible = self.isVisible()
        # Save current geometry before changing flags
        current_geo = self.geometry()
        
        if checked:
            # Tray mode ON - hide from alt-tab, stay on top
            self.btn_tray_toggle.setText("⬇")
            self.btn_tray_toggle.setToolTip("Tray Mode: ON (always on top, hidden from Alt+Tab)")
            new_flags = self.windowFlags() | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint
        else:
            # Tray mode OFF - show in alt-tab, can go to background
            self.btn_tray_toggle.setText("⬆")
            self.btn_tray_toggle.setToolTip("Tray Mode: OFF (normal window, visible in Alt+Tab)")
            new_flags = (self.windowFlags() & ~Qt.WindowType.Tool) & ~Qt.WindowType.WindowStaysOnTopHint
        
        self.setWindowFlags(new_flags)
        # Restore geometry and re-show window
        self.setGeometry(current_geo)
        if was_visible:
            self.show()

    def set_custom_mode(self):
        """Set window to saved custom size and position"""
        self.showNormal()
        w, h = self.custom_width, self.custom_height
        screen = QApplication.primaryScreen().geometry()
        if self.custom_x >= 0 and self.custom_y >= 0:
            x, y = self.custom_x, self.custom_y
        else:
            x, y = (screen.width() - w) // 2, int(screen.height() * 0.3)
        self.setGeometry(x, y, w, h)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        from PyQt6.QtCore import Qt
        key = event.key()
        modifiers = event.modifiers()
        
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
                self.zoom_in()
                return
            elif key == Qt.Key.Key_Minus:
                self.zoom_out()
                return
            elif key == Qt.Key.Key_0:
                self.reset_zoom()
                return
        elif key == Qt.Key.Key_F5:
            self.refresh_page()
            return
        
        super().keyPressEvent(event)

    def changeEvent(self, event):
        """Handle minimize to tray"""
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized() and config.getboolean('Settings', 'minimize_to_tray', fallback=True):
                event.ignore()
                self.hide()

    def resizeEvent(self, event):
        """Save custom size when user resizes the window (not when maximized/fullscreen)"""
        super().resizeEvent(event)
        if not self.isMaximized() and not self.isFullScreen():
            self.custom_width = event.size().width()
            self.custom_height = event.size().height()
            # Debounce save - wait 500ms after last resize
            self.save_geometry_timer.start(500)
    
    def moveEvent(self, event):
        """Save position when user moves the window"""
        super().moveEvent(event)
        if not self.isMaximized() and not self.isFullScreen():
            self.custom_x = event.pos().x()
            self.custom_y = event.pos().y()
            # Debounce save
            self.save_geometry_timer.start(500)
    
    def save_geometry_to_config(self):
        """Save geometry to config (called after debounce)"""
        config.set('Window', 'width', str(self.custom_width))
        config.set('Window', 'height', str(self.custom_height))
        config.set('Window', 'x', str(self.custom_x))
        config.set('Window', 'y', str(self.custom_y))
        save_config()

    def toggle_visibility(self):
        if self.isVisible():
            # If fullscreen or maximized, don't hide - just ignore the hotkey
            # Use windowState() for more reliable detection
            state = self.windowState()
            if state & Qt.WindowState.WindowFullScreen or state & Qt.WindowState.WindowMaximized:
                return
            # Save geometry before hiding (use geometry() for consistency)
            geo = self.geometry()
            self.custom_x = geo.x()
            self.custom_y = geo.y()
            self.custom_width = geo.width()
            self.custom_height = geo.height()
            self.save_geometry_to_config()
            self.hide()
        else:
            w, h = self.custom_width, self.custom_height
            screen = QApplication.primaryScreen().geometry()
            # Use saved position if available, otherwise center
            if self.custom_x >= 0 and self.custom_y >= 0:
                x, y = self.custom_x, self.custom_y
            else:
                x, y = (screen.width() - w) // 2, int(screen.height() * 0.3)
            self.setGeometry(x, y, w, h)
            self.show()
            self.raise_()
            self.activateWindow()
            
            # Auto-paste clipboard if enabled
            if config.getboolean('Settings', 'auto_paste_clipboard', fallback=False):
                self.paste_clipboard_to_input()
    
    def paste_clipboard_to_input(self):
        """Paste clipboard content into Gemini's input field"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            # Escape special characters for JavaScript
            escaped_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '')
            js_code = f"""
            (function() {{
                var textarea = document.querySelector('rich-textarea');
                if (textarea) {{
                    var p = textarea.querySelector('p');
                    if (p) {{
                        p.textContent = '{escaped_text}';
                        // Trigger input event
                        var event = new Event('input', {{ bubbles: true }});
                        textarea.dispatchEvent(event);
                    }}
                }}
            }})();
            """
            self.browser.page().runJavaScript(js_code)
    
    def open_with_text(self, text):
        """Open window and paste the provided text"""
        if not self.isVisible():
            w, h = self.custom_width, self.custom_height
            screen = QApplication.primaryScreen().geometry()
            x, y = (screen.width() - w) // 2, int(screen.height() * 0.3)
            self.setGeometry(x, y, w, h)
            self.show()
            self.raise_()
            self.activateWindow()
        
        if text:
            # Wait a bit for the page to be ready
            QTimer.singleShot(500, lambda: self.inject_text(text))
    
    def inject_text(self, text):
        """Inject text into Gemini's input field"""
        escaped_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '')
        js_code = f"""
        (function() {{
            var textarea = document.querySelector('rich-textarea');
            if (textarea) {{
                var p = textarea.querySelector('p');
                if (p) {{
                    p.textContent = '{escaped_text}';
                    var event = new Event('input', {{ bubbles: true }});
                    textarea.dispatchEvent(event);
                }}
            }}
        }})();
        """
        self.browser.page().runJavaScript(js_code)

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
        self.clipboard_hotkey_listener = None
        self.actions = {}
        self.setup_tray_icon()
        self.start_hotkey_listener()
        manage_autostart(self.config.getboolean('Settings', 'autostart'))
        self.app.aboutToQuit.connect(self.cleanup)
        
        # Connect notification method and settings signal
        self.window.show_notification = self.show_notification
        self.window.open_settings_signal.connect(self.open_settings)

    def show_notification(self, title, message):
        """Show a system tray notification"""
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon()
        self.menu = QMenu()
        icon = QIcon(str(ICON_PATH))
        self.tray_icon.setIcon(icon);
        self.tray_icon.setToolTip("Gemini Launcher")

        self.actions['open_maximize'] = QAction("□ Maximize")
        self.actions['open_normal'] = QAction("■ Normal")
        self.actions['open_custom'] = QAction("⬩ Custom Size")
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

        self.menu.addActions([self.actions['open_maximize'], self.actions['open_normal'], self.actions['open_custom']])
        self.menu.addSeparator()
        self.menu.addActions([self.actions['reset'], self.actions['settings'], self.actions['about']])
        self.menu.addSeparator()
        self.menu.addAction(self.actions['autostart'])
        self.menu.addSeparator()
        self.menu.addAction(self.actions['exit'])
        self.tray_icon.setContextMenu(self.menu)

        self.actions['open_maximize'].triggered.connect(self.show_maximized_window)
        self.actions['open_normal'].triggered.connect(self.show_normal_window)
        self.actions['open_custom'].triggered.connect(self.show_custom_window)
        self.actions['reset'].triggered.connect(self.window.reset_page)
        self.actions['settings'].triggered.connect(self.open_settings)
        self.actions['about'].triggered.connect(self.open_about)
        self.actions['autostart'].triggered.connect(self.toggle_autostart)
        self.actions['exit'].triggered.connect(self.app.quit)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.setVisible(True)

    def show_maximized_window(self):
        self.window.set_maximized_mode()
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def show_normal_window(self):
        self.window.set_normal_mode()
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def show_custom_window(self):
        self.window.set_custom_mode()
        self.window.show()
        self.window.raise_()
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
        if self.hotkey_listener and self.hotkey_listener.is_alive(): 
            self.hotkey_listener.stop()
        if self.clipboard_hotkey_listener and self.clipboard_hotkey_listener.is_alive():
            self.clipboard_hotkey_listener.stop()
        self.start_hotkey_listener()

    def start_hotkey_listener(self):
        self.config = load_config()
        hotkey_str = self.config.get('Settings', 'hotkey', fallback='<alt>+<space>')
        clipboard_hotkey_str = self.config.get('Settings', 'clipboard_hotkey', fallback='<ctrl>+<shift>+g')

        def on_activate():
            try:
                self.window.toggle_signal.emit()
            except:
                pass
        
        def on_clipboard_activate():
            """Capture current selection and send to Gemini"""
            try:
                # Use keyboard to copy current selection
                from pynput.keyboard import Controller, Key
                kb = Controller()
                # Press Ctrl+C to copy selection
                kb.press(Key.ctrl)
                kb.press('c')
                kb.release('c')
                kb.release(Key.ctrl)
                
                # Wait a bit then get clipboard
                import time
                time.sleep(0.1)
                
                # Get clipboard text (will be handled in main thread)
                clipboard = QApplication.clipboard()
                text = clipboard.text()
                if text:
                    self.window.clipboard_signal.emit(text)
            except Exception as e:
                print(f"Clipboard hotkey error: {e}")

        try:
            self.hotkey_listener = keyboard.GlobalHotKeys({hotkey_str: on_activate})
            self.hotkey_listener.start()
        except Exception as e:
            print(f"Could not set hotkey: {e}")
        
        try:
            self.clipboard_hotkey_listener = keyboard.GlobalHotKeys({clipboard_hotkey_str: on_clipboard_activate})
            self.clipboard_hotkey_listener.start()
        except Exception as e:
            print(f"Could not set clipboard hotkey: {e}")

    def cleanup(self):
        if self.hotkey_listener: self.hotkey_listener.stop()
        if self.clipboard_hotkey_listener: self.clipboard_hotkey_listener.stop()


# --- APPLICATION START ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    controller = AppController(app)
    sys.exit(app.exec())
