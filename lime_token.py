from enum import Enum
from typing import Any

class TokenType(Enum):
    #Special Tokens
    EOF = "EOF"
    ILLEGAL = "ILLEGAL"

    #data types
    IDENT = "IDENT"
    INT = "INT"
    FLOAT = "FLOAT"

    #arithemtic operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    ASTERISK = "ASTERISK"
    SLASH = "SLASH"
    POWER = "POWER"
    MODULO = "MODULO"

    # assignment operator
    EQ = "EQ"

    # comparison operators
    LT = "<"
    GT = ">"
    EQ_EQ = "=="
    NOT_EQ = "!="
    LT_EQ = "<="
    GT_EQ = ">="

    #symbols
    COLON = "COLON"
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"
    ARROW = "ARROW"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"

    #keywords
    LET = "LET"
    FN = "FN"
    RETURN = "RETURN"
    IF = "IF"
    ELSE = "ELSE"
    TRUE = "TRUE"
    FALSE = "FALSE"

    # typing
    TYPE = "TYPE"


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
    
KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE
}

ALT_KEYWORDS: dict[str, TokenType] = {
    "lit": TokenType.LET,
    "be": TokenType.EQ,
    "rn": TokenType.SEMICOLON,
    "bruh": TokenType.FN,
    "pause": TokenType.RETURN,
    "snek": TokenType.ARROW,
    "sus": TokenType.IF,
    "imposter": TokenType.ELSE
}

TYPE_KEYWORDS: list[str] = ["int", "float"]

def lookup_ident(ident: str) -> TokenType:
    tt: TokenType | None = KEYWORDS.get(ident)
    if tt is not None:
        return tt
    
    tt: TokenType | None = ALT_KEYWORDS.get(ident)
    if tt is not None:
        return tt
    
    if ident in TYPE_KEYWORDS:
        return TokenType.TYPE
    
    return TokenType.IDENT
