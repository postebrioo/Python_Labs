import pickle
import json
from collections.abc import Mapping
from functools import cached_property
from contextlib import contextmanager
from typing import Dict, List, Iterator, Any
from findex.models import Posting, DocMeta

class Index(Mapping):
    def __init__(self, metadata: Dict[int, DocMeta], index_data: Dict[str, List[Posting]], keep_positions: bool = False):
        self._metadata = metadata
        self._index = index_data
        self.keep_positions = keep_positions

    def __getitem__(self, term: str) -> List[Posting]:
        return self._index.get(term.lower(), [])

    def __len__(self) -> int:
        return len(self._index)

    def __iter__(self) -> Iterator[str]:
        return iter(self._index)

    def __contains__(self, term: object) -> bool:
        if not isinstance(term, str):
            return False
        return term.lower() in self._index

    def __repr__(self) -> str:
        return f"<Index terms={len(self)} docs={self.num_docs}>"

    @property
    def metadata(self) -> Dict[int, DocMeta]:
        return self._metadata

    @cached_property
    def num_docs(self) -> int:
        return len(self._metadata)

    @cached_property
    def avg_doc_length(self) -> float:
        if not self._metadata:
            return 0.0
        return sum(m.length for m in self._metadata.values()) / self.num_docs

    def df(self, term: str) -> int:
        return len(self[term])

@contextmanager
def open_index(filepath: str):
    """Context manager для безпечного відкриття індексу"""
    file_obj = open(filepath, 'rb' if filepath.endswith('.pkl') else 'r', encoding=None if filepath.endswith('.pkl') else 'utf-8')
    try:
        if filepath.endswith('.pkl'):
            keep_positions, metadata, index_data = pickle.load(file_obj)
        else:
            data = json.load(file_obj)
            keep_positions = data["keep_positions"]
            metadata = {int(k): DocMeta(**v) for k, v in data["metadata"].items()}
            index_data = {
                term: [Posting(p["doc_id"], p["tf"], tuple(p["positions"]) if p.get("positions") else None) for p in posts]
                for term, posts in data["index"].items()
            }
        idx = Index(metadata, index_data, keep_positions)
        yield idx
    finally:
        file_obj.close()