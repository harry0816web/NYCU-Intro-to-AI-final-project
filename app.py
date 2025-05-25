from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import json, re
from datetime import datetime
from google import genai
from google.genai import types
from PIL import Image
import io
import uuid
import shutil

app = Flask(__name__, static_folder="static", template_folder="templates")

####### login system ######

import secrets
from flask import session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

# 配置 session
app.secret_key = secrets.token_hex(16)

# 用戶資料存儲
USER_AUTH_FILE = "user_auth.json"

def load_user_auth():
    if os.path.exists(USER_AUTH_FILE):
        with open(USER_AUTH_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_user_auth(data):
    with open(USER_AUTH_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# 登入頁面
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        users = load_user_auth()
        if username in users and check_password_hash(users[username]["password"], password):
            session["user_id"] = username
            return redirect(url_for("index"))
        
        return render_template("login.html", error="用戶名或密碼錯誤")
    
    return render_template("login.html")

# 註冊頁面
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        users = load_user_auth()
        if username in users:
            return render_template("register.html", error="用戶名已存在")
        
        users[username] = {
            "password": generate_password_hash(password),
            "created_at": datetime.now().isoformat()
        }
        save_user_auth(users)
        
        # 創建用戶偏好
        prefs = {
            "user_id": username,
            "flavor_preference": "無",
            "recipe_type_preference": "無",
            "avoid_ingredients": "無",
            "cooking_constraints": "無",
            "dietary_restrictions": "無"
        }
        save_user_preferences(prefs, username)
        
        session["user_id"] = username
        return redirect(url_for("index"))
    
    return render_template("register.html")

# 登出
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

#############################################################################

# 模擬一個分類器（你可以替換成你自己的模型）
def classify_image(image_path):
    # 讀取圖片
    from PIL import Image
    img = Image.open(image_path)

    # 前處理 → 模型預測
    # result = model.predict(img)
    # return result

    # 暫時回傳假資料
    return "雞胸肉"


# 載入你原本的功能函式
from testPrompt import (
    init_preference_file,
    load_user_preferences,
    save_user_preferences,
    store_preference_json,
    get_optimized_system_prompt,
    build_user_request,
    extract_cooking_timeline,      # 新增
    format_timeline_text,          # 新增
    format_timeline_checklist      # 新增
)

# 初始化
load_dotenv()
init_preference_file()

# GenAI Client
client = genai.Client(api_key=os.getenv("GOOGLE-API-KEY"))
MODEL = "gemini-2.0-flash"

def generate_recipe(user_id, ingredients, prefs):
    """使用統一的 system prompt 生成食譜"""
    
    # 使用共享的 system prompt
    system_prompt = get_optimized_system_prompt()
    
    # 使用共享的請求構建函數
    user_request = build_user_request(ingredients, prefs)
    
    # 使用 system instruction
    system_instruction = [types.Part(text=system_prompt)]
    
    generate_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        system_instruction=system_instruction,
    )

    response = ""
    for chunk in client.models.generate_content_stream(
        model=MODEL,
        contents=[types.Content(
            role="user",
            parts=[types.Part(text=user_request)]
        )],
        config=generate_config
    ):
        response += chunk.text
    return response

@app.route("/")
def index():
    # 檢查是否已登入
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    # 從 session 獲取用戶 ID
    user_id = session["user_id"]
    
    # 載入該用戶偏好
    prefs = load_user_preferences(user_id)
    
    # 傳到 template 填表
    return render_template("index.html", user_id=user_id, prefs=prefs)

@app.route("/api/preferences", methods=["GET", "POST"])
def api_preferences():
    if request.method == "POST":
        # 舊有：存偏好
        data = request.json or {}
        user_id = data.get("user_id", "default")
        prefs = {
            "flavor_preference": data.get("flavor_preference", "無"),
            "recipe_type_preference": data.get("recipe_type_preference", "無"),
            "avoid_ingredients": data.get("avoid_ingredients", "無"),
            "cooking_constraints": data.get("cooking_constraints", "無"),
            "dietary_restrictions": data.get("dietary_restrictions", "無")
        }
        save_user_preferences(prefs, user_id)
        return jsonify({"status": "ok"})
    else:
        # 新增：讀偏好
        user_id = request.args.get("user_id", "default")
        prefs = load_user_preferences(user_id)
        return jsonify(prefs)

from detect import detect_single_image  
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
@app.route("/api/upload_images", methods=["POST"])
def api_upload_images():
    files = request.files.getlist("ingredients")
    if not files:
        return jsonify({"error": "請至少上傳一張圖片"}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # 清空 uploads
    for f in os.listdir(UPLOAD_FOLDER):
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".txt")):
            os.remove(os.path.join(UPLOAD_FOLDER, f))

    # 存圖
    saved_paths = []
    for file in files:
        ext = os.path.splitext(file.filename)[1]
        fn = f"{uuid.uuid4().hex}{ext}"
        p = os.path.join(UPLOAD_FOLDER, fn)
        file.save(p)
        saved_paths.append(p)

    # 只對第一張圖做偵測
    detect_single_image(saved_paths[0])

    # 讀模型輸出的 txt
    label_dir = os.path.join("runs", "detect", "exp", "labels")
    txt_path  = os.path.join(label_dir, "ingredients.txt")
    if not os.path.exists(txt_path):
        return jsonify({"error": "辨識結果檔找不到"}), 500

    with open(txt_path, 'r', encoding='utf-8') as f:
        ingredients = [l.strip() for l in f if l.strip()]

    return jsonify({"ingredients": ingredients})

