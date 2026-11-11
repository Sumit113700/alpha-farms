# -*- coding: utf-8 -*-
import sqlite3
import random
import pandas as pd
import streamlit as st
from datetime import datetime
import io

DB_NAME = "ganna_parchi_data.db"

st.set_page_config(
    page_title="Alpha Farms | गन्ना पर्ची प्रबंधन",
    page_icon="🌾",
    layout="wide"
)

# --- DATABASE SETUP ---
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
    s = dict(c.fetchall())
    conn.close()
    return s

def get_master_list(table_name):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT name FROM {table_name} ORDER BY name ASC")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def add_to_master(table_name, name):
    if not name.strip(): return
    conn = get_db()
    c = conn.cursor()
    c.execute(f"INSERT OR IGNORE INTO {table_name} (name) VALUES (?)", (name.strip(),))
    conn.commit()
    conn.close()

def add_advance(party_type, party_name, amount, remarks=""):
    conn = get_db()
    c = conn.cursor()
    dt = datetime.now().strftime("%d-%m-%Y %I:%M %p")
    c.execute("INSERT INTO advances (party_type, party_name, date, amount, remarks) VALUES (?, ?, ?, ?, ?)",
              (party_type, party_name, dt, amount, remarks))
    conn.commit()
    conn.close()

init_db()

# --- AUTH STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None
if "target_email" not in st.session_state:
    st.session_state.target_email = ""

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #0F172A;'>🌾 ALPHA FARMS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>सुरक्षित कृषि एवं पर्ची प्रबंधन पोर्टल</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if not st.session_state.otp_sent:
            with st.form("login_email_form"):
                st.subheader("🔒 लॉगिन हेतु ईमेल दर्ज करें")
                email_input = st.text_input("अपना ईमेल दर्ज करें:", value="Sumitmishra27274@gmail.com")
                submit_otp = st.form_submit_button("📩 OTP प्राप्त करें ➔", use_container_width=True, type="primary")

                if submit_otp:
                    if email_input.strip() and "@" in email_input:
                        otp_code = str(random.randint(100000, 999999))
                        st.session_state.generated_otp = otp_code
                        st.session_state.target_email = email_input.strip()
                        st.session_state.otp_sent = True
                        st.rerun()
                    else:
                        st.warning("कृपया सही ईमेल पता दर्ज करें!")
        else:
            with st.form("verify_otp_form"):
                st.subheader("📩 OTP सत्यापन")
                st.caption(f"ईमेल: **{st.session_state.target_email}**")
                
                # स्क्रीन पर स्पष्ट डेमो OTP
                st.success(f"🔑 आपका लॉगिन OTP कोड है: **{st.session_state.generated_otp}**")
                
                entered_otp = st.text_input("6 अंकों का OTP दर्ज करें:", max_chars=6)
                verify_btn = st.form_submit_button("✅ सत्यापित करें और प्रवेश करें ➔", use_container_width=True, type="primary")

                if verify_btn:
                    if entered_otp.strip() == str(st.session_state.generated_otp):
                        st.session_state.authenticated = True
                        st.session_state.user_info = {
                            "id": st.session_state.target_email.split('@')[0],
                            "name": st.session_state.target_email
                        }
                        st.session_state.otp_sent = False
                        st.session_state.generated_otp = None
                        st.rerun()
                    else:
                        st.error("गलत OTP दर्ज किया गया है!")

            if st.button("🔄 ईमेल बदलें या नया OTP लें"):
                st.session_state.otp_sent = False
                st.session_state.generated_otp = None
                st.rerun()
    st.stop()

# --- APP INTERFACE (POST-LOGIN) ---
settings = get_settings()

