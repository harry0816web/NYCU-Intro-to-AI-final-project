import os
from collections import Counter
import pandas as pd

# 設定你的 YOLO dataset 根目錄
base_dir = "path/to/your/dataset"  # 例如: "./Food"
splits = ["train", "valid", "test"]

# 統計每個 split 中的 class 出現次數
label_counts = {}

for split in splits:
    label_dir = os.path.join(base_dir, split, "labels")
    class_counter = Counter()

    if not os.path.exists(label_dir):
        print(f"[警告] 找不到標註資料夾: {label_dir}")
        continue

    for filename in os.listdir(label_dir):
        if filename.endswith(".txt"):
            with open(os.path.join(label_dir, filename), "r") as f:
                for line in f:
                    class_id = line.strip().split()[0]
                    class_counter[class_id] += 1

    label_counts[split] = class_counter

# 建立 DataFrame 統整各 split 資訊
all_labels = sorted(set().union(*[c.keys() for c in label_counts.values()]), key=int)
df = pd.DataFrame(index=all_labels)

for split in splits:
    df[split] = [label_counts[split].get(lbl, 0) for lbl in all_labels]

df.index.name = "class_id"
df = df.astype(int)

# 顯示結果
print("\n🧾 Label 出現次數統計表：")
print(df)

# 顯示只出現在 valid/test 但不在 train 的類別（可能導致 valid loss 急升）
missing_in_train = df[(df["train"] == 0) & ((df["valid"] > 0) | (df["test"] > 0))]
if not missing_in_train.empty:
    print("\n⚠️ 下列類別未出現在 train，但出現在 valid/test：")
    print(missing_in_train)
else:
    print("\n✅ 所有 valid/test 類別在 train 中均有出現。")
