import os
import h5py
import numpy as np
from PIL import Image
from tqdm import tqdm

input_dir = "data/turkey/disk"
output_file = "data/turkey/hdf5/part0.h5"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Find all jpg images in the input_dir (not recursive)
image_files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(".jpg")])

images = []
labels = []  # Dummy label 0 for all

for fname in tqdm(image_files):
    img_path = os.path.join(input_dir, fname)
    img = Image.open(img_path).convert("RGB")
    arr = np.array(img.resize((640, 640)))
    images.append(arr)
    labels.append(0)  # Set to 0, or parse from txt file as needed

images = np.stack(images, axis=0)  # shape (N, H, W, C)
labels = np.array(labels, dtype=np.uint8)

with h5py.File(output_file, "w") as f:
    f.create_dataset("images", data=images, dtype="uint8", compression="gzip")
    f.create_dataset("labels", data=labels, dtype="uint8")

print(f"Saved {len(images)} images to {output_file}")
