#!/usr/bin/env python3

import glob
import os
import argparse
import os.path
import tinify
import shutil
import re
from PIL import Image
from pathlib import Path

RESOLUTIONS = [0, 256, 512, 1024, 2048]


def all_images(suffix=''):
    return (
        os.path.normpath(filename)
        for filename
        in glob.iglob(f'./assets/img{suffix}/' + '**/**/*', recursive=True)
        if os.path.splitext(filename)[1] in ('.png', '.jpg')
    )


def compressed_image_name(image, resolution):
    fn, fe = os.path.splitext(image)
    if resolution != 0:
        return f'{fn.replace("/img", "/img_gen")}_{resolution}{fe}'
    else:
        return f'{fn.replace("/img", "/img_gen")}{fe}'


def extract_resoltion(image):
    res = re.match(r'.*?_(\d*)\..*', image)
    if res:
        return int(res.group(1))
    return 0

def orig_image_name(image):
    res = re.match(r'(.*?)_\d*(\..*)', image)
    if res:
        res_ = res.group(1) + res.group(2)
    else:
        res_ = image
    return res_.replace("/img_gen", "/img")

def image_width(image):
    return Image.open(image).size[0]

def compress_image(image, resolution):
    cin = compressed_image_name(image, resolution)
    if os.path.isfile(cin):
        return
    Path(os.path.dirname(cin)).mkdir(parents=True, exist_ok=True)
    source = tinify.from_file(image)

    if resolution != 0:
        resized = source.resize(
            method="scale",
            width=resolution,
        )
        resized.to_file(cin)
    else:
        source.to_file(cin)

    print('done baking', cin)


def process_image(image):
    [compress_image(image, x) for x in RESOLUTIONS]


def cleanup_image(image):
    resolution = extract_resoltion(image)
    oin = orig_image_name(image)
    if resolution in RESOLUTIONS and os.path.isfile(oin):
        return
    os.remove(image)
    print('removed', image)


def main(args):
    tinify.key = args.tinify_key
    [cleanup_image(x) for x in all_images('_gen')]
    [process_image(x) for x in all_images()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--tinify_key',
                        help='Access key to tinypng.com API')
    main(parser.parse_args())
