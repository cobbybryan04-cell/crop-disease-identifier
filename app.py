import os
import base64
from groq import Groq
from flask import Flask, render_template, request, redirect, url_for
from database import init_db, save_scan, get_all_scans
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_crop_image(image_path):
    client = Groq(api_key=GROQ_API_KEY)
    
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    ext = image_path.rsplit('.', 1)[1].lower()
    media_type = 'image/jpeg' if ext == 'jpg' else f'image/{ext}'
    
    response = client.chat.completions.create(
        model='meta-llama/llama-4-scout-17b-16e-instruct',
        messages=[
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:{media_type};base64,{image_data}'
                        }
                    },
                    {
                        'type': 'text',
                        'text': '''You are an expert agricultural scientist. Analyze this crop image and provide:
1. Crop Type: What crop is this?
2. Disease Name: What disease or problem do you see? (If healthy, say "No Disease Detected")
3. Severity: Rate as Low, Medium, or High (or "None" if healthy)
4. Treatment: What treatment or action should the farmer take?

Respond in exactly this format:
CROP TYPE: [answer]
DISEASE NAME: [answer]
SEVERITY: [answer]
TREATMENT: [answer]'''
                    }
                ]
            }
        ],
        max_tokens=1024
    )
    
    return response.choices[0].message.content

def parse_analysis(analysis_text):
    result = {
        'crop_type': 'Unknown',
        'disease_name': 'Unknown',
        'severity': 'Unknown',
        'treatment': 'Unknown'
    }
    
    lines = analysis_text.strip().split('\n')
    for line in lines:
        if line.startswith('CROP TYPE:'):
            result['crop_type'] = line.replace('CROP TYPE:', '').strip()
        elif line.startswith('DISEASE NAME:'):
            result['disease_name'] = line.replace('DISEASE NAME:', '').strip()
        elif line.startswith('SEVERITY:'):
            result['severity'] = line.replace('SEVERITY:', '').strip()
        elif line.startswith('TREATMENT:'):
            result['treatment'] = line.replace('TREATMENT:', '').strip()
    
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        analysis_text = analyze_crop_image(filepath)
        result = parse_analysis(analysis_text)
        
        save_scan(
            filename,
            result['crop_type'],
            result['disease_name'],
            result['treatment'],
            result['severity']
        )
        
        return render_template('result.html', result=result, image=filename)
    
    return redirect(url_for('index'))

@app.route('/history')
def history():
    scans = get_all_scans()
    return render_template('history.html', scans=scans)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)