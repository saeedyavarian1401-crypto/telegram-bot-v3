from flask import Flask, request
import requests
import json
import os
import re
import asyncio
from datetime import datetime

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = "226168396"

# =========================
# 📤 ارسال پیام
# =========================
def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)
    requests.post(url, json=payload)

def send_message_async(chat_id, text, keyboard=None):
    """نسخه async برای استفاده در تابع analyze"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)
    requests.post(url, json=payload)

# =========================
# 📋 منوی آبی (Command Menu)
# =========================
def set_commands():
    url = f"https://api.telegram.org/bot{TOKEN}/setMyCommands"
    commands = [
        {"command": "start", "description": "🔄 شروع مجدد"},
        {"command": "analyze", "description": "🔍 شروع تحلیل جدید"},
        {"command": "history", "description": "📂 تاریخچه تحلیل‌ها"},
        {"command": "rules", "description": "📜 قوانین"},
        {"command": "about", "description": "📖 درباره سامانه"},
        {"command": "contact", "description": "📩 تماس با ادمین"}
    ]
    requests.post(url, json={"commands": commands})

def cancel_keyboard():
    return {
        "keyboard": [["❌ لغو"]],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }

# =========================
# 🧠 مدیریت اطلاعات کاربر
# =========================
user_data = {}

def process_analysis(chat_id, text):
    if chat_id not in user_data:
        return

    step = user_data[chat_id].get("step")

    if step == "name":
        user_data[chat_id]["name"] = text
        user_data[chat_id]["step"] = "mother"
        send_message(chat_id, "👩 لطفاً **نام مادر** خود را وارد کنید:")

    elif step == "mother":
        user_data[chat_id]["mother"] = text
        user_data[chat_id]["step"] = "birthdate"
        send_message(chat_id, "📅 لطفاً **تاریخ تولد** خود را وارد کنید (مثلاً ۱۵/۶/۱۳۷۵):")

    elif step == "birthdate":
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', text):
            day, month, year = text.split('/')
            user_data[chat_id]["day"] = int(day)
            user_data[chat_id]["month"] = int(month)
            user_data[chat_id]["year"] = int(year)
            user_data[chat_id]["step"] = "question"
            send_message(chat_id, "❓ **سوال** خود را بپرسید:")
        else:
            send_message(chat_id, "❌ فرمت تاریخ اشتباه است. لطفاً به صورت **روز/ماه/سال** وارد کنید (مثلاً ۱۵/۶/۱۳۷۵):")

    elif step == "question":
        user_data[chat_id]["question"] = text
        # اجرای تحلیل به صورت async
        asyncio.run(run_analysis_async(chat_id, user_data[chat_id]))
        del user_data[chat_id]

    elif step == "contact_message":
        send_message(
            ADMIN_CHAT_ID,
            f"📩 پیام جدید از کاربر {chat_id}:\n\n{text}"
        )
        send_message(
            chat_id,
            "✅ پیام شما به ادمین ارسال شد. به زودی پاسخ داده می‌شود."
        )
        del user_data[chat_id]

# =========================
# 🧮 فرهنگ ابجد
# =========================
ABJAD = {
    'ا':1, 'ب':2, 'ج':3, 'د':4, 'ه':5, 'و':6, 'ز':7, 'ح':8, 'ط':9, 'ی':10,
    'ک':20, 'ل':30, 'م':40, 'ن':50, 'س':60, 'ع':70, 'ف':80, 'ص':90, 'ق':100,
    'ر':200, 'ش':300, 'ت':400, 'ث':500, 'خ':600, 'ذ':700, 'ض':800, 'ظ':900, 'غ':1000,
    'پ':2, 'چ':3, 'ژ':7, 'گ':20, 'آ':1, 'أ':1, 'إ':1, 'ة':5, 'ى':10, 'ئ':10, 'ؤ':6
}

def abjad_sum(word):
    if not word:
        return 0
    return sum(ABJAD.get(ch, 1) for ch in word)

# =========================
# برج فلکی و عناصر
# =========================
ZODIAC = [
    {"name": "حمل", "element": "آتشی", "planet": "مریخ", "stone": "یاقوت سرخ", "start": (21, 3), "end": (19, 4)},
    {"name": "ثور", "element": "خاکی", "planet": "زهره", "stone": "زمرد", "start": (20, 4), "end": (20, 5)},
    {"name": "جوزا", "element": "بادی", "planet": "عطارد", "stone": "عقیق", "start": (21, 5), "end": (20, 6)},
    {"name": "سرطان", "element": "آبی", "planet": "ماه", "stone": "مروارید", "start": (21, 6), "end": (22, 7)},
    {"name": "اسد", "element": "آتشی", "planet": "خورشید", "stone": "یاقوت زرد", "start": (23, 7), "end": (22, 8)},
    {"name": "سنبله", "element": "خاکی", "planet": "عطارد", "stone": "زبرجد", "start": (23, 8), "end": (22, 9)},
    {"name": "میزان", "element": "بادی", "planet": "زهره", "stone": "عقیق", "start": (23, 9), "end": (22, 10)},
    {"name": "عقرب", "element": "آبی", "planet": "مریخ", "stone": "یاقوت کبود", "start": (23, 10), "end": (21, 11)},
    {"name": "قوس", "element": "آتشی", "planet": "مشتری", "stone": "فیروزه", "start": (22, 11), "end": (21, 12)},
    {"name": "جدی", "element": "خاکی", "planet": "زحل", "stone": "یشم", "start": (22, 12), "end": (19, 1)},
    {"name": "دلو", "element": "بادی", "planet": "زحل", "stone": "لاجورد", "start": (20, 1), "end": (18, 2)},
    {"name": "حوت", "element": "آبی", "planet": "مشتری", "stone": "سنگ ماه", "start": (19, 2), "end": (20, 3)}
]

def get_zodiac_info(day, month, year):
    try:
        import jdatetime
        greg = jdatetime.date(year, month, day).togregorian()
        g_month, g_day = greg.month, greg.day
    except:
        g_month, g_day = month, day
    
    for z in ZODIAC:
        s_day, s_month = z["start"]
        e_day, e_month = z["end"]
        if s_month > e_month:
            if (g_month == s_month and g_day >= s_day) or (g_month == e_month and g_day <= e_day):
                return z
        else:
            if (g_month == s_month and g_day >= s_day) or (g_month == e_month and g_day <= e_day):
                return z
    return ZODIAC[0]

# =========================
# معادن و کواکب
# =========================
MINERALS = {
    "شمس": {"metal": "طلا", "plant": "صندل", "animal": "شیر", "incense": "عود", "color": "زرد"},
    "قمر": {"metal": "نقره", "plant": "کافور", "animal": "فیل", "incense": "قسط أبيض", "color": "سفید"},
    "مریخ": {"metal": "مس", "plant": "فلفل", "animal": "پلنگ", "incense": "فلفل", "color": "قرمز"},
    "عطارد": {"metal": "زئبق", "plant": "ریحان", "animal": "کبوتر", "incense": "شمع أبيض", "color": "آبی"},
    "مشتری": {"metal": "قلع", "plant": "لبان", "animal": "گاو", "incense": "لبان أبيض", "color": "سبز"},
    "زهره": {"metal": "مس قرمز", "plant": "گلاب", "animal": "کبوتر", "incense": "مسک", "color": "صورتی"},
    "زحل": {"metal": "سرب", "plant": "بنفشه", "animal": "خفاش", "incense": "صمغ أسود", "color": "سیاه"}
}

def get_mineral(planet):
    return MINERALS.get(planet, {"metal": "نامشخص", "plant": "نامشخص", "animal": "نامشخص", "incense": "نامشخص", "color": "نامشخص"})

# =========================
# جفر ۳۶ و ۳۶۰
# =========================
def jafar_36(question):
    total = abjad_sum(question)
    remainder = total % 36
    return {
        "total": total,
        "remainder": remainder,
        "answer": "✅ بله - با احتمال زیاد" if remainder <= 9 else "❌ خیر - مشکل دارد" if remainder > 27 else "⚠️ بله - با احتیاط" if remainder <= 18 else "❓ شاید - مصلحت نیست",
        "score": 85 if remainder <= 9 else 30 if remainder > 27 else 65 if remainder <= 18 else 50,
        "advice": "مانعی نیست، اقدام کن" if remainder <= 9 else "بهتر است منصرف شوید" if remainder > 27 else "صدقه بدهید و توکل کنید" if remainder <= 18 else "چند روز صبر کنید"
    }

def jafar_360(question, name, mother):
    total = abjad_sum(question) + abjad_sum(name) + abjad_sum(mother)
    remainder = total % 360
    return {
        "total": total,
        "remainder": remainder,
        "answer": "✅ بله قطعی - گشایش بزرگ" if remainder < 30 else "✅ بله - موفقیت" if remainder < 90 else "⚠️ احتمالاً - با تلاش" if remainder < 150 else "❓ شاید - صبر کن" if remainder < 210 else "❌ خیر - مانع داره" if remainder < 270 else "❌ خیر قطعی - مشکل داره",
        "score": 98 if remainder < 30 else 85 if remainder < 90 else 65 if remainder < 150 else 50 if remainder < 210 else 35 if remainder < 270 else 20,
        "degree": "عالی" if remainder < 30 else "خوب" if remainder < 90 else "متوسط" if remainder < 150 else "متوسط" if remainder < 210 else "ضعیف" if remainder < 270 else "خیلی ضعیف",
        "advice": "بدون تردید اقدام کن" if remainder < 30 else "زمان مناسبه، اقدام کن" if remainder < 90 else "تلاش بیشتری کن" if remainder < 150 else "فعلاً صبر کن" if remainder < 210 else "بهتره منصرف شی" if remainder < 270 else "اصلاً مناسب نیست"
    }

# =========================
# رمل ۸ و ۱۶ شکل
# =========================
RAML_8 = {
    "اطلال": {"sign": "⚪⚪⚪⚪", "meaning": "رفتن و از دست دادن", "good": False},
    "نقا": {"sign": "⚪⚪⚪⚫", "meaning": "نقص و کمبود", "good": False},
    "عقله": {"sign": "⚪⚪⚫⚪", "meaning": "عقل و تدبیر", "good": True},
    "بید": {"sign": "⚪⚪⚫⚫", "meaning": "محبت", "good": True},
    "سعاده": {"sign": "⚪⚫⚪⚪", "meaning": "خوشبختی", "good": True},
    "رجل": {"sign": "⚪⚫⚪⚫", "meaning": "مردانگی", "good": True},
    "نصر": {"sign": "⚫⚪⚫⚪", "meaning": "پیروزی", "good": True},
    "ثابت": {"sign": "⚫⚫⚫⚫", "meaning": "ثبات", "good": True}
}

RAML_16 = {
    "اطلال": {"sign": "⚪⚪⚪⚪", "meaning": "رفتن و از دست دادن", "good": False},
    "منقاد": {"sign": "⚪⚪⚪⚫", "meaning": "فرمانبردار", "good": True},
    "انفراد": {"sign": "⚪⚪⚫⚪", "meaning": "تنهایی", "good": False},
    "اتصال": {"sign": "⚪⚪⚫⚫", "meaning": "ارتباط", "good": True},
    "فتح": {"sign": "⚪⚫⚪⚪", "meaning": "گشایش", "good": True},
    "نصر": {"sign": "⚪⚫⚪⚫", "meaning": "پیروزی", "good": True},
    "سعادت": {"sign": "⚪⚫⚫⚪", "meaning": "خوشبختی", "good": True},
    "عاقبت": {"sign": "⚪⚫⚫⚫", "meaning": "پایان", "good": False},
    "زیاده": {"sign": "⚫⚪⚪⚪", "meaning": "افزایش", "good": True},
    "نقصان": {"sign": "⚫⚪⚪⚫", "meaning": "کمبود", "good": False},
    "اجتماع": {"sign": "⚫⚪⚫⚪", "meaning": "جمع شدن", "good": True},
    "افتراق": {"sign": "⚫⚪⚫⚫", "meaning": "جدایی", "good": False},
    "جذب": {"sign": "⚫⚫⚪⚪", "meaning": "جذب", "good": True},
    "دفع": {"sign": "⚫⚫⚪⚫", "meaning": "دفع", "good": False},
    "نور": {"sign": "⚫⚫⚫⚪", "meaning": "روشنایی", "good": True},
    "ظلمت": {"sign": "⚫⚫⚫⚫", "meaning": "تاریکی", "good": False}
}

def raml_extract(name, use_16=False):
    total = abjad_sum(name)
    raml_dict = RAML_16 if use_16 else RAML_8
    keys = list(raml_dict.keys())
    shape_key = keys[total % len(keys)]
    shape = raml_dict[shape_key]
    return {"shape": shape_key, "sign": shape["sign"], "meaning": shape["meaning"], "good": shape["good"]}

# =========================
# همزاد
# =========================
HAMZAD_SYMPTOMS = [
    "تنگی رزق", "عصبانیت بی‌دلیل", "کم شدن آرامش", "افکار منفی",
    "ترس از تاریکی", "گره در امورات", "افسردگی", "باردار نشدن",
    "بیماری‌های جسمی", "ریزش مو", "بستگی بخت", "بدبیاری متوالی"
]

def check_hamzad(symptoms):
    matched = [s for s in symptoms if s in HAMZAD_SYMPTOMS]
    severity = "شدید" if len(matched) >= 8 else "متوسط" if len(matched) >= 4 else "ضعیف" if len(matched) >= 1 else "هیچ"
    return {"has_hamzad": len(matched) >= 4, "matched_symptoms": matched, "severity": severity, "advice": "آیت الکرسی و سوره فلق و ناس را بخوانید"}

def hamzad_name(name):
    total = abjad_sum(name)
    letters = list(name)
    return {"malaki": ''.join(letters[:5]) + "اییل" if len(letters) >= 5 else ''.join(letters) + "اییل", "jinni": ''.join(letters[-5:]) + "ؤش" if len(letters) >= 5 else ''.join(letters) + "ؤش", "total": total}

# =========================
# زایجه عدل
# =========================
def zayejah_adl(question, day, hour=None):
    if hour is None:
        hour = datetime.now().hour
    total = abjad_sum(question)
    hour_type = 3 if hour % 2 == 1 else 4
    main_num = total + day + hour_type
    remainder = main_num % 4
    tabaye = {1: "آتش", 2: "خاک", 3: "هوا", 0: "آب"}
    interpretations = {"آتش": "خیر و برکت با سرعت", "خاک": "پایداری با صبر", "هوا": "گشایش با کمک", "آب": "آرامش با احساسات"}
    return {"tab": tabaye[remainder], "text": interpretations[tabaye[remainder]], "remainder": remainder}

# =========================
# اوقات سعد و نحس
# =========================
def get_saad_nahs(day, month, year):
    lunar_day = (day + month) % 30 + 1
    lunar_month = (month + year) % 12 + 1
    saad_list = {
        1: [1,3,5,7,9,11,13], 2: [2,4,6,8,10,12,14],
        3: [1,4,7,10,13,16,19], 4: [3,6,9,12,15,18,21],
        5: [5,10,15,20,25,30], 6: [2,7,12,17,22,27],
        7: [1,8,15,22,29], 8: [2,9,16,23,30],
        9: [1,4,7,10,13,16,19,22], 10: [3,6,9,12,15,18,21,24],
        11: [5,10,15,20,25,30], 12: [2,7,12,17,22,27]
    }
    saad = saad_list.get(lunar_month, [])
    return {"lunar_day": lunar_day, "is_saad": lunar_day in saad, "status": "سعد" if lunar_day in saad else "نحس"}

# =========================
# تکسیر و بسط
# =========================
def taksir_correct(word):
    if not word:
        return {"lines": [], "zamam": None}
    chars = list(word)
    all_lines = [word]
    current = chars.copy()
    for _ in range(4):
        new_chars = []
        left, right = 0, len(current) - 1
        while left <= right:
            if left == right:
                new_chars.append(current[left])
                break
            new_chars.append(current[left])
            new_chars.append(current[right])
            left += 1
            right -= 1
        new_word = ''.join(new_chars)
        all_lines.append(new_word)
        current = new_chars
        if new_word == word:
            break
    return {"lines": all_lines, "zamam": all_lines[-1] if len(all_lines) > 1 else None}

def basts_azizi(name, mother):
    combined = name + mother
    total_abjad = abjad_sum(combined)
    letters = list(combined)
    malak = ''.join(letters[:5]) + "ائیل" if len(letters) >= 5 else ''.join(letters) + "ائیل"
    awn = ''.join(letters[-5:]) + "وش" if len(letters) >= 5 else ''.join(letters) + "وش"
    return {"malak": malak, "awn": awn, "total_abjad": total_abjad}

# =========================
# 🧠 تحلیل کامل با نمایش مراحل محاسبه (با فاصله ۵ ثانیه)
# =========================
async def run_analysis_async(chat_id, data):
    name = data.get('name', '')
    mother = data.get('mother', '')
    day = data.get('day', 1)
    month = data.get('month', 1)
    year = data.get('year', 1300)
    question = data.get('question', '')
    hour = datetime.now().hour

    # 1️⃣ برج فلکی و عناصر
    zodiac = get_zodiac_info(day, month, year)
    planet = zodiac["planet"]
    element = zodiac["element"]
    mineral = get_mineral(planet)

    life_path = sum(int(d) for d in f"{day}{month}{year}")
    while life_path > 9:
        life_path = sum(int(d) for d in str(life_path))

    # نمایش برج فلکی
    msg = f"""