with st.sidebar:
    st.markdown("## 🌾 Alpha Farms")
    st.markdown(f"👤 **{st.session_state.user_info['name']}**")
    st.divider()
    
    menu = st.radio(
        "नेविगेशन मेन्यू",
        [
            "📝 नई पर्ची एंट्री",
            "📋 पर्ची रजिस्टर, एडिट व डिलीट",
            "🚛 ट्रांसपोर्टर हिसाब",
            "🌾 छिलाईदार (1/2 बंटवारा)",
            "📈 ओवरऑल प्रोग्रेस सारांश"
        ]
    )
    st.divider()
    if st.button("🔒 लॉग आउट (Logout)", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_info = {}
        st.session_state.otp_sent = False
        st.session_state.generated_otp = None
        st.rerun()

# 1. नई पर्ची
if menu == "📝 नई पर्ची एंट्री":
    st.title("📝 नई गन्ना पर्ची एंट्री")
    farmers_list = get_master_list("master_farmers")
    trans_list = get_master_list("master_transporters")
    chilai_list = get_master_list("master_chilai")

    with st.form("full_slip_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            f_slip = st.text_input("पर्ची क्र. *")
            f_date = st.text_input("दिनांक व समय", value=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"), disabled=True)
            f_farmer = st.selectbox("किसान", farmers_list if farmers_list else ["Self"])
            f_variety = st.selectbox("प्रजाति", ["शीघ्र", "सामान्य"])
        with c2:
            f_weight = st.number_input("शुद्ध वजन (क्विंटल) *", min_value=0.0, value=0.0, step=0.1)
            f_trans = st.selectbox("ट्रांसपोर्टर", trans_list if trans_list else ["ARPIT"])
            f_trans_charge = st.number_input("ट्रांसपोर्ट भाड़ा (₹)", value=float(settings.get("transport_rate", 420.0)))
            f_chilai_by = st.selectbox("छिलाईदार", chilai_list if chilai_list else ["लेबर टीम 1"])
        with c3:
            f_chilai_rate = st.number_input("छिलाई दर (₹/Qtl)", value=float(settings.get("chilai_rate", 50.0)))
            f_status = st.selectbox("पेमेंट स्थिति", ["Unpaid", "Paid", "Partially Paid"])
            f_paid = st.number_input("प्राप्त भुगतान (₹)", value=0.0)

        if st.form_submit_button("💾 पर्ची सुरक्षित करें", type="primary", use_container_width=True):
            if f_slip.strip() and f_weight > 0:
                rate = settings.get("normal_rate", 379.38) if f_variety == "सामान्य" else settings.get("early_rate", 389.38)
                gross = round(f_weight * rate, 2)
                chilai_cost = round(f_weight * f_chilai_rate, 2)
                tot_ded = round(f_trans_charge + chilai_cost, 2)
                net = round(gross - tot_ded, 2)
                amount_paid = gross if f_status == "Paid" else (f_paid if f_status == "Partially Paid" else 0.0)
                balance_due = round(gross - amount_paid, 2)
                conn = get_db()
                c = conn.cursor()
                try:
                    c.execute("""INSERT INTO parchis (slip_no, date_time, variety, weight, rate, gross_amount, eticket_no, person, transporter, chilai_by, transport_charge, chilai_charge, total_deductions, net_in_hand, payment_status, amount_paid, balance_due, generated_by)
                                 VALUES (?, ?, ?, ?, ?, ?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                              (f_slip.strip(), f_date, f_variety, f_weight, rate, gross, f_farmer, f_trans, f_chilai_by, f_trans_charge, chilai_cost, tot_ded, net, f_status, amount_paid, balance_due, st.session_state.user_info['name']))
                    conn.commit()
                    st.success(f"✅ पर्ची नं. {f_slip} सुरक्षित हो गई!")
                except sqlite3.IntegrityError:
                    st.error("यह पर्ची नंबर पहले से मौजूद है!")
                finally: conn.close()

# 2. पर्ची रजिस्टर
elif menu == "📋 पर्ची रजिस्टर, एडिट व डिलीट":
    st.title("📋 पर्ची रजिस्टर एवं प्रबंधन")
    conn = get_db()
    df = pd.read_sql_query("SELECT id, slip_no AS 'पर्ची नं.', COALESCE(date_time, date) AS 'दिनांक व समय', person AS 'किसान', variety AS 'प्रजाति', weight AS 'वजन (Q)', gross_amount AS 'सकल ₹', transporter AS 'ट्रांसपोर्टर', transport_charge AS 'भाड़ा ₹', chilai_by AS 'छिलाईदार', chilai_charge AS 'छिलाई ₹', net_in_hand AS 'शुद्ध ₹', payment_status AS 'स्थिति' FROM parchis ORDER BY id DESC", conn)
    conn.close()

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1: search = st.text_input("🔍 खोजें:")
    with col_s2:
        if not df.empty:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w: df.to_excel(w, index=False)
            st.download_button("📊 Excel एक्सपोर्ट", buf.getvalue(), f"Report_{datetime.now().strftime('%Y%m%d')}.xlsx", use_container_width=True)

    if search.strip() and not df.empty:
        q = search.strip().lower()
        df = df[df.apply(lambda r: q in str(r['पर्ची नं.']).lower() or q in str(r['किसान']).lower() or q in str(r['ट्रांसपोर्टर']).lower(), axis=1)]
    st.dataframe(df, use_container_width=True, hide_index=True)

    if not df.empty:
        st.divider()
        c_ed1, c_ed2 = st.columns(2)
        slip_list = df['पर्ची नं.'].tolist()
        with c_ed1:
            st.subheader("✏️ पर्ची वजन अपडेट करें")
            sel_e = st.selectbox("पर्ची चुनें:", slip_list, key="esel")
            new_w = st.number_input("नया वजन (Q):", min_value=0.0, step=0.1)
            if st.button("🔄 अपडेट करें"):
                conn = get_db(); c = conn.cursor()
                rate = float(settings.get("early_rate", 389.38))
                gross = round(new_w * rate, 2)
                c.execute("UPDATE parchis SET weight=?, gross_amount=? WHERE slip_no=?", (new_w, gross, sel_e))
                conn.commit(); conn.close(); st.success("अपडेट हो गया!"); st.rerun()

        with c_ed2:
            st.subheader("🗑️ पर्ची डिलीट करें")
            sel_d = st.selectbox("डिलीट करने के लिए पर्ची:", slip_list, key="dsel")
            if st.checkbox("डिलीट करने की पुष्टि करें", key="dchk"):
                if st.button("🚨 पर्ची हमेशा के लिए डिलीट करें", type="primary"):
                    conn = get_db(); c = conn.cursor()
                    c.execute("DELETE FROM parchis WHERE slip_no=?", (sel_d,))
                    conn.commit(); conn.close(); st.success("पर्ची हटा दी गई!"); st.rerun()

# 3. ट्रांसपोर्टर हिसाब
elif menu == "🚛 ट्रांसपोर्टर हिसाब":
    st.title("🚛 ट्रांसपोर्टर हिसाब")
    t_list = get_master_list("master_transporters")
    if t_list:
        sel_t = st.selectbox("ट्रांसपोर्टर चुनें:", t_list)
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT slip_no, COALESCE(date_time, date), person, transport_charge FROM parchis WHERE transporter=?", (sel_t,))
        t_rows = c.fetchall()
        c.execute("SELECT COALESCE(SUM(amount),0) FROM advances WHERE party_type='transporter' AND party_name=?", (sel_t,))
        t_adv = c.fetchone()[0]; conn.close()
        t_total = sum(r[3] for r in t_rows)
        net_t = round(t_total - t_adv, 2)

        c1, c2, c3 = st.columns(3)
        c1.metric("कुल पर्चियाँ", f"{len(t_rows)} पर्ची")
        c2.metric("कुल भाड़ा", f"₹{t_total:,.2f}")
        c3.metric("एडवांस कटौती", f"₹{t_adv:,.2f}")
        st.metric("अंतिम शुद्ध देय", f"₹{net_t:,.2f}")

        with st.expander("➕ एडवांस राशि दर्ज करें"):
            with st.form("adv_t"):
                amt = st.number_input("राशि (₹):", min_value=1.0)
                if st.form_submit_button("सुरक्षित करें"):
                    add_advance("transporter", sel_t, amt, "नगद")
                    st.rerun()

# 4. छिलाई 50-50 बंटवारा
elif menu == "🌾 छिलाईदार (1/2 बंटवारा)":
    st.title("🌾 छिलाईदार 50-50 बंटवारा विवरण")
    ch_list = get_master_list("master_chilai")
    if ch_list:
        sel_ch = st.selectbox("छिलाईदार चुनें:", ch_list)
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT slip_no, COALESCE(date_time, date), weight, chilai_charge FROM parchis WHERE chilai_by=?", (sel_ch,))
        c_rows = c.fetchall()
        c.execute("SELECT COALESCE(SUM(amount),0) FROM advances WHERE party_type='chilai' AND party_name=?", (sel_ch,))
        c_adv = c.fetchone()[0]; conn.close()
        tot_wt = sum(r[2] for r in c_rows)
        tot_ch = sum(r[3] for r in c_rows)
        half = round(tot_ch / 2, 2)
        part_a = round(half - c_adv, 2)
        part_b = half
        net_ch = round(tot_ch - c_adv, 2)

        c1, c2, c3 = st.columns(3)
        c1.metric("कुल पर्चियाँ", f"{len(c_rows)}")
        c2.metric("कुल छिला वजन", f"{tot_wt:.2f} Qtl")
        c3.metric("कुल मजदूरी", f"₹{tot_ch:,.2f}")

        st.info(f"**👤 हिस्सा A (एडवांस समायोजित):** ₹{half:,.2f} - ₹{c_adv:,.2f} = **₹{part_a:,.2f}**")
        st.success(f"**👤 हिस्सा B (पूर्ण भुगतान):** **₹{part_b:,.2f}**")
        st.metric("फ़ार्म द्वारा शुद्ध नकद देय", f"₹{net_ch:,.2f}")

        with st.expander("➕ एडवांस राशि दर्ज करें"):
            with st.form("adv_c"):
                amt_c = st.number_input("राशि (₹):", min_value=1.0)
                if st.form_submit_button("सुरक्षित करें"):
                    add_advance("chilai", sel_ch, amt_c, "नगद")
                    st.rerun()

# 5. ओवरऑल सारांश
elif menu == "📈 ओवरऑल प्रोग्रेस सारांश":
    st.title("📈 ओवरऑल प्रोग्रेस सारांश")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*), COALESCE(SUM(weight), 0), COALESCE(SUM(gross_amount), 0), COALESCE(SUM(net_in_hand), 0) FROM parchis")
    kpi = c.fetchone(); conn.close()
    if kpi:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("कुल पर्चियाँ", f"{kpi[0]}")
        c2.metric("कुल वजन", f"{kpi[1]:.2f} Qtl")
        c3.metric("सकल गन्ना मूल्य", f"₹{kpi[2]:,.2f}")
        c4.metric("शुद्ध बचत (In-Hand)", f"₹{kpi[3]:,.2f}")
