import argparse
import sys
import time
import tracemalloc
from collections import Counter
from itertools import islice
from pathlib import Path
from typing import Iterable

from findex.corpus import iter_documents
from findex.tokenize import tokenize


def run_lazy_pipeline(docs_iter: Iterable) -> tuple[int, int, Counter]:
    doc_count = 0
    total_tokens = 0
    counts: Counter[str] = Counter()

    for doc in docs_iter:
        doc_count += 1
        for tok in tokenize(doc.text):
            total_tokens += 1
            counts[tok] += 1

    return doc_count, total_tokens, counts


def run_eager_pipeline(docs_iter: Iterable) -> tuple[int, int, Counter]:
    # Спеціально завантажуємо все в пам'ять (M4)
    all_docs = list(docs_iter)
    all_tokens = []
    for doc in all_docs:
        all_tokens.extend(list(tokenize(doc.text)))

    return len(all_docs), len(all_tokens), Counter(all_tokens)


def main() -> None:
    parser = argparse.ArgumentParser(description="Обчислення статистики корпусу.")
    parser.add_argument("data_path", type=Path, help="Шлях до папки з даними")
    parser.add_argument("--limit", type=int, default=None, help="Обмежити кількість документів")
    parser.add_argument("--eager", action="store_true", help="Запустити жадібну (eager) версію для M4")
    args = parser.parse_args()

    docs = iter_documents(args.data_path)
    if args.limit is not None:
        docs = islice(docs, args.limit)

    tracemalloc.start()
    start_time = time.perf_counter()

    if args.eager:
        doc_count, total_tokens, counts = run_eager_pipeline(docs)
    else:
        doc_count, total_tokens, counts = run_lazy_pipeline(docs)

    elapsed_time = time.perf_counter() - start_time
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak_bytes / (1024 * 1024)

    mode_label = "EAGER (lists)" if args.eager else "LAZY (generators)"
    print(f"=== Режим: {mode_label} ===")
    print(f"Документів оброблено: {doc_count}")
    print(f"Всього токенів:       {total_tokens}")
    print(f"Розмір словника:      {len(counts)}")
    print(f"Час виконання:        {elapsed_time:.3f} сек")
    print(f"Пік пам'яті:          {peak_mb:.2f} MB\n")

    print("Топ-50 найчастіших слів:")
    for rank, (word, freq) in enumerate(counts.most_common(50), start=1):
        print(f"{rank:>2}. {word:<15} {freq}")


if __name__ == "__main__":
    main()