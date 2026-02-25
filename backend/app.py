from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
CORS(app)


# =========================
# DATABASE INITIALIZATION
# =========================
def init_db():
    conn = sqlite3.connect("appointments.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            date TEXT,
            time TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


# =========================
# HOME ROUTE
# =========================
@app.route("/")
def home():
    return "KAMAL AI Backend Running 🚀"


# =========================
# BOOKING ROUTE
# =========================
@app.route("/book", methods=["POST"])
def book():

    data = request.json

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    date = data.get("date")
    time = data.get("time")

    # Save to database
    conn = sqlite3.connect("appointments.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO bookings (name, email, phone, date, time) VALUES (?, ?, ?, ?, ?)",
        (name, email, phone, date, time)
    )
    conn.commit()
    conn.close()

    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))

        # =========================
        # CLIENT EMAIL
        # =========================
        html_content = f"""
        <html>
        <body style="font-family: Arial; background:#f4f4f4; padding:20px;">
            <div style="max-width:600px; background:white; padding:30px; border-radius:10px;">
                <h2>Demo Confirmed 🚀</h2>
                <p>Hi <strong>{name}</strong>,</p>
                <p>Your booking has been confirmed.</p>
                <p><strong>Date:</strong> {date}</p>
                <p><strong>Time:</strong> {time}</p>
                <br>
                <p>– Kamal AI Team</p>
            </div>
        </body>
        </html>
        """

        message = Mail(
            from_email="avslorenikola@gmail.com",
            to_emails=email,
            subject="Booking Confirmation - Kamal AI",
            plain_text_content=f"""
Hi {name},

Your booking has been confirmed.

Date: {date}
Time: {time}

– Kamal AI Team
""",
            html_content=html_content
        )

        client_response = sg.send(message)
        print("Client email sent:", client_response.status_code)

        # =========================
        # INTERNAL ALERT EMAIL
        # =========================
        internal_message = Mail(
            from_email="avslorenikola@gmail.com",
            to_emails="avslorenikola@gmail.com",
            subject="🚨 New Demo Booking - Kamal AI",
            plain_text_content=f"""
New booking received!

Name: {name}
Email: {email}
Phone: {phone}
Date: {date}
Time: {time}
""",
            html_content=f"""
<h2>🚨 New Booking Alert</h2>
<p><strong>Name:</strong> {name}</p>
<p><strong>Email:</strong> {email}</p>
<p><strong>Phone:</strong> {phone}</p>
<p><strong>Date:</strong> {date}</p>
<p><strong>Time:</strong> {time}</p>
"""
        )

        internal_response = sg.send(internal_message)
        print("Internal notification sent:", internal_response.status_code)

    except Exception as e:
        print("Email error:", e)

    return jsonify({"message": "Booking Confirmed"})


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)