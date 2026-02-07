from llvmlite import ir

from lime_ast import Node, NodeType, Program, Expression, Statement
from lime_ast import ExpressionStatement, InfixExpression, LetStatement, CallExpression
from lime_ast import FunctionStatement, ReturnStatement, BlockStatement, AssignStatement, IfStatement
from lime_ast import IntegerLiteral, FloatLiteral, IdentifierLiteral, BooleanLiteral
from lime_ast import FunctionParameter
from lime_ast import StringLiteral

from environment import Environment

class Compiler:
    def __init__(self) -> None:
        self.type_map: dict[str, ir.Type] = {
            "int": ir.IntType(32),
            "float": ir.FloatType(),
            "bool": ir.IntType(1),
            "str": ir.PointerType(ir.IntType(8)),
            "void": ir.VoidType()
        }

        self.module: ir.Module = ir.Module("main")
        self.builder: ir.IRBuilder = ir.IRBuilder()
        self.env: Environment = Environment()
        self.counter: int = 0

        # temporary keep track of errora
        self.errors: list[str] = []

        self.__initialize_builtins()

    def __initialize_builtins(self) -> None:
        def __init_print() -> ir.Function:
            fnty: ir.FunctionType = ir.FunctionType(
                self.type_map['int'],
                [ir.IntType(8).as_pointer()],
                var_arg=True
            )
            return ir.Function(self.module, fnty, name="printf")

        def __init_booleans() -> tuple[ir.GlobalVariable, ir.GlobalVariable]:
            bool_type: ir.Type = self.type_map["bool"]

            true_global = ir.GlobalVariable(self.module, bool_type, name="true")
            true_global.linkage = 'internal'
            true_global.global_constant = True
            true_global.initializer = ir.Constant(bool_type, 1)

            false_global = ir.GlobalVariable(self.module, ir.IntType(1), name="false")
            false_global.linkage = 'internal'
            false_global.global_constant = True
            false_global.initializer = ir.Constant(ir.IntType(1), 0)

            return true_global, false_global
        
        self.env.define("printf", __init_print(), ir.IntType(32))

        true_global, false_global = __init_booleans()
        self.env.define("true", true_global, self.type_map["bool"])
        self.env.define("false", false_global, self.type_map["bool"])

    def compile(self, node: Node) -> None:
        match node.type():
            case NodeType.Program:
                self.__visit_program(node)

            # statements
            case NodeType.ExpressionStatement:
                self.__visit_expression_statement(node)

            case NodeType.LetStatement:
                self.__visit_let_statement(node)

            case NodeType.FunctionStatement:
                self.__visit_function_statement(node)

            case NodeType.BlockStatement:
                self.__visit_block_statement(node)

            case NodeType.ReturnStatement:
                self.__visit_return_statement(node)
            
            case NodeType.AssignStatement:
                self.__visit_assign_statement(node)

            case NodeType.IfStatement:
                self.__visit_if_statement(node)

            # Expressions
            case NodeType.InfixExpression:
                self.__visit_infix_expression(node)
            case NodeType.CallExpression:
                self.__visit_call_expression(node)

