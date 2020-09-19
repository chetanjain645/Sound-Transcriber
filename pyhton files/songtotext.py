import speech_recognition as sr

audio = "english.wav"
r = sr.Recognizer()


with sr.AudioFile(audio) as source:
    audio = r.record(source)
    print("done")

    try:
        text = r.recognize_google(audio)
        print(text)

    except Exception as e:
        print(e)
