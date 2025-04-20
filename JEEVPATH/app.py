import os # Added for environment variables
from flask import Flask, render_template, request, redirect, url_for, make_response, session, flash, jsonify
from groq import Groq # Added Groq import

app = Flask(__name__)
# IMPORTANT: Replace with a strong, unique secret key!
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_default_weak_secret_key_change_me")

# --- Login/Authentication Routes (Mostly Unchanged) ---

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
    user_type = request.args.get("type", "user")
    response = make_response(render_template("login.html", user_type=user_type))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

# Authenticate User and Redirect
@app.route('/authenticate', methods=['POST'])
def authenticate():
    email = request.form.get("email")
    password = request.form.get("password")

    # Hardcoded valid users (FOR DEMO ONLY, DO NOT USE IN PRODUCTION!)
    # Consider using a database and password hashing (e.g., Werkzeug's security helpers)
    valid_users = {
        "vishmapasayat003@gmail.com": "Vishma@0101",
        "kumarsubhendu2003@gmail.com": "Subhendu@42",
        "sahasransu.kirti@gmail.com": "Kirti@2025",
        "stuteesarangi@gmail.com": "Stutee@2025"
    }

    if email in valid_users and valid_users[email] == password:
        session["user"] = email
        return redirect(url_for("clinic"))
    else:
        flash("Invalid Credentials. Please try again.", "danger")
        # Redirect back to login page preserving the user_type if possible
        # Find the user type associated with the failed login (or default to 'user')
        # This part is tricky without more info - let's redirect to the general login for simplicity
        return redirect(url_for("login_option")) # Or maybe login_page? Depends on flow

# Clinic Home Page (Protected)
@app.route('/clinic')
def clinic():
    if "user" not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for("login_option")) # Redirect to option page if not logged in
    return render_template("clinic.html")

# Logout Route
@app.route('/logout', methods=['POST']) # Good practice to use POST for actions like logout
def logout():
    session.pop("user", None)
    flash("Logged out successfully.", "info")
    # Redirect to the initial login option page after logout
    response = make_response(redirect(url_for('login_option')))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # Prevent caching logged-out state
    return response

# --- Protected Page Routes ---

# Decorator to require login
def login_required(f):
    @wraps(f) # Important: Use wraps from functools to preserve function metadata
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in first!", "warning")
            return redirect(url_for("login_option", next=request.url)) # Redirect to login option
        return f(*args, **kwargs)
    # decorated_function.__name__ = f.__name__ # Not needed if using @wraps
    return decorated_function

# Make sure to import wraps
from functools import wraps # Added import

@app.route('/blood-pressure')
@login_required
def blood_pressure():
    return render_template("blood_pressure.html")

# ... (keep all your other @login_required routes: sugar_test, periods, etc.) ...
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


# --- Chatbot Logic and Route with Groq ---

# Remove the old hardcoded dictionary
# chatbot_responses = { ... } # REMOVED

# Initialize Groq client (optional: could also init inside the route)
# Doing it outside might slightly improve performance for repeated calls,
# but requires careful handling of the API key potentially changing.
# Let's initialize inside the route for simplicity and security.

@app.route('/get_chatbot_response', methods=['POST'])
@login_required # Keep protection
def get_chatbot_response():
    user_message = request.form.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided.'}), 400

    try:
        # Get API Key from environment variable
        api_key = os.environ.get("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")
        if not api_key:
            print("Error: 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 environment variable not set.") # Log for server admin
            return jsonify({'response': "Error: Chat service is not configured correctly."}), 500 # User message

        # Initialize Groq client inside the request context
        client = Groq(api_key=api_key)

        # Prepare the message for the Groq API
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant designed to answer general health-related questions suitable for a rural clinic setting. Provide concise and clear information. Do not provide specific medical diagnoses or prescribe medication. Advise users to consult a healthcare professional for serious concerns."
                # You can customize this system prompt further
            },
            {
                "role": "user",
                "content": user_message,
            }
        ]

        # Make the API call to Groq
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",  # Or choose another model like mixtral-8x7b-32768
            temperature=0.7,       # Adjust creativity (0.0 to 1.0)
            max_tokens=256,        # Limit response length
            top_p=1,
            stop=None,
            stream=False,
        )

        # Extract the response content
        groq_response = chat_completion.choices[0].message.content
        response = groq_response

    except Exception as e:
        print(f"Error communicating with Groq API: {e}") # Log the actual error
        # Provide a generic error message to the user
        response = "Sorry, I encountered an error trying to get a response. Please try again later."
        # You might want to return a different HTTP status code for server errors
        # return jsonify({'response': response}), 503 # Service Unavailable

    return jsonify({'response': response})


# --- Run Flask App ---
if __name__ == "__main__":
    # Use debug=False in production!
    # Consider using Gunicorn or Waitress for production deployments.
    app.run(debug=True) # debug=True is okay for development