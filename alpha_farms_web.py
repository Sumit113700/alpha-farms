# -*- coding: utf-8 -*-
"""
🌾 Alpha Farms - वेब ऐप (Streamlit Full Parity Edition)
100% Free Hosting Ready | Complete Offline Parity | Mobile & Desktop Responsive
"""

import os
import sqlite3
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS master_farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            village TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS master_transporters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            default_fare REAL DEFAULT 420.0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS master_chilai (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS advances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            party_type TEXT,
            party_name TEXT,
            date TEXT,
            amount REAL,
            remarks TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            full_name TEXT,
            role TEXT
        )
    """)
    c.execute("INSERT OR IGNORE INTO users (username, password, full_name, role) VALUES ('admin', '1234', 'फ़ार्म प्रबंधक (Alpha Farms)', 'Admin')")
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value REAL
        )
    """)
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

def delete_from_master(table_name, name):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"DELETE FROM {table_name} WHERE name=?", (name,))
    conn.commit()
    conn.close()

def get_total_advance(party_type, party_name):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM advances WHERE party_type=? AND party_name=?", (party_type, party_name))
    val = c.fetchone()[0]
    conn.close()
    return val

def add_advance(party_type, party_name, amount, remarks=""):
    conn = get_db()
    c = conn.cursor()
    dt = datetime.now().strftime("%d-%m-%Y %I:%M %p")
    c.execute("INSERT INTO advances (party_type, party_name, date, amount, remarks) VALUES (?, ?, ?, ?, ?)",
              (party_type, party_name, dt, amount, remarks))
    conn.commit()
    conn.close()

init_db()

# --- AUTHENTICATION STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #0F172A; margin-bottom: 2px;'>🌾 ALPHA FARMS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 15px;'>गन्ना पर्ची, ढुलाई, छिलाई एवं कृषि प्रबंधन पोर्टल</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.subheader("🔒 सुरक्षित लॉगिन पैनल")
            user_input = st.text_input("यूजर आईडी (User ID)", value="admin")
            pass_input = st.text_input("पासवर्ड (Password)", type="password", value="1234")
            submitted = st.form_submit_button("लॉगिन करें ➔", use_container_width=True, type="primary")
            
            if submitted:
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT full_name, role FROM users WHERE username=? AND password=?", (user_input.strip(), pass_input.strip()))
                row = c.fetchone()
                conn.close()
                if row:
                    st.session_state.authenticated = True
                    st.session_state.user_info = {"id": user_input, "name": row[0], "role": row[1]}
                    st.success("लॉगिन सफल! पोर्टल लोड हो रहा है...")
                    st.rerun()
                else:
                    st.error("गलत यूजर आईडी या पासवर्ड!")
    st.stop()

# --- APP INTERFACE (POST-LOGIN) ---
settings = get_settings()

