"""
╔══════════════════════════════════════════════╗
║   FranzCode Parser  —  Stage 2 of 3         ║
║   Consumes Tokens and builds an AST.         ║
╚══════════════════════════════════════════════╝

Token flow:  [Token, Token, ...]  ──►  [ Parser ]  ──►  ProgramNode (AST)

Grammar (simplified):
  program     → statement* EOF
  statement   → say | yell | whisper | confuse | repeat
              | set | modify | if | loop | breakout
              | wait | dump | stop | troll_cmd
  expr        → logic
  logic       → compare (('AND'|'OR') compare)*
  compare     → addition (('=='|'!='|'>'|'<'|'>='|'<=') addition)*
  addition    → multiply (('+' | '-') multiply)*
  multiply    → unary (('*' | '/' | '%' | '**') unary)*
  unary       → NOT unary | '-' unary | primary
  primary     → NUMBER | STRING | IDENTIFIER | '(' expr ')'
"""

from __future__ import annotations
from typing import List, Optional

from lexer import Token, TT
from ast_nodes import *


# ─────────────────────────────────────────────────────────────
#  ParseError
# ─────────────────────────────────────────────────────────────
class ParseError(Exception):
    pass


# ─────────────────────────────────────────────────────────────
#  Parser
# ─────────────────────────────────────────────────────────────
class Parser:
    """
    Recursive-descent parser.

    Usage:
        parser = Parser(tokens)
        ast    = parser.parse()  # returns ProgramNode
    """

    def __init__(self, tokens: List[Token]):
        # Strip out NEWLINE tokens — we don't need them structurally,
        # statement parsing handles everything by position.
        self.tokens  = [t for t in tokens if t.type != TT.NEWLINE]
        self.pos     = 0

    # ── Token navigation ──────────────────────────────────────
    @property
    def _current(self) -> Token:
        return self.tokens[self.pos]

    @property
    def _line(self) -> int:
        return self._current.line

    def _peek(self, offset: int = 1) -> Optional[Token]:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def _check(self, *types: TT) -> bool:
        return self._current.type in types

    def _match(self, *types: TT) -> Optional[Token]:
        if self._check(*types):
            tok = self._current
            self.pos += 1
            return tok
        return None

    def _expect(self, tt: TT, msg: str = "") -> Token:
        tok = self._match(tt)
        if tok is None:
            got = self._current
            hint = msg or f"expected {tt.name}"
            raise ParseError(
                f"[Line {got.line}] {hint} — "
                f"got '{got.value}' ({got.type.name}) instead."
            )
        return tok

    def _at_end(self) -> bool:
        return self._current.type == TT.EOF

    # ── Public entry ──────────────────────────────────────────
    def parse(self) -> ProgramNode:
        body = []
        while not self._at_end():
            stmt = self._statement()
            if stmt is not None:
                body.append(stmt)
        return ProgramNode(body=body, line=0)

    # ── Statement dispatcher ──────────────────────────────────
    def _statement(self) -> Optional[Node]:
        line = self._line
        tt   = self._current.type

        # ── Output ─────────────────────────────────────────
        if tt == TT.SAY:
            return self._say(line)
        if tt == TT.YELL:
            return self._yell(line)
        if tt == TT.WHISPER:
            return self._whisper(line)
        if tt == TT.CONFUSE:
            return self._confuse(line)
        if tt == TT.REPEAT:
            return self._repeat(line)
        if tt == TT.YEET:
            return self._yeet(line)

        # ── Variables ──────────────────────────────────────
        if tt == TT.SET:
            return self._set(line)
        if tt in (TT.ADD, TT.SUB, TT.MUL, TT.DIV):
            return self._modify(line)

        # ── Logic ──────────────────────────────────────────
        if tt == TT.IF:
            return self._if(line)

        # ── Loops ──────────────────────────────────────────
        if tt == TT.LOOP:
            return self._loop(line)
        if tt == TT.BREAKOUT:
            self.pos += 1
            return BreakoutNode(line=line)

        # ── Utility ────────────────────────────────────────
        if tt == TT.WAIT:
            return self._wait(line)
        if tt == TT.DUMP:
            self.pos += 1
            return DumpNode(line=line)
        if tt == TT.STOP:
            self.pos += 1
            return StopNode(line=line)

        # ── Troll ──────────────────────────────────────────
        if tt == TT.RICKROLL:
            self.pos += 1; return RickrollNode(line=line)
        if tt == TT.MYSTERY:
            self.pos += 1; return MysteryNode(line=line)
        if tt == TT.OOPS:
            self.pos += 1; return OopsNode(line=line)
        if tt == TT.FLIP:
            self.pos += 1; return FlipNode(line=line)
        if tt == TT.DICE:
            self.pos += 1; return DiceNode(line=line)
        if tt == TT.BRUH:
            self.pos += 1; return BruhNode(line=line)
        if tt == TT.POGGERS:
            self.pos += 1; return PoggersNode(line=line)

        raise ParseError(
            f"[Line {self._line}] Unexpected token '{self._current.value}' "
            f"({self._current.type.name}). Franz doesn't know what to do with that."
        )

    # ─── Statement parsers ────────────────────────────────────

    def _say(self, line) -> SayNode:
        self.pos += 1
        return SayNode(expr=self._expr(), line=line)

    def _yell(self, line) -> YellNode:
        self.pos += 1
        return YellNode(expr=self._expr(), line=line)

    def _whisper(self, line) -> WhisperNode:
        self.pos += 1
        return WhisperNode(expr=self._expr(), line=line)

    def _confuse(self, line) -> ConfuseNode:
        self.pos += 1
        return ConfuseNode(expr=self._expr(), line=line)

    def _yeet(self, line) -> YeetNode:
        self.pos += 1
        return YeetNode(expr=self._expr(), line=line)

    def _repeat(self, line) -> RepeatNode:
        # REPEAT expr n TIMES
        self.pos += 1
        expr  = self._expr()
        count = self._expr()
        self._expect(TT.TIMES, "expected TIMES after count in REPEAT")
        return RepeatNode(expr=expr, count=count, line=line)

    def _set(self, line) -> SetNode:
        # SET name TO expr
        self.pos += 1
        name_tok = self._expect(TT.IDENTIFIER, "expected variable name after SET")
        self._expect(TT.TO, "expected TO after variable name in SET")
        value    = self._expr()
        return SetNode(name=name_tok.value, value=value, line=line)

    def _modify(self, line) -> ModifyNode:
        # ADD/SUB/MUL/DIV name BY expr
        op_tok = self._current; self.pos += 1
        name   = self._expect(TT.IDENTIFIER, f"expected variable name after {op_tok.value}")
        self._expect(TT.BY, f"expected BY after variable name in {op_tok.value}")
        amount = self._expr()
        return ModifyNode(op=op_tok.value, name=name.value, amount=amount, line=line)

    def _if(self, line) -> IfNode:
        # IF expr THEN ... [ELSE ...] ENDIF
        self.pos += 1
        condition = self._expr()
        self._expect(TT.THEN, "expected THEN after condition in IF")

        then_body: List[Node] = []
        else_body: List[Node] = []

        # Collect THEN body until ELSE or ENDIF
        while not self._at_end() and not self._check(TT.ELSE, TT.ENDIF):
            then_body.append(self._statement())

        if self._match(TT.ELSE):
            while not self._at_end() and not self._check(TT.ENDIF):
                else_body.append(self._statement())

        self._expect(TT.ENDIF, "expected ENDIF to close IF block")
        return IfNode(condition=condition, then_body=then_body, else_body=else_body, line=line)

    def _loop(self, line) -> LoopNode:
        # LOOP expr TIMES ... ENDLOOP
        self.pos += 1
        count = self._expr()
        self._expect(TT.TIMES, "expected TIMES after count in LOOP")

        body: List[Node] = []
        while not self._at_end() and not self._check(TT.ENDLOOP):
            body.append(self._statement())

        self._expect(TT.ENDLOOP, "expected ENDLOOP to close LOOP block")
        return LoopNode(count=count, body=body, line=line)

    def _wait(self, line) -> WaitNode:
        # WAIT expr SECONDS
        self.pos += 1
        seconds = self._expr()
        self._expect(TT.SECONDS, "expected SECONDS after duration in WAIT")
        return WaitNode(seconds=seconds, line=line)

    # ─── Expression parsers (recursive descent) ───────────────

    def _expr(self) -> Node:
        return self._logic()

    def _logic(self) -> Node:
        """Handles: AND / OR"""
        left = self._compare()
        while self._check(TT.AND, TT.OR):
            op  = self._current.value.lower()
            self.pos += 1
            right = self._compare()
            left  = LogicNode(left=left, op=op, right=right, line=left.line)
        return left

    def _compare(self) -> Node:
        """Handles: == != > < >= <="""
        left = self._addition()
        while self._check(TT.EQ, TT.NEQ, TT.GT, TT.LT, TT.GTE, TT.LTE):
            op  = self._current.value
            self.pos += 1
            right = self._addition()
            left  = CompareNode(left=left, op=op, right=right, line=left.line)
        return left

    def _addition(self) -> Node:
        """Handles: + -"""
        left = self._multiply()
        while self._check(TT.PLUS, TT.MINUS):
            op  = self._current.value
            self.pos += 1
            right = self._multiply()
            left  = BinOpNode(left=left, op=op, right=right, line=left.line)
        return left

    def _multiply(self) -> Node:
        """Handles: * / % **"""
        left = self._unary()
        while self._check(TT.STAR, TT.SLASH, TT.PERCENT, TT.POWER):
            op  = self._current.value
            self.pos += 1
            right = self._unary()
            left  = BinOpNode(left=left, op=op, right=right, line=left.line)
        return left

    def _unary(self) -> Node:
        """Handles: -x  or  NOT x"""
        if self._check(TT.MINUS):
            line = self._line; self.pos += 1
            return UnaryOpNode(op="-", operand=self._unary(), line=line)
        if self._check(TT.NOT):
            line = self._line; self.pos += 1
            return UnaryOpNode(op="not", operand=self._unary(), line=line)
        return self._primary()

    def _primary(self) -> Node:
        """Handles: literals, identifiers, grouped expressions"""
        tok  = self._current
        line = tok.line

        if tok.type == TT.NUMBER:
            self.pos += 1
            return NumberNode(value=tok.value, line=line)

        if tok.type == TT.STRING:
            self.pos += 1
            return StringNode(value=tok.value, line=line)

        if tok.type == TT.IDENTIFIER:
            self.pos += 1
            return IdentNode(name=tok.value, line=line)

        if tok.type == TT.LPAREN:
            self.pos += 1
            inner = self._expr()
            self._expect(TT.RPAREN, "expected ')' to close grouped expression")
            return inner

        raise ParseError(
            f"[Line {line}] Unexpected token '{tok.value}' ({tok.type.name}) "
            f"in expression — expected a number, string, or variable name."
        )
