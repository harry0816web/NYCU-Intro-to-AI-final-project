from ultralytics import YOLO

def detect_single_image(image_path):
    # 載入訓練好的模型
    # model = YOLO("../runs/food_detection/food_model/weights/best.pt")
    model = YOLO("C:/Users/harry/OneDrive/Desktop/AI_test/v8s.pt")
    
    # 執行圖片檢測
    results = model.predict(source=image_path, show=True, save=True, save_txt=True)
    
    print("[INFO] Detection finished!")
    return results

# 測試用
detect_single_image("C:/Users/harry/OneDrive/Desktop/AI_test/test1.png")



# 'Beans', 'Beef', 'Bell pepper', 'Carrot', 'Chicken', Egg', 'Fish', 'Garlic', 'Lemon', 'Onion', 'Pasta', 'Potato', 'Tomato', 'avocado', 'beet', 'broccoli', 'cabbage', 'cayliflower', 'celery', 'choux de bruxelles', 'corn', 'cucumber'

