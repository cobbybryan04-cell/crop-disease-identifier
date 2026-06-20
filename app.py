import os
import base64
from groq import Groq
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from database import init_db, save_scan, get_user_scans, get_all_scans, delete_scan, delete_all_scans, register_user, get_user_by_email, get_user_by_id, delete_user, delete_user_scans, get_all_users, get_total_users, get_total_scans, get_disease_stats, get_severity_stats, get_healthy_crops, get_recent_scans_with_users, admin_delete_user, get_top_crops, get_top_farmers, get_all_diseases
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import bcrypt

load_dotenv()

app = Flask(__name__)
app.secret_key = 'cropkey2026'
app.config['UPLOAD_FOLDER'] = os.path.abspath('uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'cropAdmin2026'

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
                        'image_url': {'url': f'data:{media_type};base64,{image_data}'}
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
    if 'user_id' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.abspath('uploads'), filename)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        location = request.form['location']
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        success = register_user(name, email, hashed, location)
        if success:
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email already exists!', 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'user_id' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    if 'admin' in session:
        return redirect(url_for('admin_dashboard'))
    user = get_user_by_id(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/delete-account')
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    delete_user(session['user_id'])
    session.clear()
    flash('Account deleted successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    user_id = session.get('user_id', 0)
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
            user_id,
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
    if 'user_id' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    if 'admin' in session:
        scans = get_all_scans()
    else:
        scans = get_user_scans(session['user_id'])
    return render_template('history.html', scans=scans)

@app.route('/delete/<int:scan_id>')
def delete(scan_id):
    if 'user_id' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    delete_scan(scan_id)
    return redirect(url_for('history'))

@app.route('/delete-all')
def delete_all():
    if 'user_id' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    if 'admin' in session:
        delete_all_scans()
    else:
        delete_user_scans(session['user_id'])
    return redirect(url_for('history'))

@app.route('/chatbot')
def chatbot():
    if 'user_id' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('chatbot.html')

@app.route('/chatbot/ask', methods=['POST'])
def chatbot_ask():
    if 'user_id' not in session and 'admin' not in session:
        return jsonify({'response': 'Please login first!'})
    data = request.get_json()
    user_message = data.get('message', '')
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model='meta-llama/llama-4-scout-17b-16e-instruct',
        messages=[
            {
                'role': 'system',
               'content': '''You are an expert agricultural assistant helping farmers worldwide.
                You help farmers with:
                - Crop disease identification and treatment
                - Farming best practices
                - Agriculture advice for any country or region
                - Crop management tips
                - Soil and weather related farming advice
                - Pest and weed control
                Keep answers clear, practical and friendly.
                Adapt your advice based on the farmer location and crop type they mention.
                You support all crops from any country in the world.'''
            },
            {
                'role': 'user',
                'content': user_message
            }
        ],
        max_tokens=500
    )
    bot_response = response.choices[0].message.content
    return jsonify({'response': bot_response})

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            session['user_name'] = 'Admin'
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'error')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    disease_stats = get_disease_stats()
    severity_stats = get_severity_stats()

    disease_labels = [d[0] for d in disease_stats] if disease_stats else ['No Data']
    disease_counts = [d[1] for d in disease_stats] if disease_stats else [0]
    severity_labels = [s[0] for s in severity_stats] if severity_stats else ['No Data']
    severity_counts = [s[1] for s in severity_stats] if severity_stats else [0]

    return render_template('admin_dashboard.html',
        total_users=get_total_users(),
        total_scans=get_total_scans(),
        total_diseases=len(disease_stats),
        healthy_crops=get_healthy_crops(),
        recent_scans=get_recent_scans_with_users(),
        top_crops=get_top_crops(),
        top_farmers=get_top_farmers(),
        disease_labels=disease_labels,
        disease_counts=disease_counts,
        severity_labels=severity_labels,
        severity_counts=severity_counts
    )

@app.route('/admin/users')
def admin_users():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    users = get_all_users()
    return render_template('admin_users.html', users=users)

@app.route('/admin/scans')
def admin_scans():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    scans = get_recent_scans_with_users()
    return render_template('admin_scans.html', scans=scans)

@app.route('/admin/delete-user/<int:user_id>')
def admin_delete_user_route(user_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    admin_delete_user(user_id)
    return redirect(url_for('admin_users'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/diseases')
def admin_diseases():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    diseases = get_all_diseases()
    return render_template('admin_diseases.html', diseases=diseases)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)