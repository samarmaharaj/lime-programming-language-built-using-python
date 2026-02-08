from lime_lexer import Lexer
from lime_token import Token, TokenType
from typing import Callable
from enum import Enum, auto

from lime_ast import Statement, Expression, Program
from lime_ast import ExpressionStatement, FunctionStatement, ReturnStatement, BlockStatement
from lime_ast import AssignStatement,  WhileStatement, BreakStatement, ContinueStatement, ForStatement
from lime_ast import InfixExpression
from lime_ast import CallExpression, PrefixExpression, PostfixExpression
from lime_ast import LetStatement, IfStatement, ImportStatement
from lime_ast import IntegerLiteral, FloatLiteral, IdentifierLiteral, BooleanLiteral
from lime_ast import FunctionParameter
from lime_ast import StringLiteral

# precedence Types
class PrecedenceType(Enum):
    P_LOWEST = 0
    P_EQUALS = auto()
    P_LESSGREATER = auto()
    P_SUM = auto()
    P_PRODUCT = auto()
    P_EXPONENT = auto()
    P_PREFIX = auto()
    P_CALL = auto()
    P_INDEX = auto()

#precedence Mapping
PRECEDENCES: dict[TokenType, PrecedenceType] = {
    TokenType.PLUS: PrecedenceType.P_SUM,
    TokenType.MINUS: PrecedenceType.P_SUM,
    TokenType.SLASH: PrecedenceType.P_PRODUCT,
    TokenType.ASTERISK: PrecedenceType.P_PRODUCT,
    TokenType.MODULO: PrecedenceType.P_PRODUCT,
    TokenType.POWER: PrecedenceType.P_EXPONENT,
    TokenType.EQ_EQ: PrecedenceType.P_EQUALS,
    TokenType.NOT_EQ: PrecedenceType.P_EQUALS,
    TokenType.LT: PrecedenceType.P_LESSGREATER,
    TokenType.GT: PrecedenceType.P_LESSGREATER,
    TokenType.LT_EQ: PrecedenceType.P_LESSGREATER,
    TokenType.GT_EQ: PrecedenceType.P_LESSGREATER,
    TokenType.LPAREN: PrecedenceType.P_CALL,

    TokenType.PLUS_PLUS: PrecedenceType.P_INDEX,
    TokenType.MINUS_MINUS: PrecedenceType.P_INDEX
}

