import concurrent.futures
import gzip
import heapq
import itertools
import string
import sys
import unicodedata
from operator import itemgetter

allow = set(string.ascii_letters)
cat = unicodedata.category


def load_word_freq(path: str) -> list[tuple[str, int]]:
    result: list[tuple[str, int]] = []
    with gzip.open(path, "rt", encoding="utf-8") as file:
        for line in file:
            # Split line into word and year records.
            word, *year_list = line.split()

            # Remove POS tag if present.
            if "_" in word:
                word, _ = word.rsplit("_", maxsplit=1)

            if not (word := validate_word(word)):
                continue

            # Sum counts from each year records.
            count = 0
            for year in year_list:
                triplet = year.split(",")
                count += int(triplet[1])

            item = (word, count)
            result.append(item)

    return sorted(result)


def main() -> None:
    # Generate one word list for all files.
    with concurrent.futures.ProcessPoolExecutor() as executor:
        mapped = executor.map(load_word_freq, sys.argv[1:])
        merged = heapq.merge(*mapped)

    # Aggregate duplicate words by summing their counts.
    result: list[tuple[str, int]] = []
    grouped = itertools.groupby(merged, key=itemgetter(0))
    for word, group in grouped:
        count = sum(c for _, c in group)
        result.append((word, count))

    # Output frequent words in descending order.
    result.sort(key=itemgetter(1), reverse=True)
    for word, count in result:
        if count < 100_000:
            break

        print(word, count, sep="\t")


def validate_word(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)

    buf: list[str] = []
    for ch in decomposed:
        if not cat(ch).startswith("M"):
            buf.append(ch)

    res = "".join(buf)

    if all(ch in allow for ch in res):
        return res.upper()
    else:
        return ""


if __name__ == "__main__":
    main()
