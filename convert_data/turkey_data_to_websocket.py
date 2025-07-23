import tarfile
import os

image_dir = "data/turkey/disk"  # Adjust if needed
output_tar = "data/turkey/webdataset/shard0.tar"
os.makedirs(os.path.dirname(output_tar), exist_ok=True)

with tarfile.open(output_tar, "w") as tar:
    for filename in sorted(os.listdir(image_dir)):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            image_path = os.path.join(image_dir, filename)
            base = os.path.splitext(filename)[0]
            # Look for a label file for this image (assuming .txt)
            label_path = os.path.join(image_dir, f"{base}.txt")
            tar.add(image_path, arcname=f"{base}.jpg")
            if os.path.exists(label_path):
                tar.add(label_path, arcname=f"{base}.txt")
