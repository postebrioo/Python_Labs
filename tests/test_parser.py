from findex.query_parser import parse_query, Term, Phrase, And, Or, Not

def test_ast_parsing():
    q1 = parse_query('python AND (async OR await)')
    expected1 = And(Term('python'), Or(Term('async'), Term('await')))
    assert q1 == expected1, f"Expected {expected1}, got {q1}"

    q2 = parse_query('"event loop"')
    expected2 = Phrase('event loop')
    assert q2 == expected2, f"Expected {expected2}, got {q2}"
    print("All AST Parser tests passed successfully!")

if __name__ == "__main__":
    test_ast_parsing()