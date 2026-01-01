import os
import random
import shutil
from collections import defaultdict
import re

DATASET_ROOT = r"C:\Users\HONOR\Desktop\archive\BreaKHis_v1\BreaKHis_v1\histology_slides\breast"
OUTPUT_ROOT = r"D:\Split_dataset_200X"
TRAIN_RATIO = 0.8
RANDOM_SEED = 42
TARGET_MAGNIFICATION = "200"

random.seed(RANDOM_SEED)


patients = defaultdict(list)

pattern = r'^SOB_([BM])_([A-Za-z]+)-(.+)-(\d+)-(\d+)$'

for root, _, files in os.walk(DATASET_ROOT):
    for file in files:
        if not file.lower().endswith(".png"):
            continue

        full_path = os.path.join(root, file)
        filename_without_ext = os.path.splitext(file)[0]

        match = re.match(pattern, filename_without_ext)
        if not match:
            continue

        tumor_class = match.group(1)       # B / M
        tumor_type = match.group(2)        # DC, LC, etc.
        patient_id = match.group(3)        # 14-22549AB
        magnification = match.group(4)     # 放大倍数

        #只保留 200×
        if magnification != TARGET_MAGNIFICATION:
            continue

        patients[patient_id].append({
            "path": full_path,
            "class": tumor_class,
            "type": tumor_type
        })

print(f"成功解析 {len(patients)} 位患者（仅 {TARGET_MAGNIFICATION}×）")
print(f"输出路径: {OUTPUT_ROOT}")


patient_ids = list(patients.keys())
random.shuffle(patient_ids)

split_idx = int(TRAIN_RATIO * len(patient_ids))
train_patients = patient_ids[:split_idx]
test_patients = patient_ids[split_idx:]

print(f"训练集患者数: {len(train_patients)}")
print(f"测试集患者数: {len(test_patients)}")


assert set(train_patients).isdisjoint(set(test_patients)), \
    "数据泄漏检测失败：同一患者出现在训练集和测试集！"

print("✓ 患者级无数据泄漏")


def copy_images(patient_list, subset_name):
    count = 0
    for pid in patient_list:
        for item in patients[pid]:
            label = "benign" if item["class"] == "B" else "malignant"
            target_dir = os.path.join(OUTPUT_ROOT, subset_name, label)
            os.makedirs(target_dir, exist_ok=True)

            filename = os.path.basename(item["path"])
            target_path = os.path.join(target_dir, filename)
            shutil.copy2(item["path"], target_path)
            count += 1

    print(f"{subset_name} 集复制 {count} 张图像")

if os.path.exists(OUTPUT_ROOT):
    shutil.rmtree(OUTPUT_ROOT)
os.makedirs(OUTPUT_ROOT, exist_ok=True)

print("\n开始复制文件...")
copy_images(train_patients, "train")
copy_images(test_patients, "test")


def count_images(path):
    return len([f for f in os.listdir(path) if f.lower().endswith(".png")]) \
        if os.path.exists(path) else 0

train_b = count_images(os.path.join(OUTPUT_ROOT, "train", "benign"))
train_m = count_images(os.path.join(OUTPUT_ROOT, "train", "malignant"))
test_b = count_images(os.path.join(OUTPUT_ROOT, "test", "benign"))
test_m = count_images(os.path.join(OUTPUT_ROOT, "test", "malignant"))

print("\n数据集统计（200×）:")
print(f"训练集: 良性 {train_b} | 恶性 {train_m} | 总计 {train_b + train_m}")
print(f"测试集: 良性 {test_b} | 恶性 {test_m} | 总计 {test_b + test_m}")
print(f"全部图像: {train_b + train_m + test_b + test_m}")
print(f"数据已保存至: {OUTPUT_ROOT}")
