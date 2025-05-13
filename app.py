from flask import Flask, render_template, request, redirect, url_for, send_file, session
from fpdf import FPDF
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'YourSuperSecretKey123'

LOG_FILE = "pdf_activity_log.csv"
STATIC_CHART = "log/pdf_activity_summary.png"
ASSETS_FOLDER = "static"

# Utility Functions
def age_group(age):
    if age < 30: return "Under 30"
    elif age < 40: return "30-39"
    elif age < 50: return "40-49"
    elif age < 60: return "50-59"
    else: return "60+"

def recommend_goals(age_group, risk_profile):
    rules = {
        ('Under 30', 'High'): ["Wealth Creation", "Equity Investing", "Travel"],
        ('30-39', 'Moderate'): ["Child Education", "Retirement", "Insurance"],
        ('40-49', 'Low'): ["Debt Reduction", "Child Marriage", "Emergency Fund"],
        ('50-59', 'Moderate'): ["Retirement Planning", "Health Corpus", "Passive Income"],
        ('60+', 'Low'): ["Health Fund", "Fixed Income", "Estate Planning"]
    }
    return rules.get((age_group, risk_profile), ["Emergency Fund", "Insurance Review"])

def log_activity(client_name, action):
    with open(LOG_FILE, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{client_name},{action},{timestamp}\n")

def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.image(os.path.join(ASSETS_FOLDER, "Round_Logo-removebg-preview.png"), x=70, y=10, w=60)
    pdf.ln(50)
    pdf.cell(200, 10, txt="Financial Summary", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for key, value in data.items():
        if key == 'goals':
            pdf.cell(200, 10, txt=f"Goals:", ln=True)
            for goal in value:
                pdf.cell(200, 10, txt=f"- {goal}", ln=True)
        else:
            pdf.cell(200, 10, txt=f"{key.title()}: {value}", ln=True)
    pdf.image(os.path.join(ASSETS_FOLDER, "Signature.png"), x=140, y=220, w=50)
    filename = f"{data['name'].replace(' ', '_')}_summary.pdf"
    pdf.output(filename)
    return filename

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        age = int(request.form['age'])
        risk = request.form['risk']

        group = age_group(age)
        goals = recommend_goals(group, risk)

        data = {
            "name": name,
            "age": age,
            "risk": risk,
            "age group": group,
            "goals": goals
        }

        pdf_path = create_pdf(data)
        log_activity(name, "PDF Downloaded")
        return send_file(pdf_path, as_attachment=True)

    return render_template('form.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'securepass123':
            session['admin'] = True
            return redirect(url_for('activity_log'))
        return "<h3>Invalid credentials</h3>"
    return render_template("admin_login.html")

@app.route('/activity-log')
def activity_log():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    if not os.path.exists(LOG_FILE):
        return "<h3>No activity yet.</h3>"

    df = pd.read_csv(LOG_FILE, names=["Client", "Action", "Timestamp"])
    summary = df["Action"].value_counts()
    plt.figure(figsize=(4,4))
    summary.plot.pie(autopct='%1.1f%%', startangle=90)
    plt.savefig(STATIC_CHART)
    plt.close()

    return render_template("activity_log.html", tables=[df.to_html(classes='table', index=False)])

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

if __name__ == "__main__":
    app.run(debug=True)
