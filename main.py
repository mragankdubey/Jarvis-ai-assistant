import speech_recognition as sr
import webbrowser
import pyttsx3

recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()


if __name__ == "__main__":
    speak("Initialising Jarvis...")

    while True:
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        print("Recognizing...")

        try:
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")

        except sr.UnknownValueError:
            speak("Sorry, I could not understand the audio.")
        except Error as e:
            print(f"Error: {e}")