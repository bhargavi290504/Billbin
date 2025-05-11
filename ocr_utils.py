import pytesseract
import cv2
import tempfile
import re

def extract_from_image(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        file.save(tmp.name)
        image = cv2.imread(tmp.name)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        text = pytesseract.image_to_string(thresh)

        amount = 0
        purpose = "Unknown"
        lines = text.splitlines()
        lines = [line.strip() for line in lines if line.strip()]
        amount_pattern = re.compile(r'[\₹$]?\s?(\d+(?:\.\d{1,2})?)')

       
        for line in lines:
            if "grand total" in line.lower():
                match = amount_pattern.search(line)
                if match:
                    amount = float(match.group(1))
                    purpose = "Grand Total"
                    return purpose, int(amount)

       
        for line in lines:
            if "total" in line.lower():
                match = amount_pattern.search(line)
                if match:
                    amount = float(match.group(1))
                    purpose = "Total"
                    return purpose, int(amount)  
                
        return purpose, int(amount)