📊 **مرحله ۱: برج فلکی و عناصر**

📅 تاریخ تولد: {day}/{month}/{year}
🔢 عدد سرنوشت: {life_path}

🌟 برج: {zodiac['name']}
🌍 عنصر: {element}
🪐 سیاره: {planet}
💎 سنگ: {zodiac['stone']}
⚗️ فلز: {mineral['metal']}
🌿 گیاه: {mineral['plant']}
🎨 رنگ: {mineral['color']}
"""
    send_message_async(chat_id, msg)
    await asyncio.sleep(5)

    # 2️⃣ جفر ۳۶
    j36 = jafar_36(question)
    msg = f"""
📊 **مرحله ۲: جفر ۳۶**

📜 سوال: {question}
🧮 محاسبه: ابجد سوال = {j36['total']}
🔢 باقیمانده: {j36['total']} % 36 = {j36['remainder']}

{j36['answer']}
⭐ امتیاز: {j36['score']}/100
💡 توصیه: {j36['advice']}
"""
    send_message_async(chat_id, msg)
    await asyncio.sleep(5)

    # 3️⃣ جفر ۳۶۰
    j360 = jafar_360(question, name, mother)
    msg = f"""
📊 **مرحله ۳: جفر ۳۶۰**

📜 سوال: {question}
👤 نام: {name}
👩 نام مادر: {mother}
🧮 محاسبه: ابجد سوال + ابجد نام + ابجد مادر = {j360['total']}
🔢 باقیمانده: {j360['total']} % 360 = {j360['remainder']}

