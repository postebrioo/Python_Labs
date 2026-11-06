import time
import argparse
import tracemalloc
from typing import List, Set, Tuple
from findex.index import InvertedIndex

def merge_and(postings1: List[int], postings2: List[int]) -> List[int]:
    """Двовказівниковий merge для операції AND"""
    res = []
    i, j = 0, 0
    len1, len2 = len(postings1), len(postings2)
    while i < len1 and j < len2:
        if postings1[i] == postings2[j]:
            res.append(postings1[i])
            i += 1
            j += 1
        elif postings1[i] < postings2[j]:
            i += 1
        else:
            j += 1
    return res

def merge_or(postings1: List[int], postings2: List[int]) -> List[int]:
    """Двовказівниковий merge для операції OR"""
    res = []
    i, j = 0, 0
    len1, len2 = len(postings1), len(postings2)
    while i < len1 and j < len2:
        if postings1[i] == postings2[j]:
            res.append(postings1[i])
            i += 1
            j += 1
        elif postings1[i] < postings2[j]:
            res.append(postings1[i])
            i += 1
        else:
            res.append(postings2[j])
            j += 1
    while i < len1:
        res.append(postings1[i])
        i += 1
    while j < len2:
        res.append(postings2[j])
        j += 1
    return res

def search_merge(index: InvertedIndex, query: str) -> List[int]:
    tokens = query.lower().split()
    if not tokens:
        return []
    
    # Витягуємо впорядковані списки doc_id для кожного терміна
    postings = [[p.doc_id for p in index.index.get(t, [])] for t in tokens if t not in ("and", "or", "not")]
    if not postings:
        return []

    # За замовчуванням обробка як AND-запит
    result = postings[0]
    for p in postings[1:]:
        result = merge_and(result, p)
    return result

def search_set(index: InvertedIndex, query: str) -> List[int]:
    tokens = query.lower().split()
    if not tokens:
        return []
    
    sets = [set(p.doc_id for p in index.index.get(t, [])) for t in tokens if t not in ("and", "or", "not")]
    if not sets:
        return []
    
    result = sets[0]
    for s in sets[1:]:
        result = result.intersection(s)
    return sorted(list(result))

def main():
    parser = argparse.ArgumentParser(description="Search in inverted index")
    parser.add_argument("index_path", type=str, help="Path to saved index file")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--engine", choices=["merge", "set"], default="merge", help="Search engine strategy")
    args = parser.parse_args()

    tracemalloc.start()
    t0 = time.perf_counter()

    if args.index_path.endswith(".json"):
        idx = InvertedIndex.load_json(args.index_path)
    else:
        idx = InvertedIndex.load_pickle(args.index_path)

    if args.engine == "merge":
        doc_ids = search_merge(idx, args.query)
    else:
        doc_ids = search_set(idx, args.query)

    t1 = time.perf_counter()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Found {len(doc_ids)} documents in {t1 - t0:.6f} s | Peak memory: {peak_mem / 1024 / 1024:.2f} MB")
    for d_id in doc_ids[:5]:
        meta = idx.metadata.get(d_id)
        print(f"  [Doc {d_id}] {meta.filename if meta else 'Unknown'} (length: {meta.length if meta else 0})")

if __name__ == "__main__":
    main()