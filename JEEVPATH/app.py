import os
import requests
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, make_response, session, flash, jsonify, send_file
from functools import wraps
from werkzeug.utils import secure_filename
from medical import (
    analyze_medical_image,
    create_pdf,
    analyze_prescription_image,
    create_prescription_pdf
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_default_weak_secret_key_change_me")

# --- DB Setup ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Auth ---
@app.route('/')
def home():
    return render_template("login_option.html")

@app.route('/login-option')
def login_option():
    return render_template("login_option.html")

@app.route('/login')
def login_page():
    user_type = request.args.get("type", "user")
    response = make_response(render_template("login.html", user_type=user_type))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not age or not email or not password:
            flash("All fields are required.", "warning")
            return redirect(url_for("signup"))

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (name, age, email, password) VALUES (?, ?, ?, ?)",
                           (name, age, email, password))
            conn.commit()
            flash("Account created successfully!", "success")
            return redirect(url_for("login_page"))
        except sqlite3.IntegrityError:
            flash("Email already registered. Try logging in.", "danger")
            return redirect(url_for("signup"))
        finally:
            conn.close()
    return render_template("signup.html")

@app.route('/authenticate', methods=['POST'])
def authenticate():
    email = request.form.get("email")
    password = request.form.get("password")

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session["user"] = email
        return redirect(url_for("clinic"))
    else:
        flash("Invalid Credentials. Please try again.", "danger")
        return redirect(url_for("login_option"))

@app.route('/logout', methods=['POST'])
def logout():
    session.pop("user", None)
    flash("Logged out successfully.", "info")
    response = make_response(redirect(url_for('login_option')))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in first!", "warning")
            return redirect(url_for("login_option", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# --- Clinic Pages ---
@app.route('/clinic')
@login_required
def clinic():
    return render_template("clinic.html")

@app.route('/blood-pressure')
@login_required
def blood_pressure():
    return render_template("blood_pressure.html")

@app.route('/sugar-test')
@login_required
def sugar_test():
    return render_template("sugar_test.html")

@app.route('/periods')
@login_required
def periods():
    return render_template("periods.html")

@app.route('/pregnancy')
@login_required
def pregnancy():
    return render_template("pregnancy.html")

@app.route('/nutrition')
@login_required
def nutrition():
    return render_template("nutrition.html")

@app.route('/cbc')
@login_required
def cbc():
    return render_template("cbc.html")

@app.route('/checkup')
@login_required
def checkup():
    return render_template("checkup.html")

@app.route('/blood-test')
@login_required
def blood_test():
    return render_template("blood_test.html")

@app.route('/report')
@login_required
def report():
    return render_template("report.html")

# --- Medical Image Analysis ---
@app.route('/scanning', methods=['GET', 'POST'])
@login_required
def scanning():
    if request.method == 'POST':
        patient_name = request.form['patient_name']
        image = request.files['medical_image']

        if image:
            filename = secure_filename(image.filename)
            if not os.path.exists('static'):
                os.makedirs('static')
            image_path = os.path.join('static', filename)
            image.save(image_path)

            report, _ = analyze_medical_image(image_path)
            session['patient_name'] = patient_name
            session['report'] = report
            session['image_filename'] = filename

            sections = []
            for section in report.split("### "):
                if section.strip():
                    if "\n" in section:
                        title, content = section.split("\n", 1)
                    else:
                        title, content = section, ""
                    sections.append((title.strip(), content.strip()))

            return render_template(
                'scanning.html',
                analyzed=True,
                patient_name=patient_name,
                sections=sections,
                image_filename=filename
            )

    return render_template("scanning.html", analyzed=False)

@app.route('/download_pdf')
@login_required
def download_pdf():
    patient_name = session.get('patient_name')
    report = session.get('report')

    if not patient_name or not report:
        return redirect('/scanning')

    pdf_path = create_pdf(patient_name, report)
    return send_file(pdf_path, as_attachment=True)

# --- Prescription Upload Route ---
@app.route('/upload_prescription', methods=['POST'])
@login_required
def upload_prescription():
    if 'prescription_image' not in request.files:
        flash("No file uploaded.")
        return redirect(url_for('scanning'))

    file = request.files['prescription_image']
    patient_name = request.form.get('patient_name', 'Unknown')

    if file.filename == '':
        flash("No selected file.")
        return redirect(url_for('scanning'))

    if not os.path.exists("static"):
        os.makedirs("static")

    filepath = os.path.join("static", secure_filename(file.filename))
    file.save(filepath)

    prescription_text = analyze_prescription_image(filepath)
    pdf_filename = create_prescription_pdf(patient_name, prescription_text)

    return render_template("scanning.html", analyzed=False, prescription_output=prescription_text, prescription_pdf=pdf_filename)

# --- Chatbot ---
@app.route('/chat')
@login_required
def chat():
    return render_template("chat.html")

@app.route('/get_chatbot_response', methods=['POST'])
@login_required
def get_chatbot_response():
    user_message = request.form.get('message', '').strip()
    if not user_message:
        return jsonify({'response': "Please enter a message."})

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": user_message,
                "stream": False
            }
        )
        data = response.json()
        return jsonify({'response': data.get("response", "Sorry, I couldn't generate a response.")})
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}"})

# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)
