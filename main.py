from lexer import Lexer

LEXER_DEBUG: bool = True

if __name__ == "__main__":
    with open("tests/lexer.lime", "r") as f:
        source_code: str = f.read()

    if LEXER_DEBUG:
        debug_lexer: Lexer = Lexer(source=source_code)
        while debug_lexer.current_char is not None:
            print(debug_lexer.next_token())