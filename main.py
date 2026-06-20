from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


# =========================
# 📤 ارسال پیام
# =========================
def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)

    requests.post(url, json=payload)


# =========================
# 🧠 قرارداد استاندارد فرمول‌ها
# =========================
def out(name, score, confidence=0.8, details=""):
    return {
        "name": name,
        "score": float(score),
        "confidence": float(confidence),
        "details": details
    }


# =========================
# 🧮 فرمول‌ها (طبق اجماع)
# =========================
def abjad(data):
    return out("abjad", 72, 0.85, "abjad calc")


def taksir(data):
    return out("taksir", 80, 0.9, "taksir calc")


def bast(data):
    return out("bast", 60, 0.75, "bast calc")


def jafar(data):
    return out("jafar", 70, 0.8, "jafar calc")


def awfaq(data):
    return out("awfaq", 65, 0.7, "awfaq calc")


# =========================
# ⚙️ موتور وزن‌دهی (Consensus Engine)
# =========================
def engine(results):

    weights = {
        "abjad": 0.30,
        "taksir": 0.25,
        "bast": 0.20,
        "jafar": 0.15,
        "awfaq": 0.10
    }

    total = 0
    wsum = 0

    for r in results:
        w = weights.get(r["name"], 0.05)
        w = w * (0.5 + r["confidence"])  # وزن پویا

        total += r["score"] * w
        wsum += w

    final_score = total / wsum if wsum else 0

    if final_score >= 80:
        status = "خیلی قوی"
    elif final_score >= 60:
        status = "قوی"
    elif final_score >= 40:
        status = "متوسط"
    else:
        status = "ضعیف"

    return {
        "final_score": round(final_score, 2),
        "status": status
    }


# =========================
# 🧠 موتور تحلیل اصلی
# =========================
def analyze(data):

    results = [
        abjad(data),
        taksir(data),
        bast(data),
        jafar(data),
        awfaq(data)
    ]

    final = engine(results)

    return final


# =========================
# 💳 منوها (سیستم پولی تستی)
# =========================
def start_menu():
    return {
        "inline_keyboard": [
            [{"text": "💳 پرداخت و شروع تحلیل", "callback_data": "pay"}]
        ]
    }


def pay_menu():
    return {
        "inline_keyboard": [
            [{"text": "💳 پرداخت 50,000 تومان (تست)", "callback_data": "pay_50000"}]
        ]
    }


def bottom_menu():
    return {
        "keyboard": [
            ["🔍 شروع تحلیل", "📂 تاریخچه تحلیل‌ها"],
            ["📖 درباره سامانه", "📜 قوانین"]
        ],
        "resize_keyboard": True
    }


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


    # =========================
    # پیام‌ها
    # =========================
    if "message" in update:

        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "سلام 👋 به سامانه تحلیل خوش آمدید", start_menu())

        elif text == "🔍 شروع تحلیل":
            send_message(chat_id, "نام و نام مادر را ارسال کن")

        elif text == "📂 تاریخچه تحلیل‌ها":
            send_message(chat_id, "فعلاً تاریخچه خالی است")

        elif text == "📖 درباره سامانه":
            send_message(chat_id, "سیستم تحلیل عددی و ساختاری")

        elif text == "📜 قوانین":
            send_message(chat_id, "استفاده مسئولیت کاربر است")

        else:
            data = {"input": text}
            result = analyze(data)

            send_message(
                chat_id,
                f"""
📊 نتیجه تحلیل

امتیاز نهایی: {result['final_score']}
وضعیت: {result['status']}
"""
            )


    # =========================
    # پرداخت (TEST MODE = همیشه آزاد)
    # =========================
    elif "callback_query" in update:

        chat_id = update["callback_query"]["from"]["id"]
        data = update["callback_query"]["data"]

        if data == "pay":
            send_message(chat_id, "💳 حالت تست: پرداخت فعال شد", pay_menu())

        elif data == "pay_50000":
            # ⚠️ TEST MODE: همیشه اجازه ورود می‌دهد
            send_message(chat_id, "✅ پرداخت تستی موفق بود", bottom_menu())

    return "ok", 200


# =========================
# 🚀 اجرا
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