{j360['answer']}
⭐ امتیاز: {j360['score']}/100
📊 درجه: {j360['degree']}
💡 توصیه: {j360['advice']}
"""
    send_message_async(chat_id, msg)
    await asyncio.sleep(5)

    # 4️⃣ رمل ۸ و ۱۶
    raml8 = raml_extract(name, use_16=False)
    raml16 = raml_extract(name, use_16=True)
    msg = f"""
📊 **مرحله ۴: رمل**

👤 نام: {name}
🧮 محاسبه: ابجد نام = {abjad_sum(name)}

🎲 رمل ۸: {raml8['sign']} → {raml8['meaning']}
🎲 رمل ۱۶: {raml16['sign']} → {raml16['meaning']}
"""
    send_message_async(chat_id, msg)
    await asyncio.sleep(5)

    # 5️⃣ همزاد
    hamzad_names = hamzad_name(name)
    msg = f"""
📊 **مرحله ۵: همزاد**

👤 نام: {name}
🧮 محاسبه: ابجد نام = {abjad_sum(name)}

👹 اسم ملکی: {hamzad_names['malaki']}
👹 اسم جنی: {hamzad_names['jinni']}
"""
    send_message_async(chat_id, msg)
    await asyncio.sleep(5)

    # 6️⃣ تکسیر و بسط
    taksir = taksir_correct(name + mother)
    basts = basts_azizi(name, mother)
    msg = f"""
