# -*- coding: utf-8 -*-
"""
🌾 Alpha Farms - वेब ऐप (Direct On-Screen Demo OTP + Email)
"""

import os
import sqlite3
import random
import smtplib
from email.mime.text import MIMEText
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import io

DB_NAME = "ganna_parchi_data.db"

st.set_page_config(
    page_title="Alpha Farms | गन्ना पर्ची प्रबंधन",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- EMAIL CREDENTIALS ---
DEFAULT_SENDER_EMAIL = "your_email@gmail.com"
DEFAULT_APP_PASSWORD = "your_16_digit_app_password"

def get_email_credentials():
    sender = st.secrets.get("SENDER_EMAIL", DEFAULT_SENDER_EMAIL) if hasattr(st, "secrets") else DEFAULT_SENDER_EMAIL
    pwd = st.secrets.get("APP_PASSWORD", DEFAULT_APP_PASSWORD) if hasattr(st, "secrets") else DEFAULT_APP_PASSWORD
    return sender, pwd

def send_otp_email(receiver_email, otp_code):
    sender_email, app_password = get_email_credentials()
    if app_password == "your_16_digit_app_password":
        return True  # डेमो मोड में स्क्रीन पर ही कोड दिखाएंगे

    subject = "🌾 Alpha Farms - लॉगिन OTP"
    body = f"नमस्ते,\n\nAlpha Farms पोर्टल में लॉगिन करने के लिए OTP है:\n👉 {otp_code}\n"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"ईमेल भेजने में विफल: {e}")
        return False

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS parchis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slip_no TEXT UNIQUE,
            date_time TEXT,
            variety TEXT,
            weight REAL,
            rate REAL,
            gross_amount REAL,
            eticket_no TEXT,
            person TEXT,
            transporter TEXT,
            chilai_by TEXT,
            transport_charge REAL,
            chilai_charge REAL,
            total_deductions REAL,
            net_in_hand REAL,
            payment_status TEXT,
            amount_paid REAL,
            balance_due REAL,
            generated_by TEXT
        )
    """)
    c.execute("CREATE TABLE IF NOT EXISTS master_farmers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, village TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS master_transporters (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, default_fare REAL DEFAULT 420.0)")
    c.execute("CREATE TABLE IF NOT EXISTS master_chilai (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
    c.execute("CREATE TABLE IF NOT EXISTS advances (id INTEGER PRIMARY KEY AUTOINCREMENT, party_type TEXT, party_name TEXT, date TEXT, amount REAL, remarks TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, full_name TEXT, role TEXT)")
    c.execute("INSERT OR IGNORE INTO users (username, password, full_name, role) VALUES ('admin', '1234', 'फ़ार्म प्रबंधक (Alpha Farms)', 'Admin')")
    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value REAL)")
    defaults = [('early_rate', 389.38), ('normal_rate', 379.38), ('transport_rate', 420.00), ('chilai_rate', 50.00)]
    for k, v in defaults:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
    c.execute("SELECT COUNT(*) FROM master_farmers")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT OR IGNORE INTO master_farmers (name, village) VALUES (?, ?)", [("Self", "गाँव"), ("रामचंद्र", ""), ("सुरेश कुमार", "")])
    c.execute("SELECT COUNT(*) FROM master_transporters")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT OR IGNORE INTO master_transporters (name, default_fare) VALUES (?, ?)", [("ARPIT", 420.0), ("ram chandra", 420.0), ("अन्य", 420.0)])
    c.execute("SELECT COUNT(*) FROM master_chilai")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT OR IGNORE INTO master_chilai (name) VALUES (?, ?)", [("लेबर टीम 1",), ("लेबर टीम 2",), ("स्वयं",)])
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def get_settings():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT key, value FROM settings")
    s = dict
