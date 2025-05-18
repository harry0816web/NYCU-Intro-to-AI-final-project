from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import json, re
from datetime import datetime
from google import genai
from google.genai import types

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

app = Flask(__name__, static_folder="static", template_folder="templates")

# GenAI Client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
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
    # 從 query string 讀 user_id，預設 default
    user_id = request.args.get("user_id", "default")
    # 載入該 user 偏好
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
