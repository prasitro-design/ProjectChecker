import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import time
import base64
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import re

# ==========================================
# 1. ตั้งค่าหน้าเว็บ (Page Config) ต้องอยู่บรรทัดแรกสุด
# ==========================================
st.set_page_config(
    page_title="ระบบตรวจแบบฟอร์มโครงการพัฒนานิสิต คณะศึกษาศาสตร์ มก.", 
    page_icon="📄", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. ตกแต่งหน้าตาเว็บด้วย CSS และตั้งค่าพื้นหลัง
# ==========================================
def set_background(image_file):
    try:
        with open(image_file, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: 
                    linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), 
                    url(data:image/jpeg;base64,{encoded_string});
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            .block-container {{
                background-color: rgba(255, 255, 255, 0.95); 
                border-radius: 20px;
                padding: 3rem 2rem;
                margin-top: 2rem;
                margin-bottom: 2rem;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            }}
            @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
            html, body, [class*="css"] {{
                font-family: 'Kanit', sans-serif !important;
            }}
            .header-box {{
                background-color: #f4fbf7;
                border: 2px solid #bce1ce;
                border-radius: 20px;
                padding: 35px 20px 40px 20px;
                margin-bottom: 30px;
                box-shadow: 0 8px 20px rgba(0, 102, 51, 0.08);
                text-align: center;
            }}
            h1 {{
                background: -webkit-linear-gradient(45deg, #006633, #96c93d);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 600;
                text-align: center;
                margin: 0; 
                padding: 0;
                line-height: 1.4;
            }}
            .subtitle-text {{
                text-align: center;
                font-size: 16px;
                color: #006633;
                background-color: #ffffff;
                padding: 8px 25px;
                border-radius: 30px;
                display: inline-block;
                margin-top: 18px;
                border: 1px solid #e0f2e9;
                box-shadow: 0 4px 10px rgba(0, 102, 51, 0.05);
                font-weight: 400;
            }}
            h2, h3 {{
                color: #006633 !important;
                font-weight: 500;
            }}
            .stButton>button {{
                background: linear-gradient(135deg, #006633, #00b09b);
                color: white;
                font-weight: 500;
                font-size: 16px;
                border-radius: 12px;
                border: none;
                padding: 12px 24px;
                box-shadow: 0 4px 15px rgba(0, 102, 51, 0.3);
                transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
                width: 100%;
            }}
            .stButton>button:hover {{
                transform: translateY(-4px) scale(1.02);
                box-shadow: 0 8px 25px rgba(0, 102, 51, 0.45);
                color: white;
            }}
            [data-testid="stFileUploadDropzone"] {{
                background-color: #f4fbf7;
                border: 2px dashed #00b09b;
                border-radius: 15px;
                padding: 20px;
                transition: all 0.3s ease;
            }}
            [data-testid="stFileUploadDropzone"]:hover {{
                background-color: #e8f7f0;
                border-color: #006633;
            }}
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            header {{visibility: hidden;}}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        pass # ป้องกัน Error กรณีหารูปไม่เจอตอน Test ในเครื่อง

set_background('background.jpg') 

# ==========================================
# 3. ตั้งค่า API Key ของ Gemini
# ==========================================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.5-flash')

# ==========================================
# 4. ฟังก์ชันเบื้องหลัง (PDF, AI, Google Sheets)
# ==========================================
def read_pdf(file):
    text = ""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page_num, page in enumerate(doc):
        text += f"\n\n[--- เริ่มหน้าที่ {page_num + 1} ---]\n"
        text += page.get_text() + "\n"
    return text

def analyze_document(text):
    if not text.strip():
        return "❌ ระบบไม่พบข้อความในไฟล์ PDF นี้ครับ สาเหตุอาจเกิดจากไฟล์เป็นรูปภาพ(สแกน) หรือมีการเข้ารหัสฟอนต์ กรุณาลองใช้ไฟล์ที่เซฟมาจาก Word โดยตรงครับ"

    prompt = f"""
    คุณคือเจ้าหน้าที่ฝ่ายพัฒนานิสิตที่มีความชำนาญการตรวจสอบแบบเสนอโครงการที่ "เข้มงวดมาก (Strict Evaluator)" ของคณะศึกษาศาสตร์ มหาวิทยาลัยเกษตรศาสตร์
    หน้าที่ของคุณคือการตรวจเอกสารตามกฎเกณฑ์ด้านล่างนี้อย่างเคร่งครัด ห้ามคิดไปเอง และห้ามอนุโลมเด็ดขาด
⚠️ กฎการพิมพ์รายงาน (สำคัญมาก):
    - ให้ขึ้นต้นรายงานบรรทัดแรกสุดด้วยข้อความว่า "**ถึง ผู้รับผิดชอบโครงการ**" เสมอ
    - การเกริ่นนำและเนื้อหาทั้งหมด **ต้องใช้ภาษาทางการระดับราชการเท่านั้น** 
    - ห้ามใช้คำสรรพนามบุรุษที่ 2 แบบไม่เป็นทางการเด็ดขาด เช่น คำว่า "เธอ", "พวกเธอ", หรือ "พวกคุณ" (หากจำเป็นต้องกล่าวถึง ให้ใช้คำว่า "นิสิต", "คณะผู้จัดทำ", หรือหลีกเลี่ยงการใช้สรรพนามไปเลย)
    - จัดเรียงลำดับการรายงานผลตามนี้:

    ส่วนที่ 1: การตรวจความครบถ้วนของรูปแบบฟอร์ม (Form Structure Validation)
    ตรวจสอบว่าผู้เสนอโครงการได้เขียนหัวข้อครบถ้วนตามแบบฟอร์มมาตรฐานทั้ง 14 ข้อหรือไม่
    
    **🚨 กฎเหล็กสำหรับการตรวจส่วนที่ 1 (Strict Rules):**
    - หากหัวข้อใดมีเงื่อนไขระบุไว้ในวงเล็บ คุณต้องหา "เนื้อหา" หรือ "คำสำคัญ" เหล่านั้นให้เจอครบทุกข้อ!
    - หากขาดรายละเอียดในวงเล็บไปแม้แต่อย่างเดียว ห้ามประเมินเป็น 🟢 เด็ดขาด ให้ปรับเป็น 🟡 ทันที และระบุสิ่งที่ขาดลงไป
    - นำเสนอผลลัพธ์ในรูปแบบตาราง 3 คอลัมน์ ดังนี้:
      - คอลัมน์ 1: "หัวข้อ" (ระบุชื่อหัวข้อทั้ง 14 ข้อ)
      - คอลัมน์ 2: "ความครบถ้วน" (🟢 = สมบูรณ์และมีครบทุกเงื่อนไขย่อย, 🟡 = มีหัวข้อแต่ขาดรายละเอียดบางส่วน, 🔴 = ไม่พบหัวข้อนี้เลย)
      - คอลัมน์ 3: "สิ่งที่ต้องแก้ไข" (หากให้ 🟡 ต้องระบุให้ชัดเจนว่าขาดอะไรไป เช่น "ขาดการระบุสมรรถนะ 8 ด้าน")

    รายการหัวข้อทั้ง 14 ข้อที่ต้องตรวจอย่างละเอียด:
    1. ข้อมูลทั่วไป (บังคับ: ต้องมีครบทั้ง ชื่อโครงการ, หน่วยงาน, ที่ปรึกษา, ประธาน, วันที่, สถานที่, กรรมการตรวจรับ)
    2. หลักการและเหตุผล
    3. วัตถุประสงค์ของโครงการ
    4. ระยะเวลาในการปฏิบัติงาน (บังคับ: ต้องมีครบทั้ง ขั้นเตรียม, ดำเนินการ, สรุป)
    5. สถานที่ดำเนินโครงการ
    6. รูปแบบในการดำเนินการ/ลักษณะกิจกรรม
    7. วิธีการดำเนินกิจกรรมและแผนการปฏิบัติงาน (บังคับ: ต้องมีรายละเอียดกิจกรรม และ ระบุผู้รับผิดชอบ)
    8. งบประมาณ (บังคับ: ต้องมีการแจกแจงรายรับ และ รายจ่ายที่ชัดเจน)
    9. ผลที่คาดว่าจะได้รับ
    10. การติดตามและประเมินผล
    11. ตัวชี้วัดความสำเร็จ (บังคับ: ต้องมีครบทั้ง ตัวชี้วัด, วิธีประเมิน, เครื่องมือ)
    12. การประเมินและบริหารความเสี่ยง
    13. ความสอดคล้องกับการพัฒนานิสิต (บังคับ: ต้องมีการระบุครบทั้ง 3 อย่าง คือ 1.อัตลักษณ์ มก., 2.SDGs และ 3.สมรรถนะ 8 ด้าน หากขาดข้อใดข้อหนึ่งไป ให้ประเมินเป็น 🟡 ทันที)
    14. กำหนดการโครงการ (ตารางเวลาอย่างละเอียด)

    ส่วนที่ 2: การตรวจสอบความถูกต้องของภาษาไทย
    ตรวจหาคำผิด การสะกดผิด หรือการเว้นวรรคที่ไม่เหมาะสมกับเอกสารราชการ พร้อมเสนอคำที่ถูกต้อง

    ส่วนที่ 3: การวิเคราะห์ความสมเหตุสมผลของเนื้อหา (Logical Check)
    - วัตถุประสงค์ สอดคล้องกับ "ผลที่คาดว่าจะได้รับ" และ "ตัวชี้วัดความสำเร็จ" หรือไม่
    - งบประมาณที่ตั้งไว้ สมเหตุสมผลกับ "รูปแบบลักษณะกิจกรรม" หรือไม่
    - แผนการปฏิบัติงานและกำหนดการ สอดคล้องกันและเป็นไปได้จริงหรือไม่

    🌟 ส่วนที่ 4: การประเมินคะแนนภาพรวม (Overall Score) - แสดงส่วนนี้ไว้ท้ายสุดของรายงาน!
    - ให้คะแนนภาพรวมของเอกสารนี้จากคะแนนเต็ม 100 คะแนน โดยแบ่งเกณฑ์ดังนี้:
      1. ความครบถ้วนของโครงสร้างแบบฟอร์ม (50 คะแนน)
      2. ความถูกต้องของภาษาและการสะกดคำ (20 คะแนน)
      3. ความสมเหตุสมผลของเนื้อหา (30 คะแนน)
    - กฎเหล็กการแสดงผล: ให้คุณแสดงคะแนนภาพรวมไว้ล่างสุดของเอกสารให้โดดเด่น เช่น "--- \n ## 🏆 คะแนนภาพรวมโครงการ: [คะแนนที่ได้] / 100 คะแนน" 
    - ตามด้วยคำวิจารณ์สั้นๆ (Feedback) ว่าทำไมถึงได้คะแนนเท่านี้

    เนื้อหาโครงการที่นิสิตส่งมา:
    {text}
    """
    response = model.generate_content(prompt)
    return response.text

def log_to_google_sheets(filename, result_text):
    try:
        # 1. เชื่อมต่อบัญชี Google Service Account
        creds_dict = json.loads(st.secrets["GCP_CREDENTIALS"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # 2. ค้นหาไฟล์ Google Sheets
        sheet = client.open("ประวัติการตรวจโครงการ").sheet1
        
        # 3. เตรียมข้อมูล
        tz = pytz.timezone('Asia/Bangkok')
        current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        
        # ดึงตัวเลขคะแนนด้วย Regex (หาตัวเลขที่อยู่หลังคำว่า "คะแนนภาพรวมโครงการ:")
        score = "N/A"
        match = re.search(r'คะแนนภาพรวมโครงการ:\s*\*?\*?(\d+)', result_text)
        if match:
            score = match.group(1)
            
        # 4. บันทึกลงชีต
        row_data = [current_time, filename, f"{score}/100"]
        sheet.append_row(row_data)
        
    except Exception as e:
        # หากบันทึกไม่สำเร็จ จะปล่อยผ่านเงียบๆ ไม่ให้รบกวนหน้าเว็บผู้ใช้
        print(f"Error logging to Google Sheets: {e}")

# ==========================================
# 5. การจัด Layout แถบด้านข้าง (Sidebar)
# ==========================================
with st.sidebar:
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        try:
            st.image("logo.png", use_container_width=True) 
        except FileNotFoundError:
            pass
            
    st.markdown("### 📌 คำแนะนำการใช้งาน")
    st.info("""
    **ขั้นตอนการตรวจเอกสาร:**
    1. บันทึกไฟล์แบบเสนอโครงการของท่านเป็นนามสกุล **.pdf** 
       *(ต้องเป็นไฟล์ที่แปลงจาก MS Word เท่านั้น!)*
    2. อัปโหลดไฟล์จากข้อ 1
    3. ตรวจสอบว่าระบบอ่านเนื้อหาได้ครบถ้วน
    4. กดปุ่ม **เริ่มให้ AI ตรวจสอบและให้คะแนน**
    """)
    st.markdown("---")
    st.caption("👨‍💻 พัฒนาโดย: นายประสิทธิ์ รอดพันธุ์\n\nนักวิชาการศึกษาชำนาญการ")

# ==========================================
# 6. ส่วนแสดงผลเนื้อหาหลัก
# ==========================================
st.markdown("""
<div class="header-box">
    <h1>📄 ระบบตรวจแบบฟอร์มเสนอโครงการพัฒนานิสิต<br>คณะศึกษาศาสตร์ มหาวิทยาลัยเกษตรศาสตร์ (AI)</h1>
    <div class="subtitle-text">
        ✨ ระบบจะช่วยตรวจสอบโครงสร้าง การสะกดคำ และความสมเหตุสมผลของโครงการในเบื้องต้น ก่อนนำเสนอคณะกรรมการฝ่ายพัฒนานิสิต
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.markdown("### 📁 1. อัปโหลดเอกสาร")
    uploaded_file = st.file_uploader("ลากไฟล์ PDF มาวางที่นี่", type="pdf", label_visibility="collapsed")
    
    if uploaded_file is not None:
        st.toast("✅ อัปโหลดไฟล์สำเร็จ! พร้อมให้ AI ตรวจสอบแล้ว", icon="🎉")
        st.success("✅ อัปโหลดไฟล์สำเร็จ!")
        document_text = read_pdf(uploaded_file)
        
        with st.expander("🔍 ดูข้อความที่ระบบดึงออกมาได้ (คลิกเพื่อขยาย)"):
            if not document_text.strip():
                st.error("⚠️ ไม่พบข้อความในเอกสาร (อาจเป็นไฟล์สแกน)")
            else:
                st.write(document_text)

with col2:
    st.markdown("### 🤖 2. ผลการวิเคราะห์จาก AI")
    
    if uploaded_file is not None and document_text.strip():
        if st.button("🚀 เริ่มให้ AI ตรวจสอบเอกสารโครงการ"):
            
            result = "" 
            
            with st.status("🤖 AI กำลังอ่านและตรวจสอบเอกสารโครงการ ระบบใช้เวลาประมาณ 1 นาที กรุณารอสักครู่...", expanded=True) as status:
                st.write("⏳ กำลังตรวจสอบโครงสร้างตามแบบฟอร์ม...")
                time.sleep(1.5)
                st.write("🔍 กำลังประเมินความสมเหตุสมผลและตรวจสอบการสะกดคำ...")
                time.sleep(1)
                st.write("💯 กำลังคำนวณคะแนนภาพรวม...")
                
                try:
                    result = analyze_document(document_text)
                    
                    # --- เพิ่มส่วนการทำงานเบื้องหลัง: บันทึกลง Google Sheets ---
                    st.write("📊 กำลังบันทึกประวัติการตรวจเข้าระบบ...")
                    log_to_google_sheets(uploaded_file.name, result)
                    # --------------------------------------------------
                    
                    status.update(label="✅ AI ประเมินผลเสร็จสิ้น!", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="❌ เกิดข้อผิดพลาด!", state="error")
                    st.error(f"เกิดข้อผิดพลาด: {e}")
            
            if result:
                st.balloons()
                st.toast("🎉 AI ให้คะแนนเอกสารเรียบร้อยแล้ว!", icon="✨")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📋 สรุปผลการตรวจสอบ")
                st.markdown(result)
                
    else:
        st.info("👈 กรุณาอัปโหลดเอกสารในช่องด้านซ้ายมือ เพื่อเปิดใช้งานระบบ AI")
