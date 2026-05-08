# =========================
# CFG (Grammar)
# =========================
# <Program>   ::= yalla <Block>
# <Block>     ::= { <Statement>* }
# <Statement> ::= <Print> | <If> | <While> | <For> | <Func> | <Return> | <AssignOrCall>
#
# <Print>     ::= ekteb ( <Expr> )
# <If>        ::= lw <Expr> <Block> [ nafez <Block> ]
# <While>     ::= Lamma <Expr> <Block>
# <For>       ::= kol IDENTIFIER fi <Expr> <Block>
# <Func>      ::= dalla IDENTIFIER ( <Params> ) <Block>
# <Return>    ::= khalas <Expr>
#
# <Expr>      ::= <Compare>
# <Compare>   ::= <Add> ( (== != > < >= <=) <Add> )*
# <Add>       ::= <Term> ( (+ | -) <Term> )*
# <Term>      ::= <Factor> ( (* | / | %) <Factor> )*
# <Factor>    ::= NUMBER | STRING | BOOLEAN | IDENTIFIER | ( <Expr> )

import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEYWORDS = {
    "yalla", "ekteb",
    "lw", "nafez",
    "Lamma", "kol", "fi",
    "dalla", "khalas"
}

BOOLEANS = {"true", "false"}

TOKEN_PATTERN = r'''
(?P<COMMENT>\#.*) |
(?P<EQEQ>==) |
(?P<NOTEQ>!=) |
(?P<GTEQ>>=) |
(?P<LTEQ><=) |
(?P<FLOAT>\d+\.\d+) |
(?P<INTEGER>\d+) |
(?P<STRING>"[^"]*") |
(?P<LBRACE>\{) |
(?P<RBRACE>\}) |
(?P<COMMA>,) |
(?P<ID>[A-Za-z_][A-Za-z0-9_]*) |
(?P<LPAREN>\() |
(?P<RPAREN>\)) |
(?P<NEWLINE>\n) |
(?P<WHITESPACE>[ \t]+) |
(?P<ASSIGN>=) |
(?P<OPERATOR>[+\-*/%<>])
'''

