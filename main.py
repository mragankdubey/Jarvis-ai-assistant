import speech_recognition as sr
import webbrowser
import pyttsx3

engine = pyttsx3.init()
recognizer = sr.Recognizer()

def speak(text):
    print("JARVIS SPEAKING:", text)
    engine.say(text)
    engine.runAndWait()

def processCommand(C):
    print(C)

    if "open google" in C.lower():
        webbrowser.open("https://www.google.com")
        
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


            #wake word = Jarvis
            word = recognizer.recognize_google(audio)
            print("Heard:", word)
            
            if (word.lower() == "jarvis"):
                speak("Yes")
                
                #listen for command 

                with sr.Microphone() as source:
                    print("Jarvis Active...")
                    audio = recognizer.listen(source)
                command = recognizer.recognize_google(audio)

                processCommand(command)

           


        except sr.UnknownValueError:
            speak("Sorry, I could not understand the audio.")
        except sr.RequestError as e:
            print(f"Error: {e}")