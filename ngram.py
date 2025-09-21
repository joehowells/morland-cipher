import functools
import itertools
import math
import string
import sys
from collections import deque
from typing import Iterable, Iterator, TypeVar

type NGram = tuple[str, ...]
T = TypeVar("T")

WORD_LIST = sys.argv[1]


def sliding_window(iterable: Iterable[T], n: int) -> Iterator[tuple[T, ...]]:
    "Collect data into overlapping fixed-length chunks or blocks."
    # https://docs.python.org/3/library/itertools.html
    # sliding_window('ABCDEFG', 4) → ABCD BCDE CDEF DEFG
    iterator = iter(iterable)
    window = deque(itertools.islice(iterator, n - 1), maxlen=n)
    for x in iterator:
        window.append(x)
        yield tuple(window)


@functools.cache
def log_expected(n: int) -> dict[NGram, float]:
    log_obs = log_observed(1)
    all_ngrams = itertools.product(string.ascii_uppercase, repeat=n)

    result: dict[NGram, float] = {}
    for ngram in all_ngrams:
        result[ngram] = sum(log_obs.get((ch,), 0.0) for ch in ngram)

    return result


@functools.cache
def log_observed(n: int) -> dict[NGram, float]:
    counts = ngram_count(n)
    log_total = math.log(sum(counts.values()))

    return {
        ngram: (math.log(ngram_count) - log_total)
        for ngram, ngram_count in counts.items()
    }


@functools.cache
def log_observed_expected(n: int) -> dict[NGram, float]:
    log_obs = log_observed(n)
    log_exp = log_expected(n)

    return {ngram: (log_obs[ngram] - log_exp[ngram]) for ngram in log_obs}


@functools.cache
def ngram_count(n: int) -> dict[NGram, int]:
    all_ngrams = itertools.product(string.ascii_uppercase, repeat=n)
    result = {ngram: 1 for ngram in all_ngrams}

    with open(WORD_LIST, encoding="utf-8") as file:
        for line in file:
            word, count = line.split(maxsplit=1)
            for ngram in sliding_window(word, n):
                result[ngram] += int(count)

    return result