def scanner(code):
    tokens = []
    line = 1

    for m in re.finditer(TOKEN_PATTERN, code, re.VERBOSE):
        typ = m.lastgroup
        val = m.group()

        if typ in ("COMMENT", "WHITESPACE"):
            continue
        if typ == "NEWLINE":
            line += 1
            continue

        if typ == "ID":
            if val in KEYWORDS:
                typ = "KEYWORD"
            elif val in BOOLEANS:
                typ = "BOOLEAN"
            else:
                typ = "IDENTIFIER"

        tokens.append((line, typ, val))

    tokens.append((line, "EOF", "EOF"))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def cur(self):
        return self.tokens[self.pos]

    def eat(self, val=None, typ=None):
        line, t, v = self.cur()

        if val and v != val:
            raise Exception(f"[Line {line}] Expected '{val}', got '{v}'")

        if typ and t != typ:
            raise Exception(f"[Line {line}] Expected {typ}, got {t}")

        self.pos += 1
        return v

    def parse(self):
        self.eat("yalla")
        return ("PROGRAM", self.block())

    def block(self):
        self.eat("{")
        stmts = []
        while self.cur()[2] != "}":
            stmts.append(self.statement())
        self.eat("}")
        return stmts

    def statement(self):
        _, t, v = self.cur()

        if v == "ekteb":
            return self.print_stmt()
        elif v == "lw":
            return self.if_stmt()
        elif v == "Lamma":
            return self.while_stmt()
        elif v == "kol":
            return self.for_loop()
        elif v == "dalla":
            return self.func_def()
        elif v == "khalas":
            return self.return_stmt()
        elif t == "IDENTIFIER":
            return self.assign_or_call()
        else:
            raise Exception(f"Invalid statement '{v}'")

    def print_stmt(self):
        self.eat("ekteb")
        self.eat("(")
        val = self.expr()
        self.eat(")")
        return ("PRINT", val)

    def assign_or_call(self):
        name = self.eat(typ="IDENTIFIER")

        if self.cur()[2] == "(":
            self.eat("(")
            args = []
            if self.cur()[2] != ")":
                args.append(self.expr())
                while self.cur()[2] == ",":
                    self.eat(",")
                    args.append(self.expr())
            self.eat(")")
            return ("CALL", name, args)
        else:
            self.eat("=")
            val = self.expr()
            return ("ASSIGN", name, val)

    def return_stmt(self):
        self.eat("khalas")
        val = self.expr()
        return ("RETURN", val)

    def func_def(self):
        self.eat("dalla")
        name = self.eat(typ="IDENTIFIER")
        self.eat("(")

        params = []
        if self.cur()[2] != ")":
            params.append(self.eat(typ="IDENTIFIER"))
            while self.cur()[2] == ",":
                self.eat(",")
                params.append(self.eat(typ="IDENTIFIER"))

        self.eat(")")
        body = self.block()
        return ("FUNC", name, params, body)

    def if_stmt(self):
        self.eat("lw")
        cond = self.expr()
        body = self.block()

        else_body = []
        if self.cur()[2] == "nafez":
            self.eat("nafez")
            else_body = self.block()

        return ("IF", cond, body, else_body)

    def while_stmt(self):
        self.eat("Lamma")
        cond = self.expr()
        body = self.block()
        return ("WHILE", cond, body)

    def for_loop(self):
        self.eat("kol")
        var = self.eat(typ="IDENTIFIER")
        self.eat("fi")
        limit = self.expr()
        body = self.block()
        return ("FOR", var, limit, body)

    def expr(self):
        return self.compare()

    def compare(self):
        left = self.add()
        while self.cur()[2] in ("==","!=",">","<",">=","<="):
            op = self.eat()
            right = self.add()
            left = ("BIN", op, left, right)
        return left

    def add(self):
        left = self.term()
        while self.cur()[2] in ("+","-"):
            op = self.eat()
            right = self.term()
            left = ("BIN", op, left, right)
        return left

    def term(self):
        left = self.factor()
        while self.cur()[2] in ("*","/","%"):
            op = self.eat()
            right = self.factor()
            left = ("BIN", op, left, right)
        return left

    def factor(self):
        line, t, v = self.cur()

        if t == "INTEGER":
            self.eat()
            return ("VAL", int(v))
        if t == "FLOAT":
            self.eat()
            return ("VAL", float(v))
        if t == "STRING":
            self.eat()
            return ("VAL", v.strip('"'))
        if t == "BOOLEAN":
            self.eat()
            return ("VAL", v == "true")
        if t == "IDENTIFIER":
            name = self.eat()
            if self.cur()[2] == "(":
                self.eat("(")
                args = []
                if self.cur()[2] != ")":
                    args.append(self.expr())
                    while self.cur()[2] == ",":
                        self.eat(",")
                        args.append(self.expr())
                self.eat(")")
                return ("CALL", name, args)
            return ("VAR", name)
        if v == "(":
            self.eat("(")
            e = self.expr()
            self.eat(")")
            return e

        raise Exception(f"[Line {line}] Invalid expression '{v}'")


class Symbol:
    def __init__(self, name, typ, kind, scope):
        self.name = name
        self.typ = typ
        self.kind = kind
        self.scope = scope


class SymbolTable:
    def __init__(self):
        self.scopes = []

    def push(self):
        self.scopes.append({})

    def pop(self):
        self.scopes.pop()

    def declare(self, name, typ, kind):
        scope = self.scopes[-1]
        if name in scope:
            raise Exception(f"Semantic Error: '{name}' already declared")
        scope[name] = Symbol(name, typ, kind, len(self.scopes)-1)

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise Exception(f"Semantic Error: '{name}' not defined")


def check_type(t1, t2, op):
    if op in ("==","!=","<",">","<=",">="):
        return "bool"

    if t1 == t2:
        return t1

    if {t1, t2} == {"int", "float"}:
        return "float"

    raise Exception(f"Type Error: {t1} {op} {t2}")


