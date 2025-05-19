from ultralytics import YOLO

def detect_single_image(image_path):
    # 載入訓練好的模型
    # model = YOLO("../runs/food_detection/food_model/weights/best.pt")
    model = YOLO("C:/Users/USER/Documents/Py/AI_final/runs/food_detection/food_model_v2/weights/best.pt")
    
    # 執行圖片檢測
    results = model.predict(source=image_path, show=True, save=True, save_txt=True)
    
    print("[INFO] Detection finished!")
    return results

# 測試用
detect_single_image("ultralytics/Food/myimage/11.jpg")
