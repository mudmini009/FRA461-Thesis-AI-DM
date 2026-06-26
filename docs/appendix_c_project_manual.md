# 📝 ภาคผนวก ค: แหล่งเก็บข้อมูลโครงงานและคู่มือการใช้งานระบบ (Appendix C: Project Repository & User Manual)
### สรุปโครงสร้างสารสนเทศเชิงแฟ้มข้อมูล การติดตั้ง และระบบจัดเก็บข้อมูลดิจิทัลฉบับสมบูรณ์

---

## 🗄️ 1. แหล่งเก็บข้อมูลดิจิทัล (Project Repository)
ผู้ใช้งานสามารถเข้าถึงรหัสต้นฉบับ (Source Code), สคริปต์ทวนสอบผลลัพธ์ประสิทธิภาพ (Evaluation Suite), และข้อมูลประวัติการพัฒนา (Trace Logs) ทั้งหมดของโครงงานนี้ได้ที่:
*   **GitHub Repository:** [https://github.com/mudmini009/FRA461-Thesis-AI-DM](https://github.com/mudmini009/FRA461-Thesis-AI-DM)
*   **สิทธิ์การเข้าถึงและการแจกจ่าย:** สัญญาอนุญาตแบบโอเพนซอร์ส (Open-Source License) สำหรับการศึกษาและวิจัยด้านปัญญาประดิษฐ์ในเกมแบบ TTRPG

### 📂 เนื้อหาภายในคลังข้อมูลดิจิทัลประกอบด้วย:
- **ซอร์สโค้ดเอนจินหลัก (Core Engine Source Code):** ระบบการประมวลผลเชิงพิกัดแบบ Zone-Based และสถาปัตยกรรม Two-Path ภายใต้โฟลเดอร์ `src/`
- **ชุดทดสอบประเมินประสิทธิภาพอัตโนมัติ (Automated Comprehensive Evaluation Suite):** รันเนอร์สคริปต์ `comprehensive_runner.py` ภายใต้โฟลเดอร์ `evaluation/system_suite/`
- **ชุดสถานการณ์จำลองระดับการรบ 90 รูปแบบ (Comprehensive 90-Scenario Suite):** ชุดข้อมูลจำลองเชิงลึกในรูปแบบ JSON ผ่านไฟล์ `master_scenario_suite.json` 
- **ข้อมูลประวัติการรันทดสอบประสิทธิภาพจริง (Empirical Evaluation Records):** ไฟล์บันทึกการทำงานอย่างละเอียด `trace_log.json` และไฟล์สถิติสรุปเชิงเวลา/ความแม่นยำแยกหมวดหมู่ `category_summary.csv` ภายใต้โฟลเดอร์ย่อย `results/`

---

## 📁 2. โครงสร้างไฟล์และโมดูลสำคัญในระบบ (System File Structure)
ซอฟต์แวร์ได้รับการออกแบบบนหลักการสถาปัตยกรรมแบ่งส่วนความรับผิดชอบ (Separation of Concerns) ทำให้โค้ดมีความยืดหยุ่น ปลอดภัยสูง และบำรุงรักษาง่าย โดยแยกโมดูลหลักออกเป็นสัดส่วนดังนี้:

```text
AI_Dungeon_Master/
├── data/
│   ├── active/                # จัดเก็บสถานะเซฟเกมและล็อกการกระทำแบบไดนามิก
│   │   ├── campaign_active.json
│   │   └── campaign_log.txt   # บันทึกประวัติการรบแบบเรียลไทม์
│   └── config/                # คอนฟิกูเรชันกลางแยกจากแกนหลักโค้ด
│       ├── bestiary.json      # คลังคุณสมบัติมอนสเตอร์พื้นฐาน
│       └── settings.json      # ตัวควบคุมพารามิเตอร์ของระบบ
├── evaluation/                # สวีตการประเมินผลเชิงลึกและเปรียบเทียบ
│   └── system_suite/
│       ├── comprehensive_runner.py
│       └── master_scenario_suite.json
├── src/                       # ซอร์สโค้ดแกนหลัก (Python)
│   ├── agents/                # ตัวแทนโมเดลปัญญาประดิษฐ์ (Generative Core)
│   │   ├── quest_architect_agent.py   # เอเจนต์วางสตอรี่ธีมด่าน
│   │   ├── quest_cartographer_agent.py# เอเจนต์ขีดแผนที่และทวนสอบ Guardrails 7 ชั้น
│   │   ├── arbiter_agent.py           # ตัวตัดสินการกระทำอิสระและกำหนดค่า DC
│   │   └── dm_narrator_agent.py       # เอเจนต์ถักทอบทบรรยายวรรณศิลป์แฟนตาซี
│   ├── engine/                # แกนกลางและลูปเกมหลัก
│   │   ├── game_loop.py       # ระบบควบคุมอินเตอร์เฟซและสเตตเกม Explore/Combat
│   │   └── startup.py         # บริการวิซาร์ดและติดตั้งค่าเริ่มต้น
│   ├── logic/                 # ตรรกะเชิงกำหนด (Deterministic Rules Engine)
│   │   ├── rules_engine.py    # คำนวณดาเมจ เกราะ AC การโจมตีประชิด/ไกล/หนี ตามกฎ Lite 5e
│   │   ├── enemy_factory.py   # โมเดลสเกล HP/Stats แบบ Skeleton & Flesh
│   │   └── time_manager.py    # คุมความก้าวหน้าเวลาและลอจิกนอนหลับ (Auto-Heal)
│   ├── router/                # ระบบจัดแบ่งเส้นทางคำสั่ง (Intent Routing Layer)
│   │   ├── intent_router.py   # คัดกรองและแบ่งเส้นทาง Path A / Path B
│   │   ├── intents.py         # กำหนดคลาสข้อมูลสเตตและเมทาดาต้า
│   │   └── exploration_router.py # โฮบริดเราเตอร์ (Regex Pass 1, LLM Pass 2)
│   ├── models/                # โครงสร้างคลาสข้อมูลและระบบตัวแปร
│   │   ├── character.py       # นิยาม Toon Data, Recharge, Status
│   │   └── toon_converter.py  # โมดูลถอดและเข้ารหัสออปเจ็กต์เป็นสายอักขระ
│   └── ui/                    # โมดูลการแสดงหน้าจอและ HUD คอนโซล
│       ├── combat_ui.py       # หน้าจอสถานะการรบและการทอยเต๋า
│       └── exploration_ui.py  # หน้าจอสำรวจเมือง แผนที่ และบอร์ดเควสสตรีมไลน์
└── LITE_5E_RULES.md           # คู่มือและเอกสารอ้างอิงกฎเกณฑ์อย่างเป็นทางการ
```

---

## 🛠️ 3. การติดตั้งและข้อกำหนดพื้นฐาน (Installation & Setup)
*   **ภาษาโปรแกรมและสภาพแวดล้อม:** ต้องการ **Python เวอร์ชัน 3.10 ขึ้นไป** 
*   **การตั้งค่ารหัส API (API Key Secure Setup):** เมื่อรันเกมครั้งแรก ระบบจะมีระบบวิซาร์ดช่วยคำแนะนำอัตโนมัติ (Automated Configuration CLI Wizard) เพื่อสร้างไฟล์ความปลอดภัย `.env` และผูกคีย์ของ Gemini Pro / Flash โดยไม่ต้องให้ผู้เล่นทำแมนนวลเองผ่านโฟลเดอร์ภายนอก
*   **การปรับแต่งค่าผ่านศูนย์กลาง (Decoupled Parameters Settings):**
    - พารามิเตอร์ในการจำลองโลกและการทดสอบ เช่น ขนาดบอร์ดภารกิจ (`quest_board_size`), ค่า DC ปริศนาพื้นฐาน (`default_puzzle_dc`), ระบบเจนเควสอัตโนมัติ (`auto_generate_quests`) และจำนวนการลองสร้างแผนที่ใหม่เมื่อตรวจพบ Guardrails ล้มเหลว (`max_quest_gen_retries`) จะถูกจัดการอย่างเป็นระบบผ่านไฟล์ [settings.json](file:///home/mudmini009/AI_Dungeon_Master/data/config/settings.json) ทำให้เปลี่ยนสมดุลของเอนจินได้โดยไม่ต้องแก้ซอร์สโค้ด

---

## 🔍 4. โหมดสำหรับการตรวจสอบและการบันทึกย้อนกลับ (Developer & Traceability Features)
- **Developer Debug Mode:** สวิตช์สถิติดิบที่ฝังไว้ใน CLI (เปิดใช้งานผ่าน settings หรือคำสั่งตั้งค่าเริ่มต้น) ช่วยเปิดเผยข้อมูลเชิงวิศวกรรมที่อยู่เบื้องหลังคำบรรยายของ AI (Under the Hood Visualizer) เช่น ข้อมูลสายอักขระ TOON/JSON ผลลัพธ์การทอยเต๋าจริงของเครื่องยนต์ และ Intent Classifier เพื่อยืนยันความโปร่งใสของระบบการตัดสินใจ
- **Persistent Campaign Log:** เมื่อเริ่มการรณรงค์ ทุกการสื่อสารจาก DM การทอยลูกเต๋าเชิงฟิสิกส์ และคำสั่งการต่อสู้จะถูกบันทึกเป็นคลังประวัติแบบเรียลไทม์ไว้ในไฟล์ [campaign_log.txt](file:///home/mudmini009/AI_Dungeon_Master/data/active/campaign_log.txt) ทำให้ผู้วิจัยสามารถดึงข้อมูลประวัติการรันและนำไปประกอบการทำบทวิจัยหรือทวนสอบย้อนกลับ (Dungeon Master Auditing) ได้อย่างสมบูรณ์แบบ