class Semantic:
    def __init__(self):
        self.table = SymbolTable()
        self.funcs = {}

    def visit(self, node):
        if isinstance(node, tuple):
            method = "v_" + node[0]
            return getattr(self, method)(node)
        elif isinstance(node, list):
            for n in node:
                self.visit(n)

    def v_PROGRAM(self, n):
        self.table.push()
        self.visit(n[1])
        self.table.pop()

    def v_ASSIGN(self, n):
        _, name, val = n
        t = self.visit(val)
        self.table.declare(name, t, "variable")

    def v_VAR(self, n):
        return self.table.lookup(n[1]).typ

    def v_VAL(self, n):
        v = n[1]
        if isinstance(v, bool): return "bool"
        if isinstance(v, int): return "int"
        if isinstance(v, float): return "float"
        return "string"

    def v_BIN(self, n):
        _, op, a, b = n
        return check_type(self.visit(a), self.visit(b), op)

    def v_PRINT(self, n):
        self.visit(n[1])

    def v_IF(self, n):
        _, cond, body, elseb = n
        if self.visit(cond) != "bool":
            raise Exception("IF condition must be boolean")

        self.table.push()
        self.visit(body)
        self.table.pop()

        self.table.push()
        self.visit(elseb)
        self.table.pop()

    def v_WHILE(self, n):
        _, cond, body = n
        if self.visit(cond) != "bool":
            raise Exception("WHILE condition must be boolean")

        self.table.push()
        self.visit(body)
        self.table.pop()

    def v_FOR(self, n):
        _, var, limit, body = n
        if self.visit(limit) != "int":
            raise Exception("FOR needs integer")

        self.table.push()
        self.table.declare(var, "int", "variable")
        self.visit(body)
        self.table.pop()

    def v_FUNC(self, n):
        _, name, params, body = n
        self.funcs[name] = params

        self.table.push()
        for p in params:
            self.table.declare(p, "any", "param")
        self.visit(body)
        self.table.pop()

    def v_CALL(self, n):
        _, name, args = n

        if name not in self.funcs:
            raise Exception(f"function '{name}' not defined")

        if len(args) != len(self.funcs[name]):
            raise Exception("wrong number of args")

        for a in args:
            self.visit(a)

        return "any"

    def v_RETURN(self, n):
        return self.visit(n[1])


# CODE GENERATOR

class CodeGenerator:
    def __init__(self):
        self.lines = []
        self.indent = 0

    def emit(self, line):
        self.lines.append("    " * self.indent + line)

    def generate(self, node):
        return self.visit(node)

    def get_code(self):
        return "\n".join(self.lines)

    def visit(self, node):
        if isinstance(node, tuple):
            method = "v_" + node[0]
            return getattr(self, method)(node)
        elif isinstance(node, list):
            for n in node:
                self.visit(n)

    def v_PROGRAM(self, n):
        self.visit(n[1])

    def v_ASSIGN(self, n):
        _, name, val = n
        self.emit(f"{name} = {self.expr(val)}")

    def v_PRINT(self, n):
        self.emit(f"print({self.expr(n[1])})")

    def v_IF(self, n):
        _, cond, body, elseb = n
        self.emit(f"if {self.expr(cond)}:")
        self.indent += 1
        self.visit(body)
        self.indent -= 1
        if elseb:
            self.emit("else:")
            self.indent += 1
            self.visit(elseb)
            self.indent -= 1

    def v_WHILE(self, n):
        _, cond, body = n
        self.emit(f"while {self.expr(cond)}:")
        self.indent += 1
        self.visit(body)
        self.indent -= 1

    def v_FOR(self, n):
        _, var, limit, body = n
        self.emit(f"for {var} in range({self.expr(limit)}):")
        self.indent += 1
        self.visit(body)
        self.indent -= 1

    def v_FUNC(self, n):
        _, name, params, body = n
        params_str = ", ".join(params)
        self.emit(f"def {name}({params_str}):")
        self.indent += 1
        self.visit(body)
        self.indent -= 1
        self.emit("")  # blank line after func

    def v_RETURN(self, n):
        self.emit(f"return {self.expr(n[1])}")

    def v_CALL(self, n):
        # statement-level call (not inside expression)
        _, name, args = n
        args_str = ", ".join(self.expr(a) for a in args)
        self.emit(f"{name}({args_str})")

    # ---- expression helpers (return string, don't emit) ----

    def expr(self, node):
        if not isinstance(node, tuple):
            return str(node)
        tag = node[0]
        if tag == "VAL":
            v = node[1]
            if isinstance(v, str):
                return repr(v)
            if isinstance(v, bool):
                return "True" if v else "False"
            return str(v)
        if tag == "VAR":
            return node[1]
        if tag == "BIN":
            _, op, a, b = node
            return f"({self.expr(a)} {op} {self.expr(b)})"
        if tag == "CALL":
            _, name, args = node
            args_str = ", ".join(self.expr(a) for a in args)
            return f"{name}({args_str})"
        raise Exception(f"Unknown expr node: {tag}")


