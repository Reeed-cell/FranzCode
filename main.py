"""
╔══════════════════════════════════════════════════════════════╗
║   FranzCode  —  main.py                                      ║
║   The entry point. Handles the CLI and interactive REPL.     ║
║                                                              ║
║   Usage:                                                     ║
║     python main.py              → Launch interactive REPL    ║
║     python main.py file.franz   → Run a .franz file          ║
║     python main.py --ast f.franz → Print AST (debug mode)   ║
║     python main.py --tokens f.franz → Print tokens          ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys

from lexer       import Lexer,       LexError
from parser      import Parser,      ParseError
from interpreter import Interpreter, RuntimeError_
from ast_nodes   import ProgramNode


# ─────────────────────────────────────────────────────────────
#  Banner / Help
# ─────────────────────────────────────────────────────────────
BANNER = r"""
  ███████╗██████╗  █████╗ ███╗   ██╗███████╗
  ██╔════╝██╔══██╗██╔══██╗████╗  ██║╚══███╔╝
  █████╗  ██████╔╝███████║██╔██╗ ██║  ███╔╝
  ██╔══╝  ██╔══██╗██╔══██║██║╚██╗██║ ███╔╝
  ██║     ██║  ██║██║  ██║██║ ╚████║███████╗
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝
        C O D E   v1.0  |  Interactive REPL
"""

REPL_HELP = """
┌─────────────────────────────────────────────────────┐
│              FranzCode REPL Commands                │
├─────────────────────────────────────────────────────┤
│  Type any FranzCode statement and press Enter       │
│                                                     │
│  .help       Show this help message                 │
│  .run <file> Run a .franz file                      │
│  .ast <file> Show the AST of a .franz file          │
│  .tokens <f> Show the token list of a .franz file   │
│  .vars       Show all current variables             │
│  .clear      Clear all variables                    │
│  .examples   Show quick FranzCode examples          │
│  .exit       Exit the REPL                         │
└─────────────────────────────────────────────────────┘
"""

EXAMPLES = """
  SAY "Hello, World!"
  SET x TO 10
  ADD x BY 5
  SAY "x is {x}"
  IF x > 10 THEN
    YELL "big number"
  ENDIF
  LOOP 3 TIMES
    SAY "loop {LOOPCOUNT}"
  ENDLOOP
  FLIP
  DICE
  MYSTERY
  OOPS
