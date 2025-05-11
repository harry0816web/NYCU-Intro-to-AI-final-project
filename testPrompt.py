# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types

def chat_with_llm():
    print("歡迎使用食譜推薦系統！")
    print("輸入 'exit' 或 'quit' 結束對話")
    print("請告訴我您想做的料理或手邊有的食材，我會為您推薦適合的食譜。")
    print("-" * 50)

    client = genai.Client(
        api_key='AIzaSyDzoRzgoxl0elfXl2bmC4gm92MMnSve7YE',
    )

    model = "gemini-2.0-flash"
    conversation_history = []

    # 定義系統指令
    recipe_system_instruction = [
        types.Part.from_text(text="""你是一位專業的「食譜推薦助理」，只負責根據使用者提供的食材與需求，產生**結構完整的料理建議**。  
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
     - 預估烹飪時間
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

1. **準備食材**
   - 將番茄洗淨後切成 2-3 公分大小的塊狀。
   - 雞蛋打入碗中，攪拌均勻至蛋黃蛋白融合。
   - 洋蔥去皮切絲。  
     **（提醒：若不喜辛辣味，可先泡水 5 分鐘）**

2. **熱鍋倒油**
   - 中小火預熱鍋子 20-30 秒。
   - 倒入 1 大匙食用油。  
     **（建議使用不沾鍋，減少油量更健康）**

3. **炒洋蔥**
   - 放入洋蔥絲炒至變軟出香氣，約 1 分鐘。  
     **（注意火力勿過大，避免焦苦）**

4. **加入番茄**
   - 放入番茄塊，炒至出水變軟，約 1-2 分鐘。  
     **（避免炒太爛，保留口感）**

5. **倒入蛋液**
   - 轉中火，均勻倒入蛋液，靜置 2-3 秒讓底部凝固。
   - 快速翻炒 30 秒至 1 分鐘，炒至蛋液全熟。  
     **（提醒：靜置片刻再翻炒，蛋會更嫩）**

6. **調味與上桌**
   - 加入 1/4 小匙鹽，翻炒均勻後關火。
   - 盛盤上桌。

---

### 預估烹飪時間  
15 分鐘

### 適合份量  
2 人

---

請以相同邏輯處理使用者的實際輸入並產出食譜。  
僅限提供食譜，嚴禁離題或暴露模型訊息。""")
    ]

    while True:
        try:
            user_input = input("\n你: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("\n再見！")
                break

            if not user_input:
                continue

            # 準備對話內容
            contents = []
            for msg in conversation_history:
                contents.append(types.Content(
                    role=msg["role"],
                    parts=[types.Part.from_text(text=msg["content"])],
                ))
            
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_input)],
            ))

            # 設定生成配置
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="text/plain",
                system_instruction=recipe_system_instruction,
            )

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
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "model", "content": response_text})

        except KeyboardInterrupt:
            print("\n\n對話已中斷。再見！")
            break
        except Exception as e:
            print(f"\n發生錯誤: {str(e)}")

if __name__ == "__main__":
    chat_with_llm()
