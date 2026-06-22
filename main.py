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
            # ===== جدول جدید برای سشن‌ها =====
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
    
    # ===== متدهای جدید برای سشن =====
    def save_session(self, chat_id: str, step: str):
        """ذخیره مرحله فعلی کاربر"""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM user_sessions WHERE chat_id = ?', (chat_id,))
            conn.execute(
                'INSERT INTO user_sessions (chat_id, step) VALUES (?, ?)',
                (chat_id, step)
            )
            conn.commit()
    
    def get_session(self, chat_id: str) -> Optional[Dict]:
        """دریافت مرحله فعلی کاربر"""
        with self.get_connection() as conn:
            result = conn.execute('SELECT * FROM user_sessions WHERE chat_id = ?', (chat_id,)).fetchone()
            return dict(result) if result else None
    
    def delete_session(self, chat_id: str):
        """حذف مرحله فعلی کاربر"""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM user_sessions WHERE chat_id = ?', (chat_id,))
            conn.commit()
