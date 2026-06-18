from flask import Flask, request
import requests
import json

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
            [{"text": "🔮 شروع پیشگویی", "callback_data": "start_fortune"}],
            [{"text": "📖 راهنما", "callback_data": "help"}]
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
            send_message(chat_id, "🔮 به ربات جفر خوش آمدی!\n\nلطفاً یکی از گزینه‌ها رو انتخاب کن:", get_main_menu())
        else:
            send_message(chat_id, f"📩 پیام شما: {text}\n\nاز منو استفاده کنید.")
    
    elif 'callback_query' in update:
        chat_id = update['callback_query']['from']['id']
        data = update['callback_query']['data']
        
        if data == 'start_fortune':
            send_message(chat_id, "🔮 در حال پیشگویی...\n\nاین بخش به زودی تکمیل میشه.")
        elif data == 'help':
            send_message(chat_id, "📖 راهنما:\n\n/start - منوی اصلی\n\nاین ربات برای پیشگویی با جفر طراحی شده.")
    
    return "ok", 200

@app.route('/')
def home():
    return "ربات جفر فعال است", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
