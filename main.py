# ==================== main.py - ربات تصویرسازی با FLUX (Replicate) ====================

from flask import Flask, request, jsonify
import requests
from datetime import datetime
import json
import logging
import os
import sqlite3
from contextlib import contextmanager
import time
from typing import Dict, Optional, List

# ==================== تنظیمات اولیه ====================
app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8624726972:AAHa89X4pWrLaD7c-GI3OUjmx7FuSL-5pQQ')
REPLICATE_API_TOKEN = os.environ.get('REPLICATE_API_TOKEN', '')

# ==================== دیتابیس ====================
class Database:
    def __init__(self, db_path='flux_bot.db'):
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    chat_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_images INTEGER DEFAULT 0
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS image_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT,
                    prompt TEXT,
                    image_url TEXT,
                    model TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    chat_id TEXT PRIMARY KEY,
                    step TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            logger.info("✅ دیتابیس راه‌اندازی شد")
    
    def get_user(self, chat_id: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            result = conn.execute('SELECT * FROM users WHERE chat_id = ?', (chat_id,)).fetchone()
            return dict(result) if result else None
    
    def create_user(self, chat_id: str, username: str = '', first_name: str = '', last_name: str = ''):
        with self.get_connection() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO users (chat_id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
                (chat_id, username, first_name, last_name)
            )
            conn.commit()
    
    def increment_images(self, chat_id: str):
        with self.get_connection() as conn:
            conn.execute('UPDATE users SET total_images = total_images + 1 WHERE chat_id = ?', (chat_id,))
            conn.commit()
    
    def save_image(self, chat_id: str, prompt: str, image_url: str, model: str = "flux-pro"):
        with self.get_connection() as conn:
            conn.execute(
                '''INSERT INTO image_history (chat_id, prompt, image_url, model) VALUES (?, ?, ?, ?)''',
                (chat_id, prompt, image_url, model)
            )
            conn.commit()
    
    def get_history(self, chat_id: str, limit: int = 5):
        with self.get_connection() as conn:
            results = conn.execute(
                '''SELECT prompt, image_url, model, created_at FROM image_history 
                   WHERE chat_id = ? ORDER BY created_at DESC LIMIT ?''',
                (chat_id, limit)
            ).fetchall()
            return [dict(row) for row in results]
    
    def save_session(self, chat_id: str, step: str):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM user_sessions WHERE chat_id = ?', (chat_id,))
            conn.execute(
                'INSERT INTO user_sessions (chat_id, step) VALUES (?, ?)',
                (chat_id, step)
            )
            conn.commit()
    
    def get_session(self, chat_id: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            result = conn.execute('SELECT * FROM user_sessions WHERE chat_id = ?', (chat_id,)).fetchone()
            return dict(result) if result else None
    
    def delete_session(self, chat_id: str):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM user_sessions WHERE chat_id = ?', (chat_id,))
            conn.commit()

db = Database()

# ==================== Replicate API ====================
def wait_for_replicate_result(prediction_id: str, timeout: int = 120) -> Optional[str]:
    """منتظر موندن برای نتیجه Replicate"""
    if not REPLICATE_API_TOKEN:
        return None
    
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                if status == 'succeeded':
                    outputs = data.get('output', [])
                    if outputs:
                        return outputs[0]
                    return None
                elif status == 'failed':
                    logger.error(f"تولید تصویر ناموفق: {data.get('error')}")
                    return None
            else:
                logger.error(f"خطا در دریافت نتیجه: {response.status_code}")
        except Exception as e:
            logger.error(f"خطا در انتظار نتیجه: {e}")
        
        time.sleep(2)
    
    return None

def generate_image_replicate(prompt: str, model: str = "black-forest-labs/flux-1.1-pro") -> Optional[str]:
    """تولید تصویر با Replicate"""
    if not REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN تنظیم نشده!")
        return None
    
    try:
        headers = {
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "version": model,
            "input": {
                "prompt": prompt,
                "width": 1024,
                "height": 1024,
                "num_outputs": 1,
                "guidance_scale": 3.5,
                "num_inference_steps": 28
            }
        }
        
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 201:
            data = response.json()
            prediction_id = data.get('id')
            if prediction_id:
                return wait_for_replicate_result(prediction_id)
        else:
            logger.error(f"خطا در Replicate: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"خطا در Replicate: {e}")
        return None

def edit_image_replicate(image_url: str, prompt: str) -> Optional[str]:
    """ویرایش تصویر با FLUX Kontext"""
    if not REPLICATE_API_TOKEN:
        return None
    
    try:
        headers = {
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "version": "black-forest-labs/flux-kontext-pro",
            "input": {
                "prompt": prompt,
                "image": image_url,
                "width": 1024,
                "height": 1024,
                "guidance_scale": 3.5,
                "num_inference_steps": 28
            }
        }
        
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 201:
            data = response.json()
            prediction_id = data.get('id')
            if prediction_id:
                return wait_for_replicate_result(prediction_id)
        else:
            logger.error(f"خطا در ویرایش: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"خطا در ویرایش: {e}")
        return None

# ==================== کیبورد ====================
class BotKeyboard:
    @staticmethod
    def get_main_keyboard():
        keyboard = [
            ['🎨 تولید تصویر', '🖼️ ویرایش تصویر'],
            ['📊 تاریخچه', '📈 آمار من'],
            ['📖 راهنما', 'ℹ️ درباره']
        ]
        return {
            'keyboard': keyboard,
            'resize_keyboard': True,
            'one_time_keyboard': False,
            'persistent': True
        }
    
    @staticmethod
    def get_cancel_keyboard():
        keyboard = [
            ['❌ لغو عملیات']
        ]
        return {
            'keyboard': keyboard,
            'resize_keyboard': True,
            'one_time_keyboard': False,
            'persistent': True
        }

# ==================== تلگرام ====================
class TelegramBot:
    BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
    
    @staticmethod
    def send_message(chat_id: str, text: str, parse_mode: str = 'Markdown', 
                     reply_markup: Optional[Dict] = None) -> bool:
        try:
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            if reply_markup is None:
                reply_markup = BotKeyboard.get_main_keyboard()
            payload['reply_markup'] = json.dumps(reply_markup)
            
            response = requests.post(
                f"{TelegramBot.BASE_URL}/sendMessage",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"خطا در ارسال پیام: {e}")
            return False
    
    @staticmethod
    def send_photo(chat_id: str, photo_url: str, caption: str = "") -> bool:
        try:
            payload = {
                'chat_id': chat_id,
                'photo': photo_url,
                'caption': caption,
                'parse_mode': 'Markdown'
            }
            response = requests.post(
                f"{TelegramBot.BASE_URL}/sendPhoto",
                json=payload,
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"خطا در ارسال تصویر: {e}")
            return False

# ==================== مدیریت کاربر ====================
class UserManager:
    @staticmethod
    def register_user(update: Dict):
        message = update.get('message', {})
        chat = message.get('chat', {})
        chat_id = str(chat.get('id'))
        user = message.get('from', {})
        
        db.create_user(
            chat_id=chat_id,
            username=user.get('username', ''),
            first_name=user.get('first_name', ''),
            last_name=user.get('last_name', '')
        )
        return chat_id
    
    @staticmethod
    def get_stats(chat_id: str) -> str:
        user = db.get_user(chat_id)
        if not user:
            return "❌ کاربری یافت نشد."
        
        return f"""
📊 **آمار شما**

👤 کاربر: {user.get('first_name', 'ناشناس')}
📅 تاریخ ثبت: {user.get('registered_at', 'نامشخص')}
🖼️ تعداد تصاویر: {user.get('total_images', 0)}
"""
    
    @staticmethod
    def get_history(chat_id: str) -> str:
        history = db.get_history(chat_id)
        
        if not history:
            return "📭 هنوز تصویری تولید نکرده‌اید."
        
        text = "📜 **تاریخچه تصاویر شما**\n\n"
        for i, item in enumerate(history, 1):
            text += f"{i}. 📝 {item['prompt'][:50]}...\n"
            text += f"   🕐 {item['created_at'][:16]}\n"
            text += f"   🔗 [مشاهده تصویر]({item['image_url']})\n\n"
        
        return text
    
    @staticmethod
    def get_help_message() -> str:
        return """
🎨 **راهنمای ربات تصویرسازی با FLUX**

🤖 **قابلیت‌ها:**
1. 🎨 تولید تصویر از متن
2. 🖼️ ویرایش تصویر با دستور متنی
3. 📊 تاریخچه تصاویر شما
4. 📈 آمار استفاده

📝 **نحوه استفاده:**
• روی دکمه "🎨 تولید تصویر" کلیک کنید
• دستور خود را وارد کنید
• منتظر بمانید تا تصویر ساخته شود

⚡ **مدل‌ها:**
• FLUX.1 Pro - کیفیت بالا
• FLUX.1 Dev - سرعت بالا
• FLUX.1 Schnell - سریع‌ترین

⚠️ **توجه:** تولید هر تصویر چند ثانیه زمان می‌برد.
"""
    
    @staticmethod
    def generate_image(chat_id: str, prompt: str, model: str = "black-forest-labs/flux-1.1-pro") -> str:
        db.increment_images(chat_id)
        
        TelegramBot.send_message(
            chat_id,
            "🎨 **در حال تولید تصویر...**\n\n⏳ لطفاً چند ثانیه صبر کنید."
        )
        
        image_url = generate_image_replicate(prompt, model)
        
        if image_url:
            db.save_image(chat_id, prompt, image_url, model)
            return f"""
🎨 **تصویر شما آماده است!**

📝 **دستور:** {prompt}

🖼️ [مشاهده تصویر]({image_url})

💡 برای تولید دوباره، دکمه "🎨 تولید تصویر" را بزنید.
"""
        else:
            return """
❌ **خطا در تولید تصویر!**

ممکن است:
• کلید API معتبر نباشد
• سرویس موقتاً در دسترس نباشد
• دستور شما قابل پردازش نباشد

لطفاً دوباره تلاش کنید یا بعداً امتحان کنید.
"""
    
    @staticmethod
    def edit_image(chat_id: str, image_url: str, prompt: str) -> str:
        db.increment_images(chat_id)
        
        TelegramBot.send_message(
            chat_id,
            "🖼️ **در حال ویرایش تصویر...**\n\n⏳ لطفاً چند ثانیه صبر کنید."
        )
        
        result_url = edit_image_replicate(image_url, prompt)
        
        if result_url:
            db.save_image(chat_id, f"ویرایش: {prompt}", result_url, "flux-kontext")
            return f"""
🖼️ **تصویر ویرایش شده!**

📝 **دستور:** {prompt}

🖼️ [مشاهده تصویر]({result_url})

💡 برای ویرایش دوباره، دکمه "🖼️ ویرایش تصویر" را بزنید.
"""
        else:
            return """
❌ **خطا در ویرایش تصویر!**

لطفاً دوباره تلاش کنید.
"""

# ==================== وب‌هوک ====================
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        if not update:
            return jsonify({'status': 'ok'}), 200
        
        if 'message' in update:
            message = update['message']
            chat_id = str(message['chat']['id'])
            text = message.get('text', '').strip()
            photo = message.get('photo')
            caption = message.get('caption', '').strip()
            
            UserManager.register_user(update)
            
            # ===== دستورات =====
            if text == '/start' or text == '/menu':
                TelegramBot.send_message(
                    chat_id,
                    "🎨 **ربات تصویرسازی با FLUX**\n\nسلام! 👋\nبا این ربات می‌توانید:\n• 🎨 از متن تصویر بسازید\n• 🖼️ تصاویر را ویرایش کنید\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                    reply_markup=BotKeyboard.get_main_keyboard()
                )
                return jsonify({'status': 'ok'}), 200
            
            # ===== دکمه‌ها =====
            elif text == '🎨 تولید تصویر':
                db.save_session(chat_id, 'generate_prompt')
                TelegramBot.send_message(
                    chat_id,
                    "🎨 **تولید تصویر از متن**\n\nلطفاً دستور خود را وارد کنید:\n\nمثال: «یک گربه سیاه در کنار دریاچه»",
                    reply_markup=BotKeyboard.get_cancel_keyboard()
                )
                return jsonify({'status': 'ok'}), 200
            
            elif text == '🖼️ ویرایش تصویر':
                db.save_session(chat_id, 'edit_image')
                TelegramBot.send_message(
                    chat_id,
                    "🖼️ **ویرایش تصویر**\n\nلطفاً یک تصویر ارسال کنید و در کپشن آن دستور ویرایش را بنویسید.\n\nمثال: «پس‌زمینه را به جنگل تغییر بده»",
                    reply_markup=BotKeyboard.get_cancel_keyboard()
                )
                return jsonify({'status': 'ok'}), 200
            
            elif text == '📊 تاریخچه':
                response = UserManager.get_history(chat_id)
                TelegramBot.send_message(chat_id, response)
                return jsonify({'status': 'ok'}), 200
            
            elif text == '📈 آمار من':
                response = UserManager.get_stats(chat_id)
                TelegramBot.send_message(chat_id, response)
                return jsonify({'status': 'ok'}), 200
            
            elif text == '📖 راهنما':
                TelegramBot.send_message(chat_id, UserManager.get_help_message())
                return jsonify({'status': 'ok'}), 200
            
            elif text == 'ℹ️ درباره':
                TelegramBot.send_message(
                    chat_id,
                    "ℹ️ **درباره ربات**\n\nنسخه ۱.۰.۰\nربات تصویرسازی با FLUX\n\n⚡ **قابلیت‌ها:**\n• 🎨 تولید تصویر از متن\n• 🖼️ ویرایش تصویر با AI\n• 📊 تاریخچه تصاویر\n• 📈 آمار کاربری\n\n🔧 **مدل‌ها:**\n• FLUX.1 Pro\n• FLUX Kontext"
                )
                return jsonify({'status': 'ok'}), 200
            
            elif text == '❌ لغو عملیات':
                db.delete_session(chat_id)
                TelegramBot.send_message(
                    chat_id,
                    "❌ عملیات لغو شد.",
                    reply_markup=BotKeyboard.get_main_keyboard()
                )
                return jsonify({'status': 'ok'}), 200
            
            # ===== پردازش عکس =====
            if photo and caption:
                session = db.get_session(chat_id)
                if session and session.get('step') == 'edit_image':
                    file_id = photo[-1]['file_id']
                    file_info = requests.get(
                        f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
                    ).json()
                    file_path = file_info['result']['file_path']
                    image_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                    
                    result = UserManager.edit_image(chat_id, image_url, caption)
                    db.delete_session(chat_id)
                    TelegramBot.send_message(chat_id, result)
                    return jsonify({'status': 'ok'}), 200
            
            # ===== پردازش مراحل =====
            session = db.get_session(chat_id)
            if session:
                step = session.get('step')
                
                if step == 'generate_prompt':
                    result = UserManager.generate_image(chat_id, text)
                    db.delete_session(chat_id)
                    TelegramBot.send_message(chat_id, result)
                    return jsonify({'status': 'ok'}), 200
            
            # ===== دستور نامشخص =====
            TelegramBot.send_message(
                chat_id,
                "🤔 دستور نامشخص. لطفاً از دکمه‌های پایین استفاده کنید.",
                reply_markup=BotKeyboard.get_main_keyboard()
            )
            return jsonify({'status': 'ok'}), 200
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.error(f"خطا: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== صفحه اصلی ====================
@app.route('/')
def home():
    return """
    <h1>🎨 ربات تصویرسازی با FLUX</h1>
    <p>ربات آنلاین و فعال است ✅</p>
    <p>🔮 تولید و ویرایش تصویر با هوش مصنوعی FLUX</p>
    <p>نسخه ۱.۰.۰</p>
    """

# ==================== منوی پایین ====================
def set_bot_commands():
    try:
        commands = [
            {"command": "start", "description": "🔄 شروع مجدد"},
            {"command": "menu", "description": "📋 منوی اصلی"},
            {"command": "history", "description": "📊 تاریخچه"},
            {"command": "stats", "description": "📈 آمار من"},
            {"command": "help", "description": "📖 راهنما"}
        ]
        
        url = f"https://api.telegram.org/bot{TOKEN}/setMyCommands"
        response = requests.post(url, json={"commands": commands}, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ منوی پایین با موفقیت ثبت شد")
            return True
        else:
            logger.error(f"❌ خطا در ثبت منو: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ خطا در ثبت منو: {e}")
        return False

# ==================== اجرا ====================
if __name__ == '__main__':
    print("🎨 ثبت منوی پایین تلگرام...")
    set_bot_commands()
    
    if not REPLICATE_API_TOKEN:
        print("⚠️ هشدار: REPLICATE_API_TOKEN تنظیم نشده است!")
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 ربات تصویرسازی روی پورت {port} اجرا شد")
    app.run(host='0.0.0.0', port=port, debug=False)
