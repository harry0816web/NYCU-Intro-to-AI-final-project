from ultralytics import YOLOWorld
import numpy as np
from PIL import Image
import os
from glob import glob

# 設定類別
CLASSES = ['Beans', 'Beef', 'Bell pepper', 'Carrot', 'Chicken', 'Egg', 'Fish', 'Garlic', 'Lemon', 'Onion', 'Pasta', 'Potato', 'Tomato', 'avocado', 'beet', 'broccoli', 'cabbage', 'cayliflower', 'celery', 'choux de bruxelles', 'corn', 'cucumber', 'eggplant', 'hot pepper', 'peas', 'pumpkin', 'red beans', 'rediska', 'salad', 'squash-patisson', 'vegetable marrow']

model = YOLOWorld("yolov8x-worldv2.pt")
model.set_classes(CLASSES)

def iou(box1, box2):
    # box: [x_center, y_center, w, h] (YOLO 格式, 相對座標)
    x1_min = box1[0] - box1[2]/2
    y1_min = box1[1] - box1[3]/2
    x1_max = box1[0] + box1[2]/2
    y1_max = box1[1] + box1[3]/2

    x2_min = box2[0] - box2[2]/2
    y2_min = box2[1] - box2[3]/2
    x2_max = box2[0] + box2[2]/2
    y2_max = box2[1] + box2[3]/2

    inter_xmin = max(x1_min, x2_min)
    inter_ymin = max(y1_min, y2_min)
    inter_xmax = min(x1_max, x2_max)
    inter_ymax = min(y1_max, y2_max)

    inter_w = max(0, inter_xmax - inter_xmin)
    inter_h = max(0, inter_ymax - inter_ymin)
    inter_area = inter_w * inter_h

    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    area2 = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = area1 + area2 - inter_area

    if union_area == 0:
        return 0
    return inter_area / union_area

def load_yolo_label(label_path):
    # 讀取 YOLO 格式 label
    labels = []
    if not os.path.exists(label_path):
        return labels
    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            cls, x, y, w, h = map(float, parts)
            labels.append([int(cls), x, y, w, h])
    return labels

# 累積所有預測與標註
all_true = [[] for _ in CLASSES]
all_pred = [[] for _ in CLASSES]

image_dir = "test/images"
label_dir = "test/labels"
image_files = sorted(glob(os.path.join(image_dir, "*.jpg")))

for img_path in image_files:
    img_name = os.path.basename(img_path)
    label_path = os.path.join(label_dir, img_name.replace('.jpg', '.txt'))

    # 預測
    results = model.predict(img_path, conf=0.01, save=True)
    result = results[0]
    boxes = result.boxes.xyxy.cpu().numpy()  # (N, 4)
    classes = result.boxes.cls.cpu().numpy() # (N,)
    scores = result.boxes.conf.cpu().numpy() # (N,)

    # 取得圖片尺寸
    img = Image.open(img_path)
    img_w, img_h = img.size

    # 轉 YOLO 格式
    pred_labels = []
    for box, cls, score in zip(boxes, classes, scores):
        x1, y1, x2, y2 = box
        x_center = (x1 + x2) / 2 / img_w
        y_center = (y1 + y2) / 2 / img_h
        width = (x2 - x1) / img_w
        height = (y2 - y1) / img_h
        pred_labels.append([int(cls), x_center, y_center, width, height, score])

    # 讀取 ground truth
    gt_labels = load_yolo_label(label_path)

    # 按類別分開
    for c in range(len(CLASSES)):
        gt_cls = [l[1:] for l in gt_labels if l[0] == c]
        pred_cls = [l[1:] + [l[5]] for l in pred_labels if l[0] == c]  # [x, y, w, h, score]
        all_true[c].extend(gt_cls)
        all_pred[c].extend(pred_cls)

def compute_ap(recall, precision):
    # VOC 11-point
    ap = 0.0
    for t in np.arange(0, 1.1, 0.1):
        if np.sum(recall >= t) == 0:
            p = 0
        else:
            p = np.max(precision[recall >= t])
        ap += p / 11.0
    return ap

ious_thres = 0.5
aps = []
precisions = []
recalls = []

for c in range(len(CLASSES)):
    preds = np.array(all_pred[c])  # [x, y, w, h, score]
    gts = np.array(all_true[c])    # [x, y, w, h]
    if len(preds) == 0 and len(gts) == 0:
        continue
    if len(preds) == 0:
        recalls.append(0)
        precisions.append(0)
        aps.append(0)
        continue
    if len(gts) == 0:
        recalls.append(0)
        precisions.append(0)
        aps.append(0)
        continue

    # 按 score 排序
    preds = preds[np.argsort(-preds[:, 4])]
    tp = np.zeros(len(preds))
    fp = np.zeros(len(preds))
    matched = np.zeros(len(gts))

    for i, pred in enumerate(preds):
        ious = np.array([iou(pred[:4], gt) for gt in gts])
        max_iou_idx = np.argmax(ious) if len(ious) > 0 else -1
        if len(ious) > 0 and ious[max_iou_idx] >= ious_thres and matched[max_iou_idx] == 0:
            tp[i] = 1
            matched[max_iou_idx] = 1
        else:
            fp[i] = 1

    tp_cum = np.cumsum(tp)
    fp_cum = np.cumsum(fp)
    recall = tp_cum / (len(gts) + 1e-6)
    precision = tp_cum / (tp_cum + fp_cum + 1e-6)
    ap = compute_ap(recall, precision)
    recalls.append(recall[-1] if len(recall) else 0)
    precisions.append(precision[-1] if len(precision) else 0)
    aps.append(ap)

print(f"Precision: {np.mean(precisions):.4f}")
print(f"Recall: {np.mean(recalls):.4f}")
print(f"mAP@50: {np.mean(aps):.4f}")


