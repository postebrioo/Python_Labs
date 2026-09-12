\# Lab 01 — Streams, Not Lists



\## Corpus

Text files downloaded from Project Gutenberg stored in `data/`.



\## Tokenizer Policy

\- Applied Unicode NFC normalization and `casefold()`.

\- Internal apostrophes are preserved (`'`).

\- Hyphenated words are split into separate tokens.

\- Purely numeric tokens are excluded.



\## Measurements (M4)



| Version | Documents | Peak memory | Elapsed |

|  eager  |    6      | 36.68 MB    | 2.299 s |

|  lazy   |    6      | 22.67 MB    | 3.239 s |



\### Why the numbers differ

The eager version loads all documents into memory and creates flat lists of tokens, resulting in memory usage proportional to the total size of the corpus. In contrast, the lazy pipeline streams files and tokens on the fly using generators, keeping peak memory nearly constant and restricted only to the current document and the accumulated Counter table.

