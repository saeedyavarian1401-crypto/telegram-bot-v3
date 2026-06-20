from flask import Flask, request
import requests
import json
import os
import re

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = "226168396"  # آیدی عددی خودت

# =========================
# 📤 ارسال پیام
# =========================
def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)
    requests.post(url, json=payload)

# =========================
# 📋 منوی شیشه‌ای
# =========================
def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "🔍 شروع تحلیل", "callback_data": "start_analysis"}],
            [{"text": "💳 پرداخت (نمایشی)", "callback_data": "payment_demo"}],
            [{"text": "📖 درباره سامانه", "callback_data": "about"}],
            [{"text": "📂 تاریخچه تحلیل‌ها", "callback_data": "history"}],
            [{"text": "📜 قوانین", "callback_data": "rules"}],
            [{"text": "📩 تماس با ادمین", "callback_data": "contact_admin"}]
        ]
    }

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
        result = analyze(user_data[chat_id])
        send_message(chat_id, f"""
📊 نتیجه تحلیل

👤 نام: {user_data[chat_id]['name']}
👩 نام مادر: {user_data[chat_id]['mother']}
📅 تاریخ تولد: {user_data[chat_id]['day']}/{user_data[chat_id]['month']}/{user_data[chat_id]['year']}
❓ سوال: {user_data[chat_id]['question']}

امتیاز نهایی: {result['final_score']}
وضعیت: {result['status']}
""")
        del user_data[chat_id]

    elif step == "contact_message":
        # ارسال پیام کاربر به ادمین
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
# 🧠 فرمول‌ها
# =========================
def out(name, score, confidence=0.8, details=""):
    return {"name": name, "score": float(score), "confidence": float(confidence), "details": details}

def abjad(data):   return out("abjad", 72, 0.85, "abjad calc")
def taksir(data):  return out("taksir", 80, 0.9, "taksir calc")
def bast(data):    return out("bast", 60, 0.75, "bast calc")
def jafar(data):   return out("jafar", 70, 0.8, "jafar calc")
def awfaq(data):   return out("awfaq", 65, 0.7, "awfaq calc")

def engine(results):
    weights = {"abjad": 0.30, "taksir": 0.25, "bast": 0.20, "jafar": 0.15, "awfaq": 0.10}
    total = 0
    wsum = 0
    for r in results:
        w = weights.get(r["name"], 0.05) * (0.5 + r["confidence"])
        total += r["score"] * w
        wsum += w
    final_score = total / wsum if wsum else 0
    if final_score >= 80:   status = "خیلی قوی"
    elif final_score >= 60: status = "قوی"
    elif final_score >= 40: status = "متوسط"
    else:                   status = "ضعیف"
    return {"final_score": round(final_score, 2), "status": status}

def analyze(data):
    results = [abjad(data), taksir(data), bast(data), jafar(data), awfaq(data)]
    return engine(results)

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
""",
                main_menu()
            )
        else:
            process_analysis(chat_id, text)

    elif "callback_query" in update:
        chat_id = update["callback_query"]["from"]["id"]
        data = update["callback_query"]["data"]

        if data == "start_analysis":
            user_data[chat_id] = {"step": "name"}
            send_message(chat_id, "👤 لطفاً **نام** خود را وارد کنید:")

        elif data == "payment_demo":
            send_message(chat_id, "💳 درگاه پرداخت به زودی فعال خواهد شد.")

        elif data == "about":
            send_message(
                chat_id,
                """
📖 درباره سامانه

این سامانه با هدف افزایش آگاهی کاربران و جلوگیری از هرگونه سوءاستفاده احتمالی توسط افراد سودجو و شیاد طراحی و راه‌اندازی شده است.

هدف اصلی این مجموعه، فراهم کردن بستری برای ثبت، نگهداری و بررسی اطلاعات در محیطی منظم و یکپارچه است تا کاربران بتوانند با دسترسی آسان به سوابق و اطلاعات مورد نیاز خود، تصمیمات آگاهانه‌تری اتخاذ نمایند.
"""
            )

        elif data == "history":
            send_message(chat_id, "📂 هنوز تحلیلی ثبت نشده است.")

        elif data == "rules":
            send_message(
                chat_id,
                """
📜 قوانین استفاده

۱. استفاده از این سامانه به منزله پذیرش کامل قوانین و شرایط آن است.

۲. اطلاعات وارد شده توسط کاربر، صرفاً برای انجام تحلیل استفاده می‌شود و هیچگونه اطلاعات شخصی ذخیره نمی‌گردد.

۳. نتایج تحلیل صرفاً جنبه پژوهشی و اطلاع‌رسانی دارد.
"""
            )

        elif data == "contact_admin":
            user_data[chat_id] = {"step": "contact_message"}
            send_message(
                chat_id,
                "✏️ لطفاً **پیام خود** را برای ادمین بنویسید:",
                cancel_keyboard()
            )

    return "ok", 200

# =========================
# 🚀 اجرا
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
