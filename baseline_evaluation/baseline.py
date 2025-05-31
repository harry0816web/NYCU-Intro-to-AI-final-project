from ultralytics import YOLOWorld

# 設定類別
CLASSES = ['Beans', 'Beef', 'Bell pepper', 'Carrot', 'Chicken', 'Egg', 'Fish', 'Garlic', 'Lemon', 'Onion', 'Pasta', 'Potato', 'Tomato', 'avocado', 'beet', 'broccoli', 'cabbage', 'cayliflower', 'celery', 'choux de bruxelles', 'corn', 'cucumber', 'eggplant', 'hot pepper', 'peas', 'pumpkin', 'red beans', 'rediska', 'salad', 'squash-patisson', 'vegetable marrow']

model = YOLOWorld("yolov8x-worldv2.pt")
model.set_classes(CLASSES)
# results = model.predict("test.jpg")
results = model.predict("C:/Users/harry/OneDrive/Desktop/AI_test/test/images/-1-34_jpg.rf.2c8771e4f88bf964ed43fbd7a1fe7da9.jpg", conf=0.1, save=True)
print(results.box.map)
print(results.box.map50)
print(results.box.mr)

results[0].save("test_pred.jpg")

results[0].show()
