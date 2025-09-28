import argparse
import itertools
import json
import math
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from itertools import pairwise
from operator import itemgetter
from pathlib import Path
from typing import Sequence, TypedDict

from decrypt import decrypt
from ngram import NGramTable, load_tables, sliding_window
from solvers import solve_tsp

DATA_PATH = Path(__file__).parent.joinpath("data/word-list")


class Result(TypedDict):
    colScore: float
    key: list[int]
    method: int
    numCols: int
    numRows: int
    numNulls: int
    plaintext: str
    plaintok: str
    plaintokScore: float


@dataclass
class Context:
    ciphertext: list[str]
    tables: dict[int, NGramTable]
    tokens: list[str]


context: Context | None = None


def find_best_key(
    text: Sequence[str], num_columns: int, alternate: bool = False
) -> tuple[float, list[int]]:
    all_pairs = itertools.product(range(num_columns), repeat=2)
    all_score = {
        (i, j): score_column_pair(text, num_columns, i, j, alternate)
        for i, j in all_pairs
    }
    max_score = max(all_score.values())
    cost = {key: -int((val - max_score) * 1_000) for key, val in all_score.items()}
    path = solve_tsp(cost, num_columns)

    rows = list(pairwise(path))
    mean_score = sum(all_score[i, j] for i, j in rows) / len(rows)
    return mean_score, path


def score_column_pair(
    text: Sequence[str],
    num_columns: int,
    i: int,
    j: int,
    alternate: bool = False,
) -> float:
    global context
    assert context is not None

    log_obs_exp = context.tables[2]

    xs = text[i::num_columns]
    ys = text[j::num_columns]

    if alternate and (i % 2) != (j % 2):
        ys = ys[::-1]

    total = 0.0
    count = 0
    for x, y in zip(xs, ys):
        if (x, y) in log_obs_exp:
            value = log_obs_exp[x, y]
            if not math.isnan(value):
                total += value
                count += 1

    return total / count if count > 0 else 0.0


def score_sequence(text: Sequence[str], m: int) -> float:
    global context
    assert context is not None

    total = 0.0
    for n in (3, 5):
        log_obs_exp = context.tables[n]
        for ngram in sliding_window(text, n):
            value = log_obs_exp[ngram]
            if not math.isnan(value):
                total += value

    return total / m / 2


def main() -> None:
    args = parse_args()

    ciphertext = Path(args.ciphertext).read_text().strip().split()

    tasks = [
        (key_size, shift)
        for key_size in range(2, 35)
        for shift in range(key_size + 1)
        if (len(ciphertext) - shift) // key_size > 0
    ]
    total = len(tasks)

    result_list: list[Result] = []
    with ProcessPoolExecutor(initializer=init_worker, initargs=(args,)) as exe:
        futures = [exe.submit(worker, key_size, shift) for key_size, shift in tasks]

        for i, future in enumerate(as_completed(futures), 1):
            print(f"Progress: {i:>3d}/{total:>3d}")
            result_list.extend(future.result())

    result_list.sort(key=itemgetter("plaintokScore"), reverse=True)
    path = Path.cwd() / args.ciphertext.with_suffix(".json").name
    path.write_text(
        json.dumps(
            result_list,
            indent=4,
            sort_keys=True,
        )
    )
    print(f"Results saved to {path.name}")


def init_worker(args: argparse.Namespace) -> None:
    global context
    assert context is None

    with open(args.wordlist, encoding="utf-8") as file:
        tables = load_tables(file)

    with open(args.ciphertext, encoding="utf-8") as file:
        ciphertext = file.read().strip().split()

    tokens = [
        (
            x.group(1).upper()
            if (x := re.match(r"^([A-Za-z])[^A-Za-z]*$", c)) is not None
            else "_"
        )
        for c in ciphertext
    ]

    context = Context(
        ciphertext=ciphertext,
        tables=tables,
        tokens=tokens,
    )


def worker(num_cols: int, num_nulls: int) -> list[Result]:
    global context
    assert context is not None

    num_rows = (len(context.tokens) - num_nulls) // (num_cols)

    text2 = [
        context.tokens[col * num_rows + row + num_nulls]
        for row in range(num_rows)
        for col in range(num_cols)
    ]

    p12_score, p12 = find_best_key(text2, num_cols, alternate=False)
    p34_score, p34 = find_best_key(text2, num_cols, alternate=True)

    result: list[Result] = []
    for method in range(1, 11):
        match method:
            case 1 | 2:
                p_score = p12_score
                p = p12
            case 3 | 4:
                p_score = p34_score
                p = p34
            case _:
                p_score = 0.0
                p = list(range(num_cols))

        plaintext = decrypt(
            context.ciphertext[num_nulls:],
            key=p,
            method=method,
        )

        plaintok = decrypt(
            context.tokens[num_nulls:],
            key=p,
            method=method,
        )

        result.append(
            {
                "colScore": p_score,
                "key": p,
                "method": method,
                "numCols": num_cols,
                "numRows": num_rows,
                "numNulls": num_nulls,
                "plaintext": "".join(plaintext),
                "plaintok": "".join(plaintok),
                "plaintokScore": score_sequence(plaintok, len(context.tokens)),
            }
        )

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "ciphertext",
        type=Path,
        help="path to the ciphertext",
    )
    parser.add_argument(
        "-w",
        "--wordlist",
        default=Path(__file__).parent / "data/word-list/eng-gb.txt",
        type=Path,
        help="path to the word list",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
