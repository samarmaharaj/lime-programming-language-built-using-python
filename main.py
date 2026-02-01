from lime_lexer import Lexer
from lime_parser import Parser
from lime_ast import Program
import json

LEXER_DEBUG: bool = False
PARSER_DEBUG: bool = True

if __name__ == "__main__":
    with open("tests/parser.lime", "r") as f:
        source_code: str = f.read()

    if LEXER_DEBUG:
        print("------ LEXER DEBUG --------")
        debug_lexer: Lexer = Lexer(source=source_code)
        while debug_lexer.current_char is not None:
            print(debug_lexer.next_token())

    l: Lexer = Lexer(source=source_code)
    p: Parser = Parser(lexer=l)

    if PARSER_DEBUG:
        print("------ PARSER DEBUG --------")
        program: Program = p.parse_program()

        with open("debug/ast.json", "w") as f:
            json.dump(program.json(), f, indent=4)

        print("Wrote AST to debug/ast.json successfully!")