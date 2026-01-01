import os
import random
import shutil
from collections import defaultdict
import re


DATASET_ROOT = r"C:\Users\HONOR\Desktop\archive\BreaKHis_v1\BreaKHis_v1\histology_slides\breast"
OUTPUT_ROOT = r"D:\Split_dataset"
TRAIN_RATIO = 0.8
RANDOM_SEED = 42

random.seed(RANDOM_SEED)


patients = defaultdict(list)

for root, _, files in os.walk(DATASET_ROOT):
    for file in files:
        if not file.lower().endswith(".png"):
            continue

        full_path = os.path.join(root, file)


        filename_without_ext = os.path.splitext(file)[0]


        pattern = r'^SOB_([BM])_([A-Za-z]+)-(.+)-(\d+)-(\d+)$'
        match = re.match(pattern, filename_without_ext)

        if match:
            tumor_class = match.group(1)
            tumor_type = match.group(2)
            patient_id = match.group(3)

            patients[patient_id].append({
                "path": full_path,
                "class": tumor_class,
                "type": tumor_type
            })
        else:

            parts = file.split('_')

            if len(parts) >= 3:
                biopsy = parts[0]
                tumor_class = parts[1]


                patient_part = '_'.join(parts[2:]) if len(parts) > 2 else ""


                if '-' in patient_part:
                    patient_id = patient_part.split('-')[0]
                else:
                    patient_id = patient_part.split('.')[0] if '.' in patient_part else patient_part


                tumor_type = patient_id[0] if patient_id and patient_id[0].isalpha() else "Unknown"


                patient_id_match = re.search(r'(\d+-\d+[A-Za-z]*)', patient_part)
                if patient_id_match:
                    patient_id = patient_id_match.group(1)

                patients[patient_id].append({
                    "path": full_path,
                    "class": tumor_class,
                    "type": tumor_type
                })
            else:
                print(f"警告: 无法解析的文件名: {file}")

print(f"成功解析 {len(patients)} 位患者的数据")
print(f"输出将保存到: {OUTPUT_ROOT}")


print("\n样本数据（前5位患者）:")
for i, (patient_id, images) in enumerate(patients.items()):
    if i >= 5:
        break
    print(f"患者 {patient_id}: {len(images)} 张图片")
    if images:
        print(f"  类别: {images[0]['class']}, 类型: {images[0]['type']}")


patient_ids = list(patients.keys())
random.shuffle(patient_ids)

split_idx = int(TRAIN_RATIO * len(patient_ids))
train_patients = patient_ids[:split_idx]
test_patients = patient_ids[split_idx:]

print(f"\n训练集患者数: {len(train_patients)}")
print(f"测试集患者数: {len(test_patients)}")

assert set(train_patients).isdisjoint(set(test_patients)), \
    "数据泄漏检测: 同一患者同时出现在训练集和测试集!"

print("✓ 无患者级数据泄漏")



def copy_images(patient_list, subset_name):
    copied_count = 0
    for pid in patient_list:
        for item in patients[pid]:

            label = "benign" if item["class"] == "B" else "malignant"
            target_dir = os.path.join(OUTPUT_ROOT, subset_name, label)
            os.makedirs(target_dir, exist_ok=True)


            filename = os.path.basename(item["path"])
            target_path = os.path.join(target_dir, filename)
            shutil.copy2(item["path"], target_path)
            copied_count += 1

    print(f"  {subset_name}集复制了 {copied_count} 张图片")



if os.path.exists(OUTPUT_ROOT):
    shutil.rmtree(OUTPUT_ROOT)
os.makedirs(OUTPUT_ROOT, exist_ok=True)


print("\n复制文件中...")
copy_images(train_patients, "train")
copy_images(test_patients, "test")

print("\n数据集分割完成!")

train_benign_path = os.path.join(OUTPUT_ROOT, "train", "benign")
train_malignant_path = os.path.join(OUTPUT_ROOT, "train", "malignant")
test_benign_path = os.path.join(OUTPUT_ROOT, "test", "benign")
test_malignant_path = os.path.join(OUTPUT_ROOT, "test", "malignant")

train_benign = len([f for f in os.listdir(train_benign_path) if f.endswith('.png')]) if os.path.exists(
    train_benign_path) else 0
train_malignant = len([f for f in os.listdir(train_malignant_path) if f.endswith('.png')]) if os.path.exists(
    train_malignant_path) else 0
test_benign = len([f for f in os.listdir(test_benign_path) if f.endswith('.png')]) if os.path.exists(
    test_benign_path) else 0
test_malignant = len([f for f in os.listdir(test_malignant_path) if f.endswith('.png')]) if os.path.exists(
    test_malignant_path) else 0

print("\n数据集统计:")
print(f"训练集 - 良性: {train_benign} 张, 恶性: {train_malignant} 张, 总计: {train_benign + train_malignant} 张")
print(f"测试集 - 良性: {test_benign} 张, 恶性: {test_malignant} 张, 总计: {test_benign + test_malignant} 张")
print(f"总计: {train_benign + train_malignant + test_benign + test_malignant} 张")
print(f"数据集已保存到: {OUTPUT_ROOT}")