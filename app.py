from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import json, re
from datetime import datetime
from google import genai
from google.genai import types

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

# 載入你原本的功能函式
from testPrompt import (
    init_preference_file,
    load_user_preferences,
    save_user_preferences,
    store_preference_json
)

# 初始化
load_dotenv()
init_preference_file()

# GenAI Client
client = genai.Client(api_key=os.getenv("AIzaSyC2PCC4FzSWFO5rDK0M9M45dEj4qabkNAk"))
MODEL = "gemini-2.0-flash"

def generate_recipe(user_id, ingredients, prefs):
    # 這裡簡化示範，只傳必要欄位
    prompt = (
        f"請立即生成食譜：使用食材 {ingredients}；"
        f"口味 {prefs['flavor_preference']}；"
        f"避免 {prefs['avoid_ingredients']}；"
        f"料理風格 {prefs['recipe_type_preference']}；"
        f"烹飪限制 {prefs['cooking_constraints']}；"
        f"飲食限制 {prefs['dietary_restrictions']}。"
    )
    response = ""
    for chunk in client.models.generate_content_stream(
        model=MODEL,
        contents=[types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )],
        config=types.GenerateContentConfig(response_mime_type="text/plain")
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

@app.route("/api/recipe", methods=["POST"])
def api_recipe():
    data = request.json or {}
    user_id = data.get("user_id", "default")
    ingredients = data.get("ingredients", "")
    # 讀剛剛存的偏好（或取 data 內的）
    prefs = load_user_preferences(user_id)
    # 產生食譜
    try:
        recipe = generate_recipe(user_id, ingredients, prefs)
        return jsonify({"recipe": recipe})
    except Exception as e:
        import traceback
        traceback.print_exc()  # <<< 這行會印出完整錯誤堆疊
        return jsonify({"error": str(e)}), 503

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
