from flask import Flask, render_template, request, redirect, url_for, send_file, session
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'YourSuperSecretKey123'  # Needed to enable session management for admin login

DATA_FOLDER = "client_data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# Age group logic

def age_group(age):
    if age is None:
        return "Unknown"
    elif age < 30:
        return "Under 30"
    elif age < 40:
        return "30-39"
    elif age < 50:
        return "40-49"
    elif age < 60:
        return "50-59"
    else:
        return "60+"

# Goal recommendation logic

def recommend_goals(age_group, risk_profile):
    rules = {
        ('Under 30', 'High'): ["Wealth Creation", "Equity Investing", "International Travel"],
        ('30-39', 'Moderate'): ["Child Education", "Retirement Corpus", "Insurance Planning"],
        ('40-49', 'Low'): ["Debt Reduction", "Child Marriage", "Emergency Fund"],
        ('50-59', 'Moderate'): ["Retirement Planning", "Health Corpus", "Passive Income"],
        ('60+','Low'): ["Health Fund", "Fixed Income Stream", "Estate Planning"]
    }
    return rules.get((age_group, risk_profile), ["Basic Emergency Fund", "Insurance Review"])

# Activity log tracking

def log_pdf_activity(client_file, action):
    with open("pdf_activity_log.csv", "a") as log:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client_name = client_file.replace(".pdf", "").replace("client_", "").replace("_", " ").title()
        log.write(f"{client_name},{action},{timestamp}\n")

# PDF generation

def create_client_pdf(data):
    pdf = FPDF()

    # Cover Page
    pdf.add_page()
    pdf.image("static/Round_Logo-removebg-preview.png", x=65, y=10, w=80)
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(0, 0, 120)
    pdf.ln(60)
    pdf.cell(200, 10, txt="Financial Health & Goal Discovery Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Client Name: {data.get('full_name', '')}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%d %B %Y')}", ln=True, align='C')
    pdf.image("static/Signature.png", x=140, y=220, w=50)
    pdf.set_xy(140, 265)
    pdf.set_font("Arial", size=10)
    pdf.cell(50, 5, txt="Ranjit Chowdhury", ln=True, align='C')
    pdf.cell(50, 5, txt="Founder, Rudra Solutions", ln=True, align='C')

    # Summary Page
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 80)
    pdf.cell(200, 10, txt="Client Financial Summary", ln=True, align='C')
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, txt=f"Email: {data.get('email', '')}", ln=True)
    pdf.cell(200, 10, txt=f"Phone: {data.get('phone', '')}", ln=True)
    pdf.cell(200, 10, txt=f"City: {data.get('city', '')}", ln=True)
    pdf.cell(200, 10, txt=f"Age Group: {data.get('age_group', '')}", ln=True)
    pdf.cell(200, 10, txt=f"Risk Profile: {data.get('risk_profile', '')}", ln=True)
    pdf.ln(10)
    pdf.set_text_color(0, 0, 120)
    pdf.cell(200, 10, txt="Recommended Goals:", ln=True)
    pdf.set_text_color(0, 0, 0)
    for goal in data.get('recommended_goals', '').split(','):
        pdf.cell(200, 10, txt=f"- {goal.strip()}", ln=True)

    filename = f"{data.get('full_name', 'client').replace(' ', '_')}_summary.pdf"
    pdf.output(filename)
    return filename

# Admin login
@app.route('/', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'securepass123':
            session['admin_logged_in'] = True
            return redirect(url_for('submit'))
        else:
            return "<h3 style='color:red;'>❌ Invalid credentials</h3>"
    return '''
        <h2>🔐 Admin Login</h2>
        <form method="POST">
            Username: <input type="text" name="username" required><br><br>
            Password: <input type="password" name="password" required><br><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/activity-log')
def activity_log():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if not os.path.exists("pdf_activity_log.csv"):
        return "<p>No activity recorded yet.</p>"

    df = pd.read_csv("pdf_activity_log.csv", names=["Client", "Action", "Timestamp"])
    action_counts = df["Action"].value_counts()
    plt.figure(figsize=(4, 4))
    action_counts.plot.pie(autopct='%1.1f%%', startangle=90, title='PDF Engagement')
    chart_path = "pdf_activity_summary.png"
    plt.savefig(chart_path)
    plt.close()

    html_table = df.to_html(classes="table table-striped", index=False)

    return f"""
    <h2>📊 PDF Engagement Log</h2>
    <img src="/static-log/pdf-activity-chart" width="300px">
    <br><br>
    {html_table}
    <br>
    <a href="/export-activity">
        <button>📥 Export to Excel</button>
    </a>
    """

@app.route('/static-log/pdf-activity-chart')
def serve_activity_chart():
    return send_file("pdf_activity_summary.png", mimetype='image/png')

@app.route('/export-activity')
def export_activity():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if not os.path.exists("pdf_activity_log.csv"):
        return "<p>No activity log available to export.</p>"

    df = pd.read_csv("pdf_activity_log.csv", names=["Client", "Action", "Timestamp"])
    output_path = "pdf_activity_report.xlsx"
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Activity Log', index=False)
        summary = df["Action"].value_counts()
        chart = summary.plot(kind='bar', title='PDF Engagement Summary')
        fig = chart.get_figure()
        chart_path = "temp_chart.png"
        fig.savefig(chart_path)
        fig.clf()

    return send_file(output_path, as_attachment=True)

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        city = request.form.get('city')
        age = request.form.get('age', type=int)
        risk_profile = request.form.get('risk_profile')

        age_grp = age_group(age)
        goals = recommend_goals(age_grp, risk_profile)

        client_data = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "city": city,
            "age_group": age_grp,
            "risk_profile": risk_profile,
            "recommended_goals": ", ".join(goals)
        }

        pdf_filename = create_client_pdf(client_data)
        log_pdf_activity(pdf_filename, "Generated")

        return send_file(pdf_filename, as_attachment=True)

    return render_template("submit.html")

if __name__ == "__main__":
      app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))