📊 **مرحله ۶: تکسیر و بسط**

👤 نام: {name}
👩 نام مادر: {mother}

📖 تکسیر (تجزیه): {taksir['zamam'] if taksir['zamam'] else '---'}
📖 بسط (ترکیب): {basts['malak']} - {basts['awn']}
"""
    send_message_async(chat_id, msg)
    await asyncio.sleep(5)

    # 7️⃣ زایجه عدل
    zayejah = zayejah_adl(question, day, hour)
    msg = f"""
📊 **مرحله ۷: زایجه عدل**

❓ سوال: {question}
🕐 ساعت: {hour}
⚗️ طبع: {zayejah['tab']}
💬 تعبیر: {zayejah['text']}
"""
    send_message_async(chat_id, msg)
    await asyncio.sleep(5)

    # 8️⃣ اوقات سعد و نحس
    saad_nahs = get_saad_nahs(day, month, year)
    msg = f"""
📊 **مرحله ۸: اوقات سعد و نحس**

📅 روز قمری: {saad_nahs['lunar_day']}
⏰ وضعیت: {saad_nahs['status']}
"""
    send_message_async(chat_id, msg)
    await asyncio.sleep(5)

    # 9️⃣ توصیه نهایی
    msg = f"""
📊 **توصیه نهایی**

