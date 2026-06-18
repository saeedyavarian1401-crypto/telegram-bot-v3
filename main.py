from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

WELCOME_TEXT = """
📜 سامانه تخصصی تحلیل

این سامانه بر پایه منابع معتبر، نسخه‌های خطی و متون تخصصی گردآوری شده است.

جهت ورود به بخش تحلیل و بررسی اطلاعات، ادامه فرایند را انتخاب نمایید.
"""


def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)

    requests.post(url, json=payload)


def get_start_menu():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "💳 پرداخت و شروع تحلیل",
                    "callback_data": "payment"
                }
            ]
        ]
    }


def get_payment_menu():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "💳 پرداخت 50,000 تومان",
                    "callback_data": "pay_50000"
                }
            ]
        ]
    }


def get_bottom_menu():
    return {
        "keyboard": [
            ["🔍 شروع تحلیل"],
            ["📖 درباره سامانه", "📚 منابع سامانه"],
            ["❓ راهنما", "📜 قوانین"],
            ["☎️ پشتیبانی"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


@app.route("/")
def home():
    return "Bot is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():

    update = request.get_json()

    if not update:
        return "ok", 200

    # پیام‌های کاربر
    if "message" in update:

        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text == "/start":

            send_message(
                chat_id,
                WELCOME_TEXT,
                get_start_menu()
            )

        elif text == "🔍 شروع تحلیل":

            send_message(
                chat_id,
                "🔍 لطفاً نام و نام خانوادگی فرد مورد نظر را ارسال نمایید."
            )

        elif text == "📖 درباره سامانه":

            send_message(
                chat_id,
                """
📖 درباره سامانه

این سامانه با هدف گردآوری، دسته‌بندی و بررسی منابع تخصصی طراحی شده است.
                """
            )

        elif text == "📚 منابع سامانه":

            send_message(
                chat_id,
                """
📚 منابع سامانه

اطلاعات سامانه از مجموعه‌ای از منابع تخصصی و نسخه‌های قدیمی گردآوری شده است.
                """
            )

        elif text == "❓ راهنما":

            send_message(
                chat_id,
                """
❓ راهنما

برای شروع فرایند، گزینه «شروع تحلیل» را انتخاب نمایید.
                """
            )

        elif text == "📜 قوانین":

            send_message(
                chat_id,
                """
📜 قوانین استفاده

استفاده از سامانه به منزله پذیرش شرایط و قوانین آن است.
                """
            )

        elif text == "☎️ پشتیبانی":

            send_message(
                chat_id,
                """
☎️ پشتیبانی

بخش پشتیبانی به زودی فعال خواهد شد.
                """
            )

    # دکمه‌های پرداخت
    elif "callback_query" in update:

        chat_id = update["callback_query"]["from"]["id"]
        data = update["callback_query"]["data"]

        if data == "payment":

            send_message(
                chat_id,
                """
💳 هزینه دسترسی

مبلغ: 50,000 تومان

پس از پرداخت، دسترسی کامل به بخش تحلیل فعال خواهد شد.
                """,
                get_payment_menu()
            )

        elif data == "pay_50000":

            send_message(
                chat_id,
                """
✅ پرداخت با موفقیت ثبت شد.

به سامانه خوش آمدید.
                """,
                get_bottom_menu()
            )

    return "ok", 200


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