"""


# ─────────────────────────────────────────────────────────────
#  Pipeline: source → tokens → AST → execution
# ─────────────────────────────────────────────────────────────
def compile_source(source: str) -> ProgramNode:
    """Run lexer + parser on source, return AST."""
    lexer  = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def run_source(source: str, interp: Interpreter):
    """Lex, parse, and execute a FranzCode source string."""
    ast = compile_source(source)
    interp.run(ast)


# ─────────────────────────────────────────────────────────────
#  Error formatting
# ─────────────────────────────────────────────────────────────
def _fmt_error(stage: str, err: Exception) -> str:
    lines = [
        f"\n  💥  FranzCode {stage} Error",
        f"  {'─' * 40}",
        f"  {err}",
    ]
    return "\n".join(lines) + "\n"


# ─────────────────────────────────────────────────────────────
#  REPL  —  Interactive Terminal
# ─────────────────────────────────────────────────────────────
class REPL:
    """
    Interactive Read-Eval-Print Loop.
    Supports multi-line blocks (IF/LOOP) — keeps reading
    until the block is closed before executing.
    """

    BLOCK_OPENERS  = {"IF", "LOOP"}
    BLOCK_CLOSERS  = {"ENDIF", "ENDLOOP"}
    BLOCK_MID      = {"ELSE"}

    def __init__(self):
        self.interp     = Interpreter()
        self.buffer:    list[str] = []
        self.depth:     int       = 0    # nesting depth for blocks
        self.running:   bool      = True

    def start(self):
        print(BANNER)
        print("  Type .help for commands, .exit to quit.\n")
        while self.running:
            try:
                prompt = "franz❯ " if self.depth == 0 else "  ...❯ "
                line   = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print("\n[FranzCode] Goodbye! 👋")
                break

            self._handle(line)

    def _handle(self, raw: str):
        stripped = raw.strip()

        # ── REPL meta-commands (.exit, .help, etc.) ──────────
        if stripped.startswith(".") and self.depth == 0:
            self._meta(stripped)
            return

        # ── Empty line in a block → add blank / skip ─────────
        if not stripped:
            if self.depth > 0:
                self.buffer.append(raw)
            return

        # ── Track block depth ─────────────────────────────────
        upper = stripped.split()[0].upper() if stripped.split() else ""
        if upper in self.BLOCK_OPENERS:
            self.depth += 1
        elif upper in self.BLOCK_CLOSERS:
            self.depth = max(0, self.depth - 1)

        self.buffer.append(raw)

        # ── Execute when the block is complete ────────────────
        if self.depth == 0:
            source = "\n".join(self.buffer)
            self.buffer.clear()
            try:
                run_source(source, self.interp)
            except LexError as e:
                print(_fmt_error("Lexer", e))
            except ParseError as e:
                print(_fmt_error("Parser", e))
            except RuntimeError_ as e:
                print(_fmt_error("Runtime", e))
            except SystemExit:
                self.running = False

    def _meta(self, cmd: str):
        parts = cmd.split()
        key   = parts[0]

        if key == ".exit":
            print("[FranzCode] Goodbye! 👋")
            self.running = False

        elif key == ".help":
            print(REPL_HELP)

        elif key == ".examples":
            print(EXAMPLES)

        elif key == ".vars":
            all_vars = self.interp.global_env.all_vars()
            user_vars = {k: v for k, v in all_vars.items() if k not in ("TRUE", "FALSE")}
            if user_vars:
                print("┌─── Variables ───────────────────┐")
                for k, v in user_vars.items():
                    print(f"│  {k:<18} = {v!r}")
                print("└─────────────────────────────────┘")
            else:
                print("  (no variables set)")

        elif key == ".clear":
            from interpreter import Environment
            self.interp.global_env = Environment()
            self.interp.global_env.set("LOOPCOUNT", 0)
            self.interp.global_env.set("TRUE",  True)
            self.interp.global_env.set("FALSE", False)
            self.interp.global_env.set("PI",    3.141592653589793)
            print("  Variables cleared.")

        elif key == ".run" and len(parts) > 1:
            _run_file(parts[1], self.interp)

        elif key == ".ast" and len(parts) > 1:
            _show_ast(parts[1])

        elif key == ".tokens" and len(parts) > 1:
            _show_tokens(parts[1])

        else:
            print(f"  Unknown command '{cmd}'. Type .help for options.")


# ─────────────────────────────────────────────────────────────
#  File runner
# ─────────────────────────────────────────────────────────────
def _run_file(path: str, interp: Interpreter = None):
    if not os.path.isfile(path):
        print(f"\n  💥 File not found: '{path}'\n")
        return

    if not path.endswith(".franz"):
        print(f"  ⚠️  Warning: '{path}' doesn't have a .franz extension.")

    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    if interp is None:
        interp = Interpreter()

    try:
        run_source(source, interp)
    except LexError as e:
        print(_fmt_error("Lexer",   e))
        sys.exit(1)
    except ParseError as e:
        print(_fmt_error("Parser",  e))
        sys.exit(1)
    except RuntimeError_ as e:
        print(_fmt_error("Runtime", e))
        sys.exit(1)


# ─────────────────────────────────────────────────────────────
#  Debug helpers
# ─────────────────────────────────────────────────────────────
def _show_tokens(path: str):
    if not os.path.isfile(path):
        print(f"  💥 File not found: '{path}'"); return
    with open(path) as f:
        source = f.read()
    try:
        tokens = Lexer(source).tokenize()
        print(f"\n  Tokens for '{path}':")
        for tok in tokens:
            print(f"    {tok}")
        print()
    except LexError as e:
        print(_fmt_error("Lexer", e))


def _show_ast(path: str):
    if not os.path.isfile(path):
        print(f"  💥 File not found: '{path}'"); return
    with open(path) as f:
        source = f.read()
    try:
        ast = compile_source(source)
        print(f"\n  AST for '{path}':")
        _print_ast(ast, indent=0)
        print()
    except (LexError, ParseError) as e:
        print(_fmt_error("Compile", e))


def _print_ast(node, indent: int):
    """Recursively pretty-print an AST."""
    from dataclasses import fields, is_dataclass
    import ast_nodes
    from ast_nodes import Node

    pad  = "  " * indent
    name = type(node).__name__

    if not is_dataclass(node):
        print(f"{pad}{node!r}")
        return

    child_fields = [
        (f.name, getattr(node, f.name))
        for f in fields(node)
        if f.name != "line"
    ]

    # Single-value leaf nodes (Number, String, Ident)
    if len(child_fields) == 1 and not isinstance(child_fields[0][1], (list, Node)):
        print(f"{pad}{name}({child_fields[0][1]!r})")
        return

    print(f"{pad}{name}")
    for fname, fval in child_fields:
        if isinstance(fval, list):
            print(f"{pad}  [{fname}]")
            for item in fval:
                _print_ast(item, indent + 2)
        elif isinstance(fval, Node):
            print(f"{pad}  {fname}:")
            _print_ast(fval, indent + 2)
        else:
            print(f"{pad}  {fname} = {fval!r}")


# ─────────────────────────────────────────────────────────────
#  CLI entry point
# ─────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]

    # No args → interactive REPL
    if not args:
        REPL().start()
        return

    flag = args[0]

    if flag in ("-h", "--help"):
        print(BANNER)
        print("  Usage:")
        print("    franz                    Launch interactive REPL")
        print("    franz file.franz         Run a file")
        print("    franz --tokens file.franz  Print token list")
        print("    franz --ast    file.franz  Print AST tree")
        print("    franz --help             Show this message")
        return

    if flag == "--tokens" and len(args) > 1:
        _show_tokens(args[1]); return

    if flag == "--ast" and len(args) > 1:
        _show_ast(args[1]); return

    # Default: run a file
    _run_file(args[0])


if __name__ == "__main__":
    main()
