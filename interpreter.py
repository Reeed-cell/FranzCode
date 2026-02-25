"""
╔══════════════════════════════════════════════╗
║   FranzCode Interpreter  —  Stage 3 of 3    ║
║   Tree-walking executor: visits every AST   ║
║   node and runs the corresponding action.   ║
╚══════════════════════════════════════════════╝

AST flow:  ProgramNode (AST)  ──►  [ Interpreter ]  ──►  Program Output
"""

from __future__ import annotations
import random
import re
import sys
import time
import webbrowser
from typing import Any, Dict, List, Optional

from ast_nodes import *


# ─────────────────────────────────────────────────────────────
#  Custom signals (used to implement BREAKOUT)
# ─────────────────────────────────────────────────────────────
class _BreakSignal(Exception):
    """Raised by BREAKOUT to exit the nearest LOOP."""
    pass

class RuntimeError_(Exception):
    """FranzCode runtime error (renamed to avoid shadowing Python's)."""
    pass


# ─────────────────────────────────────────────────────────────
#  Environment  —  variable scope
# ─────────────────────────────────────────────────────────────
class Environment:
    """
    Stores variables in a nested scope chain.
    Inner scopes shadow outer ones.
    """

    def __init__(self, parent: Optional[Environment] = None):
        self._vars:  Dict[str, Any] = {}
        self.parent: Optional[Environment] = parent

    def get(self, name: str, line: int = 0) -> Any:
        if name in self._vars:
            return self._vars[name]
        if self.parent:
            return self.parent.get(name, line)
        raise RuntimeError_(
            f"[Line {line}] Variable '{name}' is not defined. "
            f"Use SET {name} TO <value> first."
        )

    def set(self, name: str, value: Any):
        """Set in current scope."""
        self._vars[name] = value

    def set_existing(self, name: str, value: Any, line: int = 0):
        """Modify an already-existing variable (searches up the chain)."""
        if name in self._vars:
            self._vars[name] = value
            return
        if self.parent:
            self.parent.set_existing(name, value, line)
            return
        raise RuntimeError_(
            f"[Line {line}] Variable '{name}' is not defined. "
            f"Cannot modify it before setting it."
        )

    def all_vars(self) -> Dict[str, Any]:
        """Flatten the full scope chain for DUMP."""
        merged = {}
        if self.parent:
            merged.update(self.parent.all_vars())
        merged.update(self._vars)
        return merged


