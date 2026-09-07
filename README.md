# 🤖 PLUCK - AI Voice and Text Desktop Assistant

PLUCK is a personal AI-powered desktop assistant designed to provide an interactive and intelligent experience through **voice and text communication**. Inspired by virtual assistants like Jarvis, PLUCK can listen to user commands, respond intelligently, and perform various tasks on a Windows computer.

---

## ✨ Features

* 🎤 **Voice Recognition** – Listen to user commands through the microphone.
* 🔊 **Text-to-Speech** – Respond to users using a natural voice.
* 💬 **Chat Interface** – Communicate with PLUCK through a graphical chat interface.
* 🤖 **AI-Powered Responses** – Uses an AI model/API to understand and respond to user queries.
* 🖥️ **Desktop Assistant** – Designed to perform tasks and assist users on their computer.
* 🎨 **Jarvis-Style User Interface** – Modern and interactive assistant interface.
* 🔄 **Continuous Interaction** – Supports ongoing conversations with the assistant.
* 👑 **Personalized Greeting** – PLUCK greets the user when the application starts.

Example greeting:

> **"Hi Queen, I am PLUCK, your assistant. How can I help you today?"**

---

## 🛠️ Technologies Used

* **Python**
* **Tkinter** – Graphical User Interface (GUI)
* **Speech Recognition** – Voice input processing
* **Text-to-Speech (TTS)** – Voice responses
* **Edge TTS** – Natural voice synthesis
* **Pygame** – Audio playback
* **AI API / Large Language Model (LLM)** – Intelligent responses and command understanding

---

## 📂 Project Structure

```text
PLUCK-AI/
│
├── main.py
├── requirements.txt
├── README.md

> The file structure may vary depending on the version of the PLUCK project.

---

## ⚙️ Installation

### 1. Clone or Download the Project

Download the project files and extract them into a folder.

```bash
git clone <repository-url>
```

Or download the ZIP file from the repository.

---

### 2. Open the Project Folder

Open the project folder in **Visual Studio Code** or any Python IDE.

---

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the virtual environment:

### Windows

```bash
.venv\Scripts\activate
```

---

### 4. Install Required Libraries

```bash
pip install -r requirements.txt
```

If a `requirements.txt` file is not available, install the required packages manually.

Example:

```bash
pip install pygame edge-tts SpeechRecognition
```

Additional packages may be required depending on the features enabled in your version of PLUCK.

---

## 🔑 API Configuration

PLUCK uses an AI model/API to generate intelligent responses.

Add your API key to the appropriate configuration file or environment variable.

Example:

```python
API_KEY = "YOUR_API_KEY_HERE"
```

⚠️ **Important:** Never upload your API key to GitHub or share it publicly.

A better approach is to store the API key in an environment variable or `.env` file.

Example `.env` file:

```text
API_KEY=your_api_key_here
```

---

## ▶️ Running PLUCK

After installing all dependencies, run the application using:

```bash
python main.py
```

PLUCK will start and display the graphical user interface.

---

## 🎤 Using Voice Commands

1. Open PLUCK.
2. Click the **Start Listening** button.
3. Speak your command clearly.
4. PLUCK will process your command.
5. The assistant will respond through text and voice.

---

## 💬 Using the Chat Interface

You can also interact with PLUCK by typing your message into the chat box.

Example commands:

```text
Hello PLUCK
What time is it?
Open Google
Tell me a joke
How are you?
```

PLUCK will process the request and provide a response.

---

## 🖥️ System Requirements

* Windows 10 or Windows 11
* Python 3.10 or above
* Internet connection for AI/API features
* Working microphone for voice commands
* Speaker or headphones for voice responses

---

## 🚀 Future Improvements

Future versions of PLUCK may include:

* 🔐 Improved security and API key management
* 🖥️ Advanced PC control
* 🌐 Web search capabilities
* 📁 File and folder management
* 📧 Email assistance
* 🗓️ Calendar and reminder support
* 🎵 Music control
* 🧠 Improved conversation memory
* 🤖 More advanced AI models
* 📱 Integration with additional applications and services

---

## 👩‍💻 Developer

**Pooja Hibare**

PLUCK is a personal AI assistant project developed as part of an exploration into **Artificial Intelligence, Voice Assistants, Python Development, and Desktop Automation**.

---

## 📜 License

This project is currently intended for educational and personal use.

You may modify and improve the project for learning purposes.

---

## ⭐ About PLUCK

PLUCK is more than just a voice assistant. It is an attempt to build an intelligent, interactive, and personalized AI companion for everyday computer tasks.

> **"Hi Queen, I am PLUCK, your assistant. How can I help you today?" 👑🤖**

---

### ⭐ If you like this project, consider giving it a star!
