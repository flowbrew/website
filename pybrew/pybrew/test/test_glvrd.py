import pytest
from pybrew import glvrd_proofread_io


@pytest.mark.slow
@pytest.mark.pybrew
def test_glvrd_proofread_io():
    tests = (

        ('''
Очень рад, что вам так понравился чай!
''',
            {
                'red': 6.2,
                'blue': 8.0,
                'hints':
                [
                    {
                        'tab': 'red',
                        'penalty': 0,
                        'weight': 0,
                        'name': 'Личное местоимение',
                        'text': 'вам'
                    },
                    {
                        'tab': 'red',
                        'penalty': 0,
                        'weight': 100,
                        'name': 'Усилитель',
                        'text': 'Очень'
                    },
                    {
                        'tab': 'blue',
                        'penalty': 0,
                        'weight': 50,
                        'name': 'Восклицание',
                        'text': 'чай!'
                    },
                ]
            }
         ),


        ('''
Вам и мне знакомо состояние, когда с утра тяжело проснуться, днем! работаешь в полудреме, а вечером издевательски сложно заснуть!

Дела копятся, а энергии не добавляется. Вы чувствуете, что ничего не успеваете.
''',
            {
                'red': 10.0,
                'blue': 9.0,
                'hints':
                [
                    {
                        'tab': 'red',
                        'penalty': 0,
                        'weight': 0,
                        'name': 'Личное местоимение',
                        'text': 'Вам'
                    },
                    {
                        'tab': 'red',
                        'penalty': 0,
                        'weight': 0,
                        'name': 'Личное местоимение',
                        'text': 'мне'
                    },
                    {
                        'tab': 'red',
                        'penalty': 0,
                        'weight': 0,
                        'name': 'Личное местоимение',
                        'text': 'Вы'
                    },
                    {
                        'tab': 'blue',
                        'penalty': 0,
                        'weight': 50,
                        'name': 'Восклицание',
                        'text': 'днем!'
                    },
                    {
                        'tab': 'blue',
                        'penalty': 0,
                        'weight': 50,
                        'name': 'Восклицание',
                        'text': 'заснуть!'
                    },
                ]
            }
         ),


        ('''
Л-Теанин до 2-х раз уменьшает особенно физический и психологический стресс и приносит чувство релаксации.
Что дело в том, что Л-Теанин увеличивает концентрацию гормонов счастья серотонина и дофамина в мозге?
Вы замурчите от удовольствия !!! уже через 2 минуты после чашки чая матча!
''',
            {
                'red': 7.9,
                'blue': 9.6,
                'hints':
                [
                    {
                        'tab': 'red',
                        'penalty': 0,
                        'weight': 100,
                        'name': 'Усилитель',
                        'text': 'особенно'
                    },
                    {
                        'tab': 'red',
                        'penalty': 0,
                        'weight': 50,
                        'name': 'Возможно, риторический вопрос',
                        'text': 'мозге?'
                    },
                    {
                        'tab': 'red',
                        'penalty': 0,
                        'weight': 0,
                        'name': 'Личное местоимение',
                        'text': 'Вы'
                    },
                    {
                        'tab': 'red',
                        'penalty': 0,
                        'weight': 150,
                        'name': 'Многократное восклицание',
                        'text': '!!!'
                    },
                    {
                        'tab': 'blue',
                        'penalty': 0,
                        'weight': 50,
                        'name': 'Восклицание',
                        'text': 'матча!'
                    },
                ]
            }
         ),


         ('''
количество EGCG в зеленом чае достигает 55 мг/г
''',
            {
                'red': 10.0,
                'blue': 10.0,
                'hints': []
            }
         ),
    )

    for text, result in tests:
        r = glvrd_proofread_io(text, use_cache=False)

        assert abs(r['red'] - result['red']) <= 0.01
        assert abs(r['blue'] - result['blue']) <= 0.01

        def s(x):
            return sorted(x, key=str)

        assert s(r['hints']) == s(result['hints'])