# ─────────────────────────────────────────────────────────────
#  Interpreter
# ─────────────────────────────────────────────────────────────
class Interpreter:
    """
    Walks the AST produced by the Parser and executes each node.

    Usage:
        interp = Interpreter()
        interp.run(program_node)
    """

    # Troll pools
    _MYSTERY_POOL = [
        "🎉 A wild treasure appeared!",
        "🐸 Ribbit. Just... ribbit.",
        "Nothing happened. Or did it? 🤔",
        "⚠️  WARNING: Your keyboard is haunted.",
        "🦆 Quack.",
        "The answer is 42.",
        "404: Mystery not found.",
        "Yes.",
        "No.",
        "Maybe.",
        "¯\\_(ツ)_/¯",
        "Potato.",
        "🌮 Taco appeared out of nowhere.",
        "ERROR: Too much fun detected.",
        "🕵️ Someone is watching. Probably not.",
    ]
    _POGGERS_POOL = [
        "🎊 POGGERS! LETS GOOO!",
        "W + ratio + you're built different!",
        "🔥 ABSOLUTELY FIRE 🔥",
        "NO CAP THAT WAS WILD 🐐",
        "SHEEEESH 😤",
        "This is the way. 💪",
        "GOATED WITH THE SAUCE 🐐",
    ]

    def __init__(self):
        self.global_env = Environment()
        # Seed some built-ins
        self.global_env.set("LOOPCOUNT", 0)
        self.global_env.set("TRUE",  True)
        self.global_env.set("FALSE", False)
        self.global_env.set("PI",    3.141592653589793)
        self.global_env.set("TAU",   6.283185307179586)

    # ── Public entry ──────────────────────────────────────────
    def run(self, node: ProgramNode):
        self._exec_block(node.body, self.global_env)

    # ── Block execution ───────────────────────────────────────
    def _exec_block(self, stmts: List[Node], env: Environment):
        for stmt in stmts:
            self._exec(stmt, env)

    # ── Node dispatcher ───────────────────────────────────────
    def _exec(self, node: Node, env: Environment):
        method_name = f"_exec_{type(node).__name__}"
        method      = getattr(self, method_name, None)
        if method is None:
            raise RuntimeError_(
                f"[Line {node.line}] Interpreter bug — "
                f"no handler for node type {type(node).__name__}"
            )
        return method(node, env)

    def _eval(self, node: Node, env: Environment) -> Any:
        method_name = f"_eval_{type(node).__name__}"
        method      = getattr(self, method_name, None)
        if method is None:
            raise RuntimeError_(
                f"[Line {node.line}] Interpreter bug — "
                f"no evaluator for node type {type(node).__name__}"
            )
        return method(node, env)

    # ─── Expression evaluators ────────────────────────────────

    def _eval_NumberNode(self, node: NumberNode, env) -> float | int:
        return node.value

    def _eval_StringNode(self, node: StringNode, env) -> str:
        """Evaluate a string, resolving {variable} interpolations."""
        def replacer(m):
            vname = m.group(1)
            try:
                val = env.get(vname)
                # Pretty-print floats that are whole numbers
                if isinstance(val, float) and val.is_integer():
                    return str(int(val))
                return str(val)
            except RuntimeError_:
                return f"{{{vname}}}"
        return re.sub(r"\{(\w+)\}", replacer, node.value)

    def _eval_IdentNode(self, node: IdentNode, env) -> Any:
        return env.get(node.name, node.line)

    def _eval_BinOpNode(self, node: BinOpNode, env) -> Any:
        left  = self._eval(node.left,  env)
        right = self._eval(node.right, env)
        try:
            if node.op == "+":  return left + right
            if node.op == "-":  return left - right
            if node.op == "*":  return left * right
            if node.op == "/":
                if right == 0:
                    raise RuntimeError_(
                        f"[Line {node.line}] Division by zero! Franz says no."
                    )
                return left / right
            if node.op == "%":  return left % right
            if node.op == "**": return left ** right
        except TypeError as e:
            raise RuntimeError_(
                f"[Line {node.line}] Type error in '{node.op}' operation: {e}"
            )

    def _eval_UnaryOpNode(self, node: UnaryOpNode, env) -> Any:
        val = self._eval(node.operand, env)
        if node.op == "-":   return -val
        if node.op == "not": return not val

    def _eval_CompareNode(self, node: CompareNode, env) -> bool:
        left  = self._eval(node.left,  env)
        right = self._eval(node.right, env)
        if node.op == "==": return left == right
        if node.op == "!=": return left != right
        if node.op == ">":  return left >  right
        if node.op == "<":  return left <  right
        if node.op == ">=": return left >= right
        if node.op == "<=": return left <= right

    def _eval_LogicNode(self, node: LogicNode, env) -> bool:
        left = self._eval(node.left, env)
        # Short-circuit evaluation
        if node.op == "and": return bool(left) and bool(self._eval(node.right, env))
        if node.op == "or":  return bool(left) or  bool(self._eval(node.right, env))

    # ─── Statement executors ──────────────────────────────────

    def _fmt(self, val: Any) -> str:
        """Pretty-format a value for printing."""
        if isinstance(val, float) and val.is_integer():
            return str(int(val))
        if isinstance(val, bool):
            return "TRUE" if val else "FALSE"
        return str(val)

    # ── Output ────────────────────────────────────────────────
    def _exec_SayNode(self, node: SayNode, env):
        print(self._fmt(self._eval(node.expr, env)))

    def _exec_YellNode(self, node: YellNode, env):
        print(self._fmt(self._eval(node.expr, env)).upper() + "!!!")

    def _exec_WhisperNode(self, node: WhisperNode, env):
        print(self._fmt(self._eval(node.expr, env)).lower() + "...")

    def _exec_ConfuseNode(self, node: ConfuseNode, env):
        val   = list(self._fmt(self._eval(node.expr, env)))
        random.shuffle(val)
        print("".join(val))

    def _exec_RepeatNode(self, node: RepeatNode, env):
        val   = self._fmt(self._eval(node.expr,  env))
        count = int(self._eval(node.count, env))
        print((val + " ") * count)

    def _exec_YeetNode(self, node: YeetNode, env):
        val = self._fmt(self._eval(node.expr, env))
        print(f"YEET ➜ {val} 🚀")

    # ── Variables ─────────────────────────────────────────────
    def _exec_SetNode(self, node: SetNode, env):
        env.set(node.name, self._eval(node.value, env))

    def _exec_ModifyNode(self, node: ModifyNode, env):
        current = env.get(node.name, node.line)
        amount  = self._eval(node.amount, env)
        if   node.op == "ADD": result = current + amount
        elif node.op == "SUB": result = current - amount
        elif node.op == "MUL": result = current * amount
        elif node.op == "DIV":
            if amount == 0:
                raise RuntimeError_(f"[Line {node.line}] Division by zero in DIV.")
            result = current / amount
        env.set_existing(node.name, result, node.line)

    # ── Logic ─────────────────────────────────────────────────
    def _exec_IfNode(self, node: IfNode, env):
        cond = self._eval(node.condition, env)
        # Child scope so IF variables don't leak out
        child = Environment(parent=env)
        if cond:
            self._exec_block(node.then_body, child)
        else:
            self._exec_block(node.else_body, child)

    # ── Loops ─────────────────────────────────────────────────
    def _exec_LoopNode(self, node: LoopNode, env):
        count = int(self._eval(node.count, env))
        try:
            for i in range(count):
                child = Environment(parent=env)
                child.set("LOOPCOUNT", i + 1)
                self._exec_block(node.body, child)
        except _BreakSignal:
            pass   # BREAKOUT exits the loop cleanly

    def _exec_BreakoutNode(self, node: BreakoutNode, env):
        raise _BreakSignal()

    # ── Utility ───────────────────────────────────────────────
    def _exec_WaitNode(self, node: WaitNode, env):
        secs = float(self._eval(node.seconds, env))
        time.sleep(secs)

    def _exec_DumpNode(self, node: DumpNode, env):
        all_vars = env.all_vars()
        # Filter out builtins the user didn't set
        user_vars = {k: v for k, v in all_vars.items()
                     if k not in ("TRUE", "FALSE")}
        print("┌─────── FRANZCODE VARIABLE DUMP ───────┐")
        if user_vars:
            for k, v in user_vars.items():
                print(f"│  {k:<20} = {v!r}")
        else:
            print("│  (no variables set yet)")
        print("└────────────────────────────────────────┘")

    def _exec_StopNode(self, node: StopNode, env):
        print("[FranzCode] Stopped by STOP.")
        sys.exit(0)

    # ── Troll 😈 ──────────────────────────────────────────────
    def _exec_RickrollNode(self, node: RickrollNode, env):
        print("♪ Never gonna give you up... ♪")
        webbrowser.open("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def _exec_MysteryNode(self, node: MysteryNode, env):
        print(random.choice(self._MYSTERY_POOL))

    def _exec_OopsNode(self, node: OopsNode, env):
        print("\n💥 CRITICAL FRANZCODE FAILURE")
        print("   Segmentation Fault (core dumped)")
        print("   Just kidding. You've been OOPS'd. 😈\n")

    def _exec_FlipNode(self, node: FlipNode, env):
        result = random.choice(["HEADS 🪙", "TAILS 🪙"])
        print(f"Coin flip: {result}")

    def _exec_DiceNode(self, node: DiceNode, env):
        val = random.randint(1, 6)
        print(f"🎲 You rolled a {val}!")

    def _exec_BruhNode(self, node: BruhNode, env):
        print("bruh.")
        time.sleep(1)

    def _exec_PoggersNode(self, node: PoggersNode, env):
        print(random.choice(self._POGGERS_POOL))

    # ─── Top-level ProgramNode ────────────────────────────────
    def _exec_ProgramNode(self, node: ProgramNode, env):
        self._exec_block(node.body, env)
