import itertools
import json
import math
import re
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import pairwise
from operator import itemgetter
from pathlib import Path
from typing import Sequence, TypedDict, cast

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from decrypt import decrypt
from ngram import NGramTable, load_tables, sliding_window


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


tables: dict[int, NGramTable] | None = None

CIPHERTEXT = cast(list[str], re.findall(r"\S+", Path(sys.argv[2]).read_text()))
TOKENS = [
    (
        x.group(1).upper()
        if (x := re.match(r"^([A-Za-z])[^A-Za-z]*$", c)) is not None
        else "_"
    )
    for c in CIPHERTEXT
]


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
):
    global tables
    assert tables is not None

    log_obs_exp = tables[2]

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

    return total / count if count > 0 else 0


def score_sequence(text: Sequence[str], m: int) -> float:
    global tables
    assert tables is not None

    total = 0.0
    for n in (3, 5):
        log_obs_exp = tables[n]
        for ngram in sliding_window(text, n):
            value = log_obs_exp[ngram]
            if not math.isnan(value):
                total += value

    return total / m / 2


def solve_tsp(cost: dict[tuple[int, int], int], num_columns: int) -> list[int]:
    n = num_columns

    manager = pywrapcp.RoutingIndexManager(n + 1, 1, n)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(i: int, j: int) -> int:
        u = manager.IndexToNode(i)
        v = manager.IndexToNode(j)

        if v == n or u == n:
            return 0
        else:
            return cost[u, v]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        return []

    index = routing.Start(0)
    result = [manager.IndexToNode(index)]
    while not routing.IsEnd(index):
        index = solution.Value(routing.NextVar(index))
        result.append(manager.IndexToNode(index))

    assert len(result) == num_columns + 2
    return result[1:-1]


def main() -> None:
    tasks = [
        (key_size, shift)
        for key_size in range(2, 35)
        for shift in range(key_size + 1)
        if (len(TOKENS) - shift) // key_size > 0
    ]
    total = len(tasks)

    result_list: list[Result] = []
    with ProcessPoolExecutor(initializer=init_worker, initargs=(sys.argv[1],)) as exe:
        futures = [exe.submit(worker, key_size, shift) for key_size, shift in tasks]

        for i, future in enumerate(as_completed(futures), 1):
            print(f"Progress: {i:>3d}/{total:>3d}")
            result_list.extend(future.result())

    result_list.sort(key=itemgetter("plaintokScore"), reverse=True)
    path = Path.cwd() / Path(sys.argv[2]).with_suffix(".json").name
    path.write_text(
        json.dumps(
            result_list,
            indent=4,
            sort_keys=True,
        )
    )


def init_worker(path: str) -> None:
    global tables
    assert tables is None
    with open(path, encoding="utf-8") as file:
        tables = load_tables(file)


def worker(num_cols: int, num_nulls: int) -> list[Result]:
    num_rows = (len(TOKENS) - num_nulls) // (num_cols)

    text2 = [
        TOKENS[col * num_rows + row + num_nulls]
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
            CIPHERTEXT[num_nulls:],
            key=p,
            method=method,
        )

        plaintok = decrypt(
            TOKENS[num_nulls:],
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
                "plaintokScore": score_sequence(plaintok, len(TOKENS)),
            }
        )

    return result


if __name__ == "__main__":
    main()
