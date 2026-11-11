# -*- coding: utf-8 -*-
"""
🌾 Alpha Farms - वेब ऐप (Streamlit Web Application)
100% Free Hosting Ready | Mobile & Desktop Responsive | SQLite Integration
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import io

DB_NAME = "ganna_parchi_data.db"

# --- PAGE CONFIG ---
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
        
    # Check default masters
    c.execute("SELECT COUNT(*) FROM master_farmers")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT OR IGNORE INTO master_farmers (name, village) VALUES (?, ?)", [("Self", "गाँव"), ("रामचंद्र", ""), ("सुरेश कुमार", "")])
    c.execute("SELECT COUNT(*) FROM master_transporters")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT OR IGNORE INTO master_transporters (name, default_fare) VALUES (?, ?)", [("ARPIT", 420.0), ("ram chandra", 420.0), ("अन्य", 420.0)])
    c.execute("SELECT COUNT(*) FROM master_chilai")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT OR IGNORE INTO master_chilai (name) VALUES (?)", [("लेबर टीम 1",), ("लेबर टीम 2",), ("स्वयं",)])

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

# --- INITIALIZATION ---
init_db()

# Session State for Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; color: #1E293B;'>🌾 ALPHA FARMS</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>गन्ना पर्ची एवं कृषि प्रबंधन प्रणाली (वेब पोर्टल)</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("🔒 सुरक्षित लॉगिन")
            user_input = st.text_input("यूजर आईडी (User ID)", value="admin")
            pass_input = st.text_input("पासवर्ड (Password)", type="password", value="1234")
            submitted = st.form_submit_button("लॉगिन करें ➔", use_container_width=True)
            
            if submitted:
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT full_name, role FROM users WHERE username=? AND password=?", (user_input.strip(), pass_input.strip()))
                row = c.fetchone()
                conn.close()
                if row:
                    st.session_state.authenticated = True
                    st.session_state.user_info = {"id": user_input, "name": row[0], "role": row[1]}
                    st.success("लॉगिन सफल!")
                    st.rerun()
                else:
                    st.error("गलत यूजर आईडी या पासवर्ड!")
    st.stop()

# --- AUTHENTICATED USER INTERFACE ---
settings = get_settings()

# Sidebar: Navigation & Settings
with st.sidebar:
    st.markdown(f"### 🌾 Alpha Farms")
    st.caption(f"👤 **{st.session_state.user_info['name']}** ({st.session_state.user_info['id']})")
    
    menu = st.radio(
        "नेविगेशन मेन्यू",
        ["📝 नई पर्ची दर्ज करें", "📋 पर्ची रजिस्टर व खोज", "🚛 ट्रांसपोर्टर हिसाब", "🌾 छिलाईदार (1/2 हिसाब)", "📈 ओवरऑल प्रोग्रेस सारांश", "⚙️ मास्टर सेटिंग्स & यूजर"]
    )
    
    st.divider()
    if st.button("🔒 लॉग आउट (Logout)", use_container_width=True, type="secondary"):
        st.session_state.authenticated = False
        st.session_state.user_info = {}
        st.rerun()

# --- VIEW 1: नई पर्ची दर्ज करें (SLIP ENTRY FORM) ---
if menu == "📝 नई पर्ची दर्ज करें":
    st.title("📝 गन्ना पर्ची एंट्री फॉर्म")
    st.caption("त्वरित रजिस्ट्रेशन या पूर्ण विवरण के साथ पर्ची जारी करें।")
    
    farmers_list = get_master_list("master_farmers")
    trans_list = get_master_list("master_transporters")
    chilai_list = get_master_list("master_chilai")
    
    # Quick register banner
    with st.expander("⚡ केवल पर्ची नंबर से त्वरित रजिस्ट्रेशन (Quick Register)", expanded=False):
        with st.form("quick_slip_form"):
            q_slip = st.text_input("पर्ची / रसीद क्र. * (Quick Slip No)")
            q_date = st.text_input("दिनांक व समय", value=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"), disabled=True)
            col_qa, col_qb = st.columns(2)
            with col_qa:
                q_farmer = st.selectbox("किसान / खातादार", farmers_list if farmers_list else ["Self"], key="qf")
            with col_qb:
                q_trans = st.selectbox("ट्रांसपोर्टर", trans_list if trans_list else ["ARPIT"], key="qt")
            q_submit = st.form_submit_button("🚀 तुरंत रजिस्टर करें", type="primary")
            if q_submit:
                if not q_slip.strip():
                    st.warning("कृपया पर्ची नंबर अवश्य भरें!")
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
                        st.success(f"⚡ पर्ची नं. {q_slip} पंजीकृत हो गई! बाद में वजन आने पर अपडेट कर सकते हैं।")
                    except sqlite3.IntegrityError:
                        st.error(f"पर्ची नंबर {q_slip} पहले से मौजूद है!")
                    finally:
                        conn.close()

    # Full Entry Form
    with st.form("full_slip_form"):
        st.subheader("पूर्ण पर्ची विवरण दर्ज करें")
        col1, col2, col3 = st.columns(3)
        with col1:
            f_slip = st.text_input("पर्ची / रसीद क्र. *")
            f_date = st.text_input("दिनांक व समय (Auto)", value=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"), disabled=True)
            f_farmer = st.selectbox("किसान / खातादार (चुनें)", farmers_list if farmers_list else ["Self"])
            f_variety = st.selectbox("गन्ना प्रजाति", ["शीघ्र", "सामान्य"])
        with col2:
            f_weight = st.number_input("शुद्ध वजन (क्विंटल) *", min_value=0.0, value=0.0, step=0.1, format="%.2f")
            f_trans = st.selectbox("ट्रांसपोर्टर (चुनें)", trans_list if trans_list else ["ARPIT"])
            f_trans_charge = st.number_input("ट्रांसपोर्ट भाड़ा (₹)", value=float(settings.get("transport_rate", 420.0)), step=10.0)
            f_chilai_by = st.selectbox("छिलाईदार (चुनें)", chilai_list if chilai_list else ["लेबर टीम 1"])
        with col3:
            f_chilai_rate = st.number_input("छिलाई दर (₹/Qtl)", value=float(settings.get("chilai_rate", 50.0)), step=1.0)
            f_status = st.selectbox("पेमेंट स्थिति", ["Unpaid", "Paid", "Partially Paid"])
            f_paid = st.number_input("प्राप्त भुगतान (₹)", value=0.0, step=50.0)
            f_gen_by = st.text_input("Generated By", value=st.session_state.user_info['name'], disabled=True)
            
        full_submit = st.form_submit_button("💾 पर्ची सुरक्षित करें", type="primary", use_container_width=True)
        if full_submit:
            if not f_slip.strip() or f_weight <= 0:
                st.warning("कृपया पर्ची नंबर और सही वजन अवश्य भरें!")
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
                    st.success(f"✅ पर्ची नं. {f_slip} सफलतापूर्वक सुरक्षित हो गई! (सकल: ₹{gross:,.2f} | शुद्ध: ₹{net:,.2f})")
                except sqlite3.IntegrityError:
                    st.error(f"पर्ची नंबर {f_slip} पहले से मौजूद है!")
                finally:
                    conn.close()

# --- VIEW 2: पर्ची रजिस्टर व खोज (TABLE VIEW & EDIT) ---
elif menu == "📋 पर्ची रजिस्टर व खोज":
    st.title("📋 पर्ची रजिस्टर एवं रिकॉर्ड")
    
    conn = get_db()
    df = pd.read_sql_query("""
        SELECT id, slip_no AS 'पर्ची नं.', COALESCE(date_time, date) AS 'दिनांक व समय', person AS 'किसान',
               variety AS 'प्रजाति', weight AS 'वजन (Q)', gross_amount AS 'सकल ₹', transporter AS 'ट्रांसपोर्टर',
               transport_charge AS 'भाड़ा ₹', chilai_by AS 'छिलाईदार', chilai_charge AS 'छिलाई ₹',
               net_in_hand AS 'शुद्ध ₹', payment_status AS 'स्थिति', balance_due AS 'बकाया ₹', generated_by AS 'Gen By'
        FROM parchis ORDER BY id DESC
    """, conn)
    conn.close()
    
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search = st.text_input("🔍 पर्ची नंबर / किसान / ट्रांसपोर्टर से खोजें:")
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
                file_name=f"Alpha_Farms_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
    if search.strip() and not df.empty:
        q = search.strip().lower()
        df = df[df.apply(lambda r: q in str(r['पर्ची नं.']).lower() or q in str(r['किसान']).lower() or q in str(r['ट्रांसपोर्टर']).lower(), axis=1)]
        
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- VIEW 3: ट्रांसपोर्टर हिसाब (TRANSPORTER LEDGER & BILL) ---
elif menu == "🚛 ट्रांसपोर्टर हिसाब":
    st.title("🚛 ट्रांसपोर्टर हिसाब एवं बिल प्रिंट")
    
    t_list = get_master_list("master_transporters")
    if not t_list:
        st.info("कृपया पहले मास्टर सेटिंग्स में ट्रांसपोर्टर जोड़ें।")
    else:
        col_t1, col_t2 = st.columns([1, 2])
        with col_t1:
            sel_trans = st.selectbox("ट्रांसपोर्टर चुनें:", t_list)
            
            # Advance entry for transporter
            with st.expander("➕ ट्रांसपोर्टर को एडवांस दर्ज करें", expanded=False):
                with st.form("adv_trans_form"):
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
            m2.metric("कुल भाड़ा", f"₹{total_fare:,.2f}")
            m3.metric("कुल एडवांस", f"₹{total_adv:,.2f}", delta=f"-₹{total_adv:,.2f}", delta_color="inverse")
            st.metric("अंतिम शुद्ध देय शेष भाड़ा (Net Payable)", f"₹{net_payable:,.2f}")
            
            if rows:
                df_t = pd.DataFrame(rows, columns=["पर्ची नं.", "दिनांक/समय", "किसान", "वजन (Q)", "भाड़ा (₹)"])
                st.dataframe(df_t[["पर्ची नं.", "दिनांक/समय", "किसान", "भाड़ा (₹)"]], use_container_width=True, hide_index=True)

# --- VIEW 4: छिलाईदार (1/2 हिसाब) (CHILAI 50-50 SPLIT) ---
elif menu == "🌾 छिलाईदार (1/2 हिसाब)":
    st.title("🌾 छिलाईदार मजदूरी एवं 50-50 बंटवारा विवरण")
    
    ch_list = get_master_list("master_chilai")
    if not ch_list:
        st.info("कृपया पहले मास्टर सेटिंग्स में छिलाईदार जोड़ें।")
    else:
        col_c1, col_c2 = st.columns([1, 2])
        with col_c1:
            sel_chilai = st.selectbox("छिलाईदार / लेबर टीम चुनें:", ch_list)
            
            with st.expander("➕ छिलाईदार को एडवांस दर्ज करें", expanded=False):
                with st.form("adv_chilai_form"):
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
            k1.metric("कुल पर्चियाँ", f"{total_slips}")
            k2.metric("कुल छिला वजन", f"{total_weight:,.2f} Qtl")
            k3.metric("कुल सकल मजदूरी", f"₹{total_chilai:,.2f}")
            
            st.divider()
            st.markdown("#### 👥 50% - 50% बंटवारा एवं एडवांस समायोजन नियम")
            st.caption("नियम: एडवांस केवल हिस्सा A से कटेगा, हिस्सा B बिना किसी कटौती के पूरा रहेगा।")
            
            col_pa, col_pb = st.columns(2)
            with col_pa:
                st.info(f"""
                **👤 हिस्सा A (Part A - एडवांस समायोजित)**
                * 50% मूल हिस्सा: ₹{half_gross:,.2f}
                * (-) एडवांस कटौती: - ₹{total_adv_c:,.2f}
                * **शुद्ध देय राशि: ₹{part_a_net:,.2f}**
                """)
            with col_pb:
                st.success(f"""
                **👤 हिस्सा B (Part B - पूर्ण भुगतान)**
                * 50% मूल हिस्सा: ₹{half_gross:,.2f}
                * (-) एडवांस कटौती: ₹0.00 (शून्य)
                * **शुद्ध देय राशि: ₹{part_b_net:,.2f}**
                """)
                
            st.metric("फ़ार्म द्वारा कुल अंतिम शुद्ध नकद देय", f"₹{net_payable:,.2f}")
            
            if rows:
                df_c = pd.DataFrame(rows, columns=["पर्ची नं.", "दिनांक/समय", "वजन (Q)", "छिलाई (₹)", "किसान"])
                st.dataframe(df_c[["पर्ची नं.", "दिनांक/समय", "वजन (Q)", "छिलाई (₹)"]], use_container_width=True, hide_index=True)

# --- VIEW 5: ओवरऑल प्रोग्रेस सारांश (PROGRESS DASHBOARD) ---
elif menu == "📈 ओवरऑल प्रोग्रेस सारांश":
    st.title("📈 Alpha Farms - ओवरऑल प्रोग्रेस सारांश")
    
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

# --- VIEW 6: मास्टर सेटिंग्स & यूजर (SETTINGS & MASTER DATA) ---
elif menu == "⚙️ मास्टर सेटिंग्स & यूजर":
    st.title("⚙️ सिस्टम सेटिंग्स, मास्टर डेटा एवं यूजर मैनेजमेंट")
    
    tab_m, tab_r, tab_u = st.tabs(["👥 किसान / ट्रांसपोर्टर सूची", "⚙️ दर सेटिंग्स", "👤 यूजर मैनेजमेंट"])
    
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
