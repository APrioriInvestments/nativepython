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

import typed_python.compiler
from typed_python.compiler.type_wrappers.wrapper import Wrapper
import typed_python.compiler.native_ast as native_ast
from typed_python import Float32, ListOf, Tuple, TupleOf, NamedTuple, Dict
from typed_python.compiler.conversion_level import ConversionLevel
import typed_python.compiler.type_wrappers.runtime_functions as runtime_functions
from typed_python.compiler.type_wrappers.tuple_wrapper import MasqueradingTupleWrapper
import sys

from math import (
    acos,
    acosh,
    asin,
    asinh,
    atan,
    atan2,
    atanh,
    # ceil,
    copysign,
    cos,
    cosh,
    degrees,
    # e,
    erf,
    erfc,
    exp,
    expm1,
    fabs,
    factorial,
    # floor,
    fmod,
    frexp,
    fsum,
    gamma,
    gcd,
    hypot,
    # inf,
    isclose,
    isfinite,
    isinf,
    isnan,
    ldexp,
    lgamma,
    log,
    log10,
    log1p,
    log2,
    modf,
    # nan,
    pi,
    pow,
    radians,
    sin,
    sinh,
    sqrt,
    tan,
    tanh,
    # tau,
    # trunc
    # added in 3.7:
    # remainder
    # added in 3.8:
    # comb
    # dist
    # isqrt
    # perm
    # prod
)


def sumIterable(iterable):
    """Full precision summation using multiple floats for intermediate values.
    Code modified from msum() at code.activestate.com/recipes/393090/, which
    is licensed under the PSF License.
    Processes arguments as python3.6 or 3.7 math module.
    Original comment below.
    """
    # Rounded x+y stored in hi with the round-off stored in lo.  Together
    # hi+lo are exactly equal to x+y.  The inner loop applies hi/lo summation
    # to each partial so that the list of partial sums remains exact.
    # Depends on IEEE-754 arithmetic guarantees.  See proof of correctness at:
    # www-2.cs.cmu.edu/afs/cs/project/quake/public/papers/robust-arithmetic.ps

    partials = ListOf(float)()
    for item in iterable:
        # float(item) would convert str to float, so __float__ is better
        if not isinstance(item, float):
            try:
                item = item.__float__()  # does not convert str to float
            except AttributeError:
                raise TypeError('must be real number')
        x = float(item)  # I know item is a float now, but force compiler to know this too

        i = 0
        for y in partials:
            if abs(x) < abs(y):
                t = x
                x = y
                y = t
            hi = x + y
            lo = y - (hi - x)
            if lo:
                partials[i] = lo
                i += 1
            x = hi
        popindex = len(partials) - 1
        while popindex >= i:
            partials.pop()
            popindex -= 1
        partials.append(x)
    ret = 0.0
    for p in partials:
        ret += p
    return ret


def sumIterable38(iterable):
    """Full precision summation using multiple floats for intermediate values.
    Code modified from msum() at code.activestate.com/recipes/393090/, which
    is licensed under the PSF License.
    Processes arguments as python3.8+ math module.
    Original comment below.
    """
    # Rounded x+y stored in hi with the round-off stored in lo.  Together
    # hi+lo are exactly equal to x+y.  The inner loop applies hi/lo summation
    # to each partial so that the list of partial sums remains exact.
    # Depends on IEEE-754 arithmetic guarantees.  See proof of correctness at:
    # www-2.cs.cmu.edu/afs/cs/project/quake/public/papers/robust-arithmetic.ps

    partials = ListOf(float)()
    for item in iterable:
        # float(item) would convert str to float, so __float__ is better
        if not isinstance(item, float):
            try:
                item = item.__float__()  # does not convert str to float
            except AttributeError:
                try:
                    item = item.__index__()
                except AttributeError:
                    raise TypeError('must be real number')
        x = float(item)  # force to float

        i = 0
        for y in partials:
            if abs(x) < abs(y):
                t = x
                x = y
                y = t
            hi = x + y
            lo = y - (hi - x)
            if lo:
                partials[i] = lo
                i += 1
            x = hi
        popindex = len(partials) - 1
        while popindex >= i:
            partials.pop()
            popindex -= 1
        partials.append(x)
    ret = 0.0
    for p in partials:
        ret += p
    return ret


