# To run this code you need to install the following dependencies:
# pip install google-genai

import os
import csv
import json
import re
from datetime import datetime, timedelta
from google import genai
from google.genai import types

PREF_FILE = "preferences.json"
USER_PREF_FILE = "user_preferences.json"  # 新增用戶偏好檔案

# ============================================================
# prompt engineering
# ============================================================

def get_optimized_system_prompt():
    """返回優化後的系統 prompt"""
    return """你是一位專業的「食譜推薦助理」，只負責根據使用者提供的食材與需求，產生**結構完整的料理建議**。  
請嚴格遵守以下規則：

0. 用中文回答
                                           
1. **限制任務範圍**
   - 可以跟使用者打招呼，以及簡單的交流
   - 只提供「食譜建議」，不得回答任何與食譜無關的問題。
   - 不提供醫療、法律、健康診斷、心理建議或其他非食譜資訊。
   - 不評論或描述你是誰、你的能力或開發背景。
   - 不要描述任何跟你有關的任何訊息(限制、能力範圍等等)

2. **食譜內容要求**
   - 根據使用者提供的【食材】與【需求】生成食譜，包括：
     - 料理名稱
     - 料理類型（如：家常、中式、日式、義式）
     - 食材列表（不含使用者指定要避免的食材）
     - 步驟說明（具體且易於理解，像是教學般詳細說明，並特別標註重要提醒）
     - **每個步驟的預估時間**（必須明確標註分鐘數）
     - 總預估烹飪時間
     - 適合份量（1人、2人或多人）
   - 依據使用者需求調整口味（如：清淡、重口味）、料理時間限制、飲食限制（如：素食、無麩質、低醣），讓食譜盡量符合使用者提供的食材，不要多出太多其他的食材，並且可以在用家中常見的器具以及調味料簡單料理。

3. **安全性要求**
   - 僅建議安全、常見、可食用的食材與料理方式。
   - 禁止建議生食未經處理的肉類、魚類或可能危害健康的行為。
   - 遇到不適當請求（色情、暴力、敏感話題等）應回應：「抱歉，我只能提供食譜建議。
  
4. **保護使用者隱私**
   - 不記錄、不假設、不回應任何使用者個人資訊問題。

---

**請先將使用者輸入自動解析為以下格式，如果某一項未指定，請填寫「無」：**

【食材】：（使用者提到的主要可用食材）
【料理偏好】：（口味、料理風格或其他偏好）
【避免食材】：（使用者明確表示不希望出現的食材）
【其他需求】：（料理時間、份量、特殊飲食限制）

---

### 🎯 以下為示範解析與食譜格式：

#### 使用者提供的資訊如下：
【食材】：番茄、雞蛋、洋蔥  
【料理偏好】：家常料理（清淡、不油膩）  
【避免食材】：蔥、辣椒  
【其他需求】：15 分鐘內完成，適合2人

---

#### 料理名稱：番茄炒蛋洋蔥盅  

#### 料理類型：家常料理（清淡口味）

---

### 食材準備

| 食材       | 份量 |
|------------|------|
| 番茄       | 2 顆 |
| 雞蛋       | 3 顆 |
| 洋蔥       | 1 顆 |
| 食用油     | 適量 |
| 鹽         | 少許 |

---

### 料理步驟（詳細教學版）

1. **準備食材**（⏰ 5分鐘）
   - 將番茄洗淨後切成 2-3 公分大小的塊狀。
   - 雞蛋打入碗中，攪拌均勻至蛋黃蛋白融合。
   - 洋蔥去皮切絲。  
     **（提醒：若不喜辛辣味，可先泡水 5 分鐘）**

2. **熱鍋倒油**（⏰ 2分鐘）
   - 中小火預熱鍋子 20-30 秒。
   - 倒入 1 大匙食用油。  
     **（建議使用不沾鍋，減少油量更健康）**

3. **炒洋蔥**（⏰ 2分鐘）
   - 放入洋蔥絲炒至變軟出香氣，約 1-2 分鐘。  
     **（注意火力勿過大，避免焦苦）**

4. **加入番茄**（⏰ 3分鐘）
   - 放入番茄塊，炒至出水變軟，約 2-3 分鐘。  
     **（避免炒太爛，保留口感）**

5. **倒入蛋液**（⏰ 2分鐘）
   - 轉中火，均勻倒入蛋液，靜置 2-3 秒讓底部凝固。
   - 快速翻炒 30 秒至 1 分鐘，炒至蛋液全熟。  
     **（提醒：靜置片刻再翻炒，蛋會更嫩）**

6. **調味與上桌**（⏰ 1分鐘）
   - 加入 1/4 小匙鹽，翻炒均勻後關火。
   - 盛盤上桌。

---

### ⏰ 烹飪時間軸
- 準備工作：5分鐘
- 烹飪過程：10分鐘
- **總計時間：15分鐘**

### 👥 適合份量  
2 人

---

**重要格式要求：**
1. 每個步驟標題後必須標註時間：（⏰ X分鐘)
2. 在步驟內容中具體說明該步驟的操作時間
3. 最後必須提供烹飪時間軸總結
4. 時間估算要合理且實用

請以相同邏輯處理使用者的實際輸入並產出食譜。  
僅限提供食譜，嚴禁離題或暴露模型訊息."""

