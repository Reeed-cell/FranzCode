"""
╔══════════════════════════════════════════════╗
║   FranzCode Lexer  —  Stage 1 of 3          ║
║   Reads raw .franz source text and produces  ║
║   a flat list of typed Token objects.        ║
╚══════════════════════════════════════════════╝

Token flow:  Source Text  ──►  [ Lexer ]  ──►  [Token, Token, ...]
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional


# ─────────────────────────────────────────────────────────────
#  Token Types
# ─────────────────────────────────────────────────────────────
class TT(Enum):
    """All possible token types in FranzCode."""

    # ── Literals ──────────────────────────────────────────────
    NUMBER      = auto()   # 42 / 3.14
    STRING      = auto()   # "hello world"
    IDENTIFIER  = auto()   # variableName

    # ── Arithmetic operators ──────────────────────────────────
    PLUS        = auto()   # +
    MINUS       = auto()   # -
    STAR        = auto()   # *
    SLASH       = auto()   # /
    PERCENT     = auto()   # %
    POWER       = auto()   # **

    # ── Comparison operators ──────────────────────────────────
    EQ          = auto()   # ==
    NEQ         = auto()   # !=
    GT          = auto()   # >
    LT          = auto()   # <
    GTE         = auto()   # >=
    LTE         = auto()   # <=

    # ── Grouping ──────────────────────────────────────────────
    LPAREN      = auto()   # (
    RPAREN      = auto()   # )

    # ── Keywords — Output ─────────────────────────────────────
    SAY         = auto()
    YELL        = auto()
    WHISPER     = auto()
    CONFUSE     = auto()
    REPEAT      = auto()
    TIMES       = auto()

    # ── Keywords — Variables ──────────────────────────────────
    SET         = auto()
    TO          = auto()
    ADD         = auto()
    SUB         = auto()
    MUL         = auto()
    DIV         = auto()
    BY          = auto()

    # ── Keywords — Logic ──────────────────────────────────────
    IF          = auto()
    THEN        = auto()
    ELSE        = auto()
    ENDIF       = auto()
    AND         = auto()
    OR          = auto()
    NOT         = auto()

    # ── Keywords — Loops ──────────────────────────────────────
    LOOP        = auto()
    ENDLOOP     = auto()
    BREAKOUT    = auto()

    # ── Keywords — Utility ────────────────────────────────────
    WAIT        = auto()
    SECONDS     = auto()
    DUMP        = auto()
    STOP        = auto()

    # ── Keywords — Troll 😈 ───────────────────────────────────
    RICKROLL    = auto()
    MYSTERY     = auto()
    OOPS        = auto()
    FLIP        = auto()
    DICE        = auto()
    YEET        = auto()   # alias for SAY (with flair)
    BRUH        = auto()   # prints "bruh." and pauses
    POGGERS     = auto()   # celebratory random output

    # ── Structure ─────────────────────────────────────────────
    NEWLINE     = auto()
    EOF         = auto()


# Map of keyword strings (uppercase) → TT
KEYWORDS: dict[str, TT] = {
    "SAY":      TT.SAY,
    "YELL":     TT.YELL,
    "WHISPER":  TT.WHISPER,
    "CONFUSE":  TT.CONFUSE,
    "REPEAT":   TT.REPEAT,
    "TIMES":    TT.TIMES,
    "SET":      TT.SET,
    "TO":       TT.TO,
    "ADD":      TT.ADD,
    "SUB":      TT.SUB,
    "MUL":      TT.MUL,
    "DIV":      TT.DIV,
    "BY":       TT.BY,
    "IF":       TT.IF,
    "THEN":     TT.THEN,
    "ELSE":     TT.ELSE,
    "ENDIF":    TT.ENDIF,
    "AND":      TT.AND,
    "OR":       TT.OR,
    "NOT":      TT.NOT,
    "LOOP":     TT.LOOP,
    "ENDLOOP":  TT.ENDLOOP,
    "BREAKOUT": TT.BREAKOUT,
    "WAIT":     TT.WAIT,
    "SECONDS":  TT.SECONDS,
    "DUMP":     TT.DUMP,
    "STOP":     TT.STOP,
    "RICKROLL": TT.RICKROLL,
    "MYSTERY":  TT.MYSTERY,
    "OOPS":     TT.OOPS,
    "FLIP":     TT.FLIP,
    "DICE":     TT.DICE,
    "YEET":     TT.YEET,
    "BRUH":     TT.BRUH,
    "POGGERS":  TT.POGGERS,
}


# ─────────────────────────────────────────────────────────────
#  Token  —  a single unit from the source
# ─────────────────────────────────────────────────────────────
@dataclass
class Token:
    type:    TT
    value:   object         # raw Python value (str, float, None)
    line:    int = 0        # 1-based line number (for error messages)
    col:     int = 0        # 1-based column number

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.col})"


# ─────────────────────────────────────────────────────────────
#  LexError
# ─────────────────────────────────────────────────────────────
class LexError(Exception):
    pass


# ─────────────────────────────────────────────────────────────
#  Lexer
# ─────────────────────────────────────────────────────────────
class Lexer:
    """
    Converts a raw FranzCode source string into a list of Token objects.

    Usage:
        lexer  = Lexer(source_code)
        tokens = lexer.tokenize()
    """

    def __init__(self, source: str):
        self.source  = source
        self.pos     = 0       # current char index
        self.line    = 1
        self.col     = 1
        self.tokens: List[Token] = []

    # ── Helpers ───────────────────────────────────────────────
    @property
    def _current(self) -> Optional[str]:
        return self.source[self.pos] if self.pos < len(self.source) else None

    @property
    def _peek(self) -> Optional[str]:
        nxt = self.pos + 1
        return self.source[nxt] if nxt < len(self.source) else None

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col   = 1
        else:
            self.col  += 1
        return ch

    def _add(self, tt: TT, value: object = None):
        self.tokens.append(Token(tt, value, self.line, self.col))

    # ── Main tokenize loop ────────────────────────────────────
    def tokenize(self) -> List[Token]:
        while self._current is not None:
            ch = self._current

            # ── Whitespace (not newline) ───────────────────
            if ch in (" ", "\t", "\r"):
                self._advance()

            # ── Newline ────────────────────────────────────
            elif ch == "\n":
                self._add(TT.NEWLINE)
                self._advance()

            # ── Comments  (// or #) ───────────────────────
            elif ch == "/" and self._peek == "/":
                self._skip_line_comment()
            elif ch == "#":
                self._skip_line_comment()

            # ── String literal ─────────────────────────────
            elif ch in ('"', "'"):
                self._read_string(ch)

            # ── Number ────────────────────────────────────
            elif ch.isdigit() or (ch == "." and self._peek and self._peek.isdigit()):
                self._read_number()

            # ── Identifier / keyword ──────────────────────
            elif ch.isalpha() or ch == "_":
                self._read_word()

            # ── Two-char operators ─────────────────────────
            elif ch == "*" and self._peek == "*":
                self._advance(); self._advance()
                self._add(TT.POWER, "**")
            elif ch == "=" and self._peek == "=":
                self._advance(); self._advance()
                self._add(TT.EQ, "==")
            elif ch == "!" and self._peek == "=":
                self._advance(); self._advance()
                self._add(TT.NEQ, "!=")
            elif ch == ">" and self._peek == "=":
                self._advance(); self._advance()
                self._add(TT.GTE, ">=")
            elif ch == "<" and self._peek == "=":
                self._advance(); self._advance()
                self._add(TT.LTE, "<=")

            # ── Single-char operators ──────────────────────
            elif ch == "+": self._advance(); self._add(TT.PLUS,    "+")
            elif ch == "-": self._advance(); self._add(TT.MINUS,   "-")
            elif ch == "*": self._advance(); self._add(TT.STAR,    "*")
            elif ch == "/": self._advance(); self._add(TT.SLASH,   "/")
            elif ch == "%": self._advance(); self._add(TT.PERCENT, "%")
            elif ch == ">": self._advance(); self._add(TT.GT,      ">")
            elif ch == "<": self._advance(); self._add(TT.LT,      "<")
            elif ch == "(": self._advance(); self._add(TT.LPAREN,  "(")
            elif ch == ")": self._advance(); self._add(TT.RPAREN,  ")")

            else:
                raise LexError(
                    f"[Line {self.line}, Col {self.col}] "
                    f"Unexpected character: '{ch}'"
                )

        self._add(TT.EOF)
        return self.tokens

    # ── Sub-readers ───────────────────────────────────────────
    def _skip_line_comment(self):
        while self._current is not None and self._current != "\n":
            self._advance()

    def _read_string(self, quote: str):
        self._advance()   # consume opening quote
        buf = []
        while self._current is not None and self._current != quote:
            if self._current == "\n":
                raise LexError(
                    f"[Line {self.line}] Unterminated string — "
                    f"did you forget a closing {quote}?"
                )
            buf.append(self._advance())
        if self._current is None:
            raise LexError(f"[Line {self.line}] Unterminated string at end of file.")
        self._advance()   # consume closing quote
        self._add(TT.STRING, "".join(buf))

    def _read_number(self):
        buf  = []
        dots = 0
        while self._current is not None and (self._current.isdigit() or self._current == "."):
            if self._current == ".":
                dots += 1
                if dots > 1:
                    raise LexError(f"[Line {self.line}] Malformed number — too many dots.")
            buf.append(self._advance())
        raw = "".join(buf)
        self._add(TT.NUMBER, float(raw) if dots else int(raw))

    def _read_word(self):
        buf = []
        while self._current is not None and (self._current.isalnum() or self._current == "_"):
            buf.append(self._advance())
        word = "".join(buf)
        tt   = KEYWORDS.get(word.upper())
        if tt:
            self._add(tt, word.upper())
        else:
            self._add(TT.IDENTIFIER, word)
