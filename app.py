import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import time
import base64
# ==========================================
# ฟังก์ชันสำหรับดึงรูปภาพจากเครื่องมาทำเป็นพื้นหลัง
# ==========================================
def set_background(image_file):
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()
    
    st.markdown(
        f"""
        <style>
        /* 1. ตั้งค่ารูปภาพเป็นพื้นหลังของเว็บ พร้อมใส่เลเยอร์สีขาวโปร่งแสงทับให้รูปดูจางลง */
        .stApp {{
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.70), rgba(255, 255, 255, 0.70)), 
                url(data:image/jpeg;base64,{encoded_string});
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        
        /* 2. สร้างกรอบสีขาวโปร่งแสงรองรับเนื้อหาตรงกลาง เพื่อให้อ่านง่ายขึ้นอีกระดับ */
        .block-container {{
            background-color: rgba(255, 255, 255, 0.90); 
            border-radius: 20px;
            padding: 3rem 2rem;
            margin-top: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ⚠️ อย่าลืมเปลี่ยน 'background.jpg' เป็นชื่อไฟล์รูปของคุณที่อยู่ในโฟลเดอร์ ProjectChecker
set_background('background.jpg')

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
# 2. ตกแต่งหน้าตาเว็บด้วย CSS (Modern UI & Gimmicks)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Kanit', sans-serif !important;
    }

    .header-box {
        background-color: #f4fbf7;
        border: 2px solid #bce1ce;
        border-radius: 20px;
        padding: 35px 20px 40px 20px;
        margin-bottom: 30px;
        box-shadow: 0 8px 20px rgba(0, 102, 51, 0.08);
        text-align: center;
    }

    h1 {
        background: -webkit-linear-gradient(45deg, #006633, #96c93d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 600;
        text-align: center;
        margin: 0; 
        padding: 0;
        line-height: 1.4;
    }
    
    .subtitle-text {
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
    }
    
    h2, h3 {
        color: #006633 !important;
        font-weight: 500;
    }
    
    .stButton>button {
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
    }
    .stButton>button:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 102, 51, 0.45);
        color: white;
    }
    .stButton>button:active {
        transform: translateY(0px);
    }

    [data-testid="stFileUploadDropzone"] {
        background-color: #f4fbf7;
        border: 2px dashed #00b09b;
        border-radius: 15px;
        padding: 20px;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        background-color: #e8f7f0;
        border-color: #006633;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. ตั้งค่า API Key ของ Gemini
# ==========================================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.6-flash')

# ==========================================
# 4. ฟังก์ชันสำหรับอ่านไฟล์ PDF ด้วย PyMuPDF
# ==========================================
def read_pdf(file):
    text = ""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page_num, page in enumerate(doc):
        text += f"\n\n[--- เริ่มหน้าที่ {page_num + 1} ---]\n"
        text += page.get_text() + "\n"
    return text

# ==========================================
# 5. ฟังก์ชันสำหรับให้ AI ตรวจเอกสาร (อัปเดตย้ายคะแนนไปท้ายสุด)
# ==========================================
def analyze_document(text):
    if not text.strip():
        return "❌ ระบบไม่พบข้อความในไฟล์ PDF นี้ครับ สาเหตุอาจเกิดจากไฟล์เป็นรูปภาพ(สแกน) หรือมีการเข้ารหัสฟอนต์ กรุณาลองใช้ไฟล์ที่เซฟมาจาก Word โดยตรงครับ"

    prompt = f"""
    คุณคือเจ้าหน้าที่ตรวจสอบแบบเสนอโครงการที่ "เข้มงวดมาก (Strict Evaluator)" ของคณะศึกษาศาสตร์ มหาวิทยาลัยเกษตรศาสตร์
    หน้าที่ของคุณคือการตรวจเอกสารตามกฎเกณฑ์ด้านล่างนี้อย่างเคร่งครัด ห้ามคิดไปเอง และห้ามอนุโลมเด็ดขาด:

    ส่วนที่ 1: การตรวจความครบถ้วนของรูปแบบฟอร์ม (Form Structure Validation)
    ตรวจสอบว่าผู้เสนอโครงการได้เขียนหัวข้อครบถ้วนตามแบบฟอร์มมาตรฐานทั้ง 14 ข้อหรือไม่
    
    🚨 กฎเหล็กสำหรับการตรวจส่วนที่ 1 (Strict Rules):
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

    ส่วนที่ 2: การตรวจสอบความถูกต้องของภาษาไทยและการใช้อักขรวิธี
    ตรวจหาคำผิด การสะกดผิด หรือการเว้นวรรคที่ไม่เหมาะสมกับเอกสารราชการ
    **🚨 กฎเหล็กสำหรับส่วนที่ 2:**
    - หากพบคำผิด **ต้องระบุตำแหน่งที่พบให้ชัดเจน** ว่าอยู่ใน "หัวข้ออะไร" และ "หน้าที่เท่าไหร่" (ให้อ้างอิงเลขหน้าจากแท็ก [--- เริ่มหน้าที่ X ---] ที่ปรากฏในเนื้อหา) 
    - ให้นำเสนอในรูปแบบ Bullet Points ย่อยง่ายๆ เช่น:
      * **คำที่เขียนผิด** -> ควรแก้ไขเป็น **คำที่ถูกต้อง** (พบที่: หัวข้อยกตัวอย่าง, หน้าที่ X)
    - หากไม่พบคำผิดเลย ให้แจ้งว่า "ไม่พบคำผิดหรือการเว้นวรรคที่ไม่เหมาะสมในเอกสาร สะกดได้ถูกต้องดีมาก"

    ส่วนที่ 3: การวิเคราะห์ความสมเหตุสมผลของเนื้อหา (Logical Check)
    - วัตถุประสงค์ สอดคล้องกับ "ผลที่คาดว่าจะได้รับ" และ "ตัวชี้วัดความสำเร็จ" หรือไม่
    - งบประมาณที่ตั้งไว้ สมเหตุสมผลกับ "รูปแบบลักษณะกิจกรรม" หรือไม่
    - แผนการปฏิบัติงานและกำหนดการ สอดคล้องกันและเป็นไปได้จริงหรือไม่

    🌟 **ส่วนที่ 4: การประเมินคะแนนภาพรวม (Overall Score) - แสดงส่วนนี้ไว้ท้ายสุดของรายงาน!**
    - ให้คะแนนภาพรวมของเอกสารนี้จากคะแนนเต็ม 100 คะแนน โดยแบ่งเกณฑ์ดังนี้:
      1. ความครบถ้วนของโครงสร้างแบบฟอร์ม (50 คะแนน)
      2. ความถูกต้องของภาษาและการสะกดคำ (20 คะแนน)
      3. ความสมเหตุสมผลของเนื้อหา (30 คะแนน)
    - **กฎเหล็กการแสดงผล:** เมื่อรายงานผลส่วนที่ 1-3 เสร็จแล้ว ให้คุณแสดงคะแนนภาพรวมไว้ล่างสุดของเอกสารให้โดดเด่น เช่น "--- \n ## 🏆 คะแนนภาพรวมโครงการ: [คะแนนที่ได้] / 100 คะแนน" 
    - ตามด้วยคำวิจารณ์สั้นๆ (Feedback) ว่าทำไมถึงได้คะแนนเท่านี้ โครงการนี้มีจุดเด่นตรงไหน และต้องแก้จุดไหนเป็นพิเศษก่อนนำไปส่งจริง

    เนื้อหาโครงการที่นิสิตส่งมา:
    {text}
    """
    response = model.generate_content(prompt)
    return response.text

# ==========================================
# 6. การจัด Layout และส่วนแสดงผลหน้าเว็บ
# ==========================================

with st.sidebar:
    # จัดโลโก้ให้อยู่ตรงกลาง Sidebar โดยใช้ Columns
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        st.image("logo.png", use_container_width=True)
    st.markdown("### 📌 คำแนะนำการใช้งาน")
    st.info("""
    **ขั้นตอนการตรวจเอกสาร:**
    1. บันทึกไฟล์แบบเสนอโครงการของท่านเป็นนามสกุล **.pdf** 
       *(ต้องเป็นไฟล์ที่แปลงจาก MS Word เท่านั้น!)*
    2. อัปโหลดไฟล์จากข้อ 1
    3. ตรวจสอบว่าระบบอ่านเนื้อหาได้ครบถ้วน
    4. กดปุ่ม **เริ่มให้ AI ตรวจสอบเอกสาร**
    """)
    st.markdown("---")
    st.caption("👨‍💻 พัฒนาโดย: \nนายประสิทธิ์ รอดพันธุ์\n\nนักวิชาการศึกษาชำนาญการ")

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
        if st.button("✨ เริ่มให้ AI ตรวจสอบเอกสาร"):
            
            result = "" # สร้างตัวแปรมารับค่าก่อน
            
            # กล่องสถานะ (โชว์ตอนกำลังโหลด พอโหลดเสร็จกล่องนี้จะหุบลง)
            with st.status("🤖 AI กำลังอ่านและประเมินเอกสาร ระบบ AI ใช้เวลาประมาณ 1 นาที กรุณารอสักครู่...", expanded=True) as status:
                st.write("⏳ กำลังตรวจสอบโครงสร้างตามแบบฟอร์ม...")
                time.sleep(1.5)
                st.write("🔍 กำลังประเมินความสมเหตุสมผลและหาคำผิด...")
                time.sleep(1)
                st.write("💯 กำลังคำนวณคะแนนภาพรวม...")
                
                try:
                    result = analyze_document(document_text)
                    # โหลดเสร็จแล้ว สั่งให้กล่องสถานะหุบลง (expanded=False)
                    status.update(label="✅ AI ประเมินผลเสร็จสิ้น!", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="❌ เกิดข้อผิดพลาด!", state="error")
                    st.error(f"เกิดข้อผิดพลาด: {e}")
            
            # ===============================================
            # ดึงการแสดงผลลัพธ์ออกมาไว้ "นอกกล่อง" st.status
            # พอโหลดเสร็จ ข้อความจะโชว์ขึ้นมาทันที ไม่ถูกซ่อน
            # ===============================================
            if result:
                st.balloons()
                st.toast("🎉 AI ให้คะแนนเอกสารเรียบร้อยแล้ว!", icon="✨")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📋 สรุปผลการตรวจสอบ")
                
                # แสดงผลลัพธ์แบบเด่นๆ ไม่ต้องกดขยาย
                st.markdown(result)
                
    else:
        st.info("👈 กรุณาอัปโหลดเอกสารในช่องด้านซ้ายมือ เพื่อเปิดใช้งานระบบ AI")