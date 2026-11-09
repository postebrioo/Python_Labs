import sys
import time
import json
import pickle
import array
from dataclasses import dataclass
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
from multiprocessing import get_context
import concurrent.futures

from findex.corpus import iter_documents
from findex.tokenize import tokenize_text
from findex.models import Posting, DocMeta

@dataclass(frozen=True, slots=True)
class Posting:
    doc_id: int
    tf: int
    positions: Optional[Tuple[int, ...]] = None

@dataclass(frozen=True, slots=True)
class DocMeta:
    doc_id: int
    filename: str
    length: int

class CompactPostingStorage:
    """Зберігання постінгів через array('I') (doc_id, tf) послідовно"""
    def __init__(self):
        self.data = array.array('I')
    
    def add(self, doc_id: int, tf: int):
        self.data.append(doc_id)
        self.data.append(tf)

    def to_list(self) -> List[Tuple[int, int]]:
        return [(self.data[i], self.data[i+1]) for i in range(0, len(self.data), 2)]

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


# Функція рівня модуля для паралельної збірки (multiprocessing spawn)
def build_partial(file_paths: List[str], start_doc_id: int, keep_positions: bool = False) -> Tuple[Dict[str, List[Posting]], Dict[int, DocMeta]]:
    local_index: Dict[str, List[Posting]] = defaultdict(list)
    local_metadata: Dict[int, DocMeta] = {}
    doc_id = start_doc_id

    for fp in file_paths:
        path = Path(fp)
        text = path.read_text(encoding='utf-8', errors='ignore')
        tokens = list(tokenize_text(text))
        doc_len = len(tokens)
        local_metadata[doc_id] = DocMeta(doc_id=doc_id, filename=str(path), length=doc_len)

        if keep_positions:
            pos_map: Dict[str, List[int]] = defaultdict(list)
            for pos, token in enumerate(tokens):
                pos_map[token].append(pos)
            for token, positions in pos_map.items():
                local_index[token].append(Posting(doc_id=doc_id, tf=len(positions), positions=tuple(positions)))
        else:
            counts = Counter(tokens)
            for token, count in counts.items():
                local_index[token].append(Posting(doc_id=doc_id, tf=count))
        doc_id += 1

    return dict(local_index), local_metadata


def merge(partials: List[Tuple[Dict[str, List[Posting]], Dict[int, DocMeta]]]) -> Tuple[Dict[str, List[Posting]], Dict[int, DocMeta]]:
    merged_index: Dict[str, List[Posting]] = defaultdict(list)
    merged_metadata: Dict[int, DocMeta] = {}

    for index_part, meta_part in partials:
        merged_metadata.update(meta_part)
        for term, postings in index_part.items():
            merged_index[term].extend(postings)

    for term in merged_index:
        merged_index[term].sort(key=lambda p: p.doc_id)

    return dict(merged_index), merged_metadata


def build_index_parallel(corpus_dir: str, workers: int = 1, executor_type: str = "serial", keep_positions: bool = False) -> InvertedIndex:
    path = Path(corpus_dir)
    files = sorted([str(p) for p in path.glob("**/*") if p.is_file() and p.suffix in ('.txt', '.md')])
    
    if not files:
        return InvertedIndex(keep_positions=keep_positions)

    chunk_size = max(1, len(files) // workers)
    chunks = []
    current_id = 1
    for i in range(0, len(files), chunk_size):
        chunk_files = files[i:i + chunk_size]
        if chunk_files:
            chunks.append((chunk_files, current_id))
            current_id += len(chunk_files)

    partials = []
    if executor_type == "serial":
        for chunk_files, start_id in chunks:
            partials.append(build_partial(chunk_files, start_id, keep_positions))
    elif executor_type == "threads":
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(build_partial, cf, sid, keep_positions) for cf, sid in chunks]
            partials = [f.result() for f in futures]
    elif executor_type == "processes":
        ctx = get_context("spawn")
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as executor:
            futures = [executor.submit(build_partial, cf, sid, keep_positions) for cf, sid in chunks]
            partials = [f.result() for f in futures]

    index_data, metadata = merge(partials)
    idx = InvertedIndex(keep_positions=keep_positions)
    idx.index = defaultdict(list, index_data)
    idx.metadata = metadata
    return idx

Index = InvertedIndex