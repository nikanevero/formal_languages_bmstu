"""Self-contained verification of a decoding for laboratory 1, variant 3.

Run with Python 3.10+; no external dependencies.
Search is not required: this file verifies the explicit solution.
"""
from dataclasses import dataclass
from itertools import product
from data import CONSTRUCTOR_COUNT, GIVEN, MAX_ARITY


@dataclass(frozen=True)
class Term:
    name: str
    children: tuple = ()

    def __str__(self):
        return self.name + ("(" + ", ".join(map(str, self.children)) + ")" if self.children else "")


def t(name, *children):
    return Term(name, children)


# Буквы обозначают только символы сигнатуры, без математического смысла.
ARITY = {'A': 0, 'B': 0, 'C': 0, 'F': 1, 'G': 1, 'H': 2, 'J': 2}
VARIABLES = {'z', 'x', 'y'}
CODE = {
    'A': '2002', 'B': '21112', 'C': '20102',
    'F': '2102', 'G': '21102', 'H': '201112', 'J': '201102',
    'z': '311', 'x': '312', 'y': '321',
}
A, B, C = t('A'), t('B'), t('C')
z, x, y = t('z'), t('x'), t('y')
RULES = [
    (t('F', A), B),
    (t('F', t('G', z)), C),
    (t('F', t('H', x, y)), t('H', t('F', x), t('F', y))),
    (t('F', t('J', x, y)),
     t('H', t('J', t('F', x), y), t('J', x, t('F', y)))),
]


def postfix(term):
    return [s for child in term.children for s in postfix(child)] + [term.name]


def encode(term):
    return ''.join(CODE[s] for s in postfix(term))


def decode(text):
    """Decode from right to left using the suffix-free code, then parse postfix."""
    rev_symbols = []
    while text:
        matches = [(name, word) for name, word in CODE.items() if text.endswith(word)]
        if len(matches) != 1:
            raise ValueError(f'Not uniquely decodable: {text!r}, {matches!r}')
        name, word = matches[0]
        rev_symbols.append(name)
        text = text[:-len(word)]
    stack = []
    for name in reversed(rev_symbols):
        n = ARITY.get(name, 0)
        if len(stack) < n:
            raise ValueError('Incomplete postfix term')
        children = tuple(stack[-n:]) if n else ()
        if n:
            del stack[-n:]
        stack.append(Term(name, children))
    if len(stack) != 1:
        raise ValueError('More than one term')
    return stack[0]


def variables(term):
    return ({term.name} if term.name in VARIABLES else set()).union(
        *(variables(child) for child in term.children))


def validate(term):
    assert term.name in ARITY or term.name in VARIABLES
    assert len(term.children) == ARITY.get(term.name, 0)
    for child in term.children:
        validate(child)


def weight(term, assignment):
    if term.name in VARIABLES:
        return assignment[term.name]
    args = [weight(c, assignment) for c in term.children]
    if term.name in {'A', 'B', 'C'}:
        return 1
    if term.name == 'G':
        return args[0] + 1
    if term.name == 'F':
        return args[0] ** 2 + 1
    return args[0] + args[1] + 1


def main():
    assert len(RULES) == len(GIVEN) == 4
    assert len(ARITY) == CONSTRUCTOR_COUNT
    assert sum(n == 0 for n in ARITY.values()) == 3
    assert max(ARITY.values()) <= MAX_ARITY
    assert set(CODE) == set(ARITY) | VARIABLES
    assert not set(ARITY) & VARIABLES
    assert all(CODE.values())
    assert len(set(CODE.values())) == len(CODE)
    for name, word in CODE.items():
        for other_name, other_word in CODE.items():
            assert name == other_name or not word.endswith(other_word), 'Not suffix-free'
    used = set()
    for i, ((left, right), expected) in enumerate(zip(RULES, GIVEN), 1):
        validate(left)
        validate(right)
        assert left.name not in VARIABLES
        assert variables(right) <= variables(left)
        used.update(postfix(left) + postfix(right))
        actual = encode(left), encode(right)
        assert actual == expected, (i, actual, expected)
        assert decode(expected[0]) == left
        assert decode(expected[1]) == right
        print(f'Rule {i}: {left} -> {right}')
        print('  ' + ' | '.join(CODE[s] for s in postfix(left)))
        print('  -> ' + ' | '.join(CODE[s] for s in postfix(right)))
        print('  EXACT MATCH; inverse decoding OK')
    assert used == set(CODE)

    # Extra numerical sanity check, NOT the termination proof.
    # The all-values proof is given algebraically in solution.md.
    checks = 0
    for zv, xv, yv in product(range(1, 11), repeat=3):
        env = {'z': zv, 'x': xv, 'y': yv}
        predicted = [1, (zv+1)**2, 2*xv*yv+2*xv+2*yv-1, 2*xv*yv+xv+yv-3]
        for (left, right), delta in zip(RULES, predicted):
            assert weight(left, env) - weight(right, env) == delta > 0
            checks += 1
    print(f'7 constructors, including 3 constants; 3 variables; suffix-free code.')
    print(f'All 8 strings verified. Polynomial identities checked on {checks} instances.')
    print('See solution.md for the universal termination proof (not a bounded test).')


if __name__ == '__main__':
    main()
