import lark

from datacube_ows.ogc_utils import ConfigException
from datacube_ows.styles.expr import formula_parser

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
    from operator import add, sub, mul, truediv, floordiv, neg, pos, mod, pow
    not_ = inv = or_ = and_ = xor = not_supported("Bitwise logical operators")
    eq = ne = le = ge = lt = gt = not_supported("Comparison operators")
    lshift = rshift = not_supported("Left and right-shift operators")

    float_literal = float
    int_literal = int

    def __init__(self, style, *args, **kwargs):
        self.ows_style = style
        super().__init__(*args, **kwargs)


@lark.v_args(inline=True)
class BandListEvaluator(ExpressionEvaluator):
    neg = pos = identity
    add = sub = mul = truediv = floordiv = mod = pow = union

    float_literal = empty_gen
    int_literal = empty_gen

    def var_name(self, key):
        return set([self.ows_style.local_band(key.value)])


class Expression:
    def __init__(self, style, expr_str):
        self.style = style
        self.expr_str = expr_str
        parser = formula_parser()
        try:
            self.tree = parser.parse(self.expr_str)
            self.needed_bands = BandListEvaluator(self.style).transform(self.tree)
        except lark.LarkError as e:
            raise ConfigException(f"Invalid expression: {e} {self.expr_str}")
        except KeyError as e:
            raise ConfigException(f"Unrecognised band '{e}' in {expr_str}")
        if len(self.needed_bands) == 0:
            raise ConfigException(f"Expression references no bands: {self.expr_str}")


    def __call__(self, data):
        @lark.v_args(inline=True)
        class ExpressionDataEvaluator(ExpressionEvaluator):
            def var_name(self, key):
                return data[self.ows_style.local_band(key.value)]

        return ExpressionDataEvaluator(self.style).transform(self.tree)

