import sys
import time
import json
import pickle
import argparse
import tracemalloc
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any
from pathlib import Path

from findex.corpus import iter_documents
from findex.tokenize import tokenize_text
from findex.models import Posting, DocMeta

class InvertedIndex:
    def __init__(self, keep_positions: bool = False):
        self.keep_positions = keep_positions
        self.index: Dict[str, List[Posting]] = defaultdict(list)
        self.metadata: Dict[int, DocMeta] = {}

    def build(self, corpus_dir: str):
        for doc_id, filename, text in iter_documents(corpus_dir):
            tokens = list(tokenize_text(text))
            doc_len = len(tokens)
            self.metadata[doc_id] = DocMeta(doc_id=doc_id, filename=filename, length=doc_len)

            if self.keep_positions:
                pos_map = defaultdict(list)
                for pos, token in enumerate(tokens):
                    pos_map[token].append(pos)
                for token, positions in pos_map.items():
                    posting = Posting(doc_id=doc_id, tf=len(positions), positions=tuple(positions))
                    self.index[token].append(posting)
            else:
                counts = Counter(tokens)
                for token, count in counts.items():
                    posting = Posting(doc_id=doc_id, tf=count)
                    self.index[token].append(posting)

    def save_pickle(self, filepath: str):
        # Примітка: load чужого pickle-файлу небезпечний через можливість виконання 
        # довільного коду під час десеріалізації (через __reduce__ / RCE).
        with open(filepath, 'wb') as f:
            pickle.dump((self.keep_positions, self.metadata, dict(self.index)), f)

    @classmethod
    def load_pickle(cls, filepath: str) -> "InvertedIndex":
        with open(filepath, 'rb') as f:
            keep_positions, metadata, index_data = pickle.load(f)
        obj = cls(keep_positions=keep_positions)
        obj.metadata = metadata
        obj.index = defaultdict(list, index_data)
        return obj

    def save_json(self, filepath: str):
        data = {
            "keep_positions": self.keep_positions,
            "metadata": {
                doc_id: {"doc_id": m.doc_id, "filename": m.filename, "length": m.length}
                for doc_id, m in self.metadata.items()
            },
            "index": {
                term: [
                    {"doc_id": p.doc_id, "tf": p.tf, "positions": p.positions}
                    for p in postings
                ]
                for term, postings in self.index.items()
            }
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    @classmethod
    def load_json(cls, filepath: str) -> "InvertedIndex":
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        obj = cls(keep_positions=data["keep_positions"])
        obj.metadata = {
            int(k): DocMeta(v["doc_id"], v["filename"], v["length"])
            for k, v in data["metadata"].items()
        }
        obj.index = defaultdict(list)
        for term, postings in data["index"].items():
            obj.index[term] = [
                Posting(doc_id=p["doc_id"], tf=p["tf"], positions=tuple(p["positions"]) if p["positions"] else None)
                for p in postings
            ]
        return obj

def main():
    parser = argparse.ArgumentParser(description="Build and save inverted index")
    parser.add_argument("corpus_dir", type=str, help="Path to corpus directory")
    parser.add_argument("--out", type=str, required=True, help="Output file path (.pkl or .json)")
    parser.add_argument("--positions", action="store_true", help="Store token positions")
    args = parser.parse_args()

    tracemalloc.start()
    t0 = time.perf_counter()

    idx = InvertedIndex(keep_positions=args.positions)
    idx.build(args.corpus_dir)

    if args.out.endswith(".json"):
        idx.save_json(args.out)
    else:
        idx.save_pickle(args.out)

    t1 = time.perf_counter()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Index built and saved in {t1 - t0:.4f} s | Peak memory: {peak_mem / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main()