with st.sidebar:
    st.markdown("## 🌾 Alpha Farms")
    st.markdown(f"👤 **{st.session_state.user_info['name']}**")
    st.caption(f"आईडी: `{st.session_state.user_info['id']}` | रोल: {st.session_state.user_info['role']}")
    st.divider()
    
    menu = st.radio(
        "नेविगेशन मेन्यू (System Menu)",
        [
            "📝 नई पर्ची एंट्री",
            "📋 पर्ची रजिस्टर, एडिट व रसीद",
            "🚛 ट्रांसपोर्टर हिसाब व बिल",
            "🌾 छिलाईदार (1/2 बंटवारा बिल)",
            "📈 ओवरऑल प्रोग्रेस सारांश",
            "⚙️ मास्टर डेटा, दरें & यूजर"
        ]
    )
    st.divider()
    if st.button("🔒 लॉग आउट (Logout)", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_info = {}
        st.rerun()

# ========================================================
# VIEW 1: नई पर्ची एंट्री (QUICK & FULL)
# ========================================================
if menu == "📝 नई पर्ची एंट्री":
    st.title("📝 नई गन्ना पर्ची एंट्री")
    st.caption("त्वरित (Quick) या विस्तृत विवरण के साथ पर्ची जारी करें।")

    farmers_list = get_master_list("master_farmers")
    trans_list = get_master_list("master_transporters")
    chilai_list = get_master_list("master_chilai")

    # 1. Quick Register
    with st.expander("⚡ केवल पर्ची नंबर से त्वरित रजिस्ट्रेशन (Quick Register - वजन बाद में दर्ज करें)", expanded=False):
        with st.form("quick_slip_form"):
            q_slip = st.text_input("पर्ची / रसीद क्र. * (Slip No)")
            q_date = st.text_input("दिनांक व समय (Auto)", value=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"), disabled=True)
            col_qa, col_qb = st.columns(2)
            with col_qa:
                q_farmer = st.selectbox("किसान / खातादार", farmers_list if farmers_list else ["Self"], key="qf")
            with col_qb:
                q_trans = st.selectbox("ट्रांसपोर्टर", trans_list if trans_list else ["ARPIT"], key="qt")
            if st.form_submit_button("🚀 तुरंत रजिस्टर करें", type="primary"):
                if not q_slip.strip():
                    st.warning("कृपया पर्ची नंबर दर्ज करें!")
                else:
                    conn = get_db()
                    c = conn.cursor()
                    try:
                        c.execute("""
                            INSERT INTO parchis (slip_no, date_time, variety, weight, rate, gross_amount, eticket_no,
                            person, transporter, chilai_by, transport_charge, chilai_charge, total_deductions, net_in_hand,
                            payment_status, amount_paid, balance_due, generated_by)
                            VALUES (?, ?, 'शीघ्र', 0.0, 389.38, 0.0, '', ?, ?, 'लेबर टीम 1', 0.0, 0.0, 0.0, 0.0, 'Registered', 0.0, 0.0, ?)
                        """, (q_slip.strip(), q_date, q_farmer, q_trans, st.session_state.user_info['name']))
                        conn.commit()
                        st.success(f"⚡ पर्ची नं. {q_slip} पंजीकृत हो गई! वजन आने पर 'पर्ची रजिस्टर' से एडिट कर सकते हैं।")
                    except sqlite3.IntegrityError:
                        st.error(f"पर्ची नंबर {q_slip} पहले से मौजूद है!")
                    finally:
                        conn.close()

    # 2. Full Entry
    with st.form("full_slip_form"):
        st.subheader("विस्तृत पर्ची विवरण")
        c1, c2, c3 = st.columns(3)
        with c1:
            f_slip = st.text_input("पर्ची / रसीद क्र. *")
            f_date = st.text_input("दिनांक व समय", value=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"), disabled=True)
            f_farmer = st.selectbox("किसान / खातादार (चुनें)", farmers_list if farmers_list else ["Self"])
            f_variety = st.selectbox("गन्ना प्रजाति", ["शीघ्र", "सामान्य"])
        with c2:
            f_weight = st.number_input("शुद्ध वजन (क्विंटल) *", min_value=0.0, value=0.0, step=0.1, format="%.2f")
            f_trans = st.selectbox("ट्रांसपोर्टर (चुनें)", trans_list if trans_list else ["ARPIT"])
            f_trans_charge = st.number_input("ट्रांसपोर्ट भाड़ा (₹)", value=float(settings.get("transport_rate", 420.0)), step=10.0)
            f_chilai_by = st.selectbox("छिलाईदार (चुनें)", chilai_list if chilai_list else ["लेबर टीम 1"])
        with c3:
            f_chilai_rate = st.number_input("छिलाई दर (₹/Qtl)", value=float(settings.get("chilai_rate", 50.0)), step=1.0)
            f_status = st.selectbox("पेमेंट स्थिति", ["Unpaid", "Paid", "Partially Paid"])
            f_paid = st.number_input("प्राप्त भुगतान (₹)", value=0.0, step=50.0)
            f_gen_by = st.text_input("Generated By", value=st.session_state.user_info['name'], disabled=True)

        if st.form_submit_button("💾 पर्ची सुरक्षित करें", type="primary", use_container_width=True):
            if not f_slip.strip() or f_weight <= 0:
                st.warning("कृपया पर्ची नंबर और शुद्ध वजन अवश्य भरें!")
            else:
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
                    c.execute("""
                        INSERT INTO parchis (slip_no, date_time, variety, weight, rate, gross_amount, eticket_no,
                        person, transporter, chilai_by, transport_charge, chilai_charge, total_deductions, net_in_hand,
                        payment_status, amount_paid, balance_due, generated_by)
                        VALUES (?, ?, ?, ?, ?, ?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (f_slip.strip(), f_date, f_variety, f_weight, rate, gross, f_farmer, f_trans, f_chilai_by,
                          f_trans_charge, chilai_cost, tot_ded, net, f_status, amount_paid, balance_due, f_gen_by))
                    conn.commit()
                    st.success(f"✅ पर्ची नं. {f_slip} दर्ज हो गई! (सकल: ₹{gross:,.2f} | शुद्ध बचत: ₹{net:,.2f})")
                except sqlite3.IntegrityError:
                    st.error(f"पर्ची नंबर {f_slip} पहले से मौजूद है!")
                finally:
                    conn.close()

# ========================================================
# VIEW 2: पर्ची रजिस्टर, खोज, एडिट, डिलीट व रसीद प्रिंट
# ========================================================
elif menu == "📋 पर्ची रजिस्टर, एडिट व रसीद":
    st.title("📋 पर्ची रजिस्टर, संपादन एवं रसीद प्रिंट")
    
    conn = get_db()
    df = pd.read_sql_query("""
        SELECT id, slip_no AS 'पर्ची नं.', COALESCE(date_time, date) AS 'दिनांक व समय', person AS 'किसान',
               variety AS 'प्रजाति', weight AS 'वजन (Q)', rate AS 'दर ₹', gross_amount AS 'सकल ₹', transporter AS 'ट्रांसपोर्टर',
               transport_charge AS 'भाड़ा ₹', chilai_by AS 'छिलाईदार', chilai_charge AS 'छिलाई ₹',
               net_in_hand AS 'शुद्ध ₹', payment_status AS 'स्थिति', balance_due AS 'बकाया ₹', generated_by AS 'Gen By'
        FROM parchis ORDER BY id DESC
    """, conn)
    conn.close()

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search = st.text_input("🔍 खोजें (पर्ची नंबर / किसान / ट्रांसपोर्टर / छिलाईदार):")
    with col_s2:
        st.write("")
        st.write("")
        if not df.empty:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Parchi_Report')
            st.download_button(
                label="📊 Excel एक्सपोर्ट",
                data=excel_buffer.getvalue(),
                file_name=f"Alpha_Farms_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    if search.strip() and not df.empty:
        q = search.strip().lower()
        df_filtered = df[df.apply(lambda r: q in str(r['पर्ची नं.']).lower() or q in str(r['किसान']).lower() or q in str(r['ट्रांसपोर्टर']).lower() or q in str(r['छिलाईदार']).lower(), axis=1)]
    else:
        df_filtered = df

    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    st.divider()

    # Action Hub: Print Slip, Edit Slip, Delete Slip
    if not df.empty:
        slip_list = df['पर्ची नं.'].tolist()
        
        tab_p, tab_e, tab_d = st.tabs(["🖨️ पर्ची रसीद प्रिंट करें", "✏️ पर्ची एडिट करें (Edit)", "🗑️ पर्ची डिलीट करें (Delete)"])

        # 1. Print Slip Receipt Tab
        with tab_p:
            sel_p_slip = st.selectbox("प्रिंट करने के लिए पर्ची चुनें:", slip_list, key="print_slip_sel")
            conn = get_db()
            c = conn.cursor()
            c.execute("""SELECT slip_no, COALESCE(date_time, date), variety, weight, rate, gross_amount,
                             person, transporter, transport_charge, COALESCE(chilai_by, 'लेबर'), chilai_charge,
                             total_deductions, net_in_hand, payment_status, amount_paid, balance_due,
                             COALESCE(generated_by, 'Admin')
                             FROM parchis WHERE slip_no=?""", (sel_p_slip,))
            row = c.fetchone()
            conn.close()

            if row:
                st_color = "#16a34a" if row[13] == "Paid" else ("#d97706" if row[13] == "Partially Paid" else "#dc2626")
                receipt_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #fff; padding: 15px; color: #0f172a; }}
        .receipt-card {{ max-width: 440px; margin: 0 auto; border: 2px dashed #334155; border-radius: 10px; padding: 20px; }}
        .brand-header {{ text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 10px; margin-bottom: 12px; }}
        .brand-header h2 {{ margin: 0; font-size: 20px; color: #0f172a; }}
        .brand-header p {{ margin: 3px 0 0; font-size: 11px; color: #64748b; }}
        .badge {{ background: #0f172a; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; display: inline-block; margin-top: 5px; }}
        .info-row {{ display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 5px; }}
        .net-card {{ background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 6px; padding: 8px 10px; margin: 10px 0; display: flex; justify-content: space-between; }}
        @media print {{ .no-print {{ display: none !important; }} }}
    </style>
</head>
<body>
    <div class="no-print" style="text-align:center; margin-bottom: 10px;">
        <button onclick="window.print()" style="background:#0284c7; color:#fff; font-size:13px; font-weight:bold; padding:8px 20px; border:none; border-radius:4px; cursor:pointer;">🖨️ पर्ची प्रिंट करें (Print / PDF)</button>
    </div>
    <div class="receipt-card">
        <div class="brand-header">
            <h2>🌾 ALPHA FARMS</h2>
            <p>गन्ना आपूर्ति एवं कटौती रसीद</p>
            <span class="badge">पर्ची क्र.: {row[0]}</span>
        </div>
        <div class="info-row"><span>दिनांक व समय:</span> <span>{row[1]}</span></div>
        <div class="info-row"><span>किसान / खातादार:</span> <strong>{row[6]}</strong></div>
        <div class="info-row"><span>गन्ना प्रजाति:</span> <span>{row[2]}</span></div>
        <div class="info-row"><span>कुल वजन:</span> <strong>{row[3]:.2f} क्विंटल</strong></div>
        <div class="info-row"><span>सरकारी दर:</span> <span>₹{row[4]:.2f} / Qtl</span></div>
        <div class="info-row" style="border-top:1px dashed #cbd5e1; padding-top:4px;"><span>सकल मूल्य:</span> <strong>₹{row[5]:,.2f}</strong></div>
        <div class="info-row"><span>ट्रांसपोर्टर ({row[7]}):</span> <span style="color:#dc2626;">- ₹{row[8]:,.2f}</span></div>
        <div class="info-row"><span>छिलाईदार ({row[9]}):</span> <span style="color:#dc2626;">- ₹{row[10]:,.2f}</span></div>
        <div class="net-card">
            <span style="font-weight:bold; color:#065f46;">शुद्ध बचत (In-Hand):</span>
            <span style="font-weight:bold; color:#059669; font-size:16px;">₹{row[12]:,.2f}</span>
        </div>
        <div class="info-row"><span>पेमेंट स्थिति:</span> <strong style="color:{st_color};">{row[13]}</strong></div>
        <div class="info-row"><span>प्राप्त राशि:</span> <span>₹{row[14]:,.2f}</span></div>
        <div class="info-row"><span>शेष बकाया:</span> <strong style="color:#dc2626;">₹{row[15]:,.2f}</strong></div>
        <div style="text-align:center; margin-top:15px; font-size:11px; color:#64748b; border-top:1px dashed #e2e8f0; padding-top:8px;">
            Slip Generated By: {row[16]} | Alpha Farms
        </div>
    </div>
</body>
</html>"""
                components.html(receipt_html, height=480, scrolling=True)

        # 2. Edit Slip Tab
        with tab_e:
            sel_e_slip = st.selectbox("एडिट करने के लिए पर्ची नंबर चुनें:", slip_list, key="edit_slip_sel")
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT id, slip_no, weight, transport_charge, chilai_charge, variety, person, transporter, chilai_by, payment_status, amount_paid FROM parchis WHERE slip_no=?", (sel_e_slip,))
            e_row = c.fetchone()
            conn.close()

            if e_row:
                with st.form("edit_parchi_form"):
                    st.markdown(f"**पर्ची संपादन: {e_row[1]}** (किसान: {e_row[6]})")
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        new_farmer = st.selectbox("किसान:", get_master_list("master_farmers"), index=get_master_list("master_farmers").index(e_row[6]) if e_row[6] in get_master_list("master_farmers") else 0)
                        new_variety = st.selectbox("प्रजाति:", ["शीघ्र", "सामान्य"], index=0 if e_row[5] == "शीघ्र" else 1)
                        new_weight = st.number_input("शुद्ध वजन (क्विंटल):", min_value=0.0, value=float(e_row[2]), step=0.1, format="%.2f")
                    with ce2:
                        new_trans = st.selectbox("ट्रांसपोर्टर:", get_master_list("master_transporters"), index=get_master_list("master_transporters").index(e_row[7]) if e_row[7] in get_master_list("master_transporters") else 0)
                        new_chilai = st.selectbox("छिलाईदार:", get_master_list("master_chilai"), index=get_master_list("master_chilai").index(e_row[8]) if e_row[8] in get_master_list("master_chilai") else 0)
                        new_status = st.selectbox("पेमेंट स्थिति:", ["Unpaid", "Paid", "Partially Paid", "Registered"], index=["Unpaid", "Paid", "Partially Paid", "Registered"].index(e_row[9]) if e_row[9] in ["Unpaid", "Paid", "Partially Paid", "Registered"] else 0)
                    
                    new_paid = st.number_input("प्राप्त भुगतान (₹):", min_value=0.0, value=float(e_row[10]), step=50.0)

                    if st.form_submit_button("🔄 बदलाव सुरक्षित करें", type="primary", use_container_width=True):
                        rate = settings.get("normal_rate", 379.38) if new_variety == "सामान्य" else settings.get("early_rate", 389.38)
                        gross = round(new_weight * rate, 2)
                        chilai_rate = float(settings.get("chilai_rate", 50.0))
                        chilai_cost = round(new_weight * chilai_rate, 2)
                        trans_cost = float(e_row[3]) if float(e_row[3]) > 0 else float(settings.get("transport_rate", 420.0))
                        tot_ded = round(trans_cost + chilai_cost, 2)
                        net = round(gross - tot_ded, 2)
                        amount_paid = gross if new_status == "Paid" else (new_paid if new_status == "Partially Paid" else 0.0)
                        due_amt = round(gross - amount_paid, 2)

                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""
                            UPDATE parchis SET person=?, variety=?, weight=?, rate=?, gross_amount=?, transporter=?,
                            transport_charge=?, chilai_by=?, chilai_charge=?, total_deductions=?, net_in_hand=?,
                            payment_status=?, amount_paid=?, balance_due=?
                            WHERE slip_no=?
                        """, (new_farmer, new_variety, new_weight, rate, gross, new_trans, trans_cost, new_chilai,
                              chilai_cost, tot_ded, net, new_status, amount_paid, due_amt, sel_e_slip))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ पर्ची नं. {sel_e_slip} अपडेट हो गई! (वजन: {new_weight:.2f} Qtl | सकल: ₹{gross:,.2f})")
                        st.rerun()

        # 3. Delete Slip Tab
        with tab_d:
            sel_d_slip = st.selectbox("डिलीट करने के लिए पर्ची नंबर चुनें:", slip_list, key="del_slip_sel")
            row_del = df[df['पर्ची नं.'] == sel_d_slip].iloc[0]
            st.warning(f"⚠️ चेतावनी: आप पर्ची नं. **{sel_d_slip}** (किसान: {row_del['किसान']}, वजन: {row_del['वजन (Q)']} Q) को हमेशा के लिए हटाने जा रहे हैं।")
            confirm = st.checkbox("हाँ, मैं इस पर्ची को हटाना चाहता हूँ।", key="del_chk")
            if st.button("🚨 पर्ची हमेशा के लिए डिलीट करें", type="primary", disabled=not confirm):
                conn = get_db()
                c = conn.cursor()
                c.execute("DELETE FROM parchis WHERE slip_no=?", (sel_d_slip,))
                conn.commit()
                conn.close()
                st.success(f"पर्ची नं. {sel_d_slip} हटा दी गई!")
                st.rerun()

# ========================================================
# VIEW 3: ट्रांसपोर्टर हिसाब व बिल प्रिंट (नो टोटल वेट)
# ========================================================
elif menu == "🚛 ट्रांसपोर्टर हिसाब व बिल":
    st.title("🚛 ट्रांसपोर्टर हिसाब एवं आधिकारिक बिल प्रिंट")
    
    t_list = get_master_list("master_transporters")
    if not t_list:
        st.info("कृपया मास्टर सेटिंग्स में ट्रांसपोर्टर जोड़ें।")
    else:
        col_t1, col_t2 = st.columns([1, 2])
        with col_t1:
            sel_trans = st.selectbox("ट्रांसपोर्टर चुनें:", t_list)
            
            with st.expander("➕ ट्रांसपोर्टर को एडवांस दर्ज करें", expanded=False):
                with st.form("adv_t_form"):
                    adv_amt = st.number_input("एडवांस राशि (₹)", min_value=1.0, step=50.0)
                    adv_rem = st.text_input("विवरण", value="नगद एडवांस")
                    if st.form_submit_button("✅ एडवांस सुरक्षित करें"):
                        add_advance("transporter", sel_trans, adv_amt, adv_rem)
                        st.success("एडवांस दर्ज हो गया!")
                        st.rerun()

        with col_t2:
            conn = get_db()
            c = conn.cursor()
            c.execute("""SELECT slip_no, COALESCE(date_time, date), person, weight, transport_charge
                         FROM parchis WHERE transporter=? ORDER BY id ASC""", (sel_trans,))
            rows = c.fetchall()
            
            c.execute("SELECT date, amount, remarks FROM advances WHERE party_type='transporter' AND party_name=? ORDER BY id ASC", (sel_trans,))
            adv_rows = c.fetchall()
            conn.close()

            total_slips = len(rows)
            total_fare = sum(r[4] for r in rows)
            total_adv = sum(a[1] for a in adv_rows)
            net_payable = round(total_fare - total_adv, 2)

            m1, m2, m3 = st.columns(3)
            m1.metric("कुल पर्चियाँ", f"{total_slips} पर्ची")
            m2.metric("सकल भाड़ा", f"₹{total_fare:,.2f}")
            m3.metric("एडवांस कटौती", f"₹{total_adv:,.2f}", delta=f"-₹{total_adv:,.2f}", delta_color="inverse")
            st.metric("अंतिम शुद्ध देय शेष भाड़ा (Net Payable)", f"₹{net_payable:,.2f}")

        st.divider()
        st.subheader("🖨️ अधिकृत ट्रांसपोर्टर भाड़ा बिल (प्रिंट प्रीव्यू)")

        if rows:
            tbl_rows_html = ""
            for i, r in enumerate(rows, 1):
                bg = "#ffffff" if i % 2 != 0 else "#f8fafc"
                tbl_rows_html += f"""<tr style="background-color: {bg};">
                    <td style="text-align:center; padding: 8px; border-bottom: 1px solid #e2e8f0;">{i:02d}</td>
                    <td style="text-align:center; padding: 8px; border-bottom: 1px solid #e2e8f0; font-weight:bold;">{r[0]}</td>
                    <td style="text-align:center; padding: 8px; border-bottom: 1px solid #e2e8f0;">{r[1]}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{r[2]}</td>
                    <td style="text-align:right; padding: 8px; border-bottom: 1px solid #e2e8f0; font-weight:bold; color:#0284c7;">₹{r[4]:,.2f}</td>
                </tr>"""

            adv_details_html = ""
            if adv_rows:
                adv_items = "".join([f"""<tr style="border-bottom: 1px dashed #cbd5e1;">
                    <td style="padding: 5px 8px;">{a[0]}</td>
                    <td style="padding: 5px 8px; font-style: italic;">{a[2] or 'नगद'}</td>
                    <td style="padding: 5px 8px; text-align: right; font-weight: bold; color: #dc2626;">- ₹{a[1]:,.2f}</td>
                </tr>""" for a in adv_rows])
                adv_details_html = f"""
                <div style="margin-top: 15px; border: 1px solid #fed7aa; background: #fffaf5; border-radius: 6px; padding: 10px;">
                    <strong style="color: #c2410c; font-size: 12px;">💰 पूर्व एडवांस कटौती विवरण:</strong>
                    <table style="width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 5px;">{adv_items}</table>
                </div>"""

            trans_bill_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #fff; padding: 15px; color: #0f172a; }}
        .sheet {{ max-width: 780px; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 8px; padding: 25px; }}
        .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #0f172a; padding-bottom: 10px; margin-bottom: 15px; }}
        .meta-grid {{ display: flex; justify-content: space-between; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin-bottom: 15px; font-size: 13px; }}
        table.tbl {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
        table.tbl th {{ background: #0f172a; color: #fff; padding: 8px; text-align: center; }}
        .summary-card {{ background: #f0fdf4; border: 2px solid #86efac; border-radius: 6px; padding: 14px; margin-top: 15px; }}
        .sum-line {{ display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; }}
        .sum-line.net {{ border-top: 2px dashed #86efac; padding-top: 8px; margin-top: 8px; font-size: 16px; font-weight: bold; color: #166534; }}
        @media print {{ .no-print {{ display: none !important; }} }}
    </style>
</head>
<body>
    <div class="no-print" style="text-align: center; margin-bottom: 15px;">
        <button onclick="window.print()" style="background:#0284c7; color:#fff; font-size:13px; font-weight:bold; padding:9px 24px; border:none; border-radius:5px; cursor:pointer;">🖨️ ट्रांसपोर्टर बिल प्रिंट करें (Print / PDF)</button>
    </div>
    <div class="sheet">
        <div class="header">
            <div>
                <h2 style="margin:0; color:#0f172a;">🌾 ALPHA FARMS</h2>
                <div style="font-size:12px; color:#64748b;">अधिकृत ढुलाई भाड़ा भुगतान विवरण</div>
            </div>
            <div style="text-align:right;">
                <div style="font-weight:bold; color:#0284c7;">ट्रांसपोर्टर स्टेटमेंट</div>
                <div style="font-size:11px; color:#64748b;">दिनांक: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}</div>
            </div>
        </div>
        <div class="meta-grid">
            <div>
                <div>ट्रांसपोर्टर का नाम: <strong style="font-size:15px; color:#0284c7;">{sel_trans}</strong></div>
                <div style="margin-top:4px;">ऑपरेटर: <strong>{st.session_state.user_info['name']}</strong></div>
            </div>
            <div style="text-align:right;">
                <div>कुल पर्चियाँ: <strong style="font-size:16px; color:#0f172a;">{total_slips} पर्ची</strong></div>
            </div>
        </div>
        <table class="tbl">
            <thead>
                <tr>
                    <th style="width:40px;">क्र.</th>
                    <th>पर्ची नंबर</th>
                    <th>पर्ची दिनांक व समय</th>
                    <th>किसान / खातादार</th>
                    <th style="text-align:right;">भाड़ा राशि (₹)</th>
                </tr>
            </thead>
            <tbody>{tbl_rows_html}</tbody>
        </table>
        <div class="summary-card">
            <div class="sum-line"><span>कुल सकल भाड़ा ({total_slips} Slips):</span> <strong>₹{total_fare:,.2f}</strong></div>
            <div class="sum-line" style="color:#dc2626;"><span>(-) पूर्व दिया गया कुल एडवांस:</span> <strong>- ₹{total_adv:,.2f}</strong></div>
            <div class="sum-line net"><span>अंतिम शुद्ध देय शेष भुगतान:</span> <span>₹{net_payable:,.2f}</span></div>
        </div>
        {adv_details_html}
        <div style="display:flex; justify-content:space-between; margin-top:35px; border-top:1px solid #94a3b8; padding-top:8px; font-size:11px; color:#475569;">
            <div>हस्ताक्षर ट्रांसपोर्टर ({sel_trans})</div>
            <div>अधिकृत हस्ताक्षर (Alpha Farms)</div>
        </div>
    </div>
</body>
</html>"""
            components.html(trans_bill_html, height=520, scrolling=True)

# ========================================================
# VIEW 4: छिलाईदार (1/2 बंटवारा बिल प्रिंट)
# ========================================================
elif menu == "🌾 छिलाईदार (1/2 बंटवारा बिल)":
    st.title("🌾 छिलाईदार मजदूरी एवं 50-50 बंटवारा विवरण")
    
    ch_list = get_master_list("master_chilai")
    if not ch_list:
        st.info("कृपया मास्टर सेटिंग्स में छिलाईदार जोड़ें।")
    else:
        col_c1, col_c2 = st.columns([1, 2])
        with col_c1:
            sel_chilai = st.selectbox("छिलाईदार / लेबर टीम चुनें:", ch_list)
            
            with st.expander("➕ छिलाईदार को एडवांस दर्ज करें", expanded=False):
                with st.form("adv_c_form"):
                    adv_amt_c = st.number_input("एडवांस राशि (₹)", min_value=1.0, step=50.0)
                    adv_rem_c = st.text_input("विवरण", value="नगद एडवांस")
                    if st.form_submit_button("✅ एडवांस सुरक्षित करें"):
                        add_advance("chilai", sel_chilai, adv_amt_c, adv_rem_c)
                        st.success("एडवांस दर्ज हो गया!")
                        st.rerun()

        with col_c2:
            conn = get_db()
            c = conn.cursor()
            c.execute("""SELECT slip_no, COALESCE(date_time, date), weight, chilai_charge, person
                         FROM parchis WHERE chilai_by=? ORDER BY id ASC""", (sel_chilai,))
            rows = c.fetchall()
            
            c.execute("SELECT date, amount, remarks FROM advances WHERE party_type='chilai' AND party_name=? ORDER BY id ASC", (sel_chilai,))
            adv_rows = c.fetchall()
            conn.close()

            total_slips = len(rows)
            total_weight = sum(r[2] for r in rows)
            total_chilai = sum(r[3] for r in rows)
            total_adv_c = sum(a[1] for a in adv_rows)
            net_payable = round(total_chilai - total_adv_c, 2)

            half_gross = round(total_chilai / 2, 2)
            part_b_net = half_gross
            part_a_net = round(half_gross - total_adv_c, 2)

            k1, k2, k3 = st.columns(3)
            k1.metric("कुल पर्चियाँ", f"{total_slips} पर्ची")
            k2.metric("कुल छिला वजन", f"{total_weight:,.2f} Qtl")
            k3.metric("सकल मजदूरी", f"₹{total_chilai:,.2f}")

        st.divider()
        st.subheader("🖨️ छिलाईदार 50-50 लेज़र बिल (प्रिंट प्रीव्यू)")

        if rows:
            tbl_c_rows = ""
            for i, r in enumerate(rows, 1):
                bg = "#ffffff" if i % 2 != 0 else "#f8fafc"
                tbl_c_rows += f"""<tr style="background-color: {bg};">
                    <td style="text-align:center; padding: 7px 8px; border-bottom: 1px solid #e2e8f0;">{i:02d}</td>
                    <td style="text-align:center; padding: 7px 8px; border-bottom: 1px solid #e2e8f0; font-weight:bold;">{r[0]}</td>
                    <td style="text-align:center; padding: 7px 8px; border-bottom: 1px solid #e2e8f0;">{r[1]}</td>
                    <td style="text-align:right; padding: 7px 8px; border-bottom: 1px solid #e2e8f0; font-weight:bold; color:#15803d;">{r[2]:.2f} Qtl</td>
                    <td style="text-align:right; padding: 7px 8px; border-bottom: 1px solid #e2e8f0; font-weight:bold;">₹{r[3]:,.2f}</td>
                </tr>"""

            adv_c_html = ""
            if adv_rows:
                adv_items_c = "".join([f"""<tr style="border-bottom: 1px dashed #cbd5e1;">
                    <td style="padding: 5px 8px;">{a[0]}</td>
                    <td style="padding: 5px 8px; font-style: italic;">{a[2] or 'नगद'}</td>
                    <td style="padding: 5px 8px; text-align: right; font-weight: bold; color: #dc2626;">- ₹{a[1]:,.2f}</td>
                </tr>""" for a in adv_rows])
                adv_c_html = f"""
                <div style="margin-top: 12px; border: 1px solid #fed7aa; background: #fffaf5; border-radius: 6px; padding: 10px;">
                    <strong style="color: #c2410c; font-size: 11px;">💰 एडवांस कटौती विवरण (केवल हिस्सा A से काटा गया):</strong>
                    <table style="width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 4px;">{adv_items_c}</table>
                </div>"""

            chilai_bill_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #fff; padding: 15px; color: #0f172a; }}
        .sheet {{ max-width: 800px; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 8px; padding: 25px; }}
        .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #0f172a; padding-bottom: 10px; margin-bottom: 15px; }}
        .meta-grid {{ display: flex; justify-content: space-between; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin-bottom: 15px; font-size: 13px; }}
        table.tbl {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12px; }}
        table.tbl th {{ background: #0f172a; color: #fff; padding: 8px; text-align: center; }}
        table.tbl tfoot th {{ background: #f1f5f9; color: #0f172a; border-top: 2px solid #0f172a; font-size: 13px; }}
        
        .expl-box {{ background: #fdfdfe; border: 2px solid #0284c7; border-radius: 8px; padding: 14px; margin: 15px 0; }}
        .split-grid {{ display: flex; gap: 12px; margin-top: 10px; }}
        .part-card {{ flex: 1; border-radius: 6px; padding: 12px; border: 2px solid; }}
        .part-card.a {{ border-color: #2563eb; background: #eff6ff; }}
        .part-card.b {{ border-color: #16a34a; background: #f0fdf4; }}
        .part-row {{ display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 4px; }}
        .part-net {{ border-top: 1px solid; margin-top: 6px; padding-top: 6px; display: flex; justify-content: space-between; font-size: 15px; font-weight: bold; }}

        .summary-card {{ background: #fffbeb; border: 2px solid #fde68a; border-radius: 6px; padding: 12px; margin-top: 12px; }}
        .sum-line {{ display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }}
        .sum-line.net {{ border-top: 2px dashed #f59e0b; padding-top: 6px; margin-top: 6px; font-size: 16px; font-weight: bold; color: #b45309; }}
        @media print {{ .no-print {{ display: none !important; }} }}
    </style>
</head>
<body>
    <div class="no-print" style="text-align: center; margin-bottom: 15px;">
        <button onclick="window.print()" style="background:#16a34a; color:#fff; font-size:13px; font-weight:bold; padding:9px 24px; border:none; border-radius:5px; cursor:pointer;">🖨️ छिलाईदार बिल प्रिंट करें (Print / PDF)</button>
    </div>
    <div class="sheet">
        <div class="header">
            <div>
                <h2 style="margin:0; color:#0f172a;">🌾 ALPHA FARMS</h2>
                <div style="font-size:12px; color:#64748b;">गन्ना छिलाई मजदूरी एवं 50-50 बंटवारा विवरण</div>
            </div>
            <div style="text-align:right;">
                <div style="font-weight:bold; color:#16a34a;">छिलाईदार लेबर बिल</div>
                <div style="font-size:11px; color:#64748b;">दिनांक: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}</div>
            </div>
        </div>
        <div class="meta-grid">
            <div>
                <div>छिलाईदार / लेबर टीम: <strong style="font-size:15px; color:#16a34a;">{sel_chilai}</strong></div>
                <div style="margin-top:4px;">कुल पर्चियाँ: <strong>{total_slips} पर्ची</strong></div>
            </div>
            <div style="text-align:right;">
                <div>कुल छिलाई वजन: <strong style="font-size:16px; color:#15803d;">{total_weight:,.2f} क्विंटल</strong></div>
            </div>
        </div>
        <table class="tbl">
            <thead>
                <tr>
                    <th style="width:40px;">क्र.</th>
                    <th>पर्ची नंबर</th>
                    <th>पर्ची दिनांक व समय</th>
                    <th style="text-align:right;">पर्ची वजन (Q)</th>
                    <th style="text-align:right;">छिलाई रकम (₹)</th>
                </tr>
            </thead>
            <tbody>{tbl_c_rows}</tbody>
            <tfoot>
                <tr>
                    <th colspan="3" style="text-align:right;">कुल योग (TOTAL SUMMARY):</th>
                    <th style="text-align:right; color:#15803d;">{total_weight:,.2f} Qtl</th>
                    <th style="text-align:right;">₹{total_chilai:,.2f}</th>
                </tr>
            </tfoot>
        </table>

        <!-- 50-50 Explanation -->
        <div class="expl-box">
            <div style="font-weight:bold; color:#0369a1; font-size:12px; margin-bottom:6px;">
                📋 50% - 50% मजदूरी बंटवारा एवं एडवांस समायोजन नियम:
            </div>
            <div style="font-size:11px; color:#475569; line-height:1.5;">
                • कुल छिलाई ₹{total_chilai:,.2f} को 2 बराबर हिस्सों (₹{half_gross:,.2f} प्रत्येक) में बांटा गया है।<br>
                • फ़ार्म द्वारा दिया गया एडवांस (₹{total_adv_c:,.2f}) <strong>केवल हिस्सा A</strong> से काटा गया है।<br>
                • <strong>हिस्सा B बिना किसी कटौती के पूरा रहेगा।</strong>
            </div>
            <div class="split-grid">
                <div class="part-card a">
                    <div style="font-weight:bold; color:#1d4ed8; font-size:13px; margin-bottom:4px;">👤 हिस्सा A (Part A)</div>
                    <div class="part-row"><span>50% मूल हिस्सा:</span> <strong>₹{half_gross:,.2f}</strong></div>
                    <div class="part-row" style="color:#dc2626;"><span>(-) कुल एडवांस:</span> <strong>- ₹{total_adv_c:,.2f}</strong></div>
                    <div class="part-net" style="color:#1d4ed8;"><span>देय रकम:</span> <span>₹{part_a_net:,.2f}</span></div>
                </div>
                <div class="part-card b">
                    <div style="font-weight:bold; color:#15803d; font-size:13px; margin-bottom:4px;">👤 हिस्सा B (Part B - पूर्ण)</div>
                    <div class="part-row"><span>50% मूल हिस्सा:</span> <strong>₹{half_gross:,.2f}</strong></div>
                    <div class="part-row" style="color:#16a34a;"><span>(-) एडवांस कटौती:</span> <strong>₹0.00</strong></div>
                    <div class="part-net" style="color:#15803d;"><span>देय रकम:</span> <span>₹{part_b_net:,.2f}</span></div>
                </div>
            </div>
        </div>

        <div class="summary-card">
            <div class="sum-line"><span>कुल सकल छिलाई मजदूरी:</span> <strong>₹{total_chilai:,.2f}</strong></div>
            <div class="sum-line" style="color:#dc2626;"><span>(-) कुल एडवांस:</span> <strong>- ₹{total_adv_c:,.2f}</strong></div>
            <div class="sum-line net"><span>फ़ार्म द्वारा कुल अंतिम शुद्ध देय:</span> <span>₹{net_payable:,.2f}</span></div>
        </div>
        {adv_c_html}
        <div style="display:flex; justify-content:space-between; margin-top:35px; border-top:1px solid #94a3b8; padding-top:8px; font-size:11px; color:#475569;">
            <div>हस्ताक्षर छिलाईदार / टीम ({sel_chilai})</div>
            <div>अधिकृत हस्ताक्षर (Alpha Farms)</div>
        </div>
    </div>
</body>
</html>"""
            components.html(chilai_bill_html, height=580, scrolling=True)

# ========================================================
# VIEW 5: ओवरऑल प्रोग्रेस सारांश व समग्र रिपोर्ट प्रिंट
# ========================================================
elif menu == "📈 ओवरऑल प्रोग्रेस सारांश":
    st.title("📈 Alpha Farms - ओवरऑल प्रोग्रेस एवं वित्तीय सारांश")
    
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*), COALESCE(SUM(weight), 0), COALESCE(SUM(gross_amount), 0),
               COALESCE(SUM(transport_charge), 0), COALESCE(SUM(chilai_charge), 0),
               COALESCE(SUM(net_in_hand), 0), COALESCE(SUM(amount_paid), 0),
               COALESCE(SUM(balance_due), 0)
        FROM parchis
    """)
    row = c.fetchone()
    
    c.execute("SELECT transporter, SUM(transport_charge) FROM parchis GROUP BY transporter ORDER BY SUM(transport_charge) DESC")
    t_rows = c.fetchall()
    
    c.execute("SELECT COALESCE(chilai_by, 'लेबर'), SUM(chilai_charge) FROM parchis GROUP BY chilai_by ORDER BY SUM(chilai_charge) DESC")
    ch_rows = c.fetchall()
    
    c.execute("""SELECT slip_no, COALESCE(date_time, date), person, variety, weight, gross_amount,
                     transporter, transport_charge, COALESCE(chilai_by, 'लेबर'), chilai_charge,
                     net_in_hand, payment_status, balance_due, COALESCE(generated_by, 'Admin')
                     FROM parchis ORDER BY id ASC""")
    all_slips = c.fetchall()
    conn.close()

    if row:
        cnt, wt, gross, trans, chilai, net, paid, due = row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("कुल पर्चियाँ", f"{cnt} पर्ची")
        c2.metric("कुल वजन", f"{wt:,.2f} Qtl")
        c3.metric("सकल गन्ना मूल्य", f"₹{gross:,.2f}")
        c4.metric("शुद्ध बचत (In-Hand)", f"₹{net:,.2f}")
        
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("ट्रांसपोर्ट खर्च", f"₹{trans:,.2f}")
        c6.metric("छिलाई मजदूरी", f"₹{chilai:,.2f}")
        c7.metric("प्राप्त भुगतान", f"₹{paid:,.2f}")
        c8.metric("शेष बकाया", f"₹{due:,.2f}")

    st.divider()
    with st.expander("🖨️ संपूर्ण सिस्टम रिपोर्ट प्रिंट करें (Audit Report)", expanded=False):
        rep_rows_html = "".join([f"""<tr>
            <td style='text-align:center; padding:5px;'>{r[0]}</td>
            <td style='text-align:center; padding:5px;'>{r[1]}</td>
            <td style='padding:5px;'>{r[2]}</td>
            <td style='text-align:center; padding:5px;'>{r[3]}</td>
            <td style='text-align:right; padding:5px;'>{r[4]:.2f}</td>
            <td style='text-align:right; padding:5px;'>₹{r[5]:,.2f}</td>
            <td style='padding:5px;'>{r[6]}</td>
            <td style='padding:5px;'>{r[8]}</td>
            <td style='text-align:right; padding:5px; font-weight:bold; color:#15803d;'>₹{r[10]:,.2f}</td>
            <td style='text-align:center; padding:5px;'>{r[11]}</td>
            <td style='text-align:right; padding:5px;'>₹{r[12]:,.2f}</td>
        </tr>""" for r in all_slips])

        full_rep_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 15px; font-size: 11px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 6px; }}
        th {{ background: #0f172a; color: #fff; }}
        @media print {{ .no-print {{ display: none !important; }} }}
    </style>
</head>
<body>
    <div class="no-print" style="text-align:center; margin-bottom: 10px;">
        <button onclick="window.print()" style="background:#0284c7; color:#fff; font-weight:bold; padding:8px 20px; border:none; border-radius:4px; cursor:pointer;">🖨️ रिपोर्ट प्रिंट करें (Print / PDF)</button>
    </div>
    <h2 style="text-align:center; margin:0;">🌾 ALPHA FARMS</h2>
    <p style="text-align:center; margin:2px 0 10px; color:#64748b;">गन्ना पर्ची एवं वित्तीय समग्र रिपोर्ट ({datetime.now().strftime('%d-%m-%Y %I:%M %p')})</p>
    <table>
        <thead>
            <tr>
                <th>पर्ची नं.</th>
                <th>दिनांक/समय</th>
                <th>किसान</th>
                <th>प्रजाति</th>
                <th>वजन (Q)</th>
                <th>सकल ₹</th>
                <th>ट्रांसपोर्टर</th>
                <th>छिलाईदार</th>
                <th>शुद्ध बचत ₹</th>
                <th>स्थिति</th>
                <th>बकाया ₹</th>
            </tr>
        </thead>
        <tbody>{rep_rows_html}</tbody>
    </table>
</body>
</html>"""
        components.html(full_rep_html, height=500, scrolling=True)

# ========================================================
# VIEW 6: मास्टर डेटा, दरें & यूजर मैनेजमेंट
# ========================================================
elif menu == "⚙️ मास्टर डेटा, दरें & यूजर":
    st.title("⚙️ सिस्टम सेटिंग्स, मास्टर डेटा एवं यूजर मैनेजमेंट")
    
    tab_m, tab_r, tab_u = st.tabs(["👥 किसान, ट्रांसपोर्टर & लेबर सूची", "⚙️ दर सेटिंग्स", "👤 यूजर मैनेजमेंट"])
    
    with tab_m:
        st.subheader("मास्टर डेटा प्रबंधन")
        cm1, cm2, cm3 = st.columns(3)
        with cm1:
            st.markdown("**🌾 किसान सूची**")
            f_new = st.text_input("नया किसान जोड़ें:")
            if st.button("➕ किसान जोड़ें"):
                add_to_master("master_farmers", f_new)
                st.rerun()
            for name in get_master_list("master_farmers"):
                col_n, col_d = st.columns([3, 1])
                col_n.write(name)
                if col_d.button("❌", key=f"df_{name}"):
                    delete_from_master("master_farmers", name)
                    st.rerun()
        with cm2:
            st.markdown("**🚛 ट्रांसपोर्टर सूची**")
            t_new = st.text_input("नया ट्रांसपोर्टर जोड़ें:")
            if st.button("➕ ट्रांसपोर्टर जोड़ें"):
                add_to_master("master_transporters", t_new)
                st.rerun()
            for name in get_master_list("master_transporters"):
                col_n, col_d = st.columns([3, 1])
                col_n.write(name)
                if col_d.button("❌", key=f"dt_{name}"):
                    delete_from_master("master_transporters", name)
                    st.rerun()
        with cm3:
            st.markdown("**🌾 छिलाईदार सूची**")
            ch_new = st.text_input("नया छिलाईदार जोड़ें:")
            if st.button("➕ छिलाईदार जोड़ें"):
                add_to_master("master_chilai", ch_new)
                st.rerun()
            for name in get_master_list("master_chilai"):
                col_n, col_d = st.columns([3, 1])
                col_n.write(name)
                if col_d.button("❌", key=f"dc_{name}"):
                    delete_from_master("master_chilai", name)
                    st.rerun()

    with tab_r:
        st.subheader("सरकारी गन्ना व डिफ़ॉल्ट कटौती दरें")
        with st.form("rate_form"):
            e_rate = st.number_input("शीघ्र गन्ना दर (₹/Qtl)", value=float(settings.get("early_rate", 389.38)), step=0.5)
            n_rate = st.number_input("सामान्य गन्ना दर (₹/Qtl)", value=float(settings.get("normal_rate", 379.38)), step=0.5)
            tr_rate = st.number_input("डिफ़ॉल्ट ट्रांसपोर्ट भाड़ा (₹/Slip)", value=float(settings.get("transport_rate", 420.00)), step=10.0)
            ch_rate = st.number_input("डिफ़ॉल्ट छिलाई दर (₹/Qtl)", value=float(settings.get("chilai_rate", 50.00)), step=1.0)
            if st.form_submit_button("💾 दरें सुरक्षित करें"):
                conn = get_db()
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('early_rate', ?)", (e_rate,))
                c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('normal_rate', ?)", (n_rate,))
                c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('transport_rate', ?)", (tr_rate,))
                c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('chilai_rate', ?)", (ch_rate,))
                conn.commit()
                conn.close()
                st.success("दर सेटिंग्स अपडेट हो गईं!")
                st.rerun()

    with tab_u:
        st.subheader("लॉगिन यूजर एवं पासवर्ड प्रबंधन")
        with st.form("add_user_form"):
            cu1, cu2, cu3 = st.columns(3)
            with cu1:
                new_u = st.text_input("User ID")
            with cu2:
                new_p = st.text_input("Password", type="password")
            with cu3:
                new_fn = st.text_input("पूरा नाम")
            if st.form_submit_button("➕ नया यूजर जोड़ें"):
                if new_u and new_p and new_fn:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO users (username, password, full_name, role) VALUES (?, ?, ?, 'Operator')", (new_u.strip(), new_p.strip(), new_fn.strip()))
                    conn.commit()
                    conn.close()
                    st.success(f"यूजर '{new_u}' सुरक्षित हो गया!")
                    st.rerun()
                else:
                    st.warning("कृपया सभी फ़ील्ड्स भरें!")

        conn = get_db()
        df_u = pd.read_sql_query("SELECT username AS 'User ID', full_name AS 'नाम', role AS 'रोल' FROM users", conn)
        conn.close()
        st.dataframe(df_u, use_container_width=True, hide_index=True)