def build_user_request(ingredients, preferences):
    """構建用戶請求字符串"""
    user_request = f"使用食材：{ingredients}"
    
    # 添加偏好信息
    pref_parts = []
    if preferences.get('flavor_preference', '無') != "無":
        pref_parts.append(f"口味偏好：{preferences['flavor_preference']}")
    if preferences.get('recipe_type_preference', '無') != "無":
        pref_parts.append(f"料理類型：{preferences['recipe_type_preference']}")
    if preferences.get('avoid_ingredients', '無') != "無":
        pref_parts.append(f"避免食材：{preferences['avoid_ingredients']}")
    if preferences.get('cooking_constraints', '無') != "無":
        pref_parts.append(f"時間/份量要求：{preferences['cooking_constraints']}")
    if preferences.get('dietary_restrictions', '無') != "無":
        pref_parts.append(f"飲食限制：{preferences['dietary_restrictions']}")
    
    if pref_parts:
        user_request += "；" + "；".join(pref_parts)
    
    user_request += "。請按照格式模板直接生成完整食譜。"
    return user_request

# ============================================================
# cooking timeline
# ============================================================

import re
from datetime import datetime, timedelta

def extract_cooking_timeline(recipe_text):
    """從食譜文字中提取烹飪時間軸 - 增強版"""
    if not recipe_text or "料理步驟" not in recipe_text:
        print("🔍 DEBUG: 食譜中沒有找到料理步驟")
        return [], 0
    
    lines = recipe_text.split('\n')
    steps = []
    current_time = 0
    
    # 找到步驟部分
    step_section = False
    step_counter = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 檢測步驟開始標記
        if any(marker in line for marker in ['料理步驟', '### 料理步驟', '## 👩‍🍳 料理步驟']):
            step_section = True
            print(f"🔍 DEBUG: 找到料理步驟標記: {line}")
            continue
        
        # 檢測步驟結束標記
        if step_section and any(marker in line for marker in ['烹飪時間軸', '適合份量', '##', 'finish']):
            print(f"🔍 DEBUG: 遇到結束標記: {line}")
            break
            
        if step_section and line:
            # 🔥 多種時間提取模式
            time_patterns = [
                # 標準格式：1. **準備食材**（⏰ 5分鐘）
                r'(\d+)\.\s*\*\*(.+?)\*\*[（(]⏰\s*(\d+)分鐘[）)]',
                # 變體格式：### 1. **準備食材**（⏰ 5分鐘）
                r'###?\s*(\d+)\.\s*\*\*(.+?)\*\*[（(]⏰\s*(\d+)分鐘[）)]',
                # 簡化格式：1. 準備食材（5分鐘）
                r'(\d+)\.\s*(.+?)[（(](\d+)分鐘[）)]',
                # 備用格式：1. **準備食材** - 5分鐘
                r'(\d+)\.\s*\*\*(.+?)\*\*.*?(\d+)\s*分鐘',
                # 更寬鬆格式：任何包含數字分鐘的行
                r'(\d+)\.\s*(.+?).*?(\d+)\s*分',
            ]
            
            step_match = None
            duration = 0
            step_title = ""
            step_num = 0
            
            for pattern in time_patterns:
                step_match = re.search(pattern, line)
                if step_match:
                    try:
                        step_num = int(step_match.group(1))
                        step_title = step_match.group(2).strip()
                        duration = int(step_match.group(3))
                        print(f"🔍 DEBUG: 成功匹配步驟 {step_num}: {step_title} ({duration}分鐘)")
                        break
                    except (ValueError, IndexError) as e:
                        print(f"🔍 DEBUG: 模式匹配錯誤: {e}")
                        continue
            
            # 🔥 如果所有模式都失敗，嘗試基礎提取
            if not step_match:
                # 檢查是否至少包含步驟編號
                basic_pattern = r'(\d+)\.\s*(.+)'
                basic_match = re.search(basic_pattern, line)
                if basic_match:
                    step_num = int(basic_match.group(1))
                    step_title = basic_match.group(2).strip()
                    # 移除可能的markdown格式
                    step_title = re.sub(r'\*\*(.+?)\*\*', r'\1', step_title)
                    step_title = step_title.split('（')[0].split('(')[0].strip()
                    
                    # 設定預設時間
                    if any(keyword in step_title.lower() for keyword in ['準備', '切', '洗']):
                        duration = 5
                    elif any(keyword in step_title.lower() for keyword in ['炒', '煮', '烹飪']):
                        duration = 10
                    elif any(keyword in step_title.lower() for keyword in ['燉', '烤', '蒸']):
                        duration = 15
                    else:
                        duration = 8  # 預設時間
                    
                    print(f"🔍 DEBUG: 基礎匹配步驟 {step_num}: {step_title} (預設{duration}分鐘)")
            
            if step_num > 0 and step_title and duration > 0:
                # 清理標題
                step_title = re.sub(r'[⏰🔥💡⚠️]+', '', step_title).strip()
                step_title = re.sub(r'\s+', ' ', step_title)
                
                steps.append({
                    "step_number": step_num,
                    "title": step_title,
                    "start_time": current_time,
                    "duration": duration,
                    "end_time": current_time + duration
                })
                
                current_time += duration
                step_counter += 1
    
    print(f"🔍 DEBUG: 總共解析到 {len(steps)} 個步驟，總時間 {current_time} 分鐘")
    
    # 🔥 如果沒有解析到任何步驟，嘗試生成預設步驟
    if not steps:
        print("🔍 DEBUG: 嘗試生成預設步驟")
        default_steps = [
            {"step_number": 1, "title": "準備食材", "start_time": 0, "duration": 5, "end_time": 5},
            {"step_number": 2, "title": "開始烹飪", "start_time": 5, "duration": 15, "end_time": 20},
            {"step_number": 3, "title": "完成料理", "start_time": 20, "duration": 5, "end_time": 25}
        ]
        return default_steps, 25
    
    return steps, current_time

