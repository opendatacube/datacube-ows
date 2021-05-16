# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import lark


def formula_parser():
    return lark.Lark("""
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
                """, start='expr')
