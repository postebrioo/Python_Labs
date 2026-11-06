import time
import functools
from typing import List

def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        res = func(*args, **kwargs)
        t1 = time.perf_counter()
        print(f"[LOG @timed] {func.__name__} executed in {(t1 - t0)*1000:.3f} ms")
        return res
    return wrapper

@functools.lru_cache(maxsize=128)
def cached_search_ids(query_str: str, index_id: int) -> List[int]:
    print(f"[CACHE MISS] Executing search for query: '{query_str}'")
    return []

def generate_snippet(text: str, query_terms: List[str], window: int = 80) -> str:
    text_lower = text.lower()
    best_pos = -1
    for t in query_terms:
        pos = text_lower.find(t.lower())
        if pos != -1:
            best_pos = pos
            break
    if best_pos == -1:
        return text[:window*2] + "..."
    
    start = max(0, best_pos - window)
    end = min(len(text), best_pos + window)
    snippet = text[start:end]

    for t in query_terms:
        snippet = snippet.replace(t, f"**{t}**").replace(t.capitalize(), f"**{t.capitalize()}**")
    return f"...{snippet}..."