@app.route("/api/ingredients", methods=["GET"])
def api_ingredients():
    label_dir = os.path.join("runs", "detect", "exp", "labels")
    txt_path  = os.path.join(label_dir, "ingredients.txt")
    if not os.path.exists(txt_path):
        return jsonify({"error":"找不到食材清單"}), 404
    with open(txt_path, 'r', encoding='utf-8') as f:
        ingredients = [line.strip() for line in f if line.strip()]
    return jsonify({"ingredients": ingredients})

@app.route("/api/recipe", methods=["POST"])
def api_recipe():
    data = request.json or {}
    user_id = data.get("user_id", "default")
    ingredients = data.get("ingredients", "")
    include_timeline = data.get("include_timeline", True)
    
    # 🔥 從請求中獲取用戶當前的偏好設置
    current_prefs = {
        "user_id": user_id,
        "flavor_preference": data.get("flavor_preference", "無"),
        "recipe_type_preference": data.get("recipe_type_preference", "無"),
        "avoid_ingredients": data.get("avoid_ingredients", "無"),
        "cooking_constraints": data.get("cooking_constraints", "無"),
        "dietary_restrictions": data.get("dietary_restrictions", "無")
    }
    
    # 🔥 先保存用戶偏好
    save_user_preferences(current_prefs, user_id)
    
    # 生成食譜
    recipe = generate_recipe(user_id, ingredients, current_prefs)
    
    result = {"recipe": recipe}
    
    # 🔥 生成時間軸
    if include_timeline and "料理步驟" in recipe:
        try:
            steps, total_time = extract_cooking_timeline(recipe)
            if steps:
                timeline_text = format_timeline_text(steps, total_time)
                checklist = format_timeline_checklist(steps, total_time)
                
                result.update({
                    "timeline": timeline_text,
                    "checklist": checklist,
                    "total_time": total_time,
                    "steps_data": steps,
                    "has_timeline": True
                })
            else:
                result["has_timeline"] = False
                result["timeline_error"] = "食譜格式不包含時間信息"
        except Exception as e:
            print(f"生成時間軸時發生錯誤: {e}")
            result["has_timeline"] = False
            result["timeline_error"] = str(e)
    
    # 清空檔案
    for folder in (UPLOAD_FOLDER, os.path.join("runs", "detect")):
        if os.path.exists(folder):
            for f in os.listdir(folder):
                path = os.path.join(folder, f)
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                except:
                    pass
    
    return jsonify(result)

@app.route("/api/store_recipe", methods=["POST"])
def api_store_recipe():
    data = request.json or {}
    user_id     = data.get("user_id", "default")
    ingredients = [s.strip() for s in data.get("ingredients", "").split(",") if s.strip()]
    recipe_text = data.get("recipe", "")
    prefs       = load_user_preferences(user_id)

    # 寫入 preferences.json
    store_preference_json(
        ingredients=ingredients,
        recipe_text=recipe_text,
        preferences=prefs,
        user_id=user_id
    )
    return jsonify({"status": "stored"})


if __name__ == "__main__":
    app.run(debug=True)
