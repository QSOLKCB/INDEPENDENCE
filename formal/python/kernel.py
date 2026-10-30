"""PYTHON-KERNEL/1 — independently implemented Python reference under the shared semantics.

This is NOT existing application Python, and not a proof of Ada or JavaScript.
"""
from __future__ import annotations


def evaluate(operation: str, args: tuple[int, ...]) -> str:
    if not isinstance(operation, str) or type(args) is not tuple or any(type(x) is not int for x in args):
        return "ERR:INVALID"
    if any(x < 0 for x in args):
        return "ERR:INVALID"
    if operation == "ADDR" and len(args) == 3:
        row, col, width = args
        if 1 <= width <= 16 and row <= 15 and col < width:
            return f"OK:{row * width + col}"
    elif operation == "DECODE" and len(args) == 2:
        pos, width = args
        if 1 <= width <= 16 and pos <= 255 and pos < 16 * width:
            row, col = divmod(pos, width)
            return f"OK:{row},{col}"
    elif operation == "PARITY_ADD" and len(args) == 2:
        left, right = args
        if left <= 1 and right <= 1:
            return f"OK:{left ^ right}"
    elif operation == "PARITY_MUL" and len(args) == 2:
        left, right = args
        if left <= 1 and right <= 1:
            return f"OK:{left & right}"
    elif operation == "PHASE_ADD" and len(args) == 2:
        left, right = args
        if left <= 2 and right <= 2:
            return f"OK:{(left + right) % 3}"
    elif operation == "EDGE_VALID" and len(args) == 3:
        source, target, count = args
        if 2 <= count <= 256 and source <= 255 and target <= 255:
            return f"OK:{int(source < count and target < count and source != target)}"
    elif operation == "EDGE_STEP" and len(args) == 5:
        source, target, count, current, influence = args
        if (2 <= count <= 256 and source <= 255 and target <= 255
                and source < count and target < count and source != target
                and current <= 1 and influence <= 1):
            return f"OK:{current ^ influence}"
    return "ERR:INVALID"