class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer: Lexer = lexer
        
        self.errors: list[str] = []
    
        self.current_token: Token = None
        self.peek_token: Token = None

        self.prefix_parse_fns: dict[TokenType, Callable] = {
            TokenType.IDENT: self.__parse_identifier,
            TokenType.INT: self.__parse_int_literal,
            TokenType.FLOAT: self.__parse_float_literal,
            TokenType.LPAREN: self.__parse_grouped_expression,
            TokenType.IF: self.__parse_if_expression,
            TokenType.TRUE: self.__parse_boolean,
            TokenType.FALSE: self.__parse_boolean,

            TokenType.STRING: self.__parse_string_literal,

            TokenType.BANG: self.__parse_prefix_expression,
            TokenType.MINUS: self.__parse_prefix_expression
        }
        self.infix_parse_fns: dict[TokenType, Callable] = {
            TokenType.PLUS: self.__parse_infix_expression,
            TokenType.MINUS: self.__parse_infix_expression,
            TokenType.SLASH: self.__parse_infix_expression,
            TokenType.ASTERISK: self.__parse_infix_expression,
            TokenType.POWER: self.__parse_infix_expression,
            TokenType.MODULO: self.__parse_infix_expression,
            TokenType.EQ_EQ: self.__parse_infix_expression,
            TokenType.NOT_EQ: self.__parse_infix_expression,
            TokenType.LT: self.__parse_infix_expression,
            TokenType.GT: self.__parse_infix_expression,
            TokenType.LT_EQ: self.__parse_infix_expression,
            TokenType.GT_EQ: self.__parse_infix_expression,
            TokenType.LPAREN: self.__parse_call_expression,

            TokenType.PLUS_PLUS: self.__parse_postfix_expression,
            TokenType.MINUS_MINUS: self.__parse_postfix_expression
        }

        self.__next_token()
        self.__next_token()

    # region Parser Helpers
    def __next_token(self) -> None:
        self.current_token = self.peek_token
        self.peek_token = self.lexer.next_token()

    def __current_token_is(self, tt: TokenType) -> bool:
        return self.current_token.type == tt

    def __peek_token_is(self, tt: TokenType) -> bool:
        return self.peek_token.type == tt
    
    def __peek_token_is_assignment(self) -> bool:
        assignment_operators: list[TokenType] = [
            TokenType.EQ,
            TokenType.PLUS_EQ,
            TokenType.MINUS_EQ,
            TokenType.MUL_EQ,
            TokenType.DIV_EQ
        ]

        return self.peek_token.type in assignment_operators
    
    def __expect_peek(self, tt: TokenType) -> bool:
        if self.__peek_token_is(tt):
            self.__next_token()
            return True
        else:
            self.__peek_error(tt)
            return False
        
    def __current_precedence(self) -> PrecedenceType:
        prec: int | None = PRECEDENCES.get(self.current_token.type)
        if prec is None:
            return PrecedenceType.P_LOWEST
        return prec
    
    def __peek_precedence(self) -> PrecedenceType:
        prec: int | None = PRECEDENCES.get(self.peek_token.type)
        if prec is None:
            return PrecedenceType.P_LOWEST
        return prec
        
    def __peek_error(self, tt: TokenType) -> None:
        self.errors.append(
            f"Expected next token to be {tt}, got {self.peek_token.type} instead"
        )

    def __no_prefix_parse_fn_error(self, tt: TokenType):
        self.errors.append(
            f"No prefix parse function for {tt} found"
        )
    # endregion

    def parse_program(self) -> None:
        program: Program = Program()

        while self.current_token.type != TokenType.EOF:
            stmt: Statement = self.__parse_statement()
            if stmt is not None:
                program.statements.append(stmt)
            self.__next_token()
        
        return program
    
    # region statement methods
    def __parse_statement(self) -> Statement:
        if self.current_token.type == TokenType.IDENT and self.__peek_token_is_assignment():
            stmt = self.__parse_assignment_statement()
            # Handle semicolon for assignment statements in statement context
            if self.__peek_token_is(TokenType.SEMICOLON):
                self.__next_token()
            return stmt

        match self.current_token.type:
            case TokenType.LET:
                stmt = self.__parse_let_statement()
                # Handle semicolon for let statements in statement context
                if self.__peek_token_is(TokenType.SEMICOLON):
                    self.__next_token()
                return stmt
            case TokenType.FN:
                return self.__parse_function_statement()
            case TokenType.RETURN:
                return self.__parse_return_statement()
            case TokenType.WHILE:
                return self.__parse_while_statement()
            case TokenType.BREAK:
                return self.__parse_break_statement()
            case TokenType.CONTINUE:
                return self.__parse_continue_statement()
            case TokenType.FOR:
                return self.__parse_for_statement()
            case TokenType.IMPORT:
                return self.__parse_import_statement()
            case _:
                return self.__parse_expression_statement()
    
    def __parse_expression_statement(self) -> ExpressionStatement:
        expr = self.__parse_expression(PrecedenceType.P_LOWEST)

        if self.__peek_token_is(TokenType.SEMICOLON):
            self.__next_token()

        stmt: ExpressionStatement = ExpressionStatement(expr=expr)

        return stmt
    
    def __parse_let_statement(self) -> LetStatement:
        # let a: int = 10;
        stmt: LetStatement = LetStatement()

        if not self.__expect_peek(TokenType.IDENT):
            return None
        
        stmt.name = IdentifierLiteral(value=self.current_token.literal)

        if not self.__expect_peek(TokenType.COLON):
            return None
        
        if not self.__expect_peek(TokenType.TYPE):
            return None
        
        stmt.value_type = self.current_token.literal

        if not self.__expect_peek(TokenType.EQ):
            return None
        
        self.__next_token()

        stmt.value = self.__parse_expression(PrecedenceType.P_LOWEST)

        # Don't automatically consume semicolon - let the caller handle it
        return stmt
    
    def __parse_function_statement(self) -> FunctionStatement:
        stmt: FunctionStatement = FunctionStatement()

        # fn name() -> int { return 10;}
        if not self.__expect_peek(TokenType.IDENT):
            return None
        
        stmt.name = IdentifierLiteral(value=self.current_token.literal)

        if not self.__expect_peek(TokenType.LPAREN):
            return None
        
        stmt.parameters = self.__parse_function_parameters()
        
        if not self.__expect_peek(TokenType.ARROW):
            return None
        
        if not self.__expect_peek(TokenType.TYPE):
            return None
        
        stmt.return_type = self.current_token.literal

        if not self.__expect_peek(TokenType.LBRACE):
            return None
        
        stmt.body = self.__parse_block_statement()

        return stmt
    
    def __parse_function_parameters(self) -> list[FunctionParameter]:
        params: list[FunctionParameter] = []

        if self.__peek_token_is(TokenType.RPAREN):
            self.__next_token()
            return params
        
        self.__next_token()

        first_param: FunctionParameter = FunctionParameter(name=self.current_token.literal)

        if not self.__expect_peek(TokenType.COLON):
            return None
        
        self.__next_token()
        
        first_param.value_type = self.current_token.literal
        params.append(first_param)

        while self.__peek_token_is(TokenType.COMMA):
            self.__next_token()
            self.__next_token()

            param: FunctionParameter = FunctionParameter(name=self.current_token.literal)

            if not self.__expect_peek(TokenType.COLON):
                return None
            
            self.__next_token()
            
            param.value_type = self.current_token.literal

            params.append(param)
        
        if not self.__expect_peek(TokenType.RPAREN):
            return None
        
        return params

    def __parse_return_statement(self) -> ReturnStatement:
        stmt: ReturnStatement = ReturnStatement()

        self.__next_token()

        stmt.return_value = self.__parse_expression(PrecedenceType.P_LOWEST)
        
        if not self.__expect_peek(TokenType.SEMICOLON):
            return None
        
        return stmt


    def __parse_block_statement(self) -> BlockStatement:
        block_stmt: BlockStatement = BlockStatement()

        self.__next_token()

        while not self.__current_token_is(TokenType.RBRACE) and not self.__current_token_is(TokenType.EOF):
            stmt: Statement = self.__parse_statement()
            if stmt is not None:
                block_stmt.statements.append(stmt)
            self.__next_token()
        
        return block_stmt
    
    def __parse_assignment_statement(self) -> AssignStatement:
        stmt: AssignStatement = AssignStatement()

        stmt.ident = IdentifierLiteral(value=self.current_token.literal)

        # Check for any assignment operator
        if not self.__peek_token_is_assignment():
            return None
        
        self.__next_token()  # Move to the assignment operator
        stmt.operator = self.current_token.literal
        
        self.__next_token()  # Move to the right-hand side

        stmt.right_value = self.__parse_expression(PrecedenceType.P_LOWEST)

        # Don't automatically consume semicolon - let the caller handle it
        return stmt

    def __parse_if_expression(self) -> IfStatement:
        condition: Expression = None
        consequence: BlockStatement = None
        alternative: BlockStatement = None

        self.__next_token()

        condition = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.LBRACE):
            return None
        
        consequence = self.__parse_block_statement()

        if self.__peek_token_is(TokenType.ELSE):
            self.__next_token()

            if not self.__expect_peek(TokenType.LBRACE):
                return None
            
            alternative = self.__parse_block_statement()

        return IfStatement(condition, consequence, alternative)
    
    def __parse_while_statement(self) -> WhileStatement:
        condition: Expression = None
        body: BlockStatement = None

        self.__next_token()

        condition = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.LBRACE):
            return None
        
        body = self.__parse_block_statement()

        return WhileStatement(condition=condition, body=body)
    
    def __parse_break_statement(self) -> BreakStatement:
        if self.__peek_token_is(TokenType.SEMICOLON):
            self.__next_token()
        return BreakStatement()
    
    def __parse_continue_statement(self) -> ContinueStatement:
        if self.__peek_token_is(TokenType.SEMICOLON):
            self.__next_token()
        return ContinueStatement()
    
    def __parse_for_statement(self) -> ForStatement:
        stmt: ForStatement = ForStatement()

        if not self.__expect_peek(TokenType.LPAREN):
            return None
        
        if not self.__expect_peek(TokenType.LET):
            return None
        
        stmt.initializer = self.__parse_let_statement()

        if not self.__expect_peek(TokenType.SEMICOLON):
            return None
        
        self.__next_token()

        stmt.condition = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.SEMICOLON):
            return None
        
        self.__next_token()
        
        stmt.increment = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.RPAREN):
            return None

        if not self.__expect_peek(TokenType.LBRACE):
            return None

        stmt.body = self.__parse_block_statement()

        return stmt
    
    def __parse_import_statement(self) -> ImportStatement:

        if not self.__expect_peek(TokenType.STRING):
            return None
        
        # Create a StringLiteral for the module name
        module_name = StringLiteral(value=self.current_token.literal)
        stmt: ImportStatement = ImportStatement(module_name=module_name)

        if self.__peek_token_is(TokenType.SEMICOLON):
            self.__next_token()
        
        return stmt
    # endregion statement methods

    # region expression methods
    def __parse_expression(self, precedence: PrecedenceType) -> Expression:
        prefix: Callable | None = self.prefix_parse_fns.get(self.current_token.type)
        if prefix is None:
            self.__no_prefix_parse_fn_error(self.current_token.type)
            return None
        
        left_expr: Expression = prefix()

        while (not self.__peek_token_is(TokenType.SEMICOLON) and
               precedence.value < self.__peek_precedence().value):
            infix: Callable | None = self.infix_parse_fns.get(self.peek_token.type)
            if infix is None:
                return left_expr
            
            self.__next_token()

            left_expr = infix(left_expr)
        
        return left_expr
    
    def __parse_infix_expression(self, left_node: Expression) -> Expression:
        infix_expr: InfixExpression = InfixExpression(
            left_node=left_node,
            operator=self.current_token.literal
        )

        precedence = self.__current_precedence()
        self.__next_token()
        infix_expr.right_node = self.__parse_expression(precedence)

        return infix_expr
    
    def __parse_grouped_expression(self) -> Expression:
        self.__next_token()

        expr: Expression = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.RPAREN):
            return None

        return expr
    
    def __parse_call_expression(self, function) -> CallExpression:
        expr: CallExpression = CallExpression(function=function)
        expr.arguments = self.__parse_expression_list(TokenType.RPAREN)
        return expr   
    
    def __parse_expression_list(self, end: TokenType) -> list[Expression]:
        e_list: list[Expression] = []

        if self.__peek_token_is(end):
            self.__next_token()
            return e_list
        
        self.__next_token()

        e_list.append(self.__parse_expression(PrecedenceType.P_LOWEST))

        while self.__peek_token_is(TokenType.COMMA):
            self.__next_token()
            self.__next_token()
            e_list.append(self.__parse_expression(PrecedenceType.P_LOWEST))
        
        if not self.__expect_peek(end):
            return None

        return e_list
    # endregion expression methods

    # region prefix methods
    def __parse_prefix_expression(self) -> PrefixExpression:
        prefix_expr: PrefixExpression = PrefixExpression(operator=self.current_token.literal)

        self.__next_token()

        prefix_expr.right_node = self.__parse_expression(PrecedenceType.P_PREFIX)

        return prefix_expr
    
    def __parse_postfix_expression(self, left_node: Expression) -> PostfixExpression:
        postfix_expr: PostfixExpression = PostfixExpression(
            left_node=left_node,
            operator=self.current_token.literal
        )

        return postfix_expr

    def __parse_identifier(self) -> IdentifierLiteral:
        return IdentifierLiteral(value=self.current_token.literal)

    def __parse_int_literal(self) -> Expression:
        """Parses an integer literal from the current token."""
        int_lit: IntegerLiteral = IntegerLiteral()

        try:
            int_lit.value = int(self.current_token.literal)
        except:
            self.errors.append(f"Could not parse `{self.current_token.literal}` as integer")
            return None
        
        return int_lit
    
    def __parse_float_literal(self) -> Expression:
        """Parses a float literal from the current token."""
        float_lit: FloatLiteral = FloatLiteral()

        try:
            float_lit.value = float(self.current_token.literal)
        except:
            self.errors.append(f"Could not parse `{self.current_token.literal}` as float")
            return None
        
        return float_lit
        
    def __parse_boolean(self) -> BooleanLiteral:
        return BooleanLiteral(value=self.__current_token_is(TokenType.TRUE))
    
    def __parse_string_literal(self) -> StringLiteral:
        return StringLiteral(value=self.current_token.literal)
    # endregion prefix methods