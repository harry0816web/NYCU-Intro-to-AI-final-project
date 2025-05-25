from ultralytics import YOLO
import os
import shutil

def clean_label_dir(label_dir):
    if os.path.exists(label_dir):
        shutil.rmtree(label_dir)
        #print(f"[INFO] 已清空資料夾：{label_dir}")


def detect_single_image(image_path):
    # 載入訓練好的模型
    labels_dir = "runs/detect/exp/labels"
    clean_label_dir(labels_dir)

    model = YOLO("C:/Users/USER/Documents/Py/AI_final/runs/food_detection/food_model_v2/weights/best.pt")
    
    # 執行圖片檢測，並覆蓋輸出資料夾
    results = model.predict(
        source=image_path,
        show=True,
        save=True,
        save_txt=True,
        project="runs/detect",  # 固定輸出位置
        name="exp",             # 固定資料夾名稱
        exist_ok=True,           # 覆蓋舊輸出
        verbose=False
    )

    #print("[INFO] Detection finished!")

    # 指定 labels 資料夾路徑
    labels_dir = "runs/detect/exp/labels"

    # 產生中文食材清單並輸出到同一資料夾
    generate_chinese_ingredient_list(labels_dir)

    return results

def generate_chinese_ingredient_list(labels_dir):
    # 中文食材對應（index 對應 class_id）
    names = ['豆子', '牛肉', '甜椒', '紅蘿蔔', '雞肉', '雞蛋', '魚', '大蒜', '檸檬', '洋蔥',
             '義大利麵', '馬鈴薯', '番茄', '酪梨', '甜菜根', '花椰菜', '高麗菜', '菜花',
             '芹菜', '球芽甘藍', '玉米', '小黃瓜', '茄子', '辣椒', '豌豆', '南瓜', '紅豆',
             '小蘿蔔', '沙拉葉', '扁南瓜', '絲瓜']

    detected_classes = set()

    # 掃描 labels 目錄中的所有 txt 檔
    if not os.path.exists(labels_dir):
        print(f"[WARNING] Label directory not found: {labels_dir}")
        return

    for file in os.listdir(labels_dir):
        if file.endswith(".txt"):
            with open(os.path.join(labels_dir, file), "r") as f:
                for line in f:
                    class_id = int(line.strip().split()[0])
                    detected_classes.add(class_id)

    # 轉換成中文食材名稱
    detected_names = [names[i] for i in sorted(detected_classes)]

    # 輸出到 labels 目錄下的 txt 檔
    output_path = os.path.join(labels_dir, "ingredients.txt")
    with open(output_path, "w", encoding="utf-8") as out:
        for name in detected_names:
            out.write(name + "\n")

    #print(f"[INFO] 食材清單已輸出至 {output_path}")

# 測試用
detect_single_image("ultralytics/Food/myimage/11.jpg")
