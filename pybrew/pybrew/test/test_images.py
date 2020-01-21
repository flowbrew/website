import pytest
from pybrew import bake_images_tasks


def test_bake_images_tasks():
    images = {
        'blog/folder.png': None,
        'blog/b.svg': '<NO DATA>',
        'blog/b.webm': '<NO DATA>',
        'blog/a.png': '<NO DATA>',
        'blog/b.jpg': '<NO DATA>',
        'blog/c.jpeg': '<NO DATA>',
        'a.png': '<NO DATA>',
        'b.jpg': '<NO DATA>',
    }

    baked_images = {
        # 'blog/a.png': '<NO DATA>',
        'blog/a_256.png': '<NO DATA>',
        'blog/b.jpg': '<NO DATA>',
        # 'blog/b_256.jpg': '<NO DATA>',
        'blog/c.jpeg': '<NO DATA>',
        'blog/c_256.jpeg': '<NO DATA>',
        'a.png': '<NO DATA>',
        'a_256.png': '<NO DATA>',
        # 'b.jpg': '<NO DATA>',
        'b_256.jpg': '<NO DATA>',
        'c.jpeg': '<NO DATA>',
        'c_256.jpeg': '<NO DATA>',
    }

    result_tasks = [
        ('blog/a.png',   0, 'blog/a.png'),
        ('blog/b.jpg', 256, 'blog/b_256.jpg'),
        ('b.jpg',        0, 'b.jpg'),
        (None,           0, 'c.jpeg'),
        (None,           0, 'c_256.jpeg'),
    ]

    assert result_tasks == bake_images_tasks(
        images=images,
        baked_images=baked_images,
        resolutions=[0, 256],
    )
