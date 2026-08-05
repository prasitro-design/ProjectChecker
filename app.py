import pandas as pd
import math
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
import os  # เพิ่มเข้ามาเพื่อใช้เช็คไฟล์ template.docx
import streamlit.components.v1 as components

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
# 🎨 ตั้งค่า CSS เพื่อลดช่องว่างด้านบนของเว็บ
# ==========================================
st.markdown("""
    <style>
        /* ลดช่องว่างด้านบนของพื้นที่แสดงผลหลัก */
        .block-container {
            padding-top: 0rem !important; 
            padding-bottom: 0rem !important;
        }
        /* ซ่อนเมนู Header ด้านบนสุด (พวกปุ่ม Deploy, Menu) ถ้าต้องการให้ดูคลีนขึ้น */
        header {
            visibility: hidden;
        }
    </style>
""", unsafe_allow_html=True)
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

            /* ==========================================
               ✨ KEYFRAME ANIMATIONS
               ========================================== */
            
            @keyframes fadeInUpSmooth {{
                0% {{
                    opacity: 0;
                    transform: translateY(22px);
                }}
                100% {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}

            @keyframes shimmerEffect {{
                0% {{ background-position: -200% center; }}
                100% {{ background-position: 200% center; }}
            }}

            @keyframes glowPulse {{
                0%, 100% {{ filter: drop-shadow(0 0 2px rgba(0, 102, 51, 0.2)); }}
                50% {{ filter: drop-shadow(0 0 12px rgba(150, 201, 61, 0.8)); }}
            }}

            @keyframes alertPulse {{
                0%, 100% {{
                    box-shadow: 0 4px 15px rgba(255, 152, 0, 0.2);
                    transform: scale(1);
                }}
                50% {{
                    box-shadow: 0 8px 25px rgba(255, 152, 0, 0.4);
                    transform: scale(1.008);
                }}
            }}

            /* ==========================================
               📌 HEADER BOX
               ========================================== */
            .header-box {{
                background-color: #f4fbf7;
                border: 2px solid #bce1ce;
                border-radius: 20px;
                padding: 35px 20px 40px 20px;
                margin-bottom: 30px;
                box-shadow: 0 8px 20px rgba(0, 102, 51, 0.08);
                text-align: center;
                animation: fadeInUpSmooth 3s cubic-bezier(0.16, 1, 0.3, 1) both;
            }}

            h1 {{
                background: linear-gradient(
                    110deg, 
                    #006633 0%, 
                    #006633 30%, 
                    #96c93d 45%, 
                    #ffffff 50%, 
                    #96c93d 55%, 
                    #006633 70%, 
                    #006633 100%
                );
                background-size: 200% auto;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                animation: shimmerEffect 4s linear infinite, glowPulse 3s ease-in-out infinite;
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
                animation: fadeInUpSmooth 2s cubic-bezier(0.16, 1, 0.3, 1) 0.3s both;
            }}

            /* ==========================================
               🎨 กรอบ 2 ฝั่ง (ยกเว้น Sidebar)
               ========================================== */

            /* 📁 คอลัมน์ซ้าย (อัปโหลดเอกสาร) */
            [data-testid="stColumn"]:not([data-testid="stSidebar"] *):nth-child(1),
            div[data-testid="column"]:not([data-testid="stSidebar"] *):nth-child(1) {{
                background: linear-gradient(180deg, #ecfdf5 0%, #ffffff 100%) !important;
                border: 2px solid #10b981 !important;
                border-radius: 20px !important;
                padding: 24px 22px !important;
                box-shadow: 0 10px 25px rgba(16, 185, 129, 0.12) !important;
                animation: fadeInUpSmooth 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.5s both !important;
            }}

            /* 🤖 คอลัมน์ขวา (ผลวิเคราะห์ AI) */
            [data-testid="stColumn"]:not([data-testid="stSidebar"] *):nth-child(2),
            div[data-testid="column"]:not([data-testid="stSidebar"] *):nth-child(2) {{
                background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%) !important;
                border: 2px solid #0284c7 !important;
                border-radius: 20px !important;
                padding: 24px 22px !important;
                box-shadow: 0 10px 25px rgba(2, 132, 199, 0.12) !important;
                animation: fadeInUpSmooth 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.75s both !important;
            }}

            h2, h3 {{
                color: #006633 !important;
                font-weight: 600;
            }}

            .stButton>button, .stDownloadButton>button {{
                background: linear-gradient(135deg, #006633, #00b09b);
                color: white !important;
                font-weight: 500;
                font-size: 16px;
                border-radius: 12px;
                border: none;
                padding: 12px 24px;
                box-shadow: 0 4px 15px rgba(0, 102, 51, 0.3);
                transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
                width: 100%;
            }}
            .stButton>button:hover, .stDownloadButton>button:hover {{
                transform: translateY(-3px) scale(1.015);
                box-shadow: 0 8px 25px rgba(0, 102, 51, 0.45);
                color: white;
            }}

            [data-testid="stFileUploadDropzone"] {{
                background-color: #ffffff;
                border: 2px dashed #10b981;
                border-radius: 15px;
                padding: 20px;
                transition: all 0.3s ease;
            }}
            [data-testid="stFileUploadDropzone"]:hover {{
                background-color: #e8f7f0;
                border-color: #006633;
            }}

            /* 🔔 ตกแต่งกล่องสถานะประมวลผล st.status */
            [data-testid="stStatusWidget"] {{
                border: 2px solid #ffa726 !important;
                background-color: #fffde7 !important;
                border-radius: 16px !important;
                padding: 10px !important;
                box-shadow: 0 6px 20px rgba(255, 167, 38, 0.15) !important;
                animation: fadeInUpSmooth 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
            }}
            [data-testid="stStatusWidget"] summary label, 
            [data-testid="stStatusWidget"] summary span {{
                font-size: 19px !important;
                font-weight: 600 !important;
                color: #e65100 !important;
            }}

            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            header {{visibility: hidden;}}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        pass

set_background('background.jpg')
# ==========================================
# 📢 แถบประกาศข่าวสารสำคัญ (Top Announcement Banner)
# ==========================================
st.markdown("""
<div style="
    background: linear-gradient(90deg, #fde0dc 0%, #ffffff 100%);
    border-left: 6px solid #e84e40;
    border-radius: 8px;
    padding: 15px 20px;
    margin-bottom: 25px;
    margin-top: 10px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    display: flex;
    align-items: center;
    transition: transform 0.3s ease;
">
    <div style="font-size: 24px; margin-right: 15px; animation: pulse 2s infinite;">
        📢
    </div>
    <div>
        <h4 style="margin: 0; color: #166534; font-size: 16px; font-weight: 600; padding-bottom: 3px;">
            ประกาศจากฝ่ายพัฒนานิสิต
        </h4>
        <p style="margin: 0; color: #4b5563; font-size: 14px; font-weight: 400;">
            เปิดรับโครงการที่จะนำเสนอในรอบเดือนสิงหาคม 2569 ตั้งแต่วันนี้ - 10 สิงหาคม 2569 | โดยส่งโครงการที่จะนำเสนอได้ที่ศูนย์ฝึกประสบการณ์วิชาชีพ อาคาร 2 ชั้น 1
        </p>
    </div>
</div>

<style>
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.15); }
    100% { transform: scale(1); }
}
</style>
""", unsafe_allow_html=True)
# ==========================================
# 3. ตั้งค่า API Key ของ Gemini
# ==========================================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# หมายเหตุ: หาก gemini-3.6-flash มีข้อผิดพลาดในการรัน ให้ลองเปลี่ยนเป็น gemini-1.5-flash นะครับ
model = genai.GenerativeModel('gemini-3.6-flash')

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
    1. ข้อมูลทั่วไป (บังคับ: ต้องมีครบทั้ง ชื่อโครงการทั้งภาษาไทยและภาษาอังกฤษ, หน่วยงาน, อาจารย์ที่ปรึกษาโครงการ, ชื่อประธานโครงการ, วันที่, สถานที่, ผู้เข้าร่วมโครงการ, กรรมการตรวจรับ)
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
    13. ความสอดคล้องกับการพัฒนานิสิต (บังคับ: ต้องมีการระบุครบทั้ง 6 อย่าง คือ 1.การพัฒนานิสิตตามกรอบมาตรฐานคุณวุฒิระดับอุดมศึกษาของประเทศไทย 4 ด้าน, 2.อัตลักษณ์ มก., 3.การพัฒนานิสิตตามวิสัยทัศน์ของคณะศึกษาศาสตร์, 4.SDGs, 5.กิจกรรมพัฒนาผู้เรียนตามหลักเกณฑ์การรับรองปริญญาและประกาศนียบัตรทางการศึกษาของคุรุสภา และ 6.สมรรถนะ 8 ด้าน หากขาดข้อใดข้อหนึ่งไป ให้ประเมินเป็น 🟡 ทันที)
    14. กำหนดการโครงการ (ตารางเวลาอย่างละเอียด)

    ส่วนที่ 2: การตรวจสอบความถูกต้องของภาษาไทยและการใช้อักขรวิธี
    ตรวจหาคำผิด การสะกดผิด หรือการเว้นวรรคที่ไม่เหมาะสมกับเอกสารราชการ
    **🚨 กฎเหล็กสำหรับส่วนที่ 2:**
    - หากพบคำผิด **ต้องระบุตำแหน่งที่พบให้ชัดเจน** ว่าอยู่ใน "หัวข้ออะไร" และ "หน้าที่เท่าไหร่" (ให้อ้างอิงเลขหน้าจากแท็ก [--- เริ่มหน้าที่ X ---] ที่ปรากฏในเนื้อหา) 
    - ให้นำเสนอในรูปแบบ Bullet Points ย่อยง่ายๆ เช่น:
      * **คำที่เขียนผิด** -> ควรแก้ไขเป็น **คำที่ถูกต้อง** (พบที่: หัวข้อยกตัวอย่าง, หน้าที่ X)
    - หากไม่พบคำผิดเลย ให้แจ้งว่า "ไม่พบคำผิดหรือการเว้นวรรคที่ไม่เหมาะสมในเอกสาร สะกดได้ถูกต้องดีมาก"

    ส่วนที่ 3: การวิเคราะห์ความสมเหตุสมผลของเนื้อหา (Logical Check)
    - หลักการและเหตุผลมีความสอดคล้องวัตถุประสงค์ของโครงการ ปัญหาที่เกิดขึ้นจริง ข้อมูลหรือทฤษฎีที่น่าเชื่อถือ และ เป้าหมายหรือนโยบายของหน่วยงาน หรือไม่
    - วัตถุประสงค์ สอดคล้องกับ "ผลที่คาดว่าจะได้รับ" และ "ตัวชี้วัดความสำเร็จ" หรือไม่
    - วิธีการประเมิน เครื่องมือที่ใช้ และตัวชี้วัดความสำเร็จ สอดคล้องกันและประเมินได้จริงหรือไม่
    - แผนการปฏิบัติงานและกำหนดการ สอดคล้องกันและเป็นไปได้จริงหรือไม่

    🌟 ส่วนที่ 4: การประเมินคะแนนภาพรวม (Overall Score) - แสดงส่วนนี้ไว้ท้ายสุดของรายงาน!
    - ให้คะแนนภาพรวมของเอกสารนี้จากคะแนนเต็ม 100 คะแนน โดยแบ่งเกณฑ์ดังนี้:
      1. ความครบถ้วนของโครงสร้างแบบฟอร์ม (50 คะแนน)
      2. ความถูกต้องของภาษาและการสะกดคำ (20 คะแนน)
      3. ความสมเหตุสมผลของเนื้อหา (30 คะแนน)
    - กฎเหล็กการแสดงผล: ให้คุณแสดงคะแนนภาพรวมไว้ล่างสุดของเอกสารให้โดดเด่น เช่น "--- \n ## 🏆 คะแนนภาพรวมโครงการ: [คะแนนที่ได้] / 100 คะแนน" 
    - ตามด้วยคำวิจารณ์สั้นๆ (Feedback) ว่าทำไมถึงได้คะแนนเท่านี้ โดยขอให้มีระบุคะแนนแต่ละส่วนไว้ด้วย

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
    
    # 📌 การ์ดแสดงขั้นตอนแบบ Visual (ใช้เทคนิคต่อ String เพื่อป้องกันปัญหาเว้นวรรค)
    step_html = (
        "<div style='font-family: \"Kanit\", sans-serif; margin-top: 10px;'>"
        
        "<!-- ขั้นตอนที่ 1 -->"
        "<div style='display: flex; margin-bottom: 15px; position: relative;'>"
        "<div style='position: absolute; left: 15px; top: 32px; bottom: -20px; width: 2px; background-color: #bce1ce; z-index: 0;'></div>"
        "<div style='background: linear-gradient(135deg, #006633, #00b09b); color: white; border-radius: 50%; width: 32px; height: 32px; min-width: 32px; display: flex; align-items: center; justify-content: center; font-weight: bold; z-index: 1; box-shadow: 0 3px 6px rgba(0,102,51,0.2);'>1</div>"
        "<div style='margin-left: 15px; background: #ffffff; padding: 10px 14px; border-radius: 10px; border: 1px solid #e0f2e9; flex-grow: 1; box-shadow: 0 2px 8px rgba(0,0,0,0.03);'>"
        "<div style='font-weight: 600; color: #006633; font-size: 14px; margin-bottom: 2px;'>บันทึกเป็น PDF</div>"
        "<div style='font-size: 12.5px; color: #555; line-height: 1.4;'>บันทึกชื่อไฟล์เป็นชื่อโครงการ (ต้องเป็นไฟล์ที่แปลงจาก <b>MS Word</b> เท่านั้น!)</div>"
        "</div></div>"
        
        "<!-- ขั้นตอนที่ 2 -->"
        "<div style='display: flex; margin-bottom: 15px; position: relative;'>"
        "<div style='position: absolute; left: 15px; top: 32px; bottom: -20px; width: 2px; background-color: #e0f2fe; z-index: 0;'></div>"
        "<div style='background: linear-gradient(135deg, #006633, #00b09b); color: white; border-radius: 50%; width: 32px; height: 32px; min-width: 32px; display: flex; align-items: center; justify-content: center; font-weight: bold; z-index: 1; box-shadow: 0 3px 6px rgba(0,102,51,0.2);'>2</div>"
        "<div style='margin-left: 15px; background: #ffffff; padding: 10px 14px; border-radius: 10px; border: 1px solid #e0f2e9; flex-grow: 1; box-shadow: 0 2px 8px rgba(0,0,0,0.03);'>"
        "<div style='font-weight: 600; color: #006633; font-size: 14px; margin-bottom: 2px;'>อัปโหลดและยืนยัน</div>"
        "<div style='font-size: 12.5px; color: #555; line-height: 1.4;'>อัปโหลดไฟล์โครงการและติ๊ก 🛡️ <b>ยอมรับเงื่อนไข</b></div>"
        "</div></div>"
        
        "<!-- ขั้นตอนที่ 3 -->"
        "<div style='display: flex; margin-bottom: 10px; position: relative;'>"
        "<div style='background: linear-gradient(135deg, #0ea5e9, #38bdf8); color: white; border-radius: 50%; width: 32px; height: 32px; min-width: 32px; display: flex; align-items: center; justify-content: center; font-weight: bold; z-index: 1; box-shadow: 0 3px 6px rgba(14,165,233,0.2);'>3</div>"
        "<div style='margin-left: 15px; background: #ffffff; padding: 10px 14px; border-radius: 10px; border: 1px solid #e0f2fe; flex-grow: 1; box-shadow: 0 2px 8px rgba(0,0,0,0.03);'>"
        "<div style='font-weight: 600; color: #0284c7; font-size: 14px; margin-bottom: 2px;'>เริ่มการตรวจสอบ</div>"
        "<div style='font-size: 12.5px; color: #555; line-height: 1.4;'>กดปุ่ม <b>เริ่มให้ AI ตรวจสอบเอกสาร</b> และรอรับผลวิเคราะห์ 🚀</div>"
        "</div></div>"
        
        "</div>"
    )
    
    st.markdown(step_html, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📥 ดาวน์โหลดแบบฟอร์ม")
    # ปุ่มดาวน์โหลดไฟล์ Word
    if os.path.exists("template.docx"):
        with open("template.docx", "rb") as file:
            st.download_button(
                label="📄 ดาวน์โหลดแบบฟอร์มโครงการ (Word)",
                data=file,
                file_name="แบบฟอร์มเสนอโครงการ_คณะศึกษาศาสตร์.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
    else:
        st.warning("⚠️ เจ้าหน้าที่กำลังอัปเดตไฟล์แบบฟอร์ม...")

    st.markdown("---")
    st.caption("👨‍💻 พัฒนาโดย: นายประสิทธิ์ รอดพันธุ์\n\nนักวิชาการศึกษาชำนาญการ")

# 👁️ สถิติผู้เข้าใช้เว็บไซต์ (FreeVisitorCounters)
    st.markdown("---")
    
    # กำหนด HTML โค้ดที่รวม CSS การตกแต่ง และ Script ของ Counter
    counter_html = """
    <div style="text-align: center; padding: 12px; background-color: #ffffff; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 2px 8px rgba(0,0,0,0.05); font-family: sans-serif;">
        <p style="margin: 0 0 8px 0; font-size: 13px; color: #006633; font-weight: 600;">👁️ สถิติผู้เข้าใช้เว็บไซต์</p>
        
        <!-- โค้ด Script จากเว็บ Counter -->
        <a href='https://www.free-counters.org/' style='font-size: 10px; color: #999; text-decoration: none;'>www.free-Counter.org</a><br>
        <script type='text/javascript' src='https://www.freevisitorcounters.com/auth.php?id=b796677c5d35a0a92c994f959502a1b7c4c6a66c'></script>
        <script type="text/javascript" src="https://www.freevisitorcounters.com/en/home/counter/1611880/t/9"></script>
    </div>
    """
    
    # ใช้ components.html เพื่อรัน JavaScript 
    # (อาจต้องปรับค่า height ให้พอดีกับขนาดของป้าย Counter)
    components.html(counter_html, height=120)
# ==========================================
# 6. ส่วนแสดงผลเนื้อหาหลัก
# ==========================================
st.markdown("""
<div class="header-box">
    <h1>ระบบตรวจแบบฟอร์มเสนอโครงการพัฒนานิสิต<br>คณะศึกษาศาสตร์ มหาวิทยาลัยเกษตรศาสตร์</h1>
    <div class="subtitle-text">
        ✨ ระบบการตรวจสอบโครงสร้าง การสะกดคำ และความสมเหตุสมผลของโครงการ โดยใช้เทคโนโลยีปัญญาประดิษฐ์ (AI) เพื่อใช้เป็นแนวทางในการปรับปรุงเอกสารเบื้องต้น ก่อนนำเสนอคณะกรรมการฝ่ายพัฒนานิสิต ✨
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.markdown("### 📁 1. อัปโหลดเอกสาร")
    # 📌 ข้อความเตือนตัวสีแดง (ย้ายมาอยู่ล่างหัวข้อ และ อยู่ก่อนกล่องอัปโหลด)
    st.markdown(
        "<p style='color: #e74c3c; font-size: 14px; font-weight: 500; margin-top: -5px; margin-bottom: 12px;'>"
        "🔴 <b>โปรดตรวจสอบว่า ได้ตั้งชื่อไฟล์เป็นชื่อโครงการแล้วหรือยัง?</b>"
        "</p>", 
        unsafe_allow_html=True
    )
    uploaded_file = st.file_uploader("ลากไฟล์ PDF มาวางที่นี่", type="pdf", label_visibility="collapsed")

    if uploaded_file is not None:
        st.toast("✅ อัปโหลดไฟล์สำเร็จ! พร้อมให้ AI ตรวจสอบแล้ว", icon="🎉")
        st.success("✅ อัปโหลดไฟล์สำเร็จ!")
        document_text = read_pdf(uploaded_file)
        
        with st.expander("🔍 ดูข้อความที่ระบบดึงออกมาได้ (คลิกเพื่อขยาย)"):
            if not document_text.strip():
                st.error("⚠️ ไม่พบข้อความในเอกสาร (อาจเป็นไฟล์สแกน)")
            else:
                st.write(document_text) # <-- เติมคำสั่งให้แสดงข้อความที่นี่

# ==========================================
# 📊 คอลัมน์ที่ 2
# ==========================================
with col2:
    st.markdown("### 🤖 2. ผลการวิเคราะห์จาก AI")
    
    # ... (ส่วนโค้ดด้านล่างปล่อยไว้ตามเดิมได้เลยครับ) ...
    
    # ... (ส่วนโค้ดการตรวจของ AI เช่น กล่องติ๊กยอมรับ PDPA และปุ่มเริ่มตรวจ จะต่อจากบรรทัดนี้เลยครับ) ...
    
    if uploaded_file is not None and document_text.strip():
        # --- เพิ่มกล่องกดยอมรับ PDPA ---
        st.markdown("<div style='background-color: #fff9e6; padding: 15px; border-radius: 10px; border-left: 5px solid #ffcc00; margin-bottom: 20px; font-size: 14px;'>", unsafe_allow_html=True)
        pdpa_consent = st.checkbox("🛡️ ข้าพเจ้ารับทราบและยินยอมให้ระบบประมวลผลข้อมูลในเอกสารนี้ด้วยปัญญาประดิษฐ์ (AI) เพื่อการตรวจสอบความถูกต้องเบื้องต้น ข้อมูลจะไม่ถูกนำไปใช้ฝึกสอน AI (No Model Training) และไม่มีการจัดเก็บเอกสารต้นฉบับไว้ในระบบ")
        st.markdown("</div>", unsafe_allow_html=True)

        # ปุ่มจะทำงานต่อเมื่อผู้ใช้ติ๊กถูกที่ Checkbox เท่านั้น
        if pdpa_consent:
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
                    
                    # --- เพิ่มข้อความหมายเหตุด้านล่างสุด ---
                    st.info("⚠️ **หมายเหตุ:** การประเมินนี้วิเคราะห์โดยปัญญาประดิษฐ์ (AI) เพื่อใช้เป็นแนวทางในการปรับปรุงเอกสารเบื้องต้นเท่านั้น **ทั้งนี้ การพิจารณาให้ข้อเสนอแนะและการอนุมัติโครงการ จะขึ้นอยู่กับดุลยพินิจของที่ประชุมคณะกรรมการฝ่ายพัฒนานิสิตเป็นสำคัญ**")
                    
        else:
            st.info("👆 กรุณาติ๊กเครื่องหมาย ✅ หน้าข้อความ 🛡️ ยอมรับเงื่อนไขการประมวลผลข้อมูลด้านบน ก่อนกดปุ่มตรวจสอบ")
            
    else:
        st.info("👈 กรุณาอัปโหลดเอกสารในช่องด้านซ้ายมือ เพื่อเปิดใช้งานระบบ AI")

# ==========================================
# 📊 แผงสถิติภาพรวมของระบบ (สไตล์ Modern AI + แอนิเมชันลอยเข้า)
# ==========================================
st.write("") 
st.write("") 
st.markdown("---") 
st.markdown("<h4 style='text-align: center; color: #475569; font-family: \"Kanit\", sans-serif; margin-bottom: 25px; letter-spacing: 0.5px;'>✨ สถิติการประเมินโครงการภาพรวม</h4>", unsafe_allow_html=True)

try:
    sheet_id = "1jQVFbiKKQjxJVk8HHwLVzNlNDWyA2CPQSnNsVAz3aNk"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    
    df = pd.read_csv(csv_url)
    col_name_score = "คะแนนภาพรวม" 
    total_projects = len(df)
    
    if col_name_score in df.columns:
        df['clean_score'] = df[col_name_score].astype(str).str.split('/').str[0]
        df['clean_score'] = pd.to_numeric(df['clean_score'], errors='coerce')
        
        score_90_100 = len(df[df['clean_score'] >= 90])
        score_80_89 = len(df[(df['clean_score'] >= 80) & (df['clean_score'] < 90)])
        score_below_80 = len(df[df['clean_score'] < 80])
    else:
        score_90_100 = 0; score_80_89 = 0; score_below_80 = 0
        
except Exception as e:
    total_projects = 0; score_90_100 = 0; score_80_89 = 0; score_below_80 = 0

dashboard_html = f"""
<!DOCTYPE html>
<html>
<head>
    <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@400;500;600;800&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Kanit', sans-serif;
            margin: 0;
            padding: 10px;
            background-color: transparent; 
        }}
        .container {{
            display: flex;
            gap: 25px;
            max-width: 900px;
            margin: 0 auto;
        }}
        
        /* 🎬 สร้างแอนิเมชัน ลอยขึ้นพร้อมค่อยๆ ปรากฏ */
        @keyframes fadeSlideUp {{
            0% {{
                opacity: 0;
                transform: translateY(40px); /* เริ่มต้นต่ำลงไป 40px */
            }}
            100% {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .ai-card {{
            background: #ffffff;
            border-radius: 20px;
            padding: 20px 25px;
            box-shadow: 0 10px 30px -5px rgba(79, 70, 229, 0.12), inset 0 0 0 1px rgba(226, 232, 240, 0.8);
            position: relative;
            overflow: hidden;
            
            /* ตั้งค่าเริ่มต้นให้ซ่อนไว้ก่อน เพื่อรอแอนิเมชันทำงาน */
            opacity: 0; 
            animation: fadeSlideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            transition: box-shadow 0.3s ease, transform 0.3s ease;
        }}
        
        .ai-card:hover {{
            transform: translateY(-5px) !important; /* ยกขึ้นเมื่อชี้เมาส์ */
            box-shadow: 0 20px 40px -10px rgba(79, 70, 229, 0.25);
        }}
        
        .ai-card::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; height: 4px;
        }}
        
        /* ⏱️ กำหนดเวลาดีเลย์ให้แต่ละกล่อง */
        .card-1 {{ 
            flex: 1; display: flex; flex-direction: column; justify-content: center; text-align: center; 
            animation-delay: 0.2s; /* กล่องแรกโผล่มาก่อน */
        }}
        .card-1::before {{ background: linear-gradient(90deg, #3b82f6, #8b5cf6); }}
        
        .card-2 {{ 
            flex: 1.5; text-align: center; 
            animation-delay: 0.5s; /* กล่องสองตามมาทีหลัง หน่วง 0.5 วิ */
        }}
        .card-2::before {{ background: linear-gradient(90deg, #10b981, #0ea5e9, #f43f5e); }}

        .title {{ font-size: 14px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }}
        
        .gradient-text {{
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            display: inline-block;
        }}
        .total-num {{ font-size: 42px; background-image: linear-gradient(135deg, #3b82f6, #8b5cf6); line-height: 1.1; }}
        .unit {{ font-size: 14px; color: #94a3b8; font-weight: 500; margin-left: 5px; }}

        .score-container {{ display: flex; justify-content: space-around; align-items: center; margin-top: 15px; }}
        .score-box {{ text-align: center; }}
        .score-num {{ font-size: 32px; line-height: 1.1; }}
        
        .score-90 {{ background-image: linear-gradient(135deg, #10b981, #047857); }}
        .score-80 {{ background-image: linear-gradient(135deg, #0ea5e9, #2563eb); }}
        .score-below {{ background-image: linear-gradient(135deg, #f43f5e, #be123c); }}
        
        .score-label {{ font-size: 13px; color: #64748b; font-weight: 500; margin-top: 4px; }}
        
        .divider {{ 
            width: 1.5px; 
            height: 50px; 
            background: linear-gradient(to bottom, transparent, #cbd5e1, transparent); 
            margin: 0 10px; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- ส่วนที่ 1: ตรวจไปแล้วทั้งหมด -->
        <div class="ai-card card-1">
            <div class="title">🚀 โครงการที่ AI วิเคราะห์แล้ว</div>
            <div><span id="total_count" class="gradient-text total-num">0</span> <span class="unit">โครงการ</span></div>
        </div>
        
        <!-- ส่วนที่ 2: สัดส่วนคะแนน -->
        <div class="ai-card card-2">
            <div class="title">🎯 สัดส่วนคะแนนคุณภาพ</div>
            <div class="score-container">
                <div class="score-box">
                    <div id="count_90" class="gradient-text score-num score-90">0</div>
                    <div class="score-label">ดีมาก (90-100)</div>
                </div>
                <div class="divider"></div>
                <div class="score-box">
                    <div id="count_80" class="gradient-text score-num score-80">0</div>
                    <div class="score-label">ดี (80-89)</div>
                </div>
                <div class="divider"></div>
                <div class="score-box">
                    <div id="count_below" class="gradient-text score-num score-below">0</div>
                    <div class="score-label">ต้องปรับปรุง (< 80)</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function animateValue(id, start, end, duration) {{
            if (start === end) {{
                document.getElementById(id).innerHTML = end.toLocaleString();
                return;
            }}
            var obj = document.getElementById(id);
            var startTime = null;
            function step(timestamp) {{
                if (!startTime) startTime = timestamp;
                var progress = Math.min((timestamp - startTime) / duration, 1);
                obj.innerHTML = Math.floor(progress * (end - start) + start).toLocaleString();
                if (progress < 1) {{
                    window.requestAnimationFrame(step);
                }} else {{
                    obj.innerHTML = end.toLocaleString();
                }}
            }}
            window.requestAnimationFrame(step);
        }}

        // สั่งให้ตัวเลขวิ่งให้สอดคล้องกับจังหวะที่กล่องลอยขึ้นมา
        // กล่องที่ 1 ดีเลย์ 0.2s เราจะเริ่มวิ่งเลขตอน 0.4s 
        setTimeout(() => {{
            animateValue("total_count", 0, {total_projects}, 1500);
        }}, 400);

        // กล่องที่ 2 ดีเลย์ 0.5s เราจะเริ่มวิ่งเลขตอน 0.7s
        setTimeout(() => {{
            animateValue("count_90", 0, {score_90_100}, 1500);
            animateValue("count_80", 0, {score_80_89}, 1500);
            animateValue("count_below", 0, {score_below_80}, 1500);
        }}, 700);
    </script>
</body>
</html>
"""

# ปรับความสูงเพิ่มเป็น 200px เพื่อเผื่อระยะที่กล่องเริ่มลอยจากด้านล่าง (ไม่ให้โดนตัดขอบตอนเริ่มโผล่)
components.html(dashboard_html, height=100)
