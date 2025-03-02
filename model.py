import pytesseract
from PIL import Image
import cv2
import json
import google.generativeai as genai


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  

# Configure Gemini API
genai.configure(api_key="API KEY")  

def clean_text_with_gemini(ocr_text):
    """Clean and format OCR text using Gemini."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"Clean and format this OCR text:\n{ocr_text}")
        return response.text.strip()
    except Exception as e:
        print(f"Error cleaning text with Gemini: {e}")
        return ocr_text  

def extract_text_from_image(image_path):
    """Extract text from an image using Tesseract OCR."""
    try:
        image = Image.open(image_path)
        ocr_text = pytesseract.image_to_string(image, lang="eng")
        return clean_text_with_gemini(ocr_text)
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return ""

def classify_pii(text):
    """Classify PII in the given text using Gemini."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            f"Classify the following text into Low, Medium, and High Sensitivity PII based on Indian government standards. "
            f"Return only a valid JSON list, with no additional text, in this format: "
            f'[{{"pii_type": "TYPE", "detected_value": "VALUE", "category": "LEVEL"}}]:\n{text}'
        )
        
        # Extract JSON from Gemini's response
        json_start = response.text.find("[")
        json_end = response.text.rfind("]") + 1
        if json_start == -1 or json_end == -1:
            raise ValueError("Invalid JSON format received from Gemini.")
        cleaned_json = response.text[json_start:json_end]
        return json.loads(cleaned_json)
    except Exception as e:
        print(f"Error classifying PII: {e}")
        return []

def get_pii_coordinates(image_path, pii_data):
    """Get bounding box coordinates for detected PII in an image."""
    try:
        image = Image.open(image_path)
        detection_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        pii_with_coordinates = []
        for pii in pii_data:
            pii_value = pii["detected_value"]
            for i in range(len(detection_data["text"])):
                if detection_data["text"][i].strip() == pii_value:
                    x = detection_data["left"][i]
                    y = detection_data["top"][i]
                    width = detection_data["width"][i]
                    height = detection_data["height"][i]
                    pii["coordinates"] = [x, y, x + width, y + height]
                    pii_with_coordinates.append(pii)
                    break
        return pii_with_coordinates
    except Exception as e:
        print(f"Error getting PII coordinates: {e}")
        return pii_data  # Return PII data without coordinates if extraction fails
