from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
import array

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