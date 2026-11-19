"""Восстановление кодов и разбор правил в постфиксной записи.

Модель левых частей: F(A), F(G(z)), F(H(x,y)), F(J(x,y)).
Форма правых частей третьего и четвёртого правил заранее не задана:
требуем, чтобы они разбирались в один терм с найденными символами.
Готовый цифровой словарь и verify_solution.py здесь не используются.
"""
from itertools import combinations
from math import comb

from data import GIVEN


ARITY = {'A': 0, 'B': 0, 'C': 0, 'F': 1, 'G': 1, 'H': 2, 'J': 2,
         'x': 0, 'y': 0, 'z': 0}


def decode_term(text, code):
    """Вернуть дерево (имя, дети) или None, если строка не задаёт один терм.

    Вызывается для суффиксно-свободного словаря: коды снимаются с конца,
    затем постфиксная последовательность разбирается стеком.
    """
    names = []
    while text:
        matches = [name for name, word in code.items() if text.endswith(word)]
        if len(matches) != 1:
            return None
        name = matches[0]
        names.append(name)
        text = text[:-len(code[name])]
    stack = []
    for name in reversed(names):
        arity = ARITY[name]
        if len(stack) < arity:
            return None
        children = tuple(stack[-arity:]) if arity else ()
        if arity:
            del stack[-arity:]
        stack.append((name, children))
    return stack[0] if len(stack) == 1 else None


def format_term(tree):
    name, children = tree
    return name + ('(' + ', '.join(map(format_term, children)) + ')' if children else '')


def rule3_splits(left, right):
    """Разбиения left = x y H F, при которых right задаёт любой один терм."""
    # Три границы делят строку на четыре непустых блока.
    for i, j, k in combinations(range(1, len(left)), 3):
        x, y, h, f = left[:i], left[i:j], left[j:k], left[k:]
        code = {'x': x, 'y': y, 'H': h, 'F': f}
        if suffix_free(list(code.values())) and decode_term(right, code) is not None:
            yield x, y, h, f


def suffix_free(words):
    """Ни один код не является суффиксом другого, в том числе равным ему."""
    return all(
        i == j or not word.endswith(other)
        for i, word in enumerate(words)
        for j, other in enumerate(words)
    )


def recover(matches, given=GIVEN):
    """Получить все словари в выбранной форме правил с суффиксной свободой.

    matches — уже найденные разбиения третьего правила; повторно их не ищем.
    F, G — унарные символы; H, J — бинарные; A, B, C — константы;
    x, y, z — переменные правил. Ограничения длины кода нет.
    """
    if len(given) != 4:
        raise ValueError('Ожидались четыре правила')
    (left1, b), (left2, c), _, (left4, right4) = given

    for x, y, h, f in matches:
        # Четвёртая левая часть должна иметь вид x y J F.
        if not left4.startswith(x + y) or not left4.endswith(f):
            continue
        if len(left4) <= len(x + y + f):
            continue
        j = left4[len(x + y):-len(f)]
        # Структуру справа не угадываем: разбираем любой корректный терм
        # над уже найденными символами. Новый символ справа здесь не вводим.
        partial_code = {'x': x, 'y': y, 'H': h, 'F': f, 'J': j}
        if not suffix_free(list(partial_code.values())):
            continue
        if decode_term(right4, partial_code) is None:
            continue

        # Первые два правила пробуем как F(A) -> B и F(G(z)) -> C.
        if not left1.endswith(f) or not left2.endswith(f):
            continue
        a = left1[:-len(f)]
        body = left2[:-len(f)]  # Пока это неразделённое z G.
        for cut in range(1, len(body)):
            z, g = body[:cut], body[cut:]
            code = {
                'A': a, 'B': b, 'C': c, 'F': f,
                'G': g, 'H': h, 'J': j,
                'z': z, 'x': x, 'y': y,
            }
            words = list(code.values())
            if all(words) and suffix_free(words):
                yield code


def main():
    left3, right3 = GIVEN[2]
    split_count = comb(len(left3) - 1, 3)
    # Единственный запуск перебора. Список используем и для показа,
    # и для продолжения поиска — генератор повторно не запускаем.
    matches = list(rule3_splits(left3, right3))
    print('Модель: постфикс; третья левая часть x y H F; справа любой терм.')
    print(f'Разбиений на четыре блока: {split_count}; совпадений: {len(matches)}.')
    for x, y, h, f in matches:
        print(f'  x={x}, y={y}, H={h}, F={f}')
        print(f'  {x} | {y} | {h} | {f}')
        code = {'x': x, 'y': y, 'H': h, 'F': f}
        print('  Правая часть:', format_term(decode_term(right3, code)))

    candidates = list(recover(matches))
    print(f'После проверки остальных правил и суффиксной свободы: {len(candidates)} словаря.')
    if not candidates:
        raise SystemExit('Гипотеза не дала решений.')
    for i, code in enumerate(candidates, 1):
        print(f'\nСловарь {i}:')
        for name, word in code.items():
            print(f'  {name:5} = {word}')
        for left, right in GIVEN:
            print(' ', format_term(decode_term(left, code)), '->',
                  format_term(decode_term(right, code)))
    print('\nРазличается только граница z | G во втором правиле.')
    print('Для решения выбираем вариант с трёхзначными кодами z, x, y.')
    print('Независимая проверка выбранного словаря: python verify_solution.py')


if __name__ == '__main__':
    main()
