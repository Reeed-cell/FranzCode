"""
FranzCode AST Nodes — every language construct maps to one Node type.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Any


class Node:
    """Plain base class (NOT a dataclass, avoids field-ordering issues)."""
    line: int = 0

# ── Expressions ──────────────────────────────────────────────────────────────
@dataclass
class NumberNode(Node):
    value: float | int
    line: int = 0

@dataclass
class StringNode(Node):
    value: str
    line: int = 0

@dataclass
class IdentNode(Node):
    name: str
    line: int = 0

@dataclass
class BinOpNode(Node):
    left: Node
    op: str
    right: Node
    line: int = 0

@dataclass
class UnaryOpNode(Node):
    op: str
    operand: Node
    line: int = 0

@dataclass
class CompareNode(Node):
    left: Node
    op: str
    right: Node
    line: int = 0

@dataclass
class LogicNode(Node):
    left: Node
    op: str
    right: Node
    line: int = 0

# ── Statements ───────────────────────────────────────────────────────────────
@dataclass
class ProgramNode(Node):
    body: List[Node]
    line: int = 0

@dataclass
class SayNode(Node):
    expr: Node
    line: int = 0

@dataclass
class YellNode(Node):
    expr: Node
    line: int = 0

@dataclass
class WhisperNode(Node):
    expr: Node
    line: int = 0

@dataclass
class ConfuseNode(Node):
    expr: Node
    line: int = 0

@dataclass
class RepeatNode(Node):
    expr: Node
    count: Node
    line: int = 0

@dataclass
class YeetNode(Node):
    expr: Node
    line: int = 0

@dataclass
class SetNode(Node):
    name: str
    value: Node
    line: int = 0

@dataclass
class ModifyNode(Node):
    op: str
    name: str
    amount: Node
    line: int = 0

@dataclass
class IfNode(Node):
    condition: Node
    then_body: List[Node]
    else_body: List[Node]
    line: int = 0

@dataclass
class LoopNode(Node):
    count: Node
    body: List[Node]
    line: int = 0

@dataclass
class BreakoutNode(Node):
    line: int = 0

@dataclass
class WaitNode(Node):
    seconds: Node
    line: int = 0

@dataclass
class DumpNode(Node):
    line: int = 0

@dataclass
class StopNode(Node):
    line: int = 0

# ── Troll Nodes ───────────────────────────────────────────────────────────────
@dataclass
class RickrollNode(Node):
    line: int = 0

@dataclass
class MysteryNode(Node):
    line: int = 0

@dataclass
class OopsNode(Node):
    line: int = 0

@dataclass
class FlipNode(Node):
    line: int = 0

@dataclass
class DiceNode(Node):
    line: int = 0

@dataclass
class BruhNode(Node):
    line: int = 0

@dataclass
class PoggersNode(Node):
    line: int = 0
