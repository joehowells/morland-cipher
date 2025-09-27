# morland-cipher

Breaking Sir Samuel Morland's New Method of Cryptography

This project is inspired by the National Archives blog post "[Hidden in plain sight: an undeciphered letter from Louis XIV’s France](https://www.nationalarchives.gov.uk/explore-the-collection/the-collection-blog/undeciphered-letter-from-louis-xivs-france/)". The post highlights an enciphered message from 1670 that William Perwich, an English diplomat, sent to Lord Arlington, a close advisor to Charles II.

The method of encryption is not known, but it could be one of the methods published by Sir Samuel Morland in his paper "[A New Method of Cryptography](https://archive.org/details/bim_early-english-books-1641-1700_a-new-method-of-cryptogr_morland-sir-samuel_1666)", a few years earlier in 1666.

While Morland also presents methods that utilise non-rectangular patterns, he focuses on methods that are based on columnar transposition of a rectangular grid.

To illustrate the difficulty of deciphering the message without the key, Morland correctly states that encrypting a message of 81 characters on a 3x27 grid results in 27! (more than ten octillion) possible keys.

However, by using techniques developed since 1666, we can break Morland's method and possibly decrypt Perwich's message.

## Installation

Clone the repository and install its dependencies:

```bash
git clone https://github.com/joehowells/morland-cipher.git
cd morland-cipher
pip install -r requirements.txt
```

Note: This project was developed in Python 3.13. Older versions may work but have not been checked.

## Usage

Run the main script from the shell to decrypt the provided ciphertext using the provided word list:

```bash
python main.py WORD-LIST CIPHERTEXT
```

- `WORD-LIST`: Path to a word-frequency list (e.g., `data/word-list/eng-gb.txt`).
- `CIPHERTEXT`: Path to a ciphertext file (e.g., `data/ciphertext/morland-page01.txt`). Tokens in the ciphertext file should be separated by spaces to detect multi-character tokens. Line breaks are treated as spaces but otherwise do not matter.

## Example

```bash
python main.py data/word-list/eng-gb.txt data/ciphertext/morland-page01.txt
```

## Method

### Morland's New Method of Cryptography

Morland's method is a type of columnar transposition cipher where the parameters of the cipher are encoded into the message itself. The basic procedure is:

1. Write the plaintext message onto a rectangular grid.
1. Complete the grid with "nulls" (dummy letters).
1. Scramble the columns according to a key shared with the recipient (Methods 1–4).
1. Write out the grid one column at a time.

For decryption, this process is carried out in reverse, assuming that the key is known.

Rather than using a fixed number of columns based on a single key, Morland's method involves sharing a document with the recipient ahead of time: the Clavis Universalis. This document contains pre-agreed keys for grids that range from 1 to 34 columns. The number of columns and the number of nulls are encoded into the message before the start of the grid.

### Finding the Key for Given Parameters

Morland presents the following ciphertext as an example of Method 1:

> s t l e l i e c c y g t s d o t s l f s e F x s U o d W i l M a t l k e h r f T c e s l o T W O r a p A n c a n o o n i l A a o i h t E u o t p i i a h i d w o n

For the purpose of finding the best key for certain inputs, we will assume that we know there are nine columns and zero nulls.

First, we split the string into nine columns:

> S T L E L I E C C – Y G T S D O T S L – F S E F X S U O D – W I L M A T L K E – H R F T C E S L O – T W O R A P A N C – A N O O N I L A A – O I H T E U O T P – I I A H I D W O N

Then arrange these into a grid:

```text
1 2 3 4 5 6 7 8 9
S Y F W H T A O I
T G S I R W N I I
L T E L F O O H A
E S F M T R O T H
L D X A C A N E I
I O S T E P I U D
E T U L S A L O W
C S O K L N A T O
C L D E O C A P N
```

The aim is to rearrange these columns to reveal the plaintext. In this case there are 9! (362,880) possible keys. This number is small enough that brute force is feasible, but it does not scale to larger numbers of columns. The Clavis Universalis presents keys for grids as large as 34 columns, so brute force is no good.

However, we can quantify which columns are most likely to follow others using frequency analysis.

### Frequency Analysis

Frequency analysis is a common technique used to break ciphers. As a simple example, when breaking a substitution cipher with English plaintext, the most common ciphertext letter is likely to map to the letter "E".

More generally, we can assign probabilities to the letters of the alphabet based on how frequently they appear in training data. This project uses word-frequency lists that are based on a dataset constructed by Google for use in its Ngram Viewer. Here are the most and least common letters extracted from the list for British English:

```text
E  0.125
T  0.094
A  0.080
O  0.077
I  0.074
```

We can also do this for combinations of two letters (bigrams):

```text
TH  0.038
HE  0.032
IN  0.024
ER  0.021
AN  0.020
```

We could use these probabilities as-is, but that would not give us the full picture. Bigrams like "EE" are frequent partly because the letter "E" itself is frequent. In other words, if we chose letters at random, we would expect to see "EE" more often simply because there are more "E"s to draw from. We can eliminate this effect by dividing the probability of observing "EE" by the probability of drawing two "E"s at random. This is known as the observed–expected (OE) ratio.

$$
OE\left(\text{AT}\right)
=
\frac{P\left(\text{AT}\right)}{P\left(\text{A} \cap \text{T} \right)}
=
\frac{P\left(\text{AT}\right)}{P\left(\text{A}\right) \cdot P\left(\text{T}\right)}
=
\frac{0.015}{0.080 \cdot 0.094}=1.994
$$

So, "AT" appears about twice as often in the dataset as it would if letters were chosen at random.

In practice, we perform these calculations in log-space, where multiplication and division become addition and subtraction.