class MathFunctionWrapper(Wrapper):
    is_pod = True
    is_empty = False
    is_pass_by_ref = False

    MathImpl = NamedTuple(f=object, args=TupleOf(object), ret=object, check_inf=bool)
    # f is a runtime_function, or None.
    #   None means this implementation is a special case.
    # args is the tuple of argument types, if it's not just (float,), with elements float, int, "index", or "iterable".
    #   None means arg_types=(float,)
    # ret is the appropriate type or Wrapper for the return value, if it's not float.
    #   None means float.
    #   A tuple is permitted, meaning that a Masqueraded Tuple of those types should be returned.
    # check_inf=True means we should generate code to raise an error if the inputs were finite but the output was not finite
    #    This is only needed if the runtime function doesn't do this already, for example, if it is an LLVM intrinsic.
    math_impls = Dict(object, MathImpl)({
        acos: MathImpl(f=runtime_functions.acos64),
        acosh: MathImpl(f=runtime_functions.acosh64),
        asin: MathImpl(f=runtime_functions.asin64),
        asinh: MathImpl(f=runtime_functions.asinh64),
        atan: MathImpl(f=runtime_functions.atan64),
        atanh: MathImpl(f=runtime_functions.atanh64),
        # ceil: MathImpl(f=runtime_functions.ceil64),  # see BuiltinWrapper
        cos: MathImpl(f=runtime_functions.cos64),
        cosh: MathImpl(f=runtime_functions.cosh64),
        degrees: MathImpl(f=None),
        erf: MathImpl(f=runtime_functions.erf64),
        erfc: MathImpl(f=runtime_functions.erfc64),
        exp: MathImpl(f=runtime_functions.exp64, check_inf=True),
        expm1: MathImpl(f=runtime_functions.expm1_64),
        fabs: MathImpl(f=runtime_functions.fabs64),
        factorial: MathImpl(f=runtime_functions.factorial64),
        # floor: MathImpl(f=runtime_functions.floor64),  # see BuiltinWrapper
        frexp: MathImpl(f=runtime_functions.frexp64, ret=(float, int)),
        fsum: MathImpl(f=None, args=("iterable",)),  # special case, in this table for completeness
        gamma: MathImpl(f=runtime_functions.gamma64),
        isfinite: MathImpl(f=runtime_functions.isfinite_float64, ret=bool),
        isinf: MathImpl(f=runtime_functions.isinf_float64, ret=bool),
        isnan: MathImpl(f=runtime_functions.isnan_float64, ret=bool),
        ldexp: MathImpl(f=runtime_functions.ldexp64, args=(float, int)),
        lgamma: MathImpl(f=runtime_functions.lgamma64),
        log: MathImpl(f=runtime_functions.log64),
        log1p: MathImpl(f=runtime_functions.log1p64),
        log2: MathImpl(f=runtime_functions.log2_64),
        log10: MathImpl(f=runtime_functions.log10_64),
        modf: MathImpl(f=runtime_functions.modf64, ret=(float, float)),
        radians: MathImpl(f=None),
        sin: MathImpl(f=runtime_functions.sin64),
        sinh: MathImpl(f=runtime_functions.sinh64, check_inf=True),
        sqrt: MathImpl(f=runtime_functions.sqrt64),
        tan: MathImpl(f=runtime_functions.tan64),
        tanh: MathImpl(f=runtime_functions.tanh64),
        atan2: MathImpl(f=runtime_functions.atan2_64, args=(float, float)),
        copysign: MathImpl(f=runtime_functions.copysign64, args=(float, float)),
        fmod: MathImpl(f=runtime_functions.fmod64, args=(float, float)),
        gcd: MathImpl(f=runtime_functions.gcd, args=("index", "index"), ret=int),
        hypot: MathImpl(f=None, args=(float, float)),
        isclose: MathImpl(f=runtime_functions.isclose64, ret=bool),  # special case, in this table for completeness
        pow: MathImpl(f=runtime_functions.pow64, args=(float, float), check_inf=True),
        # trunc: MathImpl(f=runtime_functions.trunc64),  # see BuiltinWrapper
    })

    SUPPORTED_FUNCTIONS = tuple(math_impls.keys())

    def __init__(self, mathFun):
        assert mathFun in self.SUPPORTED_FUNCTIONS
        super().__init__(mathFun)

    def getNativeLayoutType(self):
        return native_ast.Type.Void()

    @Wrapper.unwrapOneOfAndValue
    def convert_call(self, context, expr, args, kwargs):
        # Special cases
        if self.typeRepresentation is fsum and len(args) == 1 and not kwargs:
            if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
                return context.call_py_function(sumIterable38, (args[0],), {})
            return context.call_py_function(sumIterable, (args[0],), {})

        if self.typeRepresentation is isclose and 2 <= len(args) <= 4:
            arg1 = args[0].convert_to_type(float, ConversionLevel.Math)
            if arg1 is None:
                return None
            arg2 = args[1].convert_to_type(float, ConversionLevel.Math)
            if arg2 is None:
                return None
            if "rel_tol" in kwargs:
                rel_tol = kwargs["rel_tol"].convert_to_type(float, ConversionLevel.Math)
                if rel_tol is None:
                    return None
            else:
                if args[0].expr_type.typeRepresentation is Float32 and args[1].expr_type.typeRepresentation is Float32:
                    rel_tol = native_ast.const_float_expr(1e-5)  # with Float32, default needs to be larger
                else:
                    rel_tol = native_ast.const_float_expr(1e-9)

            if "abs_tol" in kwargs:
                abs_tol = kwargs["abs_tol"].convert_to_type(float, ConversionLevel.Math)
                if abs_tol is None:
                    return None
            else:
                abs_tol = native_ast.const_float_expr(0.0)

            func = runtime_functions.isclose64
            return context.pushPod(bool, func.call(arg1.nonref_expr, arg2.nonref_expr, rel_tol, abs_tol))

        # Implementation from table
        impl = self.math_impls.get(self.typeRepresentation)
        impl_args = impl.args if impl.args else (float,)

        # Check number of arguments and kwargs
        if len(args) != len(impl_args) or kwargs:
            return super().convert_call(context, expr, args, kwargs)

        # Check for constant arguments.
        if all([a.isConstant for a in args]) and self.typeRepresentation is not isclose:
            # Don't do this for isclose, since isclose depends on type, not just values.
            try:
                return context.constant(self.typeRepresentation(*(a.constantValue for a in args)))
            except Exception:
                # For compatibility, exceptions are not optimized, and will be raised at runtime,
                # rather than during compilation.
                pass

        # Convert arguments
        converted_args = []
        for i, a in enumerate(args):
            arg_type = impl_args[i]
            if arg_type == float:
                converted_a = a.convert_to_type(arg_type, ConversionLevel.Math)
            elif arg_type == int:
                converted_a = a.convert_to_type(arg_type, ConversionLevel.Signature)
            elif arg_type == "index":
                converted_a = a.toIndex()
            if converted_a is None:
                return None
            converted_args.append(converted_a)

        # convenience variables
        arg1 = converted_args[0]
        arg2 = converted_args[1] if len(args) > 1 else None
        arg = converted_args[0]

        # Validate arguments
        if self.typeRepresentation is fmod:
            with context.ifelse(arg2.nonref_expr.eq(0.0)) as (ifTrue, ifFalse):
                with ifTrue:
                    context.pushException(ValueError, "math domain error")
        if self.typeRepresentation is pow:
            with context.ifelse(arg1.nonref_expr.lte(0.0)) as (ifTrue, ifFalse):
                with ifTrue:  # arg1 <= 0
                    with context.ifelse(arg1.nonref_expr.eq(0.0)) as (ifTrue2, ifFalse2):
                        with ifTrue2:  # arg1 == 0
                            with context.ifelse(arg2.nonref_expr.lt(0.0)) as (ifTrue3, ifFalse3):
                                with ifTrue3:  # arg1 == 0, arg2 < 0
                                    context.pushException(ValueError, "math domain error")
                        with ifFalse2:  # arg1 < 0
                            f_isinf = runtime_functions.isinf_float64
                            with context.ifelse(f_isinf.call(arg1.nonref_expr)) as (ifTrue4, ifFalse4):
                                with ifFalse4:  # arg1 < 0 and arg1 is finite
                                    f_floor = runtime_functions.floor64
                                    with context.ifelse(
                                        f_floor.call(arg2.nonref_expr).sub(arg2.nonref_expr).neq(0.0)
                                    ) as (ifTrue5, ifFalse5):
                                        with ifTrue5:  # arg1 < 0, arg1 is finite, arg2 not an integer
                                            context.pushException(ValueError, "math domain error")
        if self.typeRepresentation in (cos, sin, tan):
            with context.ifelse(runtime_functions.isinf_float64.call(arg.nonref_expr)) as (ifTrue, ifFalse):
                with ifTrue:
                    context.pushException(ValueError, "math domain error")
        elif self.typeRepresentation in (acos, asin):
            with context.ifelse(arg.nonref_expr.gt(1.0)) as (ifTrue, ifFalse):
                with ifTrue:
                    context.pushException(ValueError, "math domain error")
            with context.ifelse(arg.nonref_expr.lt(-1.0)) as (ifTrue, ifFalse):
                with ifTrue:
                    context.pushException(ValueError, "math domain error")
        elif self.typeRepresentation is acosh:
            with context.ifelse(arg.nonref_expr.lt(1.0)) as (ifTrue, ifFalse):
                with ifTrue:
                    context.pushException(ValueError, "math domain error")
        elif self.typeRepresentation is atanh:
            with context.ifelse(arg.nonref_expr.gte(1.0)) as (ifTrue, ifFalse):
                with ifTrue:
                    context.pushException(ValueError, "math domain error")
            with context.ifelse(arg.nonref_expr.lte(-1.0)) as (ifTrue, ifFalse):
                with ifTrue:
                    context.pushException(ValueError, "math domain error")
        elif self.typeRepresentation is factorial:
            with context.ifelse(arg.nonref_expr.gte(0.0)) as (ifTrue, ifFalse):
                with ifTrue:  # arg >= 0
                    f_floor = runtime_functions.floor64
                    with context.ifelse(f_floor.call(arg.nonref_expr).sub(arg.nonref_expr).neq(0.0)) as (ifTrue2, ifFalse2):
                        with ifTrue2:  # arg >= 0, arg not an integer
                            context.pushException(ValueError, "factorial() only accepts integral values")
                with ifFalse:  # arg < 0
                    context.pushException(ValueError, "factorial() not defined for negative values")
        elif self.typeRepresentation is gamma:
            with context.ifelse(arg.nonref_expr.lte(0.0)) as (ifTrue, ifFalse):
                with ifTrue:  # arg <= 0
                    with context.ifelse(runtime_functions.isinf_float64.call(arg.nonref_expr)) as (ifTrue2, ifFalse2):
                        with ifTrue2:  # arg == -inf   Note: inf is ok but not -inf
                            context.pushException(ValueError, "math domain error")
                    f_floor = runtime_functions.floor64
                    with context.ifelse(f_floor.call(arg.nonref_expr).sub(arg.nonref_expr).eq(0.0)) as (ifTrue2, ifFalse2):
                        with ifTrue2:  # arg <= 0, arg an integer
                            context.pushException(ValueError, "math domain error")
        elif self.typeRepresentation is lgamma:
            with context.ifelse(arg.nonref_expr.lte(0.0)) as (ifTrue, ifFalse):
                with ifTrue:  # arg <= 0
                    f_floor = runtime_functions.floor64
                    with context.ifelse(f_floor.call(arg.nonref_expr).sub(arg.nonref_expr).eq(0.0)) as (ifTrue2, ifFalse2):
                        with ifTrue2:  # arg <= 0, arg an integer
                            context.pushException(ValueError, "math domain error")
        elif self.typeRepresentation in (log, log2, log10):
            with context.ifelse(arg.nonref_expr.lte(0.0)) as (ifTrue, ifFalse):
                with ifTrue:  # arg <= 0
                    context.pushException(ValueError, "math domain error")
        elif self.typeRepresentation is log1p:
            with context.ifelse(arg.nonref_expr.lte(-1.0)) as (ifTrue, ifFalse):
                with ifTrue:  # arg <= -1
                    context.pushException(ValueError, "math domain error")
        elif self.typeRepresentation is sqrt:
            with context.ifelse(arg.nonref_expr.lt(0.0)) as (ifTrue, ifFalse):
                with ifTrue:  # arg < 0
                    context.pushException(ValueError, "math domain error")

        # Special implementation
        if self.typeRepresentation is hypot:
            func = runtime_functions.sqrt64
            return context.pushPod(float, func.call(arg1.nonref_expr.mul(arg1.nonref_expr).add(arg2.nonref_expr.mul(arg2.nonref_expr))))
        elif self.typeRepresentation is radians:
            return context.pushPod(float, arg.nonref_expr.mul(native_ast.const_float_expr(pi / 180)))
        elif self.typeRepresentation is degrees:
            return context.pushPod(float, arg.nonref_expr.mul(native_ast.const_float_expr(180 / pi)))

        # Implementation as C++ function or LLVM intrinsic

        # Returning a tuple
        if isinstance(impl.ret, tuple):
            outT = MasqueradingTupleWrapper(Tuple(*impl.ret))
            return_tuple = native_ast.Expression.StackSlot(name=".return_tuple", type=outT.layoutType)
            context.pushEffect(impl.f.call(arg1.nonref_expr, return_tuple.elemPtr(0).cast(native_ast.VoidPtr)))
            return typed_python.compiler.typed_expression.TypedExpression(context, return_tuple, outT, True)

        # Returning a single value
        outT = impl.ret if impl.ret else float
        ret = context.pushPod(outT, impl.f.call(*converted_args))

        # Check for nonfinite return value with finite arguments passed in
        if impl.check_inf:
            f_isinf = runtime_functions.isinf_float64
            with context.ifelse(f_isinf.call(ret.nonref_expr)) as (ifTrue, ifFalse):
                with ifTrue:
                    f_isfinite = runtime_functions.isfinite_float64
                    with context.ifelse(
                        f_isfinite.call(arg1.nonref_expr) if len(args) == 1 else
                        f_isfinite.call(arg1.nonref_expr).bitand(f_isfinite.call(arg2.nonref_expr))
                    ) as (ifTrue2, ifFalse2):
                        with ifTrue2:
                            context.pushException(OverflowError, 'math range error')
        return ret
