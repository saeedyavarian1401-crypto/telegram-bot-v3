from flask import Flask, request, jsonify, render_template_string
import requests
import os
import time
import json
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
REPLICATE_API_TOKEN = os.environ.get('REPLICATE_API_TOKEN')

# ==================== صفحه اصلی وب (مثل Perchance Revival) ====================
@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎨 ربات تصویرسازی</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Vazir', Tahoma, sans-serif;
                background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
                color: #fff;
            }
            .container {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                max-width: 700px;
                width: 100%;
                border: 1px solid rgba(255,255,255,0.1);
                box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            }
            h1 {
                text-align: center;
                font-size: 32px;
                margin-bottom: 10px;
                background: linear-gradient(90deg, #f7971e, #ffd200);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .subtitle {
                text-align: center;
                color: #aaa;
                margin-bottom: 30px;
                font-size: 14px;
            }
            .tab-container {
                display: flex;
                gap: 10px;
                margin-bottom: 30px;
                background: rgba(255,255,255,0.05);
                border-radius: 12px;
                padding: 5px;
            }
            .tab {
                flex: 1;
                padding: 12px;
                text-align: center;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
                border: none;
                background: transparent;
                color: #888;
                font-size: 14px;
            }
            .tab.active {
                background: linear-gradient(90deg, #f7971e, #ffd200);
                color: #1a1a2e;
                font-weight: bold;
            }
            .tab:hover {
                color: #fff;
            }
            .tab-content {
                display: none;
                animation: fadeIn 0.5s;
            }
            .tab-content.active {
                display: block;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-size: 14px;
                color: #ddd;
            }
            textarea, input[type="text"] {
                width: 100%;
                padding: 12px;
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,0.1);
                background: rgba(255,255,255,0.05);
                color: #fff;
                font-size: 14px;
                transition: border 0.3s;
                resize: vertical;
                font-family: inherit;
            }
            textarea:focus, input:focus {
                outline: none;
                border-color: #f7971e;
            }
            .row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }
            input[type="range"] {
                width: 100%;
                -webkit-appearance: none;
                background: rgba(255,255,255,0.1);
                height: 4px;
                border-radius: 2px;
                outline: none;
            }
            input[type="range"]::-webkit-slider-thumb {
                -webkit-appearance: none;
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: linear-gradient(90deg, #f7971e, #ffd200);
                cursor: pointer;
            }
            .range-value {
                float: right;
                color: #ffd200;
                font-weight: bold;
            }
            .btn-generate {
                width: 100%;
                padding: 15px;
                border: none;
                border-radius: 12px;
                background: linear-gradient(90deg, #f7971e, #ffd200);
                color: #1a1a2e;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
            }
            .btn-generate:hover {
                transform: scale(1.02);
                box-shadow: 0 10px 30px rgba(247, 151, 30, 0.3);
            }
            .btn-generate:disabled {
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }
            .result-container {
                margin-top: 30px;
                display: none;
            }
            .result-container.show {
                display: block;
            }
            .result-image {
                width: 100%;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            .loading {
                text-align: center;
                padding: 40px;
                display: none;
            }
            .loading.show {
                display: block;
            }
            .spinner {
                width: 50px;
                height: 50px;
                border: 4px solid rgba(255,255,255,0.1);
                border-top-color: #ffd200;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .prompt-history {
                margin-top: 20px;
                padding: 15px;
                background: rgba(255,255,255,0.03);
                border-radius: 10px;
                max-height: 200px;
                overflow-y: auto;
            }
            .prompt-history h4 {
                color: #888;
                margin-bottom: 10px;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .prompt-item {
                padding: 8px 12px;
                background: rgba(255,255,255,0.05);
                border-radius: 6px;
                margin-bottom: 5px;
                font-size: 12px;
                color: #aaa;
                cursor: pointer;
                transition: background 0.3s;
            }
            .prompt-item:hover {
                background: rgba(255,255,255,0.1);
                color: #fff;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                font-size: 12px;
                color: #555;
            }
            @media (max-width: 600px) {
                .container { padding: 20px; }
                .row { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎨 ربات تصویرسازی</h1>
            <p class="subtitle">⚡ FLUX Uncensored • بدون محدودیت</p>

            <div class="tab-container">
                <button class="tab active" onclick="switchTab('txt2img')">🎨 متن به تصویر</button>
                <button class="tab" onclick="switchTab('img2img')">🖼️ ویرایش تصویر</button>
            </div>

            <!-- تب تولید متن به تصویر -->
            <div id="txt2img" class="tab-content active">
                <form id="generateForm">
                    <div class="form-group">
                        <label>📝 دستور (Prompt)</label>
                        <textarea id="prompt" rows="3" placeholder="مثلاً: یک گربه سیاه در کنار دریاچه..." required></textarea>
                    </div>

                    <div class="row">
                        <div class="form-group">
                            <label>📐 عرض (Width)</label>
                            <input type="number" id="width" value="1024" min="256" max="2048" step="64">
                        </div>
                        <div class="form-group">
                            <label>📐 ارتفاع (Height)</label>
                            <input type="number" id="height" value="1024" min="256" max="2048" step="64">
                        </div>
                    </div>

                    <div class="form-group">
                        <label>🔢 مراحل (Steps) <span class="range-value" id="stepsValue">20</span></label>
                        <input type="range" id="steps" min="5" max="50" value="20" oninput="document.getElementById('stepsValue').textContent=this.value">
                    </div>

                    <div class="form-group">
                        <label>⚙️ راهنمایی (CFG Scale) <span class="range-value" id="cfgValue">5</span></label>
                        <input type="range" id="cfg" min="1" max="10" value="5" step="0.5" oninput="document.getElementById('cfgValue').textContent=this.value">
                    </div>

                    <button type="submit" class="btn-generate" id="generateBtn">🎨 تولید تصویر</button>
                </form>
            </div>

            <!-- تب ویرایش تصویر -->
            <div id="img2img" class="tab-content">
                <form id="editForm">
                    <div class="form-group">
                        <label>🖼️ تصویر را انتخاب کنید</label>
                        <input type="file" id="imageInput" accept="image/*" required>
                    </div>

                    <div class="form-group">
                        <label>📝 دستور ویرایش</label>
                        <textarea id="editPrompt" rows="3" placeholder="مثلاً: پس‌زمینه را به جنگل تغییر بده..." required></textarea>
                    </div>

                    <div class="form-group">
                        <label>💪 شدت تغییر (Strength) <span class="range-value" id="strengthValue">0.5</span></label>
                        <input type="range" id="strength" min="0.1" max="0.9" value="0.5" step="0.05" oninput="document.getElementById('strengthValue').textContent=this.value">
                    </div>

                    <button type="submit" class="btn-generate" id="editBtn">🖼️ ویرایش تصویر</button>
                </form>
            </div>

            <!-- بارگذاری -->
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>⏳ در حال تولید تصویر...</p>
                <p style="font-size:12px;color:#666;">چند ثانیه صبر کنید</p>
            </div>

            <!-- نتیجه -->
            <div class="result-container" id="resultContainer">
                <img id="resultImage" class="result-image" alt="تصویر تولید شده">
                <p id="resultCaption" style="margin-top:10px;font-size:14px;color:#aaa;text-align:center;"></p>
                <div style="display:flex;gap:10px;margin-top:15px;">
                    <button onclick="downloadImage()" style="flex:1;padding:10px;border:none;border-radius:8px;background:rgba(255,255,255,0.1);color:#fff;cursor:pointer;">💾 دانلود</button>
                    <button onclick="resetForm()" style="flex:1;padding:10px;border:none;border-radius:8px;background:rgba(255,255,255,0.05);color:#888;cursor:pointer;">🔄 دوباره</button>
                </div>
            </div>

            <!-- تاریخچه -->
            <div class="prompt-history" id="historyContainer">
                <h4>📜 تاریخچه</h4>
                <div id="historyList">
                    <div style="color:#555;font-size:12px;">هنوز تصویری تولید نشده</div>
                </div>
            </div>

            <div class="footer">
                ⚡ FLUX Uncensored • بدون محدودیت • نسخه ۲.۰.۰
            </div>
        </div>

        <script>
            let currentImageUrl = '';
            let history = JSON.parse(localStorage.getItem('promptHistory') || '[]');

            function switchTab(tab) {
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
                document.getElementById(tab).classList.add('active');
                document.querySelector(`.tab[onclick="switchTab('${tab}')"]`).classList.add('active');
                document.getElementById('resultContainer').classList.remove('show');
            }

            function updateHistory(prompt, imageUrl) {
                history.unshift({ prompt, imageUrl, time: new Date().toLocaleString() });
                if (history.length > 10) history.pop();
                localStorage.setItem('promptHistory', JSON.stringify(history));
                renderHistory();
            }

            function renderHistory() {
                const list = document.getElementById('historyList');
                if (history.length === 0) {
                    list.innerHTML = '<div style="color:#555;font-size:12px;">هنوز تصویری تولید نشده</div>';
                    return;
                }
                list.innerHTML = history.map((item, index) => `
                    <div class="prompt-item" onclick="loadPrompt(${index})">
                        ${item.prompt.substring(0, 60)}${item.prompt.length > 60 ? '...' : ''}
                        <span style="float:right;color:#555;font-size:10px;">${item.time}</span>
                    </div>
                `).join('');
            }

            function loadPrompt(index) {
                const item = history[index];
                document.getElementById('prompt').value = item.prompt;
                if (item.imageUrl) {
                    document.getElementById('resultImage').src = item.imageUrl;
                    document.getElementById('resultContainer').classList.add('show');
                    currentImageUrl = item.imageUrl;
                }
            }

            function downloadImage() {
                if (currentImageUrl) {
                    const a = document.createElement('a');
                    a.href = currentImageUrl;
                    a.download = `image_${Date.now()}.png`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                }
            }

            function resetForm() {
                document.getElementById('resultContainer').classList.remove('show');
                document.getElementById('loading').classList.remove('show');
                document.getElementById('generateBtn').disabled = false;
                document.getElementById('editBtn').disabled = false;
                currentImageUrl = '';
            }

            // تولید تصویر
            document.getElementById('generateForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const prompt = document.getElementById('prompt').value.trim();
                if (!prompt) return alert('لطفاً دستور را وارد کنید');

                const width = parseInt(document.getElementById('width').value);
                const height = parseInt(document.getElementById('height').value);
                const steps = parseInt(document.getElementById('steps').value);
                const cfg = parseFloat(document.getElementById('cfg').value);

                document.getElementById('loading').classList.add('show');
                document.getElementById('generateBtn').disabled = true;
                document.getElementById('resultContainer').classList.remove('show');

                try {
                    const response = await fetch('/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt, width, height, steps, cfg })
                    });

                    const data = await response.json();
                    document.getElementById('loading').classList.remove('show');

                    if (data.success && data.image_url) {
                        document.getElementById('resultImage').src = data.image_url;
                        document.getElementById('resultCaption').textContent = `✅ ${prompt}`;
                        document.getElementById('resultContainer').classList.add('show');
                        currentImageUrl = data.image_url;
                        updateHistory(prompt, data.image_url);
                    } else {
                        alert('❌ خطا: ' + (data.error || 'مشخص نیست'));
                    }
                } catch (error) {
                    document.getElementById('loading').classList.remove('show');
                    alert('❌ خطا در ارتباط با سرور');
                }
                document.getElementById('generateBtn').disabled = false;
            });

            // ویرایش تصویر
            document.getElementById('editForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const fileInput = document.getElementById('imageInput');
                const prompt = document.getElementById('editPrompt').value.trim();
                const strength = parseFloat(document.getElementById('strength').value);

                if (!fileInput.files.length) return alert('لطفاً یک تصویر انتخاب کنید');
                if (!prompt) return alert('لطفاً دستور ویرایش را وارد کنید');

                const formData = new FormData();
                formData.append('image', fileInput.files[0]);
                formData.append('prompt', prompt);
                formData.append('strength', strength);

                document.getElementById('loading').classList.add('show');
                document.getElementById('editBtn').disabled = true;
                document.getElementById('resultContainer').classList.remove('show');

                try {
                    const response = await fetch('/edit', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();
                    document.getElementById('loading').classList.remove('show');

                    if (data.success && data.image_url) {
                        document.getElementById('resultImage').src = data.image_url;
                        document.getElementById('resultCaption').textContent = `✅ ویرایش: ${prompt}`;
                        document.getElementById('resultContainer').classList.add('show');
                        currentImageUrl = data.image_url;
                        updateHistory(`ویرایش: ${prompt}`, data.image_url);
                    } else {
                        alert('❌ خطا: ' + (data.error || 'مشخص نیست'));
                    }
                } catch (error) {
                    document.getElementById('loading').classList.remove('show');
                    alert('❌ خطا در ارتباط با سرور');
                }
                document.getElementById('editBtn').disabled = false;
            });

            renderHistory();
        </script>
    </body>
    </html>
    """

# ==================== API تولید تصویر ====================
def wait_for_replicate_result(prediction_id: str, timeout: int = 120):
    if not REPLICATE_API_TOKEN:
        return None
    
    headers = {"Authorization": f"Token {REPLICATE_API_TOKEN}"}
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
                if data.get('status') == 'succeeded':
                    outputs = data.get('output', [])
                    return outputs[0] if outputs else None
                elif data.get('status') == 'failed':
                    return None
        except:
            pass
        time.sleep(2)
    return None

def generate_image(prompt: str, width: int = 1024, height: int = 1024, steps: int = 20, cfg: float = 5):
    if not REPLICATE_API_TOKEN:
        return None
    
    try:
        headers = {
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # مدل بدون سانسور
        model = "aisha-ai-official/flux.1dev-uncensored-msfluxnsfw-v3:b477d8fc3a62e591c6224e10020538c4a9c340fb1f494891aff60019ffd5bc48"
        
        payload = {
            "version": model,
            "input": {
                "prompt": prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg_scale": cfg,
                "seed": -1,
                "scheduler": "Euler flux beta"
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
        return None
    except Exception as e:
        logging.error(f"خطا: {e}")
        return None

# ==================== مسیرهای API ====================
@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        width = data.get('width', 1024)
        height = data.get('height', 1024)
        steps = data.get('steps', 20)
        cfg = data.get('cfg', 5)
        
        if not prompt:
            return jsonify({'success': False, 'error': 'دستور وارد نشده'})
        
        image_url = generate_image(prompt, width, height, steps, cfg)
        
        if image_url:
            return jsonify({'success': True, 'image_url': image_url})
        else:
            return jsonify({'success': False, 'error': 'خطا در تولید تصویر'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/edit', methods=['POST'])
def edit():
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'تصویری ارسال نشده'})
        
        file = request.files['image']
        prompt = request.form.get('prompt')
        strength = float(request.form.get('strength', 0.5))
        
        if not prompt:
            return jsonify({'success': False, 'error': 'دستور وارد نشده'})
        
        # آپلود تصویر به تلگرام برای دریافت URL
        files = {'photo': (file.filename, file.read(), file.content_type)}
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
            data={'chat_id': 'test'},
            files=files
        )
        
        if response.status_code == 200:
            # دریافت URL تصویر
            file_id = response.json()['result']['photo'][-1]['file_id']
            file_info = requests.get(
                f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
            ).json()
            file_path = file_info['result']['file_path']
            image_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
            
            # ویرایش با Replicate
            result_url = edit_image_replicate(image_url, prompt, strength)
            
            if result_url:
                return jsonify({'success': True, 'image_url': result_url})
        
        return jsonify({'success': False, 'error': 'خطا در ویرایش'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def edit_image_replicate(image_url: str, prompt: str, strength: float = 0.5):
    if not REPLICATE_API_TOKEN:
        return None
    
    try:
        headers = {
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        model = "aisha-ai-official/flux.1dev-uncensored-msfluxnsfw-v3:b477d8fc3a62e591c6224e10020538c4a9c340fb1f494891aff60019ffd5bc48"
        
        payload = {
            "version": model,
            "input": {
                "prompt": prompt,
                "image": image_url,
                "width": 1024,
                "height": 1024,
                "steps": 20,
                "cfg_scale": 5,
                "strength": strength,
                "seed": -1,
                "scheduler": "Euler flux beta"
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
        return None
    except Exception as e:
        logging.error(f"خطا: {e}")
        return None

# ==================== اجرا ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
