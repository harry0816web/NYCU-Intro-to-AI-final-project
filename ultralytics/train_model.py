import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from ultralytics import YOLO
import torch

# 設定檔案路徑
DATA_YAML = "Food/data.yaml"
MODEL_NAME = "yolov8s.pt"  # 初始模型可以先用s，後續可以嘗試m或l
PROJECT_NAME = "runs/food_detection"
EXPERIMENT_NAME = "food_model_v2" # 更改實驗名稱以便於區分

def train_model():
    # 初始化 YOLO 模型 (使用預訓練模型)
    model = YOLO(MODEL_NAME)

    # 嘗試增加epochs，並調整一些超參數
    print("[INFO] Starting training...")
    model.train(
        data=DATA_YAML,
        epochs=40,  # 增加訓練 epochs
        imgsz=640,
        batch=16,
        project=PROJECT_NAME,
        name=EXPERIMENT_NAME,
        device=0,
        exist_ok=True,
        degrees=10.0,  # 隨機旋轉角度
        scale=0.5,  # 隨機縮放
        dropout=0.3,  # Dropout，如果模型過擬合嚴重可以適當增加
        weight_decay=0.0005,  # 權重衰減，防止過擬合

        mosaic=1.0,         # 啟用 Mosaic 增強
        mixup=0.1,          # 啟用 Mixup 增強
        copy_paste=0.2,     # 啟用 Copy-Paste 增強 (需要遮罩)

    )
    print("[INFO] Training finished!")

def validate_model():
    # 驗證模型
    best_model_path = f"{PROJECT_NAME}/{EXPERIMENT_NAME}/weights/best.pt"
    if not os.path.exists(best_model_path):
        print(f"[ERROR] Best model not found at {best_model_path}. Please train the model first.")
        return

    print("[INFO] Starting validation...")
    model = YOLO(best_model_path)
    results = model.val(data=DATA_YAML)
    print("[INFO] Validation finished!")
    print(results)
    # 可以進一步處理 results 物件來獲取更詳細的指標，例如：
    # mAP50 = results.box.map50
    # mAP50_95 = results.box.map
    # print(f"mAP@0.5: {mAP50}")
    # print(f"mAP@0.5:0.95: {mAP50_95}")

def test_model():
    # 測試模型 (從 test set 選一張圖片)
    test_images_dir = "Food/test/images"
    if not os.path.exists(test_images_dir) or not os.listdir(test_images_dir):
        print(f"[ERROR] Test images directory not found or empty: {test_images_dir}")
        return

    test_image = os.path.join(test_images_dir, os.listdir(test_images_dir)[0])  # 選擇第一張圖片
    best_model_path = f"{PROJECT_NAME}/{EXPERIMENT_NAME}/weights/best.pt"
    if not os.path.exists(best_model_path):
        print(f"[ERROR] Best model not found at {best_model_path}. Please train the model first.")
        return

    print(f"[INFO] Testing model on image: {test_image}")
    model = YOLO(best_model_path)
    # show=True 會在螢幕上顯示圖片，如果你在無頭伺服器上運行，這可能會出錯
    # 可以將 show=True 改為 save=True 來保存帶有預測框的圖片
    results = model.predict(source=test_image, save=True, conf=0.25)  # 降低 conf 閾值以顯示更多偵測結果
    print("[INFO] Test finished!")
    # 打印偵測到的物件資訊
    for r in results:
        boxes = r.boxes  # Bounding boxes
        print(f"Detected {len(boxes)} objects in the image.")
        for i, box in enumerate(boxes):
            cls_id = int(box.cls)
            conf = float(box.conf)
            xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            class_name = model.names[cls_id]  # 獲取類別名稱
            print(f"  Object {i+1}: Class: {class_name}, Confidence: {conf:.2f}, BBox: {xyxy}")
    return results

if __name__ == "__main__":
    # 檢查是否有可用的 GPU
    if torch.cuda.is_available():
        print(f"[INFO] CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("[WARNING] CUDA is not available. Training will use CPU, which is much slower.")

    # 訓練模型
    train_model()

    # 驗證模型
    validate_model()

    # 測試模型
    test_model()

print(torch.cuda.is_available())
if torch.cuda.is_available():
    print(f"CUDA Device Name: {torch.cuda.get_device_name(0)}")