# region visit methods
    def __visit_program(self, node: Program) -> None:
        # func_name: str = "main"
        # param_types: list[ir.Type] = []
        # return_type: ir.Type = self.type_map["int"]

        # fnty = ir.FunctionType(return_type, param_types)
        # func = ir.Function(self.module, fnty, name=func_name)

        # block = func.append_basic_block(f"{func_name}_entry")

        # self.builder = ir.IRBuilder(block)

        for stmt in node.statements:
            self.compile(stmt)

        # return_value: ir.Constant = ir.Constant(self.type_map["int"], 69)
        # self.builder.ret(return_value)

    # region statement visit methods
    def __visit_expression_statement(self, node: ExpressionStatement) -> None:
        self.compile(node.expr)

    def __visit_let_statement(self, node: LetStatement) -> None:
        name: str = node.name.value
        value: Expression = node.value
        value_type: str = node.value_type # TODO: Implement

        value, Type = self.__resolve_value(node = value)

        if self.env.lookup(name) is None:
            # Define and allocate the Variable
            ptr = self.builder.alloca(Type)

            # Storing the value to the ptr
            self.builder.store(value, ptr)
            
            # add the variable to the environment
            self.env.define(name, ptr, Type)

        else: 
            ptr, old_type = self.env.lookup(name)
            # If types match, reuse existing pointer
            if old_type == Type:
                self.builder.store(value, ptr)
            else:
                # Allocate new pointer for different type and update environment
                ptr = self.builder.alloca(Type)
                self.builder.store(value, ptr)
                self.env.define(name, ptr, Type)


    def __visit_block_statement(self, node: BlockStatement) -> None:
        for stmt in node.statements:
            self.compile(stmt)

    def __visit_return_statement(self, node: ReturnStatement) -> None:
        value: Expression = node.return_value
        value, Type = self.__resolve_value(value)
        self.builder.ret(value)

    def __visit_function_statement(self, node: FunctionStatement) -> None:
        name: str = node.name.value
        body: BlockStatement = node.body
        params: list[FunctionParameter] = node.parameters

        # keep track of the names of each parameter
        params_names: list[str] = [param.name for param in params]

        # keep track of the types for each parameter
        params_types: list[ir.Type] = [self.type_map[param.value_type] for param in params]

        return_type: ir.Type = self.type_map[node.return_type]

        fnty: ir.FunctionType = ir.FunctionType(return_type, params_types)
        func: ir.Function = ir.Function(self.module, fnty, name=name)

        block: ir.Block = func.append_basic_block(f"{name}_entry")

        previous_builder = self.builder

        self.builder = ir.IRBuilder(block)

        # staring the pointers to each parameter
        params_ptr = []
        for i, typ in enumerate(params_types):
            ptr = self.builder.alloca(typ)
            self.builder.store(func.args[i], ptr)
            params_ptr.append(ptr)


        # adding the parameters to the environment
        previous_env = self.env
        self.env = Environment(parent=previous_env)
        for i, x in enumerate(zip(params_types, params_names)):
            typ = params_types[i]
            ptr = params_ptr[i]

            self.env.define(x[1], ptr, typ)

        self.env.define(name, func, return_type)

        self.compile(body)

        self.env = previous_env
        self.env.define(name, func, return_type)

        self.builder = previous_builder

    def __visit_assign_statement(self, node: AssignStatement) -> None:
        name: str = node.ident.value
        value: Expression = node.right_value

        value, Type = self.__resolve_value(node = value)

        if self.env.lookup(name) is None:
            self.errors.append(f"COMPILE ERROR: Identifier {name} has not been declared before it was re-assigned.")

        else:
            ptr, _ = self.env.lookup(name)
            self.builder.store(value, ptr)

    def __visit_if_statement(self, node: IfStatement) -> None:
        condition = node.condition
        consequence = node.consequence
        alternative = node.alternative

        test, _ = self.__resolve_value(condition)

        if alternative is None:
            with self.builder.if_then(test):
                self.compile(consequence)

        else:
            with self.builder.if_else(test) as (true, otherwise):
                # Creating a condition branch
                #        condition
                #         /   \
                #   true /     \ false
                #       /       \
                # if blocks   else blocks
                with true:
                    self.compile(consequence)
                with otherwise:
                    self.compile(alternative)

    # end region statement visit methods

    # region expression visit methods
    def __visit_infix_expression(self, node: InfixExpression) -> None:
        operator: str = node.operator
        left_value, left_type = self.__resolve_value(node.left_node)
        right_value, right_type = self.__resolve_value(node.right_node)

        value = None
        Type = None
        if isinstance(left_type, ir.IntType) and isinstance(right_type, ir.IntType):
            Type = self.type_map["int"]
            match operator:
                case "+":
                    value = self.builder.add(left_value, right_value)
                case "-":
                    value = self.builder.sub(left_value, right_value)
                case "*":
                    value = self.builder.mul(left_value, right_value)
                case "/":
                    value = self.builder.sdiv(left_value, right_value)
                case "%":
                    value = self.builder.srem(left_value, right_value)
                case "^":
                    # TODO
                    pass
                case "<":
                    value = self.builder.icmp_signed("<", left_value, right_value)
                    Type = ir.IntType(1)
                case "<=":
                    value = self.builder.icmp_signed("<=", left_value, right_value)
                    Type = ir.IntType(1)
                case ">":
                    value = self.builder.icmp_signed(">", left_value, right_value)
                    Type = ir.IntType(1)
                case ">=":
                    value = self.builder.icmp_signed(">=", left_value, right_value)
                    Type = ir.IntType(1)
                case "==":
                    value = self.builder.icmp_signed("==", left_value, right_value)
                    Type = ir.IntType(1)
                case "!=":
                    value = self.builder.icmp_signed("!=", left_value, right_value)
                    Type = ir.IntType(1)
                

        elif isinstance(left_type, ir.FloatType) and isinstance(right_type, ir.FloatType):
            Type = ir.FloatType()
            match operator:
                case "+":
                    value = self.builder.fadd(left_value, right_value)
                case "-":
                    value = self.builder.fsub(left_value, right_value)
                case "*":
                    value = self.builder.fmul(left_value, right_value)
                case "/":
                    value = self.builder.fdiv(left_value, right_value)
                case "%":
                    value = self.builder.frem(left_value, right_value)
                case "^":
                    # TODO
                    pass
                case "<":
                    value = self.builder.fcmp_ordered("<", left_value, right_value)
                    Type = ir.IntType(1)
                case "<=":
                    value = self.builder.fcmp_ordered("<=", left_value, right_value)
                    Type = ir.IntType(1)
                case ">":
                    value = self.builder.fcmp_ordered(">", left_value, right_value)
                    Type = ir.IntType(1)
                case ">=":
                    value = self.builder.fcmp_ordered(">=", left_value, right_value)
                    Type = ir.IntType(1)
                case "==":
                    value = self.builder.fcmp_ordered("==", left_value, right_value)
                    Type = ir.IntType(1)
                case "!=":
                    value = self.builder.fcmp_ordered("!=", left_value, right_value)
                    Type = ir.IntType(1)

        return value, Type
    
    def __visit_call_expression(self, node: CallExpression) -> tuple[ir.Instruction, ir.Type]:
        name: str = node.function.value
        params: list[Expression] = node.arguments

        args = []
        types = []

        if len(params) > 0:
            for x in params:
                p_val, p_type = self.__resolve_value(x)
                args.append(p_val)
                types.append(p_type)
        match name:
            case "printf":
                ret = self.builtin_printf(params=args, return_type=types[0])
                ret_type = self.type_map["int"]
            case _:
                func, ret_type = self.env.lookup(name)
                ret = self.builder.call(func, args)

        return ret, ret_type
    # end region expression visit methods


