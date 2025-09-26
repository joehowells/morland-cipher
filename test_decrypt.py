from pathlib import Path

import pytest

from decrypt import Method, decrypt

BASE_PATH = Path(__file__).parent / "data" / "ciphertext"
KEY = [5, 4, 8, 0, 3, 6, 1, 7, 2]
PLAINTEXT = (
    "ThisWayofWritingisOfallotherTheMostFacilandExpeditiousAswelltoUnlockAstoconcealpd"
)


@pytest.mark.parametrize("method", range(1, 11))
def test_matches_plaintext(method: Method) -> None:
    path = BASE_PATH / f"morland-page04-method{method:02d}.txt"
    seq = path.read_text().split()
    out = "".join(decrypt(seq, KEY, method))
    assert out == PLAINTEXT
