import argparse
import tracemalloc
from typing import List

from findex.index import open_index, Index
from findex.query_parser import parse_query, Term, Phrase, And, Or, Not
from findex.scoring import BM25Scorer, TfIdfScorer, Scorer
from findex.utils import timed, generate_snippet, cached_search_ids
from findex.models import SearchResult

def extract_query_terms(node) -> List[str]:
    """Витягуємо окремі терми з AST-дерева для підрахунку релевантності та сніпетів"""
    if isinstance(node, Term):
        return [node.term]
    elif isinstance(node, Phrase):
        return node.tokens
    elif isinstance(node, (And, Or)):
        return extract_query_terms(node.left) + extract_query_terms(node.right)
    elif isinstance(node, Not):
        return extract_query_terms(node.child)
    return []

@timed
def execute_search(index: Index, query_str: str, scorer: Scorer, top_k: int = 5) -> List[SearchResult]:
    # 1. Парсимо запит у дерево AST
    ast_root = parse_query(query_str)
    
    # 2. Отримуємо doc_id документів, які відповідають умовам
    matching_docs = list(ast_root.evaluate(index))
    if not matching_docs:
        return []

    # 3. Витягуємо терми для ранжування
    terms = extract_query_terms(ast_root)
    
    # 4. Ранжуємо документи через обраний Scorer (BM25 / TF-IDF)
    results = scorer.score(index, terms, matching_docs)

    # 5. Демонстрація робочого клювання кез-функції (LRU cache hit/miss)
    cached_search_ids(query_str, id(index))

    # 6. Додаємо сніпети до результатів
    final_results = []
    for res in results[:top_k]:
        # Читаємо вміст файлу для зняття сніпета
        try:
            with open(res.filename, 'r', encoding='utf-8') as f:
                content = f.read()
            snippet = generate_snippet(content, terms)
        except Exception:
            snippet = "Текст недоступний"
            
        final_results.append(SearchResult(
            score=res.score,
            doc_id=res.doc_id,
            filename=res.filename,
            snippet=snippet
        ))
    return final_results

def main():
    parser = argparse.ArgumentParser(description="Ranked Boolean Search with Snippets")
    parser.add_argument("index_path", type=str, help="Path to saved index file (.pkl or .json)")
    parser.add_argument("query", type=str, help="Search query (e.g. 'python AND (async OR await)')")
    parser.add_argument("--scorer", choices=["bm25", "tfidf"], default="bm25", help="Ranking algorithm")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    args = parser.parse_args()

    tracemalloc.start()

    # Всі ресурси відкриваються і гарантовано закриваються через open_index
    with open_index(args.index_path) as index:
        scorer = BM25Scorer() if args.scorer == "bm25" else TfIdfScorer()
        results = execute_search(index, args.query, scorer, top_k=args.top_k)

    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"\nFound {len(results)} top results | Peak memory: {peak_mem / 1024 / 1024:.2f} MB\n")
    for r in results:
        print(f" Score: {r.score:.4f} | [Doc {r.doc_id}] {r.filename}")
        print(f" Snippet: {r.snippet}\n")

if __name__ == "__main__":
    main()