# end region visit methods

    # region helper methods
    def __resolve_value(self, node: Expression) -> tuple[ir.Value, ir.Type]:
        match node.type():
            case NodeType.IntegerLiteral:
                node: IntegerLiteral = node
                value, Type = node.value, self.type_map["int"]
                return ir.Constant(Type, value), Type
            
            case NodeType.FloatLiteral:
                node: FloatLiteral = node
                value, Type = node.value, self.type_map["float"]
                return ir.Constant(Type, value), Type
            
            case NodeType.IdentifierLiteral:
                node: IdentifierLiteral = node
                ptr, Type = self.env.lookup(node.value)
                return self.builder.load(ptr), Type
            
            case NodeType.BooleanLiteral:
                node: BooleanLiteral = node
                value = 1 if node.value else 0
                Type = ir.IntType(1)
                return ir.Constant(Type, value), Type
            
            case NodeType.StringLiteral:
                node: StringLiteral = node
                string, Type = self.__convert_string(node.value)
                return string, Type

            # Expression Values
            case NodeType.InfixExpression:
                return self.__visit_infix_expression(node) 
            case NodeType.CallExpression:
                return self.__visit_call_expression(node)


    def __convert_string(self, string: str) -> tuple[ir.Constant, ir.ArrayType]:
        if string is None:
            string = ""
        
        string = string.replace("\\n", "\n\0")

        fmt : str = f"{string}\0"
        c_fmt: ir.Constant = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)), bytearray(fmt.encode("utf8")))

        global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name=f"__str_{self.__increment_counter()}")
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt
        
        return global_fmt, global_fmt.type

    def __increment_counter(self) -> int:
        self.counter += 1
        return self.counter

    def builtin_printf(self, params: list[ir.Instruction], return_type: ir.Type) -> None:
        """Basic C builtin printf function. Takes in a list of parameters and the return type, and returns the result of calling printf with the given parameters."""
        func, _ = self.env.lookup("printf")
        
        c_str = self.builder.alloca(return_type)
        self.builder.store(params[0], c_str)

        rest_params = params[1:]

        if isinstance(params[0], ir.LoadInstr):
            """ Printing from a variable load instruction"""
            # let a: str = "Hello, World!"
            # printf(a)
            c_fmt: ir.LoadInstr = params[0]
            g_var_ptr = c_fmt.operands[0]
            string_val = self.builder.load(g_var_ptr)
            fmt_arg = self.builder.bitcast(string_val, ir.IntType(8).as_pointer())
            return self.builder.call(func, [fmt_arg, *rest_params])
        else:
            """ Printing from a normal string declared within printf """
            # printf("yeet %i", 23)
            # TODO: Handle PRINTING FLOATS
            fmt_arg = self.builder.bitcast(params[0], ir.IntType(8).as_pointer())

            return self.builder.call(func, [fmt_arg, *rest_params])

    # end region helper methods
