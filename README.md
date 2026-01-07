# Gemini Launcher

A lightweight desktop launcher for Google Gemini with productivity features.

![Gemini Launcher](icon.png)

## ✨ Features

### Window Modes

- **Normal (■)** - Compact 450×700 window
- **Wide (▬)** - Expanded 1100×700 window
- **Maximize (□)** - Full screen with taskbar

### Toolbar Actions

| Button | Action                                |
| ------ | ------------------------------------- |
| −      | Zoom out                              |
| +      | Zoom in                               |
| ○      | Reset zoom                            |
| ↻      | Refresh page                          |
| ⤓      | Export chat to text file              |
| ⬇/⬆    | Toggle tray mode (Alt+Tab visibility) |
| ⚙      | Settings                              |

### Keyboard Shortcuts

| Shortcut       | Action                                   |
| -------------- | ---------------------------------------- |
| `Alt+Space`    | Toggle window visibility                 |
| `Ctrl+Shift+G` | Capture selected text and send to Gemini |
| `F5`           | Refresh page                             |

### Productivity Features

- 📌 **Position Memory** - Window opens where you left it
- 🔍 **Zoom Memory** - Remembers your preferred zoom level
- 📋 **Clipboard Integration** - Auto-paste clipboard content
- 🔔 **Notifications** - Get notified when Gemini responds
- 📤 **Export Chat** - Save conversations to text files
- 📋 **Copy Fix** - Code copy buttons work properly

### System Integration

- 🔲 **System Tray** - Runs in background
- 🚀 **Start with Windows** - Optional autostart
- 🔝 **Always on Top** - Stay above other windows (toggleable)

## 📦 Installation

### Option 1: Run from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/GeminiLauncher.git
cd GeminiLauncher

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

### Option 2: Download Executable

Download `GeminiLauncher.exe` from [Releases](https://github.com/yourusername/GeminiLauncher/releases) and run directly.

## 📋 Requirements

- Python 3.10+
- PyQt6
- PyQt6-WebEngine
- pynput
- pywin32 (Windows only)
- winshell (Windows only)
- Pillow

## ⚙️ Configuration

Settings are stored in `%APPDATA%\GeminiLauncher\config.ini`:

```ini
[Settings]
hotkey = <alt>+<space>
clipboard_hotkey = <ctrl>+<shift>+g
autostart = false
auto_paste_clipboard = false
minimize_to_tray = true
notifications_enabled = true

[Window]
width = 450
height = 700
x = -1
y = -1
zoom = 1.0
```

## 🛠️ Building Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name="GeminiLauncher" main.py
```

The executable will be in the `dist` folder.

## 📄 License

MIT License - feel free to use and modify.

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

Made with ❤️ for Gemini users
