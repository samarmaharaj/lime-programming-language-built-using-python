from lime_lexer import Lexer
from lime_parser import Parser
from lime_ast import Program
from compiler import Compiler
import json

from llvmlite import ir
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float

LEXER_DEBUG: bool = False
PARSER_DEBUG: bool = False
COMPILER_DEBUG: bool = True

if __name__ == "__main__":
    with open("tests/test.lime", "r") as f:
        source_code: str = f.read()

    if LEXER_DEBUG:
        print("------ LEXER DEBUG --------")
        debug_lexer: Lexer = Lexer(source=source_code)
        while debug_lexer.current_char is not None:
            print(debug_lexer.next_token())

    l: Lexer = Lexer(source=source_code)
    p: Parser = Parser(lexer=l)

    program: Program = p.parse_program()
    if len(p.errors) > 0:
        print("Parser encountered the following errors:")
        for err in p.errors:
            print(f"\t{err}")
        exit(1)

    if PARSER_DEBUG:
        print("------ PARSER DEBUG --------")
        

        with open("debug/ast.json", "w") as f:
            json.dump(program.json(), f, indent=4)

        print("Wrote AST to debug/ast.json successfully!")

    c: Compiler = Compiler()
    c.compile(node=program)

    # output steps
    module: ir.Module = c.module
    module.triple = llvm.get_default_triple()

    if COMPILER_DEBUG:
        print("------ COMPILER DEBUG --------")
        with open("debug/ir.ll", "w") as f:
            f.write(str(module))
        print("Wrote LLVM IR to debug/ir.ll successfully!")