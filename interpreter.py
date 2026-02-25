#!/usr/bin/env python3
"""
FranzCode Interpreter
Supports: print, variables, arithmetic (+, -, *, /, %), if/elif/else, while loops, input(), comments.
"""

import sys
import re
import operator
from enum import Enum

# ---------- Tokenization ----------
class TokenType(Enum):
    KEYWORD = 'KEYWORD'
    IDENTIFIER = 'IDENTIFIER'
    NUMBER = 'NUMBER'
    STRING = 'STRING'
    OPERATOR = 'OPERATOR'
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    LBRACE = 'LBRACE'
    RBRACE = 'RBRACE'
    ASSIGN = 'ASSIGN'
    SEMICOLON = 'SEMICOLON'
    NEWLINE = 'NEWLINE'
    COMMENT = 'COMMENT'
    EOF = 'EOF'

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"

class Lexer:
    keywords = {'if', 'elif', 'else', 'while', 'print', 'input'}

    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []

    def tokenize(self):
        while self.pos < len(self.source):
            ch = self.source[self.pos]

            # Skip whitespace (but not newlines)
            if ch in ' \t':
                self._advance()
                continue

            # Newlines
            if ch == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.col))
                self._advance()
                self.line += 1
                self.col = 1
                continue

            # Comments
            if ch == '#':
                start_col = self.col
                comment = ''
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    comment += self.source[self.pos]
                    self._advance()
                self.tokens.append(Token(TokenType.COMMENT, comment, self.line, start_col))
                # Do not add NEWLINE here; it will be handled on next iteration
                continue

            # Strings (double or single quotes)
            if ch in ('"', "'"):
                quote = ch
                start_col = self.col
                self._advance()  # skip opening quote
                string_val = ''
                while self.pos < len(self.source) and self.source[self.pos] != quote:
                    if self.source[self.pos] == '\\':
                        self._advance()
                        if self.pos < len(self.source):
                            escape = self.source[self.pos]
                            if escape == 'n':
                                string_val += '\n'
                            elif escape == 't':
                                string_val += '\t'
                            elif escape == '\\':
                                string_val += '\\'
                            elif escape == '"':
                                string_val += '"'
                            elif escape == "'":
                                string_val += "'"
                            else:
                                string_val += escape
                            self._advance()
                    else:
                        string_val += self.source[self.pos]
                        self._advance()
                if self.pos < len(self.source) and self.source[self.pos] == quote:
                    self._advance()  # skip closing quote
                else:
                    raise SyntaxError(f"Unterminated string at line {self.line}, column {start_col}")
                self.tokens.append(Token(TokenType.STRING, string_val, self.line, start_col))
                continue

            # Numbers
            if ch.isdigit() or (ch == '.' and self.pos+1 < len(self.source) and self.source[self.pos+1].isdigit()):
                start_col = self.col
                num_str = ''
                dot_count = 0
                while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
                    if self.source[self.pos] == '.':
                        dot_count += 1
                        if dot_count > 1:
                            raise SyntaxError(f"Invalid number at line {self.line}, column {start_col}")
                    num_str += self.source[self.pos]
                    self._advance()
                if dot_count == 0:
                    value = int(num_str)
                else:
                    value = float(num_str)
                self.tokens.append(Token(TokenType.NUMBER, value, self.line, start_col))
                continue

            # Identifiers and keywords
            if ch.isalpha() or ch == '_':
                start_col = self.col
                ident = ''
                while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
                    ident += self.source[self.pos]
                    self._advance()
                if ident in self.keywords:
                    self.tokens.append(Token(TokenType.KEYWORD, ident, self.line, start_col))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, ident, self.line, start_col))
                continue

            # Operators and punctuation
            if ch == '=':
                self.tokens.append(Token(TokenType.ASSIGN, '=', self.line, self.col))
                self._advance()
                continue
            if ch == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', self.line, self.col))
                self._advance()
                continue
            if ch == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', self.line, self.col))
                self._advance()
                continue
            if ch == '{':
                self.tokens.append(Token(TokenType.LBRACE, '{', self.line, self.col))
                self._advance()
                continue
            if ch == '}':
                self.tokens.append(Token(TokenType.RBRACE, '}', self.line, self.col))
                self._advance()
                continue
            if ch == ';':
                self.tokens.append(Token(TokenType.SEMICOLON, ';', self.line, self.col))
                self._advance()
                continue
            # Multi-character operators: ==, !=, <=, >=, etc.
            if ch == '=' and self.pos+1 < len(self.source) and self.source[self.pos+1] == '=':
                self.tokens.append(Token(TokenType.OPERATOR, '==', self.line, self.col))
                self._advance()
                self._advance()
                continue
            if ch == '!' and self.pos+1 < len(self.source) and self.source[self.pos+1] == '=':
                self.tokens.append(Token(TokenType.OPERATOR, '!=', self.line, self.col))
                self._advance()
                self._advance()
                continue
            if ch == '<' and self.pos+1 < len(self.source) and self.source[self.pos+1] == '=':
                self.tokens.append(Token(TokenType.OPERATOR, '<=', self.line, self.col))
                self._advance()
                self._advance()
                continue
            if ch == '>' and self.pos+1 < len(self.source) and self.source[self.pos+1] == '=':
                self.tokens.append(Token(TokenType.OPERATOR, '>=', self.line, self.col))
                self._advance()
                self._advance()
                continue
            # Single-character operators
            if ch in '+-*/%<>!':
                self.tokens.append(Token(TokenType.OPERATOR, ch, self.line, self.col))
                self._advance()
                continue

            raise SyntaxError(f"Unexpected character '{ch}' at line {self.line}, column {self.col}")

        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens

    def _advance(self):
        self.pos += 1
        self.col += 1

