# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Type, cast

import lark
from datacube.virtual.expr import formula_parser

from datacube_ows.ogc_utils import ConfigException

# Lark stuff.

identity = lambda ev, x: x


def empty_gen(ev, a):
    return set()


def union(ev, a, b):
    return a.union(b)


def not_supported(op_name):
    def impl(ev, a=None, b=None, c=None):
        raise ConfigException(f"{op_name} not supported")
    return impl


@lark.v_args(inline=True)
class ExpressionEvaluator(lark.Transformer):
    """
    Standard expression evaluator
    """
    from operator import add, floordiv, mod, mul, neg, pos, pow, sub, truediv
    not_ = inv = or_ = and_ = xor = not_supported("Bitwise logical operators")
    eq = ne = le = ge = lt = gt = not_supported("Comparison operators")
    lshift = rshift = not_supported("Left and right-shift operators")

    float_literal = float
    int_literal = int

    def __init__(self, style, *args, **kwargs):
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
    neg = pos = identity
    add = sub = mul = truediv = floordiv = mod = pow = union

    float_literal = empty_gen
    int_literal = empty_gen

    def var_name(self, key):
        return set([self.ows_style.local_band(key.value)])


### Expression wrapper - callable wrapper for a configurable expression

class ExpressionException(ConfigException):
    """
    Exception for invalid expressions
    """


class Expression:
    """
    Expression wrapper for configurable expression elements
    """
    def __init__(self, style: "datacube_ows.styles.StyleDef", expr_str: str) -> None:
        """
        Class constructor

        :param style: The style to which the expression belongs (may be a statically configured style, or user-defined.
        :param expr_str: The expression string to be parsed.
        """
        self.style = style
        self.expr_str = expr_str
        parser = formula_parser()
        try:
            self.tree = parser.parse(self.expr_str)
            self.needed_bands = BandListEvaluator(self.style).transform(self.tree)
        except lark.LarkError as e:
            raise ExpressionException(f"Invalid expression: {e} {self.expr_str}")
        except KeyError as e:
            raise ExpressionException(f"Unrecognised band '{e}' in {expr_str}")
        if len(self.needed_bands) == 0:
            raise ExpressionException(f"Expression references no bands: {self.expr_str}")

    def eval_cls(self, data: "xarray.Dataset") -> ExpressionEvaluator:
        """"
        Return an appropriate Expression Evaluator for a given Dataset
        """
        if self.style.user_defined:
            evaluator_cls: Type[ExpressionEvaluator] = UserDefinedExpressionEvaluator
        else:
            evaluator_cls = ExpressionEvaluator

        @lark.v_args(inline=True)
        class ExpressionDataEvaluator(evaluator_cls):
            def var_name(self, key):
                return data[self.ows_style.local_band(key.value)]

        # pyre-ignore[19]
        return cast(ExpressionEvaluator, ExpressionDataEvaluator(self.style))

    def __call__(self, data: "xarray.Dataset") -> Any:
        evaluator: ExpressionEvaluator = self.eval_cls(data)
        return evaluator.transform(self.tree)