$$
\log OE\left(\text{AT}\right)
=
\log P\left(\text{AT}\right)
- \log P\left(\text{A}\right)
- \log P\left(\text{T}\right)
$$

To compare columns, we can put them next to one another and sum the log-OE scores of the bigrams formed from each row of the grid.

```text
1 2             1 4 
S Y   -0.902    S W   -1.494
G G   -0.407    G I    0.079
E T   -1.056    E L    0.022
M S   -0.560    M M    0.488
C D   -4.222    C A    0.640
P O    0.836    P T   -0.680
L T   -1.128    L L    1.323
T S   -0.623    T K   -4.480
N L   -1.490    N E   -0.286
----  ------    ----  ------
Mean  -0.953    Mean   0.435 
```

The right-hand side has the higher total, so the transition 1→4 is more likely than transition 1→2.

We can repeat this process for all possible transitions to generate a matrix where larger numbers indicate more likely transitions.

```text
        1      2      3      4      5      6      7      8      9
 1    N/A -0.953 -1.148  0.435 -0.396 -0.607 -1.479 -1.624 -0.757
 2 -1.101    N/A -1.353 -0.718 -1.871 -1.942 -1.064  0.428 -0.750
 3 -1.197 -2.065    N/A -0.812 -1.182 -0.850 -1.587 -1.188 -2.141
 4 -0.029 -0.405 -0.717    N/A -0.950 -2.290  0.543 -2.458 -1.781
 5 -0.906 -1.050 -1.265 -1.187    N/A -0.860 -1.067 -1.170  0.428
 6 -0.662 -0.416 -1.758 -0.409  0.389    N/A  0.082 -1.621 -1.747
 7 -0.584  0.448 -0.875 -0.262 -1.221 -0.139    N/A -1.168 -1.348
 8 -1.548 -0.506  0.095 -1.193 -1.152 -1.896  0.008    N/A -0.841
 9  0.621 -1.630 -1.294 -1.918 -0.885 -1.565 -0.726 -1.312    N/A
```

### Finding the Key

The task is to identify the column ordering (key) that maximises the sum of terms in the transition matrix.

This problem can be modelled as a directed graph: the nodes represent columns, the edges represent possible transitions between them, and the edge weights correspond to the (log‑OE) likelihood of each transition. The most likely key then corresponds to the path that visits every node exactly once while maximising the total edge weight.

This is a variant of the Travelling Salesperson Problem (TSP), which can be solved using standard optimisation techniques such as those provided by the Google OR‑Tools library.

This yields the following path:

```text
6 → 5   0.389
5 → 9   0.428
9 → 1   0.621
1 → 4   0.435
4 → 7   0.543
7 → 2   0.448
2 → 8   0.428
8 → 3   0.095
-----  ------
Mean    0.376
```

Rearranging the columns gives us the grid:

```text
6 5 9 1 4 7 2 8 3
T H I S W A Y O F
W R I T I N G I S
O F A L L O T H E
R T H E M O S T F
A C I L A N D E X
P E D I T I O U S
A S W E L L T O U
N L O C K A S T O
C O N C E A L P D
```

And the plaintext:

> THIS WAY OF WRITING IS OF ALL OTHER THE MOST FACIL AND EXPEDITIOUS AS WELL AS TO UNLOCK AS TO CONCEAL

### Finding the Number of Columns and Number of Nulls

Now that we have an approach for determining the most likely key for each (number of columns, number of nulls) combination, we can test possible combinations of these values by brute-force search. The code currently makes the following assumptions:

- The number of columns is between 2 and 34 as per the Clavis Universalis. The single-column case is trivial.
- The number of nulls does not extend past the first row of the grid.
- It is possible for the grid size (product of columns and rows) to be smaller than the total number of tokens in the text. In this case, trailing tokens are treated as nulls that lie outside of the grid.

## Bibliography

- Furnon, Vincent, and Laurent Perron. *OR-Tools Routing Library*. Version 9.14. Google, June 19, 2025. <https://developers.google.com/optimization/routing/>.
- Michel, Jean‑Baptiste, Yuan Kui Shen, Aviva Presser Aiden, et al. "Quantitative Analysis of Culture Using Millions of Digitized Books." *Science* 331, no. 6014 (2011): 176–82. <https://doi.org/10.1126/science.1199644>.
- Morland, Sir Samuel. *A New Method of Cryptography*. 1666. Early English Books, 1641–1700. Internet Archive. Accessed September 21, 2025. <https://archive.org/details/bim_early-english-books-1641-1700_a-new-method-of-cryptogr_morland-sir-samuel_1666/>.
- Selman, Ruth. "Hidden in Plain Sight: An Undeciphered Letter from Louis XIV’s France." *The Collection Blog*. August 4, 2025. Accessed September 21, 2025. <https://www.nationalarchives.gov.uk/explore-the-collection/the-collection-blog/undeciphered-letter-from-louis-xivs-france/>.

## License

The code in this repository is licensed under the MIT license (see `LICENSE`).

The data files are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The word-frequency lists in the `data/word-list` directory are derived from Version 3 of the [Google Books Ngram Viewer Dataset](https://storage.googleapis.com/books/ngrams/books/datasetsv3.html). The source data is licensed under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). These lists were generated by running `word_list.py` on the dataset's 1‑gram files.

The Perwich ciphertexts in the `data/ciphertext` directory are derived from a [blog post](https://www.nationalarchives.gov.uk/explore-the-collection/the-collection-blog/undeciphered-letter-from-louis-xivs-france/) published by the National Archives. The source data is licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). The texts were prepared from a combination of the body text and photographs in the blog post.
