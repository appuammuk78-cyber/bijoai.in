from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import sqlite3
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)


# =========================
# DATABASE CONNECTION
# =========================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        # Use psycopg2 for PostgreSQL on Render
        conn = psycopg2.connect(db_url)
        return conn, "postgres"
    else:
        # Fallback to SQLite for local dev
        conn = sqlite3.connect("appointments.db")
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

# =========================
# DATABASE INITIALIZATION
# =========================
def init_db():
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    if db_type == "postgres":
        c.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id SERIAL PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                date TEXT,
                time TEXT
            )
        """)
    else:
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
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    if db_type == "postgres":
        c.execute(
            "INSERT INTO bookings (name, email, phone, date, time) VALUES (%s, %s, %s, %s, %s)",
            (name, email, phone, date, time)
        )
    else:
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
# ADMIN ROUTE
# =========================
def check_auth(username, password):
    # Retrieve credentials from environment variables securely
    admin_user = os.environ.get("ADMIN_USER", "kamal_admin")
    admin_pass = os.environ.get("ADMIN_PASS", "AGI2026!")
    return username == admin_user and password == admin_pass

def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

@app.route("/admin/bookings")
def view_bookings():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    try:
        conn, db_type = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM bookings ORDER BY id DESC")
        
        if db_type == "postgres":
            rows = c.fetchall()
            columns = [desc[0] for desc in c.description]
            bookings = [dict(zip(columns, row)) for row in rows]
        else:
            bookings = [dict(row) for row in c.fetchall()]
            
        conn.close()

        # Build a simple HTML table
        html = """
        <html>
        <head>
            <title>Kamal AI Admin - Bookings</title>
            <style>
                body { font-family: sans-serif; padding: 20px; background: #f4f4f4; }
                table { border-collapse: collapse; width: 100%; background: white; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #00ccb9; color: white; }
                tr:nth-child(even) { background-color: #f9f9f9; }
            </style>
        </head>
        <body>
            <h2>Kamal AI - Booking Entries</h2>
            <table>
                <tr>
                    <th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Date</th><th>Time</th>
                </tr>
        """
        for b in bookings:
            html += f"<tr><td>{b['id']}</td><td>{b['name']}</td><td>{b['email']}</td><td>{b['phone']}</td><td>{b['date']}</td><td>{b['time']}</td></tr>"
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html
    
    except Exception as e:
        return f"Error fetching bookings: {str(e)}"


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)