import pytest
import glob
import os
import argparse
import os.path
import tinify
import shutil
import re
from pathlib import Path


from .fun import curry, chain_, pipe, filter, filesystem_to_dict_io, comp, map, chain, force


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


def _bake_image_io(images_path, baked_images_path, image, resolution, dest):
    dest_ = os.path.join(baked_images_path, dest)
    image_ = os.path.join(images_path, image)

    if not image:
        os.remove(dest_)
        print('removed unlinked image', dest_)
    else:
        Path(
            os.path.dirname(dest_)
        ).mkdir(
            parents=True,
            exist_ok=True
        )

        source = tinify.from_file(image_)

        if resolution != 0:
            resized = source.resize(method='scale', width=resolution)
            resized.to_file(dest_)
        else:
            source.to_file(dest_)

        print('done baking', image_, '->', dest_)


def bake_images_io(tinify_key, images_path, baked_images_path, **kwargs):
    tinify.key = tinify_key

    tasks = bake_images_tasks(
        images=filesystem_to_dict_io(
            images_path, index_only=True
        ),
        baked_images=filesystem_to_dict_io(
            baked_images_path, index_only=True
        ),
    )

    force(_bake_image_io(images_path, baked_images_path, *x) for x in tasks)

    return tasks
