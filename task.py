import json
import time
import pyttsx3
import pyaudio
import vosk
import requests

class Speech:
    def __init__(self):
        self.speaker = 0
        self.tts = pyttsx3.init()

    def set_voice(self, speaker):
        voices = self.tts.getProperty('voices')
        return voices[speaker].id if speaker < len(voices) else voices[0].id

    def text2voice(self, speaker=0, text='Ready'):
        self.tts.setProperty('voice', self.set_voice(speaker))
        self.tts.say(text)
        self.tts.runAndWait()
        time.sleep(0.1)


class Recognize:
    def __init__(self):
        model = vosk.Model('model_small') 
        self.record = vosk.KaldiRecognizer(model, 16000)
        self.stream_audio()

    def stream_audio(self):
        pa = pyaudio.PyAudio()
        self.stream = pa.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=16000,
                              input=True,
                              frames_per_buffer=8000)

    def listen(self):
        while True:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.record.AcceptWaveform(data):
                result = json.loads(self.record.Result())
                if result['text']:
                    yield result['text']


def speak(text):
    speech = Speech()
    speech.text2voice(speaker=0, text=text)


def get_weather():
    try:
        response = requests.get("https://wttr.in/Saint-Petersburg?format=j1")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        speak("Error in getting weather, try again after a few minutes")
        return None


def handle_command(command):
    weather = get_weather()
    if not weather:
        return

    current = weather["current_condition"][0]
    temp_c = int(current["temp_C"])
    wind_sp = int(current["windspeedKmph"])
    wind_dir = current["winddir16Point"]
    description = current["weatherDesc"][0]["value"]

    if "weather" in command:
        speak(f"The temperature in Saint Petersburg today is {temp_c} degrees Celsius with {description.lower()}.")
    elif "wind" in command:
        speak(f"The wind speed is {wind_sp} kilometers per hour.")
    elif "direction" in command:
        speak(f"The wind direction is {wind_dir}.")
    elif "save" in command:
        with open("weather.txt", "w", encoding="utf-8") as f:
            f.write(f"Temperature: {temp_c}°C\n")
            f.write(f"Condition: {description}\n")
            f.write(f"Wind: {wind_sp} km/h, direction: {wind_dir}\n")
        speak("Weather saved to file.")
    elif "walk" in command:
        if temp_c < 5 or wind_sp > 15:
            speak("It is not recommended to go for a walk.")
        else:
            speak("You can go for a walk. The weather is pleasant.")
    else:
        speak("Command not recognized.")



rec = Recognize()
speak('Hello there!, i am your assistant. How can i help you today ?')
print("Assistant started. Say a command...")
text_gen = rec.listen()

for text in text_gen:
    print("Command:", text)
    if "exit" in text or "close" in text:
        speak("Have a great day, i am always there for you.")
        break
    else:
        handle_command(text)
