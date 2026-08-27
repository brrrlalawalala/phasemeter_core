import ast
import operator
from dataclasses import dataclass
from typing import Mapping

import numpy as np


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


@dataclass
class DerivedChannel:
    name: str
    expression: str
    enabled: bool = True


class SafeExpression:
    def __init__(self, expression: str, allowed_names: set[str]):
        self.expression = expression
        self.allowed_names = allowed_names
        self.tree = ast.parse(expression, mode="eval")
        self._validate(self.tree)

    def evaluate(self, values: Mapping[str, float]) -> float:
        return float(self._eval(self.tree.body, values))

    def _validate(self, node):
        if isinstance(node, ast.Expression):
            self._validate(node.body)
            return
        if isinstance(node, ast.BinOp):
            if type(node.op) not in _BIN_OPS:
                raise ValueError("Only +, -, *, and / are supported.")
            self._validate(node.left)
            self._validate(node.right)
            return
        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in _UNARY_OPS:
                raise ValueError("Only unary + and - are supported.")
            self._validate(node.operand)
            return
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ValueError("Only numeric constants are supported.")
            return
        if isinstance(node, ast.Name):
            if node.id not in self.allowed_names:
                raise ValueError(f"Unknown channel name: {node.id}")
            return
        raise ValueError("Only channel names, constants, +, -, *, /, and parentheses are supported.")

    def _eval(self, node, values: Mapping[str, float]):
        if isinstance(node, ast.BinOp):
            return _BIN_OPS[type(node.op)](
                self._eval(node.left, values),
                self._eval(node.right, values),
            )
        if isinstance(node, ast.UnaryOp):
            return _UNARY_OPS[type(node.op)](self._eval(node.operand, values))
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return values[node.id]
        raise ValueError("Unsupported expression node.")


class DerivedChannelSet:
    def __init__(self, channels: list[DerivedChannel], real_channel_names: list[str]):
        self.channels = [channel for channel in channels if channel.enabled]
        self.real_channel_names = real_channel_names
        self.expressions = [
            SafeExpression(channel.expression, set(real_channel_names))
            for channel in self.channels
        ]

    @property
    def names(self) -> list[str]:
        return [channel.name for channel in self.channels]

    def evaluate(self, real_phases: np.ndarray) -> np.ndarray:
        if not self.channels:
            return np.empty(0, dtype=np.float64)
        values = dict(zip(self.real_channel_names, real_phases))
        return np.array(
            [expression.evaluate(values) for expression in self.expressions],
            dtype=np.float64,
        )
