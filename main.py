import os
import speech_recognition as sr
import webbrowser
import pyttsx3
import requests
from dotenv import load_dotenv

load_dotenv()
newsapi_key = os.getenv("newsapi_key")

recognizer = sr.Recognizer()


def speak(text):
    print("JARVIS SPEAKING:", text)
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.stop()




def processCommand(C):
    print(C)

    if "open google" in C.lower():
        webbrowser.open("https://www.google.com")

    elif "open youtube" in C.lower():
        webbrowser.open("https://www.youtube.com")

    elif "open whatsapp" in C.lower():
        webbrowser.open("https://web.whatsapp.com/")

    elif "open github" in C.lower():
        webbrowser.open("https://github.com/")

    elif C.lower().startswith("play"):
        song = C.lower().replace("play", "").strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={song}")

    elif "news" in C.lower():
        r = requests.get(
            f"https://newsapi.org/v2/top-headlines?country=us&category=business&apiKey={newsapi_key}"
        )

        if r.status_code == 200:
            data = r.json()
            articles = data["articles"]

            if articles:
                speak("Here are the top news headlines:")

                for article in articles[:5]:
                    speak(article["title"])
            else:
                speak("No news articles found.")


if __name__ == "__main__":

    speak("Initialising Jarvis...")

    with sr.Microphone() as source:
        print("Calibrating microphone...")
        recognizer.adjust_for_ambient_noise(source, duration=1)

    while True:

        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = recognizer.listen(source)

                print("Recognizing...")

            # wake word = Jarvis
            word = recognizer.recognize_google(audio)
            print("Heard:", repr(word))

            if "jarvis" in word.casefold():
                print("Wake word detected.")
                speak("Yes")

                # listen for command
                with sr.Microphone() as source:
                    print("Jarvis Active...")
                    audio = recognizer.listen(source)

                command = recognizer.recognize_google(audio)

                processCommand(command)

        except sr.UnknownValueError:
            speak("Sorry, I could not understand the audio.")

        except sr.RequestError as e:
            print(f"Error: {e}")