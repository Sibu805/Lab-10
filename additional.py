import json
import time
import pyttsx3
import pyaudio
import vosk
import requests
import webbrowser

class Speech:
    def __init__(self):
        self.tts = pyttsx3.init()

    def set_voice(self, speaker):
        voices = self.tts.getProperty('voices')
        return voices[speaker].id if speaker < len(voices) else voices[0].id

    def speak(self, text, speaker=0):
        self.tts.setProperty('voice', self.set_voice(speaker))
        self.tts.say(text)
        self.tts.runAndWait()
        time.sleep(0.1)

class Recognize:
    def __init__(self):
        model = vosk.Model('model_small')  
        self.recognizer = vosk.KaldiRecognizer(model, 16000)
        self.start_audio_stream()

    def start_audio_stream(self):
        pa = pyaudio.PyAudio()
        self.stream = pa.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=16000,
                              input=True,
                              frames_per_buffer=8000)

    def listen(self):
        while True:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                if result['text']:
                    yield result['text']

last_word_data = {}

def lookup_word(word):
    global last_word_data
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()[0]
        last_word_data = {
            "word": word,
            "definition": data["meanings"][0]["definitions"][0]["definition"],
            "example": data["meanings"][0]["definitions"][0].get("example", "No example available."),
            "link": f"https://www.google.com/search?q=define+{word}"
        }
        return True
    except:
        return False

def handle_command(command, speaker):
    global last_word_data

    if command.startswith("find "):
        word = command.split(" ", 1)[1]
        success = lookup_word(word)
        if success:
            speaker.speak(f"I found the word {word}. You can ask for meaning, example, or save it.")
        else:
            speaker.speak("Sorry, I couldn't find that word.")

    elif "meaning" in command:
        if last_word_data:
            speaker.speak(f"The meaning of {last_word_data['word']} is: {last_word_data['definition']}")
        else:
            speaker.speak("No word found. Please say 'find' followed by a word first.")

    elif "example" in command:
        if last_word_data:
            speaker.speak(f"Example: {last_word_data['example']}")
        else:
            speaker.speak("No word found. Please say 'find' followed by a word first.")

    elif "link" in command:
        if last_word_data:
            speaker.speak("Opening dictionary link.")
            webbrowser.open(last_word_data["link"])
        else:
            speaker.speak("No word found. Please say 'find' followed by a word first.")

    elif "save" in command:
        if last_word_data:
            with open("dictionary_saved.txt", "a", encoding="utf-8") as f:
                f.write(f"Word: {last_word_data['word']}\n")
                f.write(f"Meaning: {last_word_data['definition']}\n")
                f.write(f"Example: {last_word_data['example']}\n\n")
            speaker.speak("Word saved to file.")
        else:
            speaker.speak("No word found. Please say 'find' followed by a word first.")

    else:
        speaker.speak("I didn't understand that command.")

speech = Speech()
recognizer = Recognize()

speech.speak("Hello! I am your dictionary assistant. Say 'find' followed by a word to begin.")

for command_text in recognizer.listen():
    print("Heard:", command_text)
    if "exit" in command_text or "close" in command_text:
        speech.speak("Goodbye, I am always there for you")
        break
    else:
        handle_command(command_text, speech)
