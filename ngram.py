import array
import itertools
import math
import string
from collections import deque
from typing import Iterable, Iterator, Mapping, Sequence, TypeVar

type NGram = tuple[str, ...]
T = TypeVar("T")


def sliding_window(iterable: Iterable[T], n: int) -> Iterator[tuple[T, ...]]:
    "Collect data into overlapping fixed-length chunks or blocks."
    # https://docs.python.org/3/library/itertools.html
    # sliding_window('ABCDEFG', 4) → ABCD BCDE CDEF DEFG
    iterator = iter(iterable)
    window = deque(itertools.islice(iterator, n - 1), maxlen=n)
    for x in iterator:
        window.append(x)
        yield tuple(window)


class NGramTable(Mapping[NGram, float]):
    def __init__(self, n: int, data: Sequence[float]) -> None:
        if len(data) != 26**n:
            raise ValueError(f"data must have 26**{n} elements")

        self._n = n
        self._data = data

    def __len__(self) -> int:
        return 26**self._n

    def __getitem__(self, key: NGram) -> float:
        return self._data[encode(key)]

    def __iter__(self) -> Iterator[NGram]:
        return itertools.product(string.ascii_uppercase, repeat=self._n)


def encode(key: NGram) -> int:
    idx = 0
    for c in key:
        idx = idx * 26 + (ord(c) - 65)

    return idx


def load_tables(seq: Iterable[str]) -> dict[int, NGramTable]:
    gram_count: dict[int, array.array] = {
        n: array.array("Q", (0 for _ in range(26**n))) for n in (1, 2, 3, 5)
    }

    for line in seq:
        word, count_str = line.split(maxsplit=1)
        count = int(count_str)
        for n, table in gram_count.items():
            for ngram in sliding_window(word, n):
                table[encode(ngram)] += count

    log_totals = {n: math.log(sum(table)) for n, table in gram_count.items()}

    log_observed_1 = array.array(
        "f", (math.log(x) - log_totals[1] if x > 0 else math.nan for x in gram_count[1])
    )

    log_observed_expected: dict[int, array.array] = {}
    for n, table in gram_count.items():
        if n == 1:
            continue

        all_indices = itertools.product(range(26), repeat=n)

        values = (
            (
                math.log(x) - log_totals[n] - sum(log_observed_1[ch] for ch in gram)
                if x > 0
                else math.nan
            )
            for x, gram in zip(table, all_indices)
        )
        log_observed_expected[n] = array.array("f", values)

    return {n: NGramTable(n, log_observed_expected[n]) for n in log_observed_expected}
