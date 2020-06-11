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

import unittest
from math import isnan

from typed_python import ListOf, TupleOf, NamedTuple, Dict, ConstDict, \
    Int32, Int16, Int8, UInt64, UInt32, UInt16, UInt8, Float32, \
    Alternative, Set, OneOf, Compiled, Entrypoint


def result_or_exception(f, *p):
    try:
        return f(*p)
    except Exception as e:
        return type(e)


class TestBuiltinCompilation(unittest.TestCase):
    def test_builtins_on_various_types(self):
        NT1 = NamedTuple(a=int, b=float, c=str, d=str)
        NT2 = NamedTuple(s=str, t=TupleOf(int))
        Alt1 = Alternative("Alt1", X={'a': int}, Y={'b': str})
        cases = [
            # (float, 1.23456789), # fails with compiled str=1.2345678899999999
            # (float, 12.3456789), # fails with compiled str=12.345678899999999
            # (float, -1.23456789), # fails with compiled str=-1.2345678899999999
            # (float, -12.3456789), # fails with compiled str=-12.345678899999999
            (bool, True),
            (float, 1.0/7.0),  # verify number of digits after decimal in string representation
            (float, 8.0/7.0),  # verify number of digits after decimal in string representation
            (float, 71.0/7.0),  # verify number of digits after decimal in string representation
            (float, 701.0/7.0),  # verify number of digits after decimal in string representation
            (float, 1.0/70.0),  # verify exp transition for small numbers
            (float, 1.0/700.0),  # verify exp transition for small numbers
            (float, 1.0/7000.0),  # verify exp transition for small numbers
            (float, 1.0/70000.0),  # verify exp transition for small numbers
            (float, 1.0),  # verify trailing zeros in string representation of float
            (float, 0.123456789),
            (float, 2**32),  # verify trailing zeros in string representation of float
            (float, 2**64),  # verify trailing zeros in string representation of float
            (float, 1.8e19),  # verify trailing zeros in string representation of float
            (float, 1e16),  # verify exp transition for large numbers
            (float, 1e16-2),  # verify exp transition for large numbers
            (float, 1e16+2),  # verify exp transition for large numbers
            (float, -1.0/7.0),  # verify number of digits after decimal in string representation
            (float, -8.0/7.0),  # verify number of digits after decimal in string representation
            (float, -71.0/7.0),  # verify number of digits after decimal in string representation
            (float, -701.0/7.0),  # verify number of digits after decimal in string representation
            (float, -1.0/70.0),  # verify exp transition for small numbers
            (float, -1.0/700.0),  # verify exp transition for small numbers
            (float, -1.0/7000.0),  # verify exp transition for small numbers
            (float, -1.0/70000.0),  # verify exp transition for small numbers
            (float, -0.123456789),
            (float, -1.0),  # verify trailing zeros in string representation of float
            (float, -2**32),  # verify trailing zeros in string representation of float
            (float, -2**64),  # verify trailing zeros in string representation of float
            (float, -1.8e19),  # verify trailing zeros in string representation of float
            (float, -1e16),  # verify exp transition in string representation of float
            (float, -1e16-2),  # verify exp transition in string representation of float
            (float, -1e16+2),  # verify exp transition in string representation of float
            (Alt1, Alt1.X(a=-1)),
            (Alt1, Alt1.Y(b='yes')),
            (Float32, 1.234),
            (int, 3),
            (int, -2**63),
            (bool, True),
            (Int8, -128),
            (Int16, -32768),
            (Int32, -2**31),
            (UInt8, 127),
            (UInt16, 65535),
            (UInt32, 2**32-1),
            (UInt64, 2**64-1),
            (Float32, 1.234567),
            (Float32, 1.234),
            (str, "abcd"),
            (str, "1234567890"),
            (str, "\n\r +1234"),
            (str, "-1234 \t "),
            (str, "-123_4 \t "),
            (str, "-_1234"),
            (str, "-1234_"),
            (str, "12__34"),
            (str, "-_1234"),
            (str, "-1234 _"),
            (str, "x1234"),
            (str, "1234L"),
            (str, " -1.23e-5"),
            (str, "-1.23e+5 "),
            (str, "+1.23e+5_0 "),
            (str, " +1.2_3e5_00 "),
            (str, "+1.23e-500 "),
            (str, "-0.0"),
            (str, "1."),
            (str, ".1"),
            (str, "Nan"),
            (str, " -inf"),
            (str, " +InFiNiTy "),
            (bytes, b"\01\00\02\03"),
            (Set(int), [1, 3, 5, 7]),
            (TupleOf(int), (7, 6, 5, 4, 3, 2, -1)),
            (TupleOf(Int32), (7, 6, 5, 4, 3, 2, -2)),
            (TupleOf(Int16), (7, 6, 5, 4, 3, 2, -3)),
            (TupleOf(Int8), (7, 6, 5, 4, 3, 2, -4)),
            (TupleOf(UInt64), (7, 6, 5, 4, 3, 2, 1)),
            (TupleOf(UInt32), (7, 6, 5, 4, 3, 2, 2)),
            (TupleOf(UInt16), (7, 6, 5, 4, 3, 2, 3)),
            (TupleOf(UInt8), (7, 6, 5, 4, 3, 2, 4)),
            (TupleOf(str), ("a", "b", "c")),
            (ListOf(str), ["a", "b", "d"]),
            (Dict(str, int), {'y': 7, 'n': 6}),
            (ConstDict(str, int), {'y': 2, 'n': 4}),
            (TupleOf(int), tuple(range(10000))),
            (OneOf(str, int), "ab"),
            (OneOf(str, int), 34),
            (NT1, NT1(a=1, b=2.3, c="c", d="d")),
            (NT2, NT2(s="xyz", t=tuple(range(10000))))
        ]
        for T, v in cases:
            def f_bool(x: T):
                return bool(x)

            def f_int(x: T):
                return int(x)

            def f_float(x: T):
                return float(x)

            def f_bytes(x: T):
                return str(x)

            def f_str(x: T):
                return str(x)

            def f_format(x: T):
                return format(x)

            def f_dir(x: T):
                return dir(x)

            fns = [f_bool, f_int, f_float, f_str, f_bytes, f_format, f_dir]
            for f in fns:
                if f is f_int and isinstance(v, (int, float)) and (v > 2**63-1 or v < -2**63):
                    continue
                r1 = result_or_exception(f, T(v))
                c_f = Compiled(f)
                r2 = result_or_exception(c_f, v)
                if type(r1) is float and isnan(r1):
                    self.assertEqual(isnan(r1), isnan(r2))
                else:
                    self.assertEqual(r1, r2)

    def test_min_max(self):
        def f_min(*v):
            return min(*v)

        def f_max(*v):
            return max(*v)

        C = Alternative("C", a={'val': int}, b={},
                        __eq__=lambda self, other: self.val == other.val,
                        __ne__=lambda self, other: self.val != other.val,
                        __lt__=lambda self, other: self.val > other.val,
                        __gt__=lambda self, other: self.val < other.val,
                        __le__=lambda self, other: self.val >= other.val,
                        __ge__=lambda self, other: self.val <= other.val,
                        )
        test_cases = [
            (1, 9), (9, 1),
            (-1, -9), (-9, -1),
            range(100), range(100, 0, -1),
            (3, 4, 5, 6, 2, 7, 8, 9), (9, 8, 7, 6, 5, 4, 3, 2, 0),
            (1e-99, 1e99), (1e99, 1e-99),
            (1.1, 2.1, 3.1, 0.5),
            (1, 1e99), (1e99, 1),
            (1, 1e-99), (1e-99, 1),
            (UInt8(2), Int16(10), Int32(5), 22.5),
            (UInt8(15), Int16(10), Int32(20), 12.5),
            (UInt8(10), Int16(20), Int32(5), 12.5),
            (UInt8(15), Int16(10), Int32(5), 2.5),
            (UInt8(3), Int16(3), Int32(3), 3.0),
            (3.0, UInt8(3), Int16(3), Int32(3)),
            (Int32(3), 3.0, UInt8(3), Int16(3)),
            (Int16(3), Int32(3), 3.0, UInt8(3)),
            (C.a(100), C.a(80), C.a(120)),
            (C.a(1), C.a(2), C.a(3)),
            (C.a(3), C.a(2), C.a(1)),
        ]
        for f in [f_min, f_max]:
            for v in test_cases:
                r1 = f(*v)
                r2 = Entrypoint(f)(*v)
                self.assertEqual(r1, r2)
