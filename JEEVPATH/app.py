from flask import Flask, render_template, request, redirect, url_for, make_response, session, flash, jsonify

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Set a strong secret key for sessions

# Home Page (Login Option)
@app.route('/')
def home():
    return render_template("login_option.html")

@app.route('/login-option')
def login_option():
    return render_template("login_option.html")

# Login Page with User Type
@app.route('/login')
def login_page():
    user_type = request.args.get("type", "user")  # Get user type from URL
    response = make_response(render_template("login.html", user_type=user_type))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

# Authenticate User and Redirect
@app.route('/authenticate', methods=['POST'])
def authenticate():
    email = request.form.get("email")
    password = request.form.get("password")

    # Hardcoded valid users (FOR DEMO ONLY, DO NOT USE IN PRODUCTION!)
    valid_users = {
        "vishmapasayat003@gmail.com": "Vishma@0101",
        "kumarsubhendu2003@gmail.com": "Subhendu@42",
        "sahasransu.kirti@gmail.com": "Kirti@2025",
        "stuteesarangi@gmail.com": "Stutee@2025"
    }

    if email in valid_users and valid_users[email] == password:
        session["user"] = email  # Store user in session
        # We don't flash success message on login here.
        return redirect(url_for("clinic"))
    else:
        flash("Invalid Credentials. Please try again.", "danger")
        return redirect(url_for("login_page"))

# Clinic Home Page (Protected)
@app.route('/clinic')
def clinic():
    if "user" not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for("login_page"))
    return render_template("clinic.html")

# Logout Route
@app.route('/logout', methods=['POST'])  # Changed to POST method
def logout():
    session.pop("user", None)
    flash("Logged out successfully.", "info")  #Flash the logout message
    return redirect(url_for("login_page")) #Redirected

# Additional Pages (Protected)
def login_required(f):
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please log in first!", "warning")
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

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


# Chatbot Logic and Route
chatbot_responses = {
    "What should I do if I have a high fever?": "If your fever is above 102°F (38.9°C), stay hydrated, rest, and take paracetamol if available. If symptoms persist for more than three days, seek medical help.",
    "What are the symptoms of dehydration?": "Symptoms include dry mouth, extreme thirst, dizziness, reduced urine output, and dark-colored urine. Drink clean water or an oral rehydration solution (ORS) immediately.",
    "What should I do in case of a snake bite?": "Stay calm, keep the affected limb immobilized, and avoid sucking out the venom. Seek urgent medical care.",
    "How can I help someone having a heart attack?": "If they have chest pain, help them sit in a comfortable position, loosen tight clothing, and give them aspirin if available. Call for immediate medical help.",
    "What are the signs of malnutrition in children?": "Signs include thin arms and legs, swollen belly, frequent illnesses, irritability, and slow growth. Provide a balanced diet with protein-rich foods like lentils, eggs, and milk if possible.",
    "How often should a pregnant woman visit a doctor?": "Ideally, at least four checkups during pregnancy—once in each trimester and before delivery. If not possible, monitor weight gain, blood pressure, and fetal movement regularly.",
    "How can I prevent the spread of tuberculosis (TB)?": "Cover your mouth when coughing, avoid close contact with others, and take prescribed medication regularly for at least six months.",
    "What should I do if I have diarrhea?": "Drink plenty of clean water, ORS, or homemade salt-sugar solution. Avoid dairy and greasy foods. If diarrhea lasts more than two days, seek medical help.",
    "How can I purify water if I don’t have a filter?": "Boil water for at least 10 minutes, use chlorine tablets, or strain through a clean cloth and expose it to sunlight for 6 hours in a clear plastic bottle.",
    "Why is handwashing important?": "Handwashing with soap prevents infections like diarrhea, COVID-19, and flu by removing germs from hands before eating and after using the toilet."
}

@app.route('/get_chatbot_response', methods=['POST'])
@login_required
def get_chatbot_response():
    user_message = request.form['message']
    response = chatbot_responses.get(user_message, "I am here to assist you with your health-related queries!") #default response

    return jsonify({'response': response})


# Run Flask App
if __name__ == "__main__":
    app.run(debug=True)