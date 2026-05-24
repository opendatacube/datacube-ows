# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import operator
from typing import Any, cast

import lark

from datacube_ows.config_utils import ConfigException

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable

    from xarray import Dataset

    from datacube_ows.styles import StyleDef

# Lark stuff.

identity = lambda ev, x: x  # noqa: E731


def empty_gen(ev, a: set) -> set:
    return set()


def union(ev, a: set, b: set) -> set:
    return a.union(b)


def not_supported(op_name: object) -> Callable[[object, object], Any]:
    def impl(ev: object, a: object = None, b: object = None, c: object = None) -> Any:
        raise ConfigException(f"{op_name} not supported")

    return impl


def formula_parser() -> lark.Lark:
    return lark.Lark(
        """
                ?expr: num_expr | bool_expr

                ?bool_expr: or_clause | comparison_clause

                ?or_clause: or_clause "|" and_clause -> or_
                          | or_clause "^" and_clause -> xor
                          | and_clause
                ?and_clause: and_clause "&" term -> and_
                           | term
                ?term: "not" term -> not_
                     | "(" bool_expr ")"

                ?comparison_clause: eq | ne | le | ge | lt | gt

                eq: num_expr "==" num_expr
                ne: num_expr "!=" num_expr
                le: num_expr "<=" num_expr
                ge: num_expr ">=" num_expr
                lt: num_expr "<" num_expr
                gt: num_expr ">" num_expr


                ?num_expr: shift

                ?shift: shift "<<" sum -> lshift
                      | shift ">>" sum -> rshift
                      | sum

                ?sum: sum "+" product -> add
                    | sum "-" product -> sub
                    | product

                ?product: product "*" atom -> mul
                        | product "/" atom -> truediv
                        | product "//" atom -> floordiv
                        | product "%" atom -> mod
                        | atom

                ?atom: "-" subatom -> neg
                     | "+" subatom -> pos
                     | "~" subatom -> inv
                     | subatom "**" atom -> pow
                     | subatom

                ?subatom: NAME -> var_name
                        | FLOAT -> float_literal
                        | INT -> int_literal
                        | "(" num_expr ")"


                %import common.FLOAT
                %import common.INT
                %import common.WS_INLINE
                %import common.CNAME -> NAME

                %ignore WS_INLINE
                """,
        start="expr",
    )


@lark.v_args(inline=True)
class ExpressionEvaluator(lark.Transformer):
    """
    Standard expression evaluator
    """

    add = operator.add
    floordiv = operator.floordiv
    mod = operator.mod
    mul = operator.mul
    neg = operator.neg
    pos = operator.pos
    pow = operator.pow
    sub = operator.sub
    truediv = operator.truediv

    not_ = inv = or_ = and_ = xor = not_supported("Bitwise logical operators")
    eq = ne = le = ge = lt = gt = not_supported("Comparison operators")
    lshift = rshift = not_supported("Left and right-shift operators")

    float_literal = float
    int_literal = int

    def __init__(self, style, *args, **kwargs) -> None:
        self.ows_style = style
        super().__init__(*args, **kwargs)


@lark.v_args(inline=True)
class UserDefinedExpressionEvaluator(ExpressionEvaluator):
    """
    Expression evaluator for user-defined expressions.

    (Doesn't support exponent operator)
    """

    pow = not_supported("Exponent operator")


@lark.v_args(inline=True)
class BandListEvaluator(ExpressionEvaluator):
    """
    Expression evaluator that returns a list of needed bands for the expression.
    """

    neg = pos = identity  # type: ignore[assignment]
    add = sub = mul = truediv = floordiv = mod = pow = union  # type: ignore[assignment]

    float_literal = empty_gen  # type: ignore[assignment]
    int_literal = empty_gen  # type: ignore[assignment]

    def var_name(self, key) -> set:
        return {self.ows_style.local_band(key.value)}


### Expression wrapper - callable wrapper for a configurable expression


class ExpressionException(ConfigException):
    """
    Exception for invalid expressions
    """


class Expression:
    """
    Expression wrapper for configurable expression elements
    """

    def __init__(self, style: StyleDef, expr_str: str) -> None:
        """
        Class constructor

        :param style: The style to which the expression belongs
                      (may be a statically configured style, or user-defined).
        :param expr_str: The expression string to be parsed.
        """
        self.style = style
        self.expr_str = expr_str
        parser = formula_parser()
        try:
            self.tree = parser.parse(self.expr_str)
            self.needed_bands = BandListEvaluator(self.style).transform(self.tree)
        except lark.LarkError as e:
            raise ExpressionException(
                f"Invalid expression: {e} {self.expr_str}"
            ) from None
        except KeyError as e:
            raise ExpressionException(
                f"Unrecognised band '{e}' in {expr_str}"
            ) from None
        if len(self.needed_bands) == 0:
            raise ExpressionException(
                f"Expression references no bands: {self.expr_str}"
            )

    def eval_cls(self, data: Dataset) -> ExpressionEvaluator:
        """
        Return an appropriate Expression Evaluator for a given Dataset
        """
        if self.style.user_defined:
            evaluator_cls: type[ExpressionEvaluator] = UserDefinedExpressionEvaluator
        else:
            evaluator_cls = ExpressionEvaluator

        @lark.v_args(inline=True)
        class ExpressionDataEvaluator(evaluator_cls):  # type: ignore[valid-type, misc]
            def var_name(self, key) -> str:
                return data[self.ows_style.local_band(key.value)]

        # pyre-ignore[19]
        return cast("ExpressionEvaluator", ExpressionDataEvaluator(self.style))

    def __call__(self, data: Dataset) -> Any:
        evaluator: ExpressionEvaluator = self.eval_cls(data)
        return evaluator.transform(self.tree)