# ---------- AST Nodes ----------
class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class Block(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class PrintStatement(ASTNode):
    def __init__(self, expr):
        self.expr = expr

class IfStatement(ASTNode):
    def __init__(self, condition, then_block, elif_blocks=None, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.elif_blocks = elif_blocks if elif_blocks else []  # list of (condition, block)
        self.else_block = else_block

class WhileStatement(ASTNode):
    def __init__(self, condition, block):
        self.condition = condition
        self.block = block

class Assignment(ASTNode):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

class BinaryOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class UnaryOp(ASTNode):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

class Number(ASTNode):
    def __init__(self, value):
        self.value = value

class String(ASTNode):
    def __init__(self, value):
        self.value = value

class Variable(ASTNode):
    def __init__(self, name):
        self.name = name

class Input(ASTNode):
    pass  # input() call

# ---------- Parser ----------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0] if tokens else None

    def parse(self):
        statements = []
        while self.current_token.type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
            # Skip NEWLINEs and comments between statements
            self.skip_ignorable()
        return Program(statements)

    def skip_ignorable(self):
        while self.current_token.type in (TokenType.NEWLINE, TokenType.COMMENT):
            self.advance()

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = Token(TokenType.EOF, '', self.tokens[-1].line, self.tokens[-1].column)

    def peek(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None

    def match(self, *types):
        if self.current_token.type in types:
            tok = self.current_token
            self.advance()
            return tok
        return None

    def expect(self, *types, error_msg=None):
        tok = self.current_token
        if tok.type in types:
            self.advance()
            return tok
        if error_msg is None:
            error_msg = f"Expected {types}, got {tok.type} at line {tok.line}, column {tok.column}"
        raise SyntaxError(error_msg)

    def parse_statement(self):
        # Skip leading newlines/comments
        self.skip_ignorable()

        if self.current_token.type == TokenType.EOF:
            return None

        # Print statement: print ( expression )
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'print':
            return self.parse_print()

        # If statement
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'if':
            return self.parse_if()

        # While loop
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'while':
            return self.parse_while()

        # Assignment: identifier = expression
        if self.current_token.type == TokenType.IDENTIFIER and self.peek() and self.peek().type == TokenType.ASSIGN:
            return self.parse_assignment()

        # Expression statement (could be just a number or string, but usually not standalone; maybe input call)
        # Actually, input() can be standalone? It would read and discard. We'll allow expression statements.
        expr = self.parse_expression()
        if expr:
            # Optionally expect semicolon? FranzCode may not require semicolons. We'll ignore them.
            self.match(TokenType.SEMICOLON)
            return expr
        else:
            # If we can't parse an expression, maybe it's just a newline/comment
            self.advance()  # skip whatever
            return None

    def parse_print(self):
        self.advance()  # consume 'print'
        # Expect '('
        self.expect(TokenType.LPAREN, error_msg="Expected '(' after 'print'")
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN, error_msg="Expected ')' after print expression")
        # Optionally semicolon
        self.match(TokenType.SEMICOLON)
        return PrintStatement(expr)

    def parse_if(self):
        self.advance()  # consume 'if'
        # Condition in parentheses
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        # Then block
        then_block = self.parse_block()
        # Elif blocks
        elif_blocks = []
        while self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'elif':
            self.advance()
            self.expect(TokenType.LPAREN)
            elif_cond = self.parse_expression()
            self.expect(TokenType.RPAREN)
            elif_block = self.parse_block()
            elif_blocks.append((elif_cond, elif_block))
        # Else block
        else_block = None
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'else':
            self.advance()
            else_block = self.parse_block()
        return IfStatement(condition, then_block, elif_blocks, else_block)

    def parse_while(self):
        self.advance()  # consume 'while'
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        block = self.parse_block()
        return WhileStatement(condition, block)

    def parse_block(self):
        # A block can be a single statement without braces, or multiple statements in braces.
        if self.current_token.type == TokenType.LBRACE:
            self.advance()
            statements = []
            while self.current_token.type != TokenType.RBRACE and self.current_token.type != TokenType.EOF:
                self.skip_ignorable()
                stmt = self.parse_statement()
                if stmt is not None:
                    statements.append(stmt)
                self.skip_ignorable()
            self.expect(TokenType.RBRACE, error_msg="Expected '}' to close block")
            return Block(statements)
        else:
            # Single statement (not a block)
            stmt = self.parse_statement()
            if stmt is None:
                raise SyntaxError("Expected a statement inside block")
            return Block([stmt])

    def parse_assignment(self):
        var_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.ASSIGN)
        expr = self.parse_expression()
        self.match(TokenType.SEMICOLON)
        return Assignment(var_token.value, expr)

    def parse_expression(self):
        return self.parse_logical_or()

    def parse_logical_or(self):
        expr = self.parse_logical_and()
        while self.current_token.type == TokenType.OPERATOR and self.current_token.value == 'or':
            op = self.current_token.value
            self.advance()
            right = self.parse_logical_and()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_logical_and(self):
        expr = self.parse_equality()
        while self.current_token.type == TokenType.OPERATOR and self.current_token.value == 'and':
            op = self.current_token.value
            self.advance()
            right = self.parse_equality()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_equality(self):
        expr = self.parse_comparison()
        while self.current_token.type == TokenType.OPERATOR and self.current_token.value in ('==', '!='):
            op = self.current_token.value
            self.advance()
            right = self.parse_comparison()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_comparison(self):
        expr = self.parse_addition()
        while self.current_token.type == TokenType.OPERATOR and self.current_token.value in ('<', '>', '<=', '>='):
            op = self.current_token.value
            self.advance()
            right = self.parse_addition()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_addition(self):
        expr = self.parse_multiplication()
        while self.current_token.type == TokenType.OPERATOR and self.current_token.value in ('+', '-'):
            op = self.current_token.value
            self.advance()
            right = self.parse_multiplication()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_multiplication(self):
        expr = self.parse_unary()
        while self.current_token.type == TokenType.OPERATOR and self.current_token.value in ('*', '/', '%'):
            op = self.current_token.value
            self.advance()
            right = self.parse_unary()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_unary(self):
        if self.current_token.type == TokenType.OPERATOR and self.current_token.value in ('+', '-', '!'):
            op = self.current_token.value
            self.advance()
            expr = self.parse_unary()
            return UnaryOp(op, expr)
        return self.parse_primary()

    def parse_primary(self):
        tok = self.current_token
        if tok.type == TokenType.NUMBER:
            self.advance()
            return Number(tok.value)
        if tok.type == TokenType.STRING:
            self.advance()
            return String(tok.value)
        if tok.type == TokenType.IDENTIFIER:
            self.advance()
            return Variable(tok.value)
        if tok.type == TokenType.KEYWORD and tok.value == 'input':
            self.advance()
            self.expect(TokenType.LPAREN)
            self.expect(TokenType.RPAREN)
            return Input()
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        raise SyntaxError(f"Unexpected token {tok.type} at line {tok.line}, column {tok.column}")

# ---------- Evaluator ----------
class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"Variable '{name}' is not defined")

    def set(self, name, value):
        self.vars[name] = value

    def set_global(self, name, value):
        # For assignments that should go to global scope (like in blocks)
        if self.parent is None:
            self.vars[name] = value
        else:
            self.parent.set_global(name, value)

