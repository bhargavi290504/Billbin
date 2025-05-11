import speech_recognition as sr

def extract_from_voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak your bill (e.g., Pizza 350):")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio)
        words = text.split()
        for word in words:
            if word.replace('.', '').isdigit():
                amount = int(float(word))
                purpose = text.replace(word, '').strip()
                return purpose, amount
    except:
        return "Voice Not Clear", 0
