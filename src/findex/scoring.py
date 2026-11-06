import math
import heapq
from typing import Protocol, List, Dict, Sequence, Literal
from findex.index import Index
from findex.models import SearchResult

# Тимчасовий тип для Literal-перевірок
ScorerType = Literal["tf-idf", "bm25"]


class Scorer(Protocol):
    """Protocol для перевірки відповідності реалізацій без наслідування."""

    def score(
        self, index: Index, query_terms: Sequence[str], matching_docs: Sequence[int]
    ) -> List[SearchResult]:
        ...


class TfIdfScorer:
    def score(
        self, index: Index, query_terms: Sequence[str], matching_docs: Sequence[int]
    ) -> List[SearchResult]:
        scores: Dict[int, float] = {doc_id: 0.0 for doc_id in matching_docs}
        N = index.num_docs

        for term in query_terms:
            df = index.df(term)
            if df == 0:
                continue
            idf = math.log((N + 1) / (df + 0.5)) + 1.0
            for posting in index[term]:
                if posting.doc_id in scores:
                    doc_len = index.metadata[posting.doc_id].length
                    tf = posting.tf / max(doc_len, 1)
                    scores[posting.doc_id] += tf * idf

        results = [
            SearchResult(
                score=round(sc, 4),
                doc_id=d_id,
                filename=index.metadata[d_id].filename,
                snippet="",
            )
            for d_id, sc in scores.items()
        ]
        return heapq.nlargest(len(results), results)


class BM25Scorer:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1: float = k1
        self.b: float = b

    def score(
        self, index: Index, query_terms: Sequence[str], matching_docs: Sequence[int]
    ) -> List[SearchResult]:
        scores: Dict[int, float] = {doc_id: 0.0 for doc_id in matching_docs}
        N = index.num_docs
        avgdl = index.avg_doc_length

        for term in query_terms:
            df = index.df(term)
            if df == 0:
                continue
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
            for posting in index[term]:
                if posting.doc_id in scores:
                    doc_len = index.metadata[posting.doc_id].length
                    tf = posting.tf
                    num = tf * (self.k1 + 1)
                    denom = tf + self.k1 * (1 - self.b + self.b * (doc_len / avgdl))
                    scores[posting.doc_id] += idf * (num / denom)

        results = [
            SearchResult(
                score=round(sc, 4),
                doc_id=d_id,
                filename=index.metadata[d_id].filename,
                snippet="",
            )
            for d_id, sc in scores.items()
        ]
        return heapq.nlargest(len(results), results)


def get_scorer(scorer_type: ScorerType) -> Scorer:
    """Фабрична функція для створення скорерів через Literal."""
    if scorer_type == "tf-idf":
        return TfIdfScorer()
    elif scorer_type == "bm25":
        return BM25Scorer()
    else:
        raise ValueError(f"Unknown scorer algorithm: {scorer_type}")