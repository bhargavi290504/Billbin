# 📊 Billbin – Smart Bill Tracker with Image, Voice & Alerts

Billbin is a smart personal finance tracker that helps you manage bills easily using images or voice input. It extracts bill details automatically, tracks spending in real-time, and alerts you when your balance gets low.

---

## 🔥 Features

- 📷 Upload bill **images** (OCR using Tesseract)
- 🎙️ Add bills via **voice input**
- 📅 Track bills using a **calendar view**
- 💰 Set a **monthly spending limit**
- 📆 **Add bills for past dates** if missed
- 📉 Get **alerts** when remaining balance is low (email/onsite)
- 🔐 **User authentication** (register/login)
- 🎨 Colorful, user-friendly UI

---

## 🛠️ Tech Stack

| Layer        | Tech Used                  |
|--------------|-----------------------------|
| Frontend     | HTML, CSS     
| Backend      | Python, Flask               |
| Database     | SQLite                      |
| OCR          | Tesseract                   |
| Voice Input  | SpeechRecognition (Python)  |
| Email Alert  | SMTP (Gmail)     
| Calendar API | Google Calendar (Optional)  |

---

## 📦 Installation

### 🔧 Prerequisites

- Python 3.x
- pip
- Tesseract OCR (`brew install tesseract` on Mac / `sudo apt install tesseract-ocr` on Linux)
- Gmail App Password (or SendGrid API Key)

### 🖥️ Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/billbin.git
cd billbin

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python
>>> from app import db
>>> db.create_all()
>>> exit()

# Run the app
python app.py

 