def format_timeline_checklist(steps, total_time):
    """格式化為互動式 Markdown 檢查清單 - 修復格式問題"""
    if not steps:
        return "\n⚠️ 無法生成檢查清單：未找到步驟時間信息\n"
        
    # 🔥 使用更穩定的 Markdown 格式
    checklist = f"# 📋 烹飪檢查清單\n\n**總預估時間: {total_time} 分鐘**\n\n"
    
    for i, step in enumerate(steps):
        start_time = f"{step['start_time']:02d}:00"
        duration = step['duration']
        title = step['title']
        
        # 🔥 確保格式一致性
        checklist += f"- [ ] **{start_time}** - {title} ({duration}分鐘)\n"
        checklist += f"  > 筆記空間：____________________________________________\n\n"
    
    checklist += "\n---\n\n"
    checklist += "### ✅ 完成所有步驟後，享用您的美食！🎉\n"
    
    return checklist

def format_timeline_text(steps, total_time):
    """格式化時間軸為 Markdown 文字輸出 - 增強版"""
    if not steps:
        return "\n⚠️ 無法生成時間軸：未找到步驟時間信息\n"
    
    timeline_text = f"# 🕐 烹飪時間軸詳細分析\n\n**總計: {total_time} 分鐘**\n\n"
    
    for step in steps:
        start_min = step['start_time']
        end_min = step['end_time']
        duration = step['duration']
        
        timeline_text += f"## ⏰ {start_min:02d}:00 - {end_min:02d}:00\n\n"
        timeline_text += f"**({duration}分鐘) | 步驟{step['step_number']}: {step['title']}**\n\n"
        
        # 添加進度條視覺化
        bar_length = min(duration, 20)
        progress_bar = "█" * bar_length + "░" * max(0, 20 - bar_length)
        timeline_text += f"```\n[{progress_bar}] {duration}分鐘\n```\n\n"
    
    # 添加累積時間分析
    timeline_text += "## 📊 累積時間分析\n\n"
    timeline_text += "| 步驟 | 累積時間 |\n"
    timeline_text += "|------|----------|\n"
    
    cumulative = 0
    for step in steps:
        cumulative += step['duration']
        timeline_text += f"| 完成步驟{step['step_number']} | {cumulative}分鐘 |\n"
    
    return timeline_text

