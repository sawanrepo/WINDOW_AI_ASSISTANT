# Windows Assistant Bot

A simple, offline-friendly Windows assistant that understands natural language to either launch installed apps or chat naturally with the user. Built using Python, Gemini API, and a minimal Tkinter-based GUI.

---

## Features

* **Natural Language Understanding**: Uses Google Gemini to detect intent — either open an app or chat.
* **Dynamic App Launcher**: Scans Start Menu `.lnk` shortcuts to fetch available installed apps.
* **Conversational Chat**: Uses Gemini for friendly natural conversation.
* **Error Handling**: Gracefully informs if an app is not found.
* **Lightweight GUI**: Built with Tkinter for user interaction.

---

## Technologies Used

* Python 
* Google Gemini API
* Tkinter (GUI)
* Windows OS (for `.lnk` based app scanning)

---

## File Structure

```bash
windows-assistant-bot/
├── assistant/
│   ├── __init__.py
│   ├── llm.py                 # Handles LLM communication
│   ├── app_launcher.py        # Opens apps via Start Menu shortcuts
│   ├── config.py              # Loads Gemini API key from .env
├── gui/
│   ├──__init__.py
│   ├──launcher.py
├──utils/
│    ├── __init__.py
│    ├── shortcut_scanner.py
├── main.py                    # Starts the GUI and core logic
├── requirements.txt           # Required Python packages
├── .env.temeplate             #change to .env           
└── README.md                  # This file
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/sawanrepo/WINDOW_AI_ASSISTANT.git
cd WINDOW_AI_ASSISTANT
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Gemini API Key

Create a `.env` file and add:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```
or rename .env.template to .env and fill required values.
---

## Usage

Run the assistant:

```bash
python main.py
```

Try typing commands like:

* `Open Spotify`
* `Launch Notepad`
* `Tell me a joke`
* `What's the weather today?`

The assistant will either launch the app or respond conversationally.

---

## Packaging as Executable

To build a `.exe` using PyInstaller:

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

### 2. Create Executable

```bash
pyinstaller --onefile --windowed main.py
```

The compiled `.exe` will be located in the `dist` directory.

---

## Contributions

Pull requests are welcome. If you'd like to contribute a feature, tool, or localization, open an issue first to discuss your idea.

---

## Contact

Made with ❤️ by Sawan Kumar

* Email: kumarsawan387@gmail.com
