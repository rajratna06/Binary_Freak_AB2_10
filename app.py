from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from model import extract_text_from_image, classify_pii, get_pii_coordinates
import cv2

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('redacted', exist_ok=True)


@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/styles.css')
def serve_css():
    return send_from_directory('.', 'styles.css')

@app.route('/scripts.js')
def serve_js():
    return send_from_directory('.', 'scripts.js')

@app.route('/placeholder.svg')
def serve_placeholder():
    return send_from_directory('.', 'placeholder.svg')

@app.route('/redacted/<filename>')
def serve_redacted(filename):
    return send_from_directory('redacted', filename)

def redact_image(image_path, pii_data, output_path):
    try:
        image = cv2.imread(image_path)
        for pii in pii_data:
            if "coordinates" in pii:
                x1, y1, x2, y2 = pii["coordinates"]
                
                if x2 > x1 and y2 > y1:
                    roi = image[y1:y2, x1:x2]
                    blurred_roi = cv2.GaussianBlur(roi, (51, 51), 0)  
                    image[y1:y2, x1:x2] = blurred_roi
        cv2.imwrite(output_path, image)
    except Exception as e:
        print(f"Error redacting image: {e}")


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    try:
        
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return jsonify({'error': 'Only image files (PNG, JPG, JPEG) are allowed'}), 400

        
        text = extract_text_from_image(file_path)
        pii_data = classify_pii(text)
        pii_data_with_coords = get_pii_coordinates(file_path, pii_data)

        
        redacted_filename = 'redacted_' + filename
        redacted_path = os.path.join('redacted', redacted_filename)
        redact_image(file_path, pii_data_with_coords, redacted_path)

        
        os.remove(file_path)

        
        formatted_pii = [{
            'type': item['pii_type'],
            'value': item['detected_value'],
            'risk': item['category']
        } for item in pii_data_with_coords]

        redacted_url = request.host_url + 'redacted/' + redacted_filename
        return jsonify({'pii': formatted_pii, 'redacted_url': redacted_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