class Interpreter:
    def __init__(self):
        self.global_env = Environment()

    def eval(self, node, env=None):
        if env is None:
            env = self.global_env
        if isinstance(node, Program):
            result = None
            for stmt in node.statements:
                result = self.eval(stmt, env)
            return result
        elif isinstance(node, Block):
            # Blocks create a new local environment (nested scope)
            new_env = Environment(env)
            result = None
            for stmt in node.statements:
                result = self.eval(stmt, new_env)
            return result
        elif isinstance(node, PrintStatement):
            value = self.eval(node.expr, env)
            print(value)
            return None
        elif isinstance(node, IfStatement):
            cond_val = self.eval(node.condition, env)
            if self.is_truthy(cond_val):
                return self.eval(node.then_block, env)
            for elif_cond, elif_block in node.elif_blocks:
                if self.is_truthy(self.eval(elif_cond, env)):
                    return self.eval(elif_block, env)
            if node.else_block:
                return self.eval(node.else_block, env)
            return None
        elif isinstance(node, WhileStatement):
            while self.is_truthy(self.eval(node.condition, env)):
                self.eval(node.block, env)
            return None
        elif isinstance(node, Assignment):
            value = self.eval(node.expr, env)
            # Assignment always goes to current scope (or global if not exists?) In FranzCode, assignment creates or updates in current scope.
            env.set(node.name, value)
            return None
        elif isinstance(node, BinaryOp):
            left = self.eval(node.left, env)
            right = self.eval(node.right, env)
            if node.op == '+':
                # Handle string concatenation
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)
                return left + right
            elif node.op == '-':
                return left - right
            elif node.op == '*':
                return left * right
            elif node.op == '/':
                # Division returns float
                return left / right
            elif node.op == '%':
                return left % right
            elif node.op == '==':
                return left == right
            elif node.op == '!=':
                return left != right
            elif node.op == '<':
                return left < right
            elif node.op == '>':
                return left > right
            elif node.op == '<=':
                return left <= right
            elif node.op == '>=':
                return left >= right
            elif node.op == 'and':
                return self.is_truthy(left) and self.is_truthy(right)
            elif node.op == 'or':
                return self.is_truthy(left) or self.is_truthy(right)
            else:
                raise RuntimeError(f"Unknown operator {node.op}")
        elif isinstance(node, UnaryOp):
            expr = self.eval(node.expr, env)
            if node.op == '+':
                return +expr
            elif node.op == '-':
                return -expr
            elif node.op == '!':
                return not self.is_truthy(expr)
            else:
                raise RuntimeError(f"Unknown unary operator {node.op}")
        elif isinstance(node, Number):
            return node.value
        elif isinstance(node, String):
            return node.value
        elif isinstance(node, Variable):
            return env.get(node.name)
        elif isinstance(node, Input):
            return input()
        else:
            raise RuntimeError(f"Unknown node type {type(node)}")

    def is_truthy(self, value):
        # False, None, 0, empty string are false; everything else true
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value != ""
        return True

# ---------- Main ----------
def run_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()
    run_source(source)

def run_source(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    interpreter = Interpreter()
    interpreter.eval(ast)

def repl():
    print("FranzCode REPL (type 'exit()' to quit)")
    interpreter = Interpreter()
    while True:
        try:
            line = input('>>> ')
            if line.strip() == 'exit()':
                break
            # For simplicity, treat each line as a full program (or statement)
            run_source(line)
        except (SyntaxError, NameError, RuntimeError) as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        repl()