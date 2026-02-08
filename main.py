from lime_lexer import Lexer
from lime_parser import Parser
from lime_ast import Program
from compiler import Compiler
import json
import time
from argparse import ArgumentParser, Namespace
import sys
import os

from llvmlite import ir
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float

def parse_args() -> Namespace:
    parser = ArgumentParser(description="Lime v0.1 - A simple programming language built using Python")
    parser.add_argument("source_file", type=str, help="Path to the source .lime file")
    parser.add_argument("--debug-lexer", action="store_true", help="Enable lexer debug output")
    parser.add_argument("--debug-parser", action="store_true", help="Enable parser debug output")
    parser.add_argument("--debug-compiler", action="store_true", help="Enable compiler debug output")
    parser.add_argument("--no-run", action="store_true", help="Compile but do not execute the code")
    return parser.parse_args()

LEXER_DEBUG: bool = False
PARSER_DEBUG: bool = False
COMPILER_DEBUG: bool = False
RUN_CODE: bool = True

PROD_DEBUG: bool = False

if __name__ == "__main__":
    args = parse_args()

    # Set debug flags from arguments
    LEXER_DEBUG = args.debug_lexer
    PARSER_DEBUG = args.debug_parser
    COMPILER_DEBUG = args.debug_compiler
    RUN_CODE = not args.no_run
    
    file_path: str = args.source_file

    try:
        with open(file_path, "r") as f:
            source_code: str = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find file '{file_path}'")
        print("Please check that the file path is correct and the file exists.")
        exit(1)
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        exit(1)

    if LEXER_DEBUG:
        print("------ LEXER DEBUG --------")
        debug_lexer: Lexer = Lexer(source=source_code)
        while debug_lexer.current_char is not None:
            print(debug_lexer.next_token())

    l: Lexer = Lexer(source=source_code)
    p: Parser = Parser(lexer=l)

    parse_start_time = time.time()
    program: Program = p.parse_program()
    parse_end_time = time.time()

    if len(p.errors) > 0:
        print("Parser encountered the following errors:")
        for err in p.errors:
            print(f"\t{err}")
        exit(1)

    if PARSER_DEBUG:
        print("------ PARSER DEBUG --------")
        
        try:
            with open("debug/ast.json", "w") as f:
                json.dump(program.json(), f, indent=4)
            print("Wrote AST to debug/ast.json successfully!")
        except Exception as e:
            print(f"Warning: Could not write AST debug file: {e}")

    c: Compiler = Compiler()

    compiler_start_time = time.time()
    c.compile(node=program)
    compiler_end_time = time.time()
    
    # Check for compilation errors
    if len(c.errors) > 0:
        print("Compiler encountered the following errors:")
        for err in c.errors:
            print(f"\t{err}")
        exit(1)

    # output steps
    module: ir.Module = c.module
    module.triple = llvm.get_default_triple()

    if COMPILER_DEBUG:
        print("------ COMPILER DEBUG --------")
        try:
            with open("debug/ir.ll", "w") as f:
                f.write(str(module))
            print("Wrote LLVM IR to debug/ir.ll successfully!")
        except Exception as e:
            print(f"Warning: Could not write LLVM debug file: {e}")

    if RUN_CODE:
        # llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        try:
            llvm_ir_parsed = llvm.parse_assembly(str(module))
            llvm_ir_parsed.verify()
        except Exception as e:
            print("Error verifying LLVM IR:")
            print(e)
            exit(1)

        try:
            target_machine = llvm.Target.from_default_triple().create_target_machine()
            engine = llvm.create_mcjit_compiler(llvm_ir_parsed, target_machine)
            engine.finalize_object()

            entry = engine.get_function_address("main")
            cfunc = CFUNCTYPE(c_int)(entry)

            start_time = time.time()
            result = cfunc()
            end_time = time.time()

            if PROD_DEBUG:
                print(f'\n\nProgram returned: {result}\n=== Execution Time: {round((end_time - start_time) * 1000, 6)} ms ===')
                print(f'=== Parsing Time: {round((parse_end_time - parse_start_time) * 1000, 6)} ms ===')
                print(f'=== Compilation Time: {round((compiler_end_time - compiler_start_time) * 1000, 6)} ms ===')

            print(f'\n\nProgram returned: {result}\n=== Execution Time: {round((end_time - start_time) * 1000, 6)} ms ===')
            
        except Exception as e:
            print(f"Runtime error: {e}")
            exit(1)