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


def get_main_menu():
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


def get_user_menu():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "🔍 شروع تحلیل",
                    "callback_data": "analysis"
                }
            ],
            [
                {
                    "text": "📖 درباره سامانه",
                    "callback_data": "about"
                },
                {
                    "text": "📚 منابع سامانه",
                    "callback_data": "sources"
                }
            ],
            [
                {
                    "text": "❓ راهنما",
                    "callback_data": "help"
                },
                {
                    "text": "📜 قوانین",
                    "callback_data": "rules"
                }
            ],
            [
                {
                    "text": "☎️ پشتیبانی",
                    "callback_data": "support"
                }
            ]
        ]
    }


@app.route("/")
def home():
    return "Bot is running", 200


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
                WELCOME_TEXT,
                get_main_menu()
            )

    elif "callback_query" in update:

        chat_id = update["callback_query"]["from"]["id"]
        data = update["callback_query"]["data"]

        if data == "payment":

            send_message(
                chat_id,
                """
💳 هزینه دسترسی

مبلغ: 50,000 تومان

پس از پرداخت، امکان انجام یک تحلیل کامل
برای یک فرد از تمامی بخش‌های سامانه
فعال خواهد شد.
                """,
                get_payment_menu()
            )

        elif data == "pay_50000":

            send_message(
                chat_id,
                """
✅ پرداخت با موفقیت ثبت شد.

به سامانه خوش آمدید.
لطفاً یکی از گزینه‌های زیر را انتخاب نمایید.
                """,
                get_user_menu()
            )

        elif data == "analysis":

            send_message(
                chat_id,
                "🔍 لطفاً نام و نام خانوادگی فرد مورد نظر را ارسال نمایید."
            )

        elif data == "about":

            send_message(
                chat_id,
                "📖 این سامانه برای گردآوری و تحلیل اطلاعات منابع تخصصی طراحی شده است."
            )

        elif data == "sources":

            send_message(
                chat_id,
                "📚 اطلاعات این سامانه بر پایه منابع تخصصی و نسخه‌های قدیمی گردآوری شده است."
            )

        elif data == "help":

            send_message(
                chat_id,
                "❓ برای شروع، گزینه «شروع تحلیل» را انتخاب نمایید."
            )

        elif data == "rules":

            send_message(
                chat_id,
                "📜 استفاده از سامانه به منزله پذیرش قوانین و شرایط استفاده است."
            )

        elif data == "support":

            send_message(
                chat_id,
                "☎️ بخش پشتیبانی در نسخه‌های بعدی فعال خواهد شد."
            )

    return "ok", 200


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
