# Gemini Launcher

A lightweight Windows desktop launcher for Google Gemini. It runs in the system tray and opens Gemini in its own window with a global hotkey. This is an independent project and isn't affiliated with Google.

![Gemini Launcher icon](icon.png)

<!-- Demo: remove this comment's markers after adding docs/demo.gif
![Gemini Launcher demo](docs/demo.gif)
-->

## Features

- **Global hotkeys:** show or hide the window, or copy selected text into Gemini's input box from any app. You can change both hotkeys in Settings.
- **Window sizes:** normal (450×700), wide (1100×700), maximized, or your saved custom size.
- **Stays signed in:** your Gemini session is kept between launches.
- **System tray:** closing the window hides it, and the app keeps running in the background.
- **Tray mode:** switch between an always-on-top window and a normal window.
- **Zoom:** adjust the page zoom and keep your level between launches.
- **Chat export:** save the page's text to a `.txt` file.
- **Clipboard:** optionally paste clipboard text into the input box when the window opens, and use a built-in fix for copying from the embedded page.
- **Notifications:** optionally get a tray notification when the page content grows while the window is hidden. The app checks every 10 seconds.
- **External links:** links outside Gemini open in your default browser.
- **Start with Windows:** optional, for the packaged `.exe` only.

## Installation

Gemini Launcher runs on Windows only.

### Download

Download `Gemini.Launcher.exe` from [Releases](https://github.com/ahmetelcin/Gemini-Launcher/releases) and run it.

### Run from source

You need Python 3.10 or later.

```powershell
git clone https://github.com/ahmetelcin/Gemini-Launcher.git
cd Gemini-Launcher
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Build an executable

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.ico;." --name="GeminiLauncher" main.py
```

The executable is created in the `dist` folder.

## Usage

Sign in to Google in the app window the first time you use it. To quit, right-click the tray icon and select **Exit**.

| Shortcut | Action |
|---|---|
| `Alt+Space` | Show or hide the window |
| `Ctrl+Shift+G` | Copy the selected text into Gemini's input box |
| `F5` | Refresh the page |
| `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` | Zoom in, zoom out, reset zoom |

| Toolbar button | Action |
|---|---|
| ■ ▬ □ | Normal, wide, maximized |
| − + ○ | Zoom out, zoom in, reset zoom |
| ↻ | Refresh the page |
| ⤓ | Export the chat |
| ⬇ / ⬆ | Turn tray mode on or off |
| ⚙ | Open Settings |

Left-click the tray icon to show or hide the window. Right-click it for window sizes, **Go to Home (Reset)**, **Settings...**, **About...** and **Start with Windows**.

Settings are stored in `%APPDATA%\GeminiLauncher\config.ini`, and browser data is stored in `%LOCALAPPDATA%\GeminiLauncher`.

## License

[MIT](LICENSE)
