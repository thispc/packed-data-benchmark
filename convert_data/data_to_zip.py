import os
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import PIL.Image
from datasets import ImageDataset
import torch

from convert_data.utils_convert import (
    transform,
    collate_fn,
    collate_fn_encoder_info,
    TARDataset,
)


def generate_zip_data(
    dataset, path, num_files=1, compressed=False, save_encoded=True, encoder_info=False
):
    file_ext = dataset.file_ext
    compression = zipfile.ZIP_LZMA if compressed else zipfile.ZIP_STORED
    out_label_file = "dataset.json"
    labels_json = []

    num_images = len(dataset)

    num_files = np.linspace(0, num_images, num_files + 1, dtype=int)[1:]
    num_file = 0

    if encoder_info:
        collate_fn_ = collate_fn_encoder_info
    else:
        collate_fn_ = collate_fn
    dataloader = torch.utils.data.DataLoader(
        dataset, num_workers=32, batch_size=1, collate_fn=collate_fn_
    )

    for i, batch in enumerate(dataloader):
        image = batch[0][0]
        label = batch[1][0]

        if i == 0:
            fname = path + f"/part{num_file}.zip"
            zip_file = zipfile.ZipFile(fname, "w", compression=compression)

        # Grouping folders with 1000 items per folder
        index_str = str(i).zfill(8)
        archive_fname = "{}/img{}{}".format(index_str[:5], index_str, file_ext)

        if save_encoded:
            image_bits = io.BytesIO()
            if encoder_info:
                info = batch[2][0]
                image_pil = PIL.Image.new(info["mode"], info["size"])
                image_pil.putdata(PIL.Image.fromarray(image).getdata())
                image_pil.format = info["format"]
                image_pil.progressive = info["progressive"]
                image_pil.progression = info["progressive"]
                image_pil.smooth = info["smooth"]
                image_pil.optimize = info["optimize"]
                image_pil.streamtype = info["streamtype"]
                image_pil.dpi = info["dpi"]
                image_pil.layer = info["layer"]
                image_pil.layers = info["layers"]
                image_pil.quantization = info["quantization"]

                format = image_pil.format.lower()
                if format == "png":
                    quality = "png"
                elif format == "jpeg":
                    quality = "keep"

                image_pil.save(
                    image_bits, format=image_pil.format.lower(), quality=quality
                )  # slight discrepancy because compression algorithm might not be same?
            else:
                image_pil = PIL.Image.fromarray(image)
                image_pil.save(image_bits, format="png")

            image_bytes = image_bits.getvalue()
            image_pil.close()
        else:
            # memfile = io.BytesIO()
            # np.save(memfile, image)
            # image_bytes = bytearray(memfile.getvalue())
            image_bytes = image.tobytes()

        zip_file.writestr(archive_fname, image_bytes)
        labels_json.append([archive_fname, int(label)])

        if i + 1 == num_files[num_file]:
            if i + 1 == num_images:
                metadata = {
                    "labels": labels_json,
                    "shape": image.size,
                }
                zip_file.writestr(out_label_file, json.dumps(metadata))
                zip_file.close()
                break
            zip_file.writestr(out_label_file, json.dumps(metadata))
            zip_file.close()

            num_file += 1
            fname = path + f"/part{num_file}.zip"
            zip_file = zipfile.ZipFile(fname)
            labels_json = []
    return


def cifar10_to_zip(num_files, save_encoded=False, encoder_info=False):
    output_path = "../data/cifar10/zip"
    Path(output_path).mkdir(parents=True, exist_ok=True)

    data_path = "../data/cifar10/disk/"
    dataset = ImageDataset(data_path, encoder_info=encoder_info)
    generate_zip_data(
        dataset, output_path, num_files=num_files, save_encoded=save_encoded
    )


def imagenet10k_to_zip(num_files, save_encoded, resize=False, encoder_info=False):
    output_path = "../data/imagenet10k/zip"
    Path(output_path).mkdir(parents=True, exist_ok=True)

    if resize:
        resize_dim = 256
        transform_ = transform(resize_dim)
    else:
        transform_ = None

    data_path = "../data/imagenet10k/disk/"
    dataset = ImageDataset(
        data_path,
        transform=transform_,
        prefix="ILSVRC2012_val_",
        offset_index=1,
        encoder_info=encoder_info,
    )
    generate_zip_data(
        dataset,
        output_path,
        num_files=num_files,
        save_encoded=save_encoded,
        encoder_info=encoder_info,
    )


def ffhq_to_zip(num_files, save_encoded=False, encoder_info=False):
    output_path = "/scratch-shared/{}/ffhq/zip/".format(os.getenv("USER"))

    Path(output_path).mkdir(parents=True, exist_ok=True)

    data_path = "/scratch-shared/{}/ffhq/tar/ffhq_images.tar".format(os.getenv("USER"))
    dataset = TARDataset(
        data_path,
        encoder_info=encoder_info,
        label_file="/scratch-shared/{}/ffhq/tar/members".format(os.getenv("USER")),
    )

    generate_zip_data(
        dataset,
        output_path,
        num_files=num_files,
        save_encoded=save_encoded,
        encoder_info=encoder_info,
    )
def turkey_to_zip(num_files=1, save_encoded=False, encoder_info=False):
    output_path = "../data/turkey/zip"
    Path(output_path).mkdir(parents=True, exist_ok=True)

    data_path = "../data/turkey/disk/"
    dataset = ImageDataset(data_path, encoder_info=encoder_info)
    generate_zip_data(
        dataset, output_path, num_files=num_files, save_encoded=save_encoded
    )


if __name__ == "__main__":
    """
    Creates .zip file(s) from a given dataset.

    1. Provide the output path to the zip file and the path to the input files
    2. Choose number of files to split the data into to
    3. Create a torch dataset instance to iterate through
    4. Choose by saving the images in bytes or numpy arrays
       Converting and saving the bytes is 8 times slower but the files are 2 times smaller for images of 256x256x3
       The byte version serializes the image with lossless PNG or the original JPEG compression
    """
    # Number of partitions/shard/files to subdivide the dataset into
    num_files = 1
    # Flag to save as bytes or H5 arrays
    save_encoded = False
    # Flag to use the original encoding
    encoder_info = False
    # Flag to resize the samples to a common resolution
    resize = False
    # cifar10_to_zip(num_files, save_encoded=save_encoded, encoder_info=encoder_info)
    # imagenet10k_to_zip(num_files, save_encoded=save_encoded, resize=resize, encoder_info=encoder_info)
    # ffhq_to_zip(num_files, save_encoded=save_encoded, encoder_info=encoder_info)
    # turkey_to_zip(num_files, save_encoded=save_encoded, encoder_info=encoder_info)
