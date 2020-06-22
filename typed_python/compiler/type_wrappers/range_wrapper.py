#   Copyright 2017-2020 typed_python Authors
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

from typed_python.compiler.type_wrappers.wrapper import Wrapper
from typed_python.compiler.type_wrappers.arithmetic_wrapper import IntWrapper
import typed_python.compiler.native_ast as native_ast


class RangeWrapper(Wrapper):
    is_pod = True
    is_empty = False
    is_pass_by_ref = False

    def __init__(self):
        super().__init__((range, "type"))

    def getNativeLayoutType(self):
        return native_ast.Type.Void()

    def convert_call(self, context, expr, args, kwargs):
        if len(args) == 1 and not kwargs:
            arg = args[0].toInt64()
            if not arg:
                return None
            return context.push(
                _RangeInstanceWrapper,
                lambda newInstance:
                    newInstance.expr.ElementPtrIntegers(0, 0).store(native_ast.const_int_expr(-1))
                    >> newInstance.expr.ElementPtrIntegers(0, 1).store(arg.nonref_expr)
            )

        if len(args) == 2 and not kwargs:
            arg0 = args[0].toInt64()
            if not arg0:
                return None

            arg1 = args[1].toInt64()
            if not arg1:
                return None

            return context.push(
                _RangeInstanceWrapper,
                lambda newInstance:
                    newInstance.expr.ElementPtrIntegers(0, 0).store(arg0.nonref_expr.sub(1))
                    >> newInstance.expr.ElementPtrIntegers(0, 1).store(arg1.nonref_expr)
            )
        return super().convert_call(context, expr, args, kwargs)

    def convert_str_cast(self, context, instance):
        # need this to be able to print(type(r)) if r is a range, in compiled code
        # otherwise the tuple confuses 'print'
        return context.constant(str(self.typeRepresentation[0]))


class RangeInstanceWrapper(Wrapper):
    is_pod = True
    is_empty = False
    is_pass_by_ref = False

    def __init__(self):
        super().__init__((range, "instance"))

    def getNativeLayoutType(self):
        return native_ast.Type.Struct(element_types=(('start', native_ast.Int64), ('stop', native_ast.Int64)))

    def convert_method_call(self, context, expr, methodname, args, kwargs):
        if methodname == "__iter__" and not args and not kwargs:
            return context.push(
                _RangeIteratorWrapper,
                lambda instance:
                    instance.expr.store(expr.nonref_expr)
            )
        return super().convert_method_call(context, expr, methodname, args, kwargs)

    def get_iteration_elt_wrapper(self):
        return IntWrapper(int)


class RangeIteratorWrapper(Wrapper):
    is_pod = True
    is_empty = False
    is_pass_by_ref = True

    def __init__(self):
        super().__init__((range, "iterator"))

    def getNativeLayoutType(self):
        return native_ast.Type.Struct(
            element_types=(("count", native_ast.Int64), ("len", native_ast.Int64)),
            name="range_storage"
        )

    def convert_next(self, context, expr):
        context.pushEffect(
            expr.expr.ElementPtrIntegers(0, 0).store(
                expr.expr.ElementPtrIntegers(0, 0).load().add(1)
            )
        )
        canContinue = context.pushPod(
            bool,
            expr.expr.ElementPtrIntegers(0, 0).load().lt(
                expr.expr.ElementPtrIntegers(0, 1).load()
            )
        )
        nextExpr = context.pushReference(int, expr.expr.ElementPtrIntegers(0, 0))

        return nextExpr, canContinue


_RangeWrapper = RangeWrapper()
_RangeInstanceWrapper = RangeInstanceWrapper()
_RangeIteratorWrapper = RangeIteratorWrapper()
