
import os
import yaml
from collections import Counter

# 使用者可設定區塊
BASE_DIR = "Food"  # 資料集根目錄
REMOVE_CLASS_IDS = {"13", "22"}  # 要移除的類別編號（字串格式）
SPLITS = ["train", "valid", "test"]
DATA_YAML = os.path.join(BASE_DIR, "data.yaml")

def remove_labels_and_images():
    removed_count = 0
    for split in SPLITS:
        label_dir = os.path.join(BASE_DIR, split, "labels")
        image_dir = os.path.join(BASE_DIR, split, "images")
        if not os.path.exists(label_dir):
            continue

        for file in os.listdir(label_dir):
            if file.endswith(".txt"):
                label_path = os.path.join(label_dir, file)
                image_path = os.path.join(image_dir, file.replace(".txt", ".jpg"))
                with open(label_path, "r") as f:
                    lines = f.readlines()
                if any(line.split()[0] in REMOVE_CLASS_IDS for line in lines):
                    os.remove(label_path)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                    removed_count += 1
    return removed_count

def update_data_yaml_and_labels():
    with open(DATA_YAML, "r") as f:
        data = yaml.safe_load(f)

    original_names = data.get("names", [])
    new_names = []
    mapping = {}
    new_id = 0

    for old_id, name in enumerate(original_names):
        if str(old_id) not in REMOVE_CLASS_IDS:
            mapping[str(old_id)] = str(new_id)
            new_names.append(name)
            new_id += 1

    data["names"] = new_names
    data["nc"] = len(new_names)

    with open(DATA_YAML, "w") as f:
        yaml.safe_dump(data, f, allow_unicode=True)

    # 重新寫入標註檔案，重編 class_id
    for split in SPLITS:
        label_dir = os.path.join(BASE_DIR, split, "labels")
        if not os.path.exists(label_dir):
            continue
        for file in os.listdir(label_dir):
            if file.endswith(".txt"):
                path = os.path.join(label_dir, file)
                with open(path, "r") as f:
                    lines = f.readlines()
                new_lines = []
                for line in lines:
                    parts = line.strip().split()
                    if parts and parts[0] in mapping:
                        parts[0] = mapping[parts[0]]
                        new_lines.append(" ".join(parts))
                with open(path, "w") as f:
                    f.write("\n".join(new_lines) + "\n")

    return mapping, new_names, original_names

if __name__ == "__main__":
    print("🚮 Removing unwanted labels and images...")
    removed = remove_labels_and_images()
    print(f"✅ Removed {removed} files related to classes: {', '.join(REMOVE_CLASS_IDS)}")

    print("🔄 Updating class IDs and data.yaml...")
    mapping, new_names, original_names = update_data_yaml_and_labels()
    print("✅ data.yaml updated.")
    print("📦 Class ID Mapping:")
    for old, new in mapping.items():
        print(f"   {old} → {new} : {original_names[int(old)]}")

