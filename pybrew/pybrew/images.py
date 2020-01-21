import pytest
import glob
import os
import argparse
import os.path
import tinify
import shutil
import re
from PIL import Image
from pathlib import Path


from .fun import curry, chain_, pipe, filter, filesystem_to_dict_io, comp, map, chain


def bake_images_tasks(
    images: dict,
    baked_images: dict,
    resolutions: list = [0, 256, 512, 1024, 2048],
) -> list:
    def _translate_image(resolutions, image):
        root, extension = os.path.splitext(image)
        if extension not in {'.png', '.jpg', '.jpeg'}:
            return ()
        return (
            (image, x, f'{root}_{x}{extension}')
            if x else
            (image, x, f'{root}{extension}')
            for x in resolutions
        )

    def _extract_original_image(image):
        res = re.match(r'(.*?)_\d*(\..*)', image)
        if res:
            return res.group(1) + res.group(2)
        return image

    to_delete = [
        (None, 0, x) for x in baked_images.keys()
        if _extract_original_image(x) not in images.keys()
    ]

    to_add = pipe(
        (_translate_image(resolutions, p)
            for p, data in images.items() if data),
        chain_,
        filter(lambda x: x[2] not in baked_images.keys())
    )

    return comp(list, chain)(to_add, to_delete)


def bake_images_io(images_path, baked_images_path):
    tasks = bake_images_tasks(
        images=filesystem_to_dict_io(
            images_path, index_only=True
        ),
        baked_images=filesystem_to_dict_io(
            baked_images_path, index_only=True
        ),
    )

    def _bake_image_io(image, resolution, dest):
        dest_image = dest.replace(images_path, baked_images_path, 1)

        if not image:
            os.remove(dest_image)
            print('removed unlinked image', dest_image)
        else:
            Path(
                os.path.dirname(dest_image)
            ).mkdir(
                parents=True,
                exist_ok=True
            )

            source = tinify.from_file(image)

            if resolution != 0:
                resized = source.resize(method='scale', width=resolution)
                resized.to_file(dest_image)
            else:
                source.to_file(dest_image)

            print('done baking', dest_image)

    force(_bake_image_io(*x) for x in tasks)