💡 {j36['advice']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ تحلیل کامل شد!
"""
    send_message_async(chat_id, msg)

# =========================
# 🌐 روت‌ها
# =========================
@app.route("/")
def home():
    return "Bot Running", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update:
        return "ok", 200

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text == "/start":
            send_message(
                chat_id,
                """
📜 سامانه تخصصی تحلیل

این سامانه بر پایه منابع معتبر، نسخه‌های خطی و متون تخصصی گردآوری شده است.

جهت ورود به بخش تحلیل و بررسی اطلاعات، ادامه فرایند را انتخاب نمایید.
"""
            )

        elif text == "/analyze":
            user_data[chat_id] = {"step": "name"}
            send_message(chat_id, "👤 لطفاً **نام** خود را وارد کنید:")

        elif text == "/history":
            send_message(chat_id, "📂 هنوز تحلیلی ثبت نشده است.")

        elif text == "/rules":
            send_message(
                chat_id,
                """
📜 قوانین استفاده

۱. استفاده از این سامانه به منزله پذیرش کامل قوانین و شرایط آن است.

۲. اطلاعات وارد شده توسط کاربر، صرفاً برای انجام تحلیل استفاده می‌شود و هیچگونه اطلاعات شخصی ذخیره نمی‌گردد.

۳. نتایج تحلیل صرفاً جنبه پژوهشی و اطلاع‌رسانی دارد.
"""
            )

        elif text == "/about":
            send_message(
                chat_id,
                """
📖 درباره سامانه

این سامانه با هدف افزایش آگاهی کاربران و جلوگیری از هرگونه سوءاستفاده احتمالی توسط افراد سودجو و شیاد طراحی و راه‌اندازی شده است.

هدف اصلی این مجموعه، فراهم کردن بستری برای ثبت، نگهداری و بررسی اطلاعات در محیطی منظم و یکپارچه است تا کاربران بتوانند با دسترسی آسان به سوابق و اطلاعات مورد نیاز خود، تصمیمات آگاهانه‌تری اتخاذ نمایند.
"""
            )

        elif text == "/contact":
            user_data[chat_id] = {"step": "contact_message"}
            send_message(
                chat_id,
                "✏️ لطفاً **پیام خود** را برای ادمین بنویسید:",
                cancel_keyboard()
            )

        else:
            process_analysis(chat_id, text)

    return "ok", 200

# =========================
# 🚀 اجرا
# =========================
if __name__ == "__main__":
    set_commands()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
