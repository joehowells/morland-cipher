import itertools
from typing import Sequence


def decrypt(seq: Sequence[str], key: Sequence[int], method: int = 1) -> list[str]:
    assert sorted(key) == list(range(len(key)))
    num_cols = len(key)
    num_rows = len(seq) // num_cols

    grid = [[seq[0] for _ in range(num_cols)] for _ in range(num_rows)]

    match method:
        case 1:
            # Descending
            for j, col in enumerate(key):
                for i, row in enumerate(range(num_rows)):
                    k = row
                    grid[i][j] = seq[col * num_rows + k]

        case 2:
            # Ascending
            for j, col in enumerate(key):
                for i, row in enumerate(range(num_rows)):
                    k = num_rows - row - 1
                    grid[i][j] = seq[col * num_rows + k]

        case 3:
            # Descending then ascending
            for j, col in enumerate(key):
                for i, row in enumerate(range(num_rows)):
                    k = (num_rows - row - 1) if (col % 2 > 0) else row
                    grid[i][j] = seq[col * num_rows + k]

        case 4:
            # Ascending then descending
            for j, col in enumerate(key):
                for i, row in enumerate(range(num_rows)):
                    k = (num_rows - row - 1) if (col % 2 <= 0) else row
                    grid[i][j] = seq[col * num_rows + k]

        case 5:
            # Descending
            for j, col in enumerate(range(num_cols)):
                for i, row in enumerate(range(num_rows)):
                    k = row
                    grid[i][j] = seq[col * num_rows + k]

        case 6:
            # Ascending
            for j, col in enumerate(range(num_cols)):
                for i, row in enumerate(range(num_rows)):
                    k = num_rows - row - 1
                    grid[i][j] = seq[col * num_rows + k]

        case 7:
            # Diagonals, descending
            indices = []
            for j in itertools.count():
                new_indices = [
                    (i, j - i) for i in range(num_rows) if 0 <= (j - i) < num_cols
                ]
                if not new_indices:
                    break
                else:
                    indices.extend(new_indices)

            for (i, j), tok in zip(indices, seq):
                grid[i][j] = tok

        case 8:
            # Diagonals, ascending
            indices = []
            for j in itertools.count():
                new_indices = [
                    (i, j - i) for i in range(num_rows) if 0 <= (j - i) < num_cols
                ]
                if not new_indices:
                    break
                else:
                    indices.extend(reversed(new_indices))

            for (i, j), tok in zip(indices, seq):
                grid[i][j] = tok

        case 9:
            # Diagonals, descending then ascending
            indices = []
            for j in itertools.count():
                new_indices = [
                    (i, j - i) for i in range(num_rows) if 0 <= (j - i) < num_cols
                ]
                if not new_indices:
                    break
                elif j % 2 == 0:
                    indices.extend(reversed(new_indices))
                else:
                    indices.extend(new_indices)

            for (i, j), tok in zip(indices, seq):
                grid[i][j] = tok

        case 10:
            # Diagonals, ascending then descending
            indices = []
            for j in itertools.count():
                new_indices = [
                    (i, j - i) for i in range(num_rows) if 0 <= (j - i) < num_cols
                ]
                if not new_indices:
                    break
                elif j % 2 == 1:
                    indices.extend(reversed(new_indices))
                else:
                    indices.extend(new_indices)

            for (i, j), tok in zip(indices, seq):
                grid[i][j] = tok

    return [grid[row][col] for row in range(num_rows) for col in range(num_cols)]