# ============================================================
# store to json
# ============================================================

# 轉移成函數，只有在檔案存在時才執行
def init_preference_file():
    # 如果檔案不存在，就跳過格式調整
    if not os.path.exists(PREF_FILE):
        print("preferences.json 不存在，跳過格式調整")
        return
        
    try:
        # 讀取現有的 preferences.json
        with open(PREF_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 只添加 user_id，不删除任何字段
        for entry in data.get('recipe_history', []):
            # 如果没有 user_id，添加默认值
            if 'user_id' not in entry:
                entry['user_id'] = 'default'
            
        # 保留 JSON 的原始结构，不删除任何字段
        with open(PREF_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("已完成 preferences.json 格式調整 (保留所有字段)")
    except Exception as e:
        print(f"初始化偏好文件時發生錯誤: {str(e)}")
        # 出錯時可以創建一個空的preferences.json
        with open(PREF_FILE, 'w', encoding='utf-8') as f:
            json.dump({'recipe_history': []}, f, indent=2, ensure_ascii=False)
            
# 讀取用戶偏好
def load_user_preferences(user_id="default"):
    if os.path.exists(USER_PREF_FILE):
        with open(USER_PREF_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    # 返回該用戶的偏好，如果不存在就返回默認值
                    return data.get(user_id, {
                        "user_id": user_id,
                        "flavor_preference": "無",
                        "recipe_type_preference": "無",
                        "avoid_ingredients": "無",
                        "cooking_constraints": "無",
                        "dietary_restrictions": "無"
                    })
            except (ValueError, json.JSONDecodeError):
                pass
    return {
        "user_id": user_id,
        "flavor_preference": "無",
        "recipe_type_preference": "無",
        "avoid_ingredients": "無",
        "cooking_constraints": "無",
        "dietary_restrictions": "無"
    }

# 儲存用戶偏好
def save_user_preferences(preferences, user_id="default"):
    # 初始化或讀取現有用戶偏好檔案
    if os.path.exists(USER_PREF_FILE):
        with open(USER_PREF_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
            except (ValueError, json.JSONDecodeError):
                data = {}
    else:
        data = {}
    
    # 添加或更新該用戶的偏好
    data[user_id] = preferences
    
    # 寫入檔案
    with open(USER_PREF_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def store_preference_json(ingredients, recipe_text, preferences=None, user_id="default"):
    # 初始化偏好欄位
    if preferences is None:
        preferences = {
            "flavor_preference": "無",
            "recipe_type_preference": "無",
            "avoid_ingredients": "無",
            "cooking_constraints": "無",
            "dietary_restrictions": "無"
        }
    
    # 初始化或讀取 JSON
    if os.path.exists(PREF_FILE):
        with open(PREF_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("格式錯誤")
            except (ValueError, json.JSONDecodeError):
                data = {}
    else:
        data = {}

    # 確保 recipe_history 欄位存在
    data.setdefault("recipe_history", [])

    # 擷取 recipe_text 中的食材表格 - 改進版本
    lines = recipe_text.strip().splitlines()
    extracted_ingredients = []
    extracted_quantity = []

    # 方法1：標準 Markdown 表格格式解析
    table_lines = [line for line in lines if "|" in line and "---" not in line]
    if len(table_lines) > 1:  # 至少有表頭和一行數據
        for line in table_lines[1:]:  # 跳過表頭
            parts = [cell.strip() for cell in line.strip().split('|') if cell.strip()]
            if len(parts) >= 2:
                extracted_ingredients.append(parts[0])
                extracted_quantity.append(parts[1])
    
    # 方法2：嘗試基於關鍵字或格式的解析（如果方法1沒有找到結果）
    if not extracted_ingredients:
        # 找出食材段落的開始和結束
        ingredients_section_start = -1
        ingredients_section_end = -1
        
        for i, line in enumerate(lines):
            if "食材" in line or "材料" in line or "【食材】" in line:
                ingredients_section_start = i
            elif ingredients_section_start > -1 and ("步驟" in line or "做法" in line or "【步驟】" in line):
                ingredients_section_end = i
                break
        
        # 如果找到食材段落
        if ingredients_section_start > -1:
            if ingredients_section_end == -1:  # 沒找到結束位置，設定一個合理的範圍
                ingredients_section_end = min(ingredients_section_start + 20, len(lines))
            
            # 解析食材段落中的每一行
            for i in range(ingredients_section_start + 1, ingredients_section_end):
                if i < len(lines) and lines[i].strip():
                    line = lines[i].strip()
                    
                    # 嘗試分割食材和份量 (多種可能的分隔符)
                    for separator in ['：', ':', '、', ' ', '　']:
                        if separator in line:
                            parts = line.split(separator, 1)
                            if len(parts) == 2 and all(parts):
                                ingredient = parts[0].strip()
                                quantity = parts[1].strip()
                                
                                # 進一步處理，去除雜項
                                for prefix in ['• ', '- ', '* ', '· ']:
                                    if ingredient.startswith(prefix):
                                        ingredient = ingredient[len(prefix):].strip()
                                
                                extracted_ingredients.append(ingredient)
                                extracted_quantity.append(quantity)
                                break

    # 清理使用者輸入食材
    clean_ingredients = []
    for ing in ingredients:
        ing = ing.strip()
        if ing and ing not in {"無", "沒有", "無 請直接提供給我料理", "沒有 請推薦給我"}:
            # 分割多個食材（如果用逗號或空格分隔）
            for sub_ing in re.split(r'[,，、\s]+', ing):
                if sub_ing.strip():
                    clean_ingredients.append(sub_ing.strip())

    # 如果還是沒有食材，則至少保留使用者輸入的食材
    if not extracted_ingredients and clean_ingredients:
        extracted_ingredients = clean_ingredients
        extracted_quantity = ["適量"] * len(clean_ingredients)

    # 創建記錄
    recipe_entry = {
        "timestamp": datetime.now().isoformat(),
        "input": clean_ingredients,
        "recipe_ingredients": extracted_ingredients,
        "recipe_quantity": extracted_quantity,
        "user_id": user_id,
        "flavor_preference": preferences.get("flavor_preference", "無"),
        "recipe_type_preference": preferences.get("recipe_type_preference", "無"),
        "avoid_ingredients": preferences.get("avoid_ingredients", "無"),
        "cooking_constraints": preferences.get("cooking_constraints", "無"),
        "dietary_restrictions": preferences.get("dietary_restrictions", "無")
    }

    # 更新 JSON 統計數據
    data["recipe_history"].append(recipe_entry)

    # 寫入檔案
    with open(PREF_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_preference_json():
    """讀取 preferences.json 並回傳 dict，讀不到或格式錯誤就回空 dict"""
    if os.path.exists(PREF_FILE):
        with open(PREF_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
            except (ValueError, json.JSONDecodeError):
                pass
    return {}

def chat_with_llm():
    print("歡迎使用食譜推薦系統！")
    print("輸入 'exit' 或 'quit' 結束對話")
    print("請告訴我您想做的料理或手邊有的食材，我會為您推薦適合的食譜。")
    print("-" * 50)

    # 詢問用戶 ID
    user_id = input("請問您是哪位？(直接按Enter使用'default'): ").strip() or "default"
    
    # 檢查是否有用戶偏好文件存在
    is_first_time_system = not os.path.exists(USER_PREF_FILE)
    
    # 載入現有的用戶數據（如果存在）
    existing_users = {}
    if not is_first_time_system and os.path.exists(USER_PREF_FILE):
        try:
            with open(USER_PREF_FILE, 'r', encoding='utf-8') as f:
                existing_users = json.load(f)
        except (ValueError, json.JSONDecodeError):
            existing_users = {}
    
    # 檢查是否是新用戶
    is_new_user = user_id not in existing_users
    
    # 載入用戶偏好
    user_preferences = load_user_preferences(user_id)
    
    # 如果是新用戶，收集偏好
    if is_new_user:
        print(f"\n歡迎 {user_id}！請先告訴我您的偏好：")
        user_preferences["flavor_preference"] = input("1. 您喜歡什麼口味？(例如：清淡、重口味): ").strip() or "無"
        user_preferences["recipe_type_preference"] = input("2. 您偏好什麼類型的料理？(例如：中式、日式、義式): ").strip() or "無"
        user_preferences["avoid_ingredients"] = input("3. 有什麼食材不喜歡或想避免？: ").strip() or "無"
        user_preferences["cooking_constraints"] = input("4. 對料理時間或份量有沒有特殊要求？: ").strip() or "無"
        user_preferences["dietary_restrictions"] = input("5. 是否有特殊飲食限制？(例如：素食、無麩質、低醣): ").strip() or "無"
        
        # 保存用戶偏好
        save_user_preferences(user_preferences, user_id)
        print("（✅ 用戶偏好已保存）")

    client = genai.Client(
        api_key='AIzaSyC2PCC4FzSWFO5rDK0M9M45dEj4qabkNAk',
    )

    model = "gemini-2.0-flash"
    conversation_history = []

    base_sys = get_optimized_system_prompt()
    names = []
    prefs = load_preference_json()
    summary = ""
    if prefs:
        pi = prefs.get("preferred_ingredients", [])
        pri = prefs.get("preferred_recipe_ingredients", [])
        pq = prefs.get("preferred_recipe_quantity", [])
        summary = (
            f"使用者過去偏好的主要食材：{', '.join(pi) or '無'}；"
            f"常用於食譜的食材及份量：{', '.join(f'{i}({q})' for i,q in zip(pri,pq))}。\n"
        )
        # 加入過去生成的食譜名稱列表
        rh = prefs.get("recipe_history", [])
        if isinstance(rh, list) and rh:
            names = []
            for entry in rh:
                m = re.search(r"料理名稱[:：]\s*(.+)", entry.get("recipe", ""))
                if m:
                    names.append(m.group(1).strip())
            if names:
                summary += "使用者過去生成過的食譜： " + "、".join(names) + "。\n"

    # 如果用戶有偏好，加入到 summary
    if any(v != "無" for k, v in user_preferences.items() if k != "user_id"):
        summary += f"""使用者的口味偏好：{user_preferences['flavor_preference']}；
    料理類型偏好：{user_preferences['recipe_type_preference']}；
    避免的食材：{user_preferences['avoid_ingredients']}；
    料理時間/份量要求：{user_preferences['cooking_constraints']}；
    特殊飲食限制：{user_preferences['dietary_restrictions']}。\n"""
    
    while True:
        try:
            preferences = {
                "flavor_preference": user_preferences["flavor_preference"],
                "recipe_type_preference": user_preferences["recipe_type_preference"],
                "avoid_ingredients": user_preferences["avoid_ingredients"],
                "cooking_constraints": user_preferences["cooking_constraints"],
                "dietary_restrictions": user_preferences["dietary_restrictions"]
            }
            
            # 首次使用系統或新用戶直接詢問食材，跳過風格選擇和偏好更新
            if is_first_time_system or is_new_user:
                # 只詢問食材
                user_input = input("\n今天想用什麼食材做料理？ ").strip()
                is_first_time_system = False  # 重置標記，後續使用正常流程
                is_new_user = False  # 重置新用戶標記
            else:
                # 正常流程：詢問料理風格和食材
                cooking_style = input("\n想要做跟以前類似的料理還是做新的風格的料理？(1: 類似以前 / 2: 新風格): ").strip()
                if cooking_style not in ['1', '2']:
                    print("請輸入 1 或 2")
                    continue
                    
                user_input = input("\n今天想用什麼食材做料理？ ").strip()
                
                have_preferences = input("\n您是否要更新特殊偏好？(y/n): ").strip().lower()
                
                # 如果使用者回答 y，進行五個問答收集偏好
                if have_preferences == 'y':
                    preferences["flavor_preference"] = input(f"1. 您喜歡什麼口味？(例如：清淡、重口味) [當前: {preferences['flavor_preference']}]: ").strip() or preferences["flavor_preference"]
                    preferences["recipe_type_preference"] = input(f"2. 您偏好什麼類型的料理？(例如：中式、日式、義式) [當前: {preferences['recipe_type_preference']}]: ").strip() or preferences["recipe_type_preference"]
                    preferences["avoid_ingredients"] = input(f"3. 有什麼食材不喜歡或想避免？ [當前: {preferences['avoid_ingredients']}]: ").strip() or preferences["avoid_ingredients"]
                    preferences["cooking_constraints"] = input(f"4. 對料理時間或份量有沒有特殊要求？ [當前: {preferences['cooking_constraints']}]: ").strip() or preferences["cooking_constraints"]
                    preferences["dietary_restrictions"] = input(f"5. 是否有特殊飲食限制？(例如：素食、無麩質、低醣) [當前: {preferences['dietary_restrictions']}]: ").strip() or preferences["dietary_restrictions"]
                    
                    # 更新用戶偏好
                    user_preferences.update(preferences)
                    save_user_preferences(user_preferences, user_id)
                    print("（✅ 用戶偏好已更新）")
            
            if user_input.lower() in ['exit', 'quit']:
                print("\n再見！")
                break

            if not user_input:
                continue
            
            # 組合使用者輸入和偏好為完整的請求
            full_request = user_input
            
            # 只有在非首次使用時才根據料理風格調整語境
            if not is_first_time_system and 'cooking_style' in locals():
                if cooking_style == '1' and names:
                    full_request = f"我想要做類似於 {', '.join(names[-3:] if len(names) > 3 else names)} 這樣風格的料理，使用這些食材: {user_input}"
                elif cooking_style == '2':
                    full_request = f"我想要嘗試一種與過去完全不同風格的新料理，使用這些食材: {user_input}"
            else:
                full_request = f"請立即根據以下資訊生成食譜，不要詢問更多問題：我想用這些食材做料理: {user_input}"
            
            # 添加用戶偏好到請求
            if preferences["flavor_preference"] != "無":
                full_request += f"\n我喜歡{preferences['flavor_preference']}的口味"
            if preferences["recipe_type_preference"] != "無":
                full_request += f"\n我偏好{preferences['recipe_type_preference']}料理"
            if preferences["avoid_ingredients"] != "無":
                full_request += f"\n我不喜歡{preferences['avoid_ingredients']}"
            if preferences["cooking_constraints"] != "無":
                full_request += f"\n我希望{preferences['cooking_constraints']}"
            if preferences["dietary_restrictions"] != "無":
                full_request += f"\n我有{preferences['dietary_restrictions']}飲食限制"
            
            # 在最後再次強調直接生成食譜
            full_request += "\n\n請直接生成完整食譜，不要詢問更多問題。遵循之前給出的食譜格式，包含料理名稱、類型、食材列表、步驟說明、烹飪時間和適合份量。"
            
            # 建立最終的 system instruction
            recipe_system_instruction = [
                types.Part(text=summary + base_sys)
            ]

            # 設定生成配置
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="text/plain",
                system_instruction=recipe_system_instruction,
            )
            
            # 準備對話內容
            contents = []
            for msg in conversation_history:
                contents.append(types.Content(
                    role=msg["role"],
                    parts=[types.Part(text=msg["content"])],
                ))
            
            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=full_request)],
            ))

            # 生成回應
            print("\nGemini: ", end="", flush=True)
            response_text = ""
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                print(chunk.text, end="", flush=True)
                response_text += chunk.text

            # 更新對話歷史
            conversation_history.append({"role": "user", "content": full_request})
            conversation_history.append({"role": "model", "content": response_text})

            # 如果真的有生成食譜，才詢問回饋
            if "料理名稱" in response_text and "食材" in response_text and "步驟" in response_text:
                feedback = input("\n你喜歡這份食譜嗎？輸入 y 表示喜歡，n 表示不喜歡：").strip().lower()
                like_flag = 1 if feedback == "y" else 0

                # 若使用者按讚，記錄到 JSON，連同偏好一起存
                if like_flag == 1:
                    store_preference_json(
                        ingredients=[user_input],
                        recipe_text=response_text,
                        preferences=preferences,
                        user_id=user_id
                    )
                    print("（👍 偏好已記錄至 preferences.json）")
                else:
                    print("（👎 不記錄此筆食譜）")

        except KeyboardInterrupt:
            print("\n\n對話已中斷。再見！")
            break
        except Exception as e:
            print(f"\n發生錯誤: {str(e)}")

if __name__ == "__main__":
    init_preference_file()  # 初始化preferences.json文件
    chat_with_llm()
