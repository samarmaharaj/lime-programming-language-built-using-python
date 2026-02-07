from lime_token import Token, TokenType, lookup_ident
from typing import Any

class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source

        self.position: int = -1
        self.read_position: int = 0
        self.line: int = 1

        self.current_char: str | None = None
        self.__read_char()

    def __read_char(self) -> None:
        if self.read_position >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.read_position]
        
        self.position = self.read_position
        self.read_position += 1

    def __peek_char(self) -> str | None:
        """ Peeks to the upcoming character without advancing the lexer. """
        if self.read_position >= len(self.source):
            return None
        else:
            return self.source[self.read_position]

    def __skip_whitespace(self) -> None:
        while self.current_char in [' ', '\t', '\n', '\r']:
            if self.current_char == '\n':
                self.line += 1
            self.__read_char()

    def __new_token(self, tt: TokenType, literal: Any) -> Token:
        return Token(type=tt, literal=literal, line=self.line, position=self.position)

    def __is_digit(self, ch: str) -> bool:
        return '0' <= ch <= '9'
    
    def __is_letter(self, ch: str) -> bool:
        return ('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or (ch == '_')

    def __read_number_token(self) -> Token:
        start_pos: int = self.position
        dot_count: int = 0

        output: str = ""
        while self.__is_digit(self.current_char) or self.current_char == '.':
            if self.current_char == '.':
                dot_count += 1
            
            if dot_count > 1:
                print(f"Too many decimal points in number at line {self.line}, position {self.position}")
                return self.__new_token(TokenType.ILLEGAL, output + self.current_char)
            
            output += self.source[self.position]
            self.__read_char()

            if self.current_char is None:
                break

        if dot_count == 0:
            return self.__new_token(TokenType.INT, int(output))
        else:
            return self.__new_token(TokenType.FLOAT, float(output))
        
    def __read_identifier(self) -> str:
        position = self.position
        while self.current_char is not None and (self.__is_letter(self.current_char) or self.current_char.isalnum()):
            self.__read_char()

        return self.source[position:self.position]

    def next_token(self) -> Token:
        tok: Token = None

        self.__skip_whitespace()

        match self.current_char:
            case '+':
                tok = self.__new_token(TokenType.PLUS, self.current_char)
            case '-':
                # handle ->
                if self.__peek_char() == '>':
                    current_char = self.current_char
                    self.__read_char()
                    literal = current_char + self.current_char
                    tok = self.__new_token(TokenType.ARROW, literal)
                else:
                    tok = self.__new_token(TokenType.MINUS, self.current_char)
            case '*':
                tok = self.__new_token(TokenType.ASTERISK, self.current_char)
            case '/':
                tok = self.__new_token(TokenType.SLASH, self.current_char)
            case '^':
                tok = self.__new_token(TokenType.POWER, self.current_char)
            case '%':
                tok = self.__new_token(TokenType.MODULO, self.current_char)
            case '<':
                # handle <=
                if self.__peek_char() == '=':
                    current_char = self.current_char
                    self.__read_char()
                    literal = current_char + self.current_char
                    tok = self.__new_token(TokenType.LT_EQ, literal)
                else:
                    tok = self.__new_token(TokenType.LT, self.current_char)
            case '>':
                # handle >=
                if self.__peek_char() == '=':
                    current_char = self.current_char
                    self.__read_char()
                    literal = current_char + self.current_char
                    tok = self.__new_token(TokenType.GT_EQ, literal)
                else:
                    tok = self.__new_token(TokenType.GT, self.current_char)
            case '=':
                # handle ==
                if self.__peek_char() == '=':
                    current_char = self.current_char
                    self.__read_char()
                    literal = current_char + self.current_char
                    tok = self.__new_token(TokenType.EQ_EQ, literal)
                else:
                    tok = self.__new_token(TokenType.EQ, self.current_char)
            case '!':
                # handle !=
                if self.__peek_char() == '=':
                    current_char = self.current_char
                    self.__read_char()
                    literal = current_char + self.current_char
                    tok = self.__new_token(TokenType.NOT_EQ, literal)
                else:
                    # TODO: Implement BANG``
                    tok = self.__new_token(TokenType.ILLEGAL, self.current_char)
            case ':':
                tok = self.__new_token(TokenType.COLON, self.current_char)
            case ',':
                tok = self.__new_token(TokenType.COMMA, self.current_char)
            case '"':
                tok = self.__new_token(TokenType.STRING, self.__read_string())
            case ';':
                tok = self.__new_token(TokenType.SEMICOLON, self.current_char)
            case '(':
                tok = self.__new_token(TokenType.LPAREN, self.current_char)
            case ')':
                tok = self.__new_token(TokenType.RPAREN, self.current_char)
            case '{':
                tok = self.__new_token(TokenType.LBRACE, self.current_char)
            case '}':
                tok = self.__new_token(TokenType.RBRACE, self.current_char)
            case None:
                tok = self.__new_token(TokenType.EOF, "")
            case _:
                if self.__is_letter(self.current_char):
                    literal: str = self.__read_identifier()
                    tt: TokenType = lookup_ident(literal)
                    tok = self.__new_token(tt=tt, literal=literal)
                    return tok
                elif self.current_char.isdigit():
                    tok = self.__read_number_token()
                    return tok
                else:
                    tok = self.__new_token(TokenType.ILLEGAL, self.current_char)


        self.__read_char()
        return tok
    
    def __read_string(self) -> str:
        position: int = self.position + 1
        while True:
            self.__read_char()
            if self.current_char == '"' or self.current_char is None:
                break