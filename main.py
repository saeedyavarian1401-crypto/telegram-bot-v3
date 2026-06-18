from flask import Flask, request
import requests
import json
ا
app = Flask(__name__)

TOKEN = "8624726972:AAHa89X4pWrLaD7c-GI3OUjmx7FuSL-5pQQ"

def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)
    requests.post(url, json=payload)

def get_main_menu():
    return {
        "inline_keyboard": [
            [{"text": "💳 پرداخت و شروع تحلیل", "callback_data": "payment"}]
        ]
    }

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if not update:
        return "ok", 200
    
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        if text == '/start':
            send_message(chat_id, """
📚 سامانه جامع مطالعات علوم سنتی

این سامانه بر پایه هزاران منبع خطی، سنگی و نسخه‌های قدیمی
طراحی شده است.

هدف از ایجاد این مجموعه، گردآوری و تحلیل اطلاعات پراکنده
در منابع مختلف و ارائه نتیجه‌ای منظم و یکپارچه است.

برای استفاده از سامانه ابتدا هزینه دسترسی را پرداخت نمایید.
""", get_main_menu())
    
    elif 'callback_query' in update:
        chat_id = update['callback_query']['from']['id']
        data = update['callback_query']['data']
        if data == 'payment':
            send_message(chat_id, "💳 درگاه پرداخت در مرحله بعد متصل خواهد شد.")
    
    return "ok", 200

@app.route('/')
def home():
    return "ربات فعال است", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "8624726972:AAHa89X4pWrLaD7c-GI3OUjmx7FuSL-5pQQ"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if not update:
        return "ok", 200
    
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        
        if text == '/start':
            send_message(chat_id, "سلام! ربات فعال است.")
        else:
            send_message(chat_id, f"پیام شما: {text}")
    
    return "ok", 200

@app.route('/')
def home():
    return "ربات فعال است", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
