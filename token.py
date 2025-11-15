from enum import Enum
from typing import Any

class TokenType(Enum):
    #Special Tokens
    EOF = "EOF"
    ILLEGAL = "ILLEGAL"

    #data types
    INT = "INT"
    FLOAT = "FLOAT"

    #arithemtic operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    ASTERISK = "ASTERISK"
    SLASH = "SLASH"
    POWER = "POWER"
    MODULO = "MODULO"

    #symbols
    SEMICOLON = "SEMICOLON"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"

class Token:
    def __init__(self, type: TokenType, literal: Any, line: int, position: int) -> None:
        self.type = type
        self.literal = literal
        self.line = line
        self.position = position

    def __str__(self) -> str:
        return f"Token(type={self.type}, literal={self.literal}, line={self.line}, position={self.position})"
    
    def __repr__(self) -> str:
        return str(self)
    
