import pytest
from pybrew import yandex_speller_io


@pytest.mark.slow
@pytest.mark.pybrew
@pytest.mark.skip
def test_yandex_speller_io():
    tests = (
        (
            'Карова дает малако',
            [
                {
                    'error': 'Слова нет в словаре.',
                    'word': 'Карова',
                    'hints': ['Корова', 'Карова'],
                },
                {
                    'error': 'Слова нет в словаре.',
                    'word': 'малако',
                    'hints': ['молоко', 'малака', 'малоко'],
                },
            ]
        ),
    )

    for text, result in tests:
        r = yandex_speller_io(text, use_cache=False)

        def s(x):
            return sorted(x, key=lambda y: y['word'])

        assert s(r) == s(result)
