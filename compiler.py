from llvmlite import ir
import os

from lime_ast import Node, NodeType, Program, Expression, ImportStatement
from lime_ast import ExpressionStatement, InfixExpression, LetStatement, CallExpression
from lime_ast import FunctionStatement, ReturnStatement, BlockStatement, AssignStatement, IfStatement
from lime_ast import IntegerLiteral, FloatLiteral, IdentifierLiteral, BooleanLiteral
from lime_ast import FunctionParameter
from lime_ast import StringLiteral
from lime_ast import WhileStatement, BreakStatement, ContinueStatement, ForStatement
from lime_ast import PrefixExpression, PostfixExpression

from environment import Environment

from lime_lexer import Lexer
from lime_parser import Parser

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

        # keeps a reference to the compiling Loop blocks
        self.breakpoints: list[ir.Block] = []
        self.continues: list[ir.Block] = []

        # keeps a reference to parsed pallets
        self.global_parsed_pallets: dict[str, Program] = {}


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

            case NodeType.WhileStatement:
                self.__visit_while_statement(node)

            case NodeType.BreakStatement:
                self.__visit_break_statement(node) 

            case NodeType.ContinueStatement:
                self.__visit_continue_statement(node)

            case NodeType.ForStatement:
                self.__visit_for_statement(node)

            case NodeType.ImportStatement:
                self.__visit_import_statement(node)


            # Expressions
            case NodeType.InfixExpression:
                self.__visit_infix_expression(node)
            case NodeType.CallExpression:
                self.__visit_call_expression(node)
            case NodeType.PostfixExpression:
                self.__visit_postfix_expression(node)

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
        operator: str = node.operator
        value: Expression = node.right_value


        if self.env.lookup(name) is None:
            self.errors.append(f"COMPILE ERROR: Identifier {name} has not been declared before it was re-assigned.")
            return

        right_value, right_type = self.__resolve_value(value)
        var_ptr, _ = self.env.lookup(name)
        orig_value = self.builder.load(var_ptr)

        if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.FloatType):
            orig_value = self.builder.sitofp(orig_value, ir.FloatType())

        if isinstance(orig_value.type, ir.FloatType) and isinstance(right_type, ir.IntType):
            right_value = self.builder.sitofp(right_value, ir.FloatType())

        value = None
        Type = None
        match operator:
            case "=":
                value = right_value
            case "+=":
                if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                    value = self.builder.add(orig_value, right_value)
                else:
                    value = self.builder.fadd(orig_value, right_value) 
            case "-=":
                if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                    value = self.builder.sub(orig_value, right_value)
                else:
                    value = self.builder.fsub(orig_value, right_value)
            case "*=":
                if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                    value = self.builder.mul(orig_value, right_value)
                else:
                    value = self.builder.fmul(orig_value, right_value)
            case "/=":
                if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                    value = self.builder.sdiv(orig_value, right_value)
                else:
                    value = self.builder.fdiv(orig_value, right_value)
            case _:
                self.errors.append(f"COMPILE ERROR: Unsupported assignment operator {operator}")
                return
                
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

    def __visit_while_statement(self, node: WhileStatement) -> None:
        condition: Expression = node.condition
        body: BlockStatement = node.body

        while_loop_condition = self.builder.append_basic_block(f"while_loop_condition_{self.__increment_counter()}")
        while_loop_body = self.builder.append_basic_block(f"while_loop_body_{self.counter}")
        while_loop_end = self.builder.append_basic_block(f"while_loop_end_{self.counter}")

        self.breakpoints.append(while_loop_end)
        self.continues.append(while_loop_condition)

        # Jump to condition check
        self.builder.branch(while_loop_condition)
        
        # Condition check block
        self.builder.position_at_start(while_loop_condition)
        test, _ = self.__resolve_value(condition)
        self.builder.cbranch(test, while_loop_body, while_loop_end)

        # Loop body block
        self.builder.position_at_start(while_loop_body)
        self.compile(body)
        self.builder.branch(while_loop_condition)

        # End block
        self.builder.position_at_start(while_loop_end)
        
        self.breakpoints.pop()
        self.continues.pop()

    def __visit_break_statement(self, node: BreakStatement) -> None:
        self.builder.branch(self.breakpoints[-1])

    def __visit_continue_statement(self, node: ContinueStatement) -> None:
        self.builder.branch(self.continues[-1])

    def __visit_for_statement(self, node: ForStatement) -> None:
        # for (let i: int = 0; i < 10; i++) { ... }
        initializer: LetStatement = node.initializer
        condition: Expression = node.condition
        increment: Expression = node.increment
        body: BlockStatement = node.body

        previous_env = self.env
        self.env = Environment(parent=previous_env)

        self.compile(initializer)

        for_loop_condition = self.builder.append_basic_block(f"for_loop_condition_{self.__increment_counter()}")
        for_loop_body = self.builder.append_basic_block(f"for_loop_body_{self.counter}")
        for_loop_increment = self.builder.append_basic_block(f"for_loop_increment_{self.counter}")
        for_loop_end = self.builder.append_basic_block(f"for_loop_end_{self.counter}")

        self.breakpoints.append(for_loop_end)
        self.continues.append(for_loop_increment)

        # Jump to condition check
        self.builder.branch(for_loop_condition)
        
        # Condition check block
        self.builder.position_at_start(for_loop_condition)
        test, _ = self.__resolve_value(condition)
        self.builder.cbranch(test, for_loop_body, for_loop_end)

        # Loop body block
        self.builder.position_at_start(for_loop_body)
        self.compile(body)
        self.builder.branch(for_loop_increment)

        # Increment block (continue point)
        self.builder.position_at_start(for_loop_increment)
        # Evaluate the increment expression (like i++ or i += 1)
        self.__resolve_value(increment)
        self.builder.branch(for_loop_condition)

        # End block
        self.builder.position_at_start(for_loop_end)

        self.env = previous_env
        self.breakpoints.pop()
        self.continues.pop()

    def __visit_import_statement(self, node: ImportStatement) -> None:
        # Extract module name from string literal, removing quotes and .lime extension if present
        module_name_raw: str = node.module_name.value
        # Remove quotes if present
        if module_name_raw.startswith('"') and module_name_raw.endswith('"'):
            module_name_raw = module_name_raw[1:-1]
        # Remove .lime extension if present
        if module_name_raw.endswith('.lime'):
            module_name = module_name_raw[:-5]
        else:
            module_name = module_name_raw

        # Check if already imported
        if module_name in self.global_parsed_pallets:
            # Already parsed, just compile it again in current context
            imported_program = self.global_parsed_pallets[module_name]
        else:
            # Try multiple possible file paths
            possible_paths = [
                os.path.join("tests", f"{module_name}.lime"),
                os.path.join(".", f"{module_name}.lime"),
                f"{module_name}.lime"
            ]
            
            file_path = None
            for path in possible_paths:
                if os.path.isfile(path):
                    file_path = path
                    break
            
            if file_path is None:
                self.errors.append(f"COMPILE ERROR: Cannot find module '{module_name}' in any of these locations: {possible_paths}")
                return
            
            try:
                with open(file_path, "r") as f:
                    source_code: str = f.read()
            except Exception as e:
                self.errors.append(f"COMPILE ERROR: Failed to read module '{module_name}' from '{file_path}': {e}")
                return

            lexer = Lexer(source=source_code)
            parser = Parser(lexer=lexer)
            imported_program = parser.parse_program()

            if len(parser.errors) > 0:
                self.errors.append(f"COMPILE ERROR: Errors encountered while parsing module '{module_name}':")
                for err in parser.errors:
                    self.errors.append(f"\t{err}")
                return
            
            # Cache the parsed program
            self.global_parsed_pallets[module_name] = imported_program
        
        # Compile the imported program in the current environment
        self.compile(imported_program)
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
    
    def __visit_prefix_expression(self, node: PrefixExpression) -> tuple[ir.Value, ir.Type]:
        operator: str = node.operator
        right_node: Expression = node.right_node

        right_value, right_type = self.__resolve_value(right_node)

        Type = None
        value = None
        if isinstance(right_type, ir.FloatType):
            Type = ir.FloatType()
            match operator:
                case "-":
                    value = self.builder.fmul(right_value, ir.Constant(ir.FloatType(), -1.0))
                case "!":
                    value = ir.Constant(ir.IntType(1), 0)
            
        elif isinstance(right_type, ir.IntType):
            Type = ir.IntType(32)
            match operator:
                case "-":
                    value = self.builder.mul(right_value, ir.Constant(ir.IntType(32), -1))
                case "!":
                    value = self.builder.not_(right_value)    

        return value, Type
    
    def __visit_postfix_expression(self, node: PostfixExpression) -> tuple[ir.Value, ir.Type]:
        left_node: IdentifierLiteral = node.left_node
        operator: str = node.operator

        if self.env.lookup(left_node.value) is None:
            self.errors.append(f"COMPILE ERROR: Identifier {left_node.value} has not been declared before it was used in a postfix expression.")
            return None, None
        
        var_ptr, var_type = self.env.lookup(left_node.value)
        orig_value = self.builder.load(var_ptr)

        # For postfix operators, we return the original value before modification
        result_value = orig_value

        new_value = None
        match operator:
            case "++":
                if isinstance(orig_value.type, ir.IntType):
                    new_value = self.builder.add(orig_value, ir.Constant(ir.IntType(32), 1))
                elif isinstance(orig_value.type, ir.FloatType):
                    new_value = self.builder.fadd(orig_value, ir.Constant(ir.FloatType(), 1.0))
                else:
                    self.errors.append(f"COMPILE ERROR: Unsupported type for ++ operator on identifier {left_node.value}")
                    return None, None
            case "--":
                if isinstance(orig_value.type, ir.IntType):
                    new_value = self.builder.sub(orig_value, ir.Constant(ir.IntType(32), 1))
                elif isinstance(orig_value.type, ir.FloatType):
                    new_value = self.builder.fsub(orig_value, ir.Constant(ir.FloatType(), 1.0))
                else:
                    self.errors.append(f"COMPILE ERROR: Unsupported type for -- operator on identifier {left_node.value}")
                    return None, None
                
        # Store the new value back to the variable
        self.builder.store(new_value, var_ptr)
        
        # Return the original value (postfix semantics)
        return result_value, var_type
    # endregion expression visit methods


# endregion visit methods

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
            case NodeType.PrefixExpression:
                return self.__visit_prefix_expression(node)
            case NodeType.PostfixExpression:
                return self.__visit_postfix_expression(node)


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
