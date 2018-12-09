#   Copyright 2017 Braxton Mckee
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import nativepython.native_ast as native_ast

from nativepython.type_wrappers.wrapper import Wrapper
from nativepython.type_wrappers.none_wrapper import NoneWrapper

class TypedExpression(object):
    def __init__(self, expr, t, isReference):
        """Initialize a TypedExpression

        expr - a native_ast containing an expression
        t - a subclass of Wrapper
        isReference - is this a pointer to a memory location, or the actual value?
        """
        super().__init__()
        assert isinstance(t, Wrapper) or t is None, t
        assert isinstance(expr, native_ast.Expression), expr

        self.expr = expr
        self.expr_type = t
        self.isReference = isReference

    def as_call_arg(self, context):
        """Convert this expression to a call-argument form."""
        if self.expr_type.is_pod:
            return self.ensureNonReference()
        else:
            if self.isReference:
                return self

            assert False, "we should be jamming this rvalue object into a temporary that we can pass"

    def convert_assign(self, context, toStore):
        return self.expr_type.convert_assign(context, self, toStore)

    def convert_destroy(self, context):
        return self.expr_type.convert_destroy(context, self)

    def convert_copy_initialize(self, context, target, toStore):
        return self.expr_type.convert_copy_initialize(context, self, toStore)

    def convert_getitem(self, context, item):
        return self.expr_type.convert_getitem(context, self, item)

    def convert_len(self, context):
        return self.expr_type.convert_len(context, self)

    def convert_bin_op(self, context, op, rhs):
        return self.expr_type.convert_bin_op(context, self, op, rhs)

    def convert_call(self, context, args):
        return self.expr_type.convert_call(context, self, args)

    def ensureNonReference(self):
        return self.expr_type.ensureNonReference(self)

    def toFloat64(self, context):
        return self.expr_type.toFloat64(context, self)

    def toInt64(self, context):
        return self.expr_type.toInt64(context, self)

    def toBool(self, context):
        return self.expr_type.toBool(context, self)

    def __str__(self):
        return "Expression(%s%s)" % (self.expr_type, ",[ref]" if self.isReference else "")

    @staticmethod
    def Void(expr=None):
        return TypedExpression(expr if expr is not None else native_ast.nullExpr, NoneWrapper(), False)

    def __rshift__(self, other):
        return TypedExpression(self.expr + other.expr, other.expr_type, other.isReference)

    def __or__(self, other):
        return self.expr_type.sugar_operator(self, other, "BitOr")
    def __and__(self, other):
        return self.expr_type.sugar_operator(self, other, "BitAnd")
        
    def __lt__(self, other):
        return self.expr_type.sugar_comparison(self, other, "Lt")
    def __le__(self, other):
        return self.expr_type.sugar_comparison(self, other, "LtE")
    def __gt__(self, other):
        return self.expr_type.sugar_comparison(self, other, "Gt")
    def __ge__(self, other):
        return self.expr_type.sugar_comparison(self, other, "GtE")
    def __eq__(self, other):
        return self.expr_type.sugar_comparison(self, other, "Eq")
    def __ne__(self, other):
        return self.expr_type.sugar_comparison(self, other, "NotEq")
