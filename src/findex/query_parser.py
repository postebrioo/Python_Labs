from typing import List, Set
from findex.index import Index

class ASTNode:
    def evaluate(self, index: Index) -> Set[int]:
        raise NotImplementedError
    def __and__(self, other): return And(self, other)
    def __or__(self, other): return Or(self, other)
    def __invert__(self): return Not(self)

class Term(ASTNode):
    def __init__(self, term: str): self.term = term.lower()
    def evaluate(self, index: Index) -> Set[int]:
        return {p.doc_id for p in index[self.term]}
    def __eq__(self, other): return isinstance(other, Term) and self.term == other.term
    def __repr__(self): return f"Term('{self.term}')"

class Phrase(ASTNode):
    def __init__(self, phrase: str): self.tokens = phrase.lower().split()
    def evaluate(self, index: Index) -> Set[int]:
        if not self.tokens: return set()
        first_postings = {p.doc_id: p.positions for p in index[self.tokens[0]] if p.positions}
        res = set()
        for doc_id, positions in first_postings.items():
            for pos in positions:
                match = True
                for idx, t in enumerate(self.tokens[1:], start=1):
                    t_posts = {p.doc_id: p.positions for p in index[t] if p.positions}
                    if doc_id not in t_posts or (pos + idx) not in t_posts[doc_id]:
                        match = False
                        break
                if match:
                    res.add(doc_id)
                    break
        return res
    def __eq__(self, other): return isinstance(other, Phrase) and self.tokens == other.tokens
    def __repr__(self): return f"Phrase({' '.join(self.tokens)})"

class And(ASTNode):
    def __init__(self, left: ASTNode, right: ASTNode): self.left, self.right = left, right
    def evaluate(self, index: Index) -> Set[int]: return self.left.evaluate(index) & self.right.evaluate(index)
    def __eq__(self, other): return isinstance(other, And) and self.left == other.left and self.right == other.right
    def __repr__(self): return f"And({self.left}, {self.right})"

class Or(ASTNode):
    def __init__(self, left: ASTNode, right: ASTNode): self.left, self.right = left, right
    def evaluate(self, index: Index) -> Set[int]: return self.left.evaluate(index) | self.right.evaluate(index)
    def __eq__(self, other): return isinstance(other, Or) and self.left == other.left and self.right == other.right
    def __repr__(self): return f"Or({self.left}, {self.right})"

class Not(ASTNode):
    def __init__(self, child: ASTNode): self.child = child
    def evaluate(self, index: Index) -> Set[int]:
        all_docs = set(index.metadata.keys())
        return all_docs - self.child.evaluate(index)
    def __eq__(self, other): return isinstance(other, Not) and self.child == other.child
    def __repr__(self): return f"Not({self.child})"

def parse_query(query: str) -> ASTNode:
    # Спрощений рекурсивний парсер Boolean запитів
    tokens = query.replace('(', ' ( ').replace(')', ' ) ').split()
    
    def parse_expr(idx=0):
        nodes = []
        op = None
        i = idx
        while i < len(tokens):
            tok = tokens[i]
            if tok == '(':
                node, i = parse_expr(i + 1)
                nodes.append(node)
            elif tok == ')':
                break
            elif tok in ("AND", "OR", "NOT"):
                op = tok
            elif tok.startswith('"') or tok.startswith("'"):
                phrase_tokens = [tok.strip('"\'')]
                while i + 1 < len(tokens) and not tokens[i+1].endswith('"') and not tokens[i+1].endswith("'"):
                    i += 1
                    phrase_tokens.append(tokens[i])
                if i + 1 < len(tokens):
                    i += 1
                    phrase_tokens.append(tokens[i].strip('"\''))
                nodes.append(Phrase(" ".join(phrase_tokens)))
            else:
                nodes.append(Term(tok))
            i += 1

        root = nodes[0] if nodes else Term("")
        for n in nodes[1:]:
            root = root & n if op != "OR" else root | n
        return root, i

    node, _ = parse_expr()
    return node