def read_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


def print_tokens(tokens):
    print("\n===== TOKENS =====")
    print("{:<5} {:<12} {}".format("LINE", "TYPE", "VALUE"))
    print("-" * 35)
    for t in tokens:
        print("{:<5} {:<12} {}".format(t[0], t[1], t[2]))


def print_ast(node, indent=""):
    if isinstance(node, tuple):
        print(indent + str(node[0]))
        for c in node[1:]:
            print_ast(c, indent + "  ")
    elif isinstance(node, list):
        for x in node:
            print_ast(x, indent)
    else:
        print(indent + str(node))


try:
    code = read_file("code.txt")

    # ===== LEXER =====
    tokens = scanner(code)
    print_tokens(tokens)

    # ===== PARSER =====
    parser = Parser(tokens)
    ast = parser.parse()

    print("\n===== AST (Parser Output) =====")
    print_ast(ast)

    # ===== SEMANTIC =====
    print("\n===== SEMANTIC CHECK =====")
    Semantic().visit(ast)
    print("\n✔ No Semantic Errors")

    # ===== CODE GENERATION =====
    print("\n===== CODE GENERATION =====")
    gen = CodeGenerator()
    gen.generate(ast)
    output_code = gen.get_code()
    print(output_code)

    import io

    def ast_to_lines(node, indent=""):
        lines = []
        if isinstance(node, tuple):
            lines.append(indent + str(node[0]))
            for c in node[1:]:
                lines.extend(ast_to_lines(c, indent + "  "))
        elif isinstance(node, list):
            for x in node:
                lines.extend(ast_to_lines(x, indent))
        else:
            lines.append(indent + str(node))
        return lines

    output_sections = []

    # --- Tokens ---
    output_sections.append("# " + "=" * 40)
    output_sections.append("# TOKENS")
    output_sections.append("# " + "=" * 40)
    output_sections.append('"""')
    output_sections.append("{:<5} {:<12} {}".format("LINE", "TYPE", "VALUE"))
    output_sections.append("-" * 35)
    for t in tokens:
        output_sections.append("{:<5} {:<12} {}".format(t[0], t[1], t[2]))
    output_sections.append('"""')
    output_sections.append("")

    # --- AST ---
    output_sections.append("# " + "=" * 40)
    output_sections.append("# AST (Parser Output)")
    output_sections.append("# " + "=" * 40)
    output_sections.append('"""')
    output_sections.extend(ast_to_lines(ast))
    output_sections.append('"""')
    output_sections.append("")

    # --- Generated Code ---
    output_sections.append("# " + "=" * 40)
    output_sections.append("# GENERATED CODE")
    output_sections.append("# " + "=" * 40)
    output_sections.append(output_code)

    output_file = "output.py"

    # ===== EXECUTION =====
    print("\n===== EXECUTION OUTPUT =====")

    execution_buffer = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = execution_buffer

    exec(compile(output_code, output_file, "exec"))

    sys.stdout = original_stdout
    execution_result = execution_buffer.getvalue()

    print(execution_result)

    # --- Execution Output ---
    output_sections.append("")
    output_sections.append("# " + "=" * 40)
    output_sections.append("# EXECUTION OUTPUT")
    output_sections.append("# " + "=" * 40)
    output_sections.append('"""')
    output_sections.append(execution_result.strip())
    output_sections.append('"""')

    # --- Write File ---
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output_sections))


except Exception as e:
    print("\n❌ Error:", e)