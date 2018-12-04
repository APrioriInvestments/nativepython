#   Copyright 2018 Braxton Mckee
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
from typed_python import Int8, NoneType, TupleOf, OneOf, Tuple, NamedTuple, Int64, Float64, String, \
    Bool, Bytes, ConstDict, Alternative, serialize, deserialize, Value, Class, Member, _types, TypedFunction, TypeSet

class TypesSerializationTest(unittest.TestCase):
    def test_serialize_core_python_objects(self):
        ts = TypeSet()

        self.assertEqual(ts.deserialize(ts.serialize(10)), 10)
        self.assertEqual(ts.deserialize(ts.serialize(10.5)), 10.5)
        self.assertEqual(ts.deserialize(ts.serialize(None)), None)
        self.assertEqual(ts.deserialize(ts.serialize(True)), True)
        self.assertEqual(ts.deserialize(ts.serialize(False)), False)
        self.assertEqual(ts.deserialize(ts.serialize("a string")), "a string")
        self.assertEqual(ts.deserialize(ts.serialize(b"some bytes")), b"some bytes")
        self.assertEqual(ts.deserialize(ts.serialize((1,2,3))), (1,2,3))
        self.assertEqual(ts.deserialize(ts.serialize({"key":"value"})), {"key":"value"})
        self.assertEqual(ts.deserialize(ts.serialize([1,2,3])), [1,2,3])
        self.assertEqual(ts.deserialize(ts.serialize([1,2,3])), [1,2,3])
        self.assertEqual(ts.deserialize(ts.serialize(int)), int)
        self.assertEqual(ts.deserialize(ts.serialize(object)), object)
        self.assertEqual(ts.deserialize(ts.serialize(type)), type)

    def test_serialize_recursive_list(self):
        ts = TypeSet()

        l = []
        l.append(l)

        l_alt = ts.deserialize(ts.serialize(l))
        self.assertIs(l_alt[0], l_alt)

    def test_serialize_recursive_dict(self):
        ts = TypeSet()

        d = {}
        d[0] = d

        d_alt = ts.deserialize(ts.serialize(d))
        self.assertIs(d_alt[0], d_alt)

    def test_serialize_memoizes_tuples(self):
        ts = TypeSet()

        l = (1,2,3)
        for i in range(100):
            l = (l,l)
            self.assertTrue(len(ts.serialize(l)) < (i+1) * 100)

    def test_serialize_objects(self):
        class AnObject:
            def __init__(self, o):
                self.o = o

        ts = TypeSet({'O': AnObject})

        o = AnObject(123)

        o2 = ts.deserialize(ts.serialize(o))

        self.assertIsInstance(o2, AnObject)
        self.assertEqual(o2.o, 123)

    def test_serialize_recursive_object(self):
        class AnObject:
            def __init__(self, o):
                self.o = o

        ts = TypeSet({'O': AnObject})

        o = AnObject(None)
        o.o = o

        o2 = ts.deserialize(ts.serialize(o))
        self.assertIs(o2.o.o, o2.o)

    def test_serialize_primitive_native_types(self):
        ts = TypeSet()
        for t in [Int64, Float64, Bool, NoneType, String, Bytes]:
            self.assertIs(ts.deserialize(ts.serialize(t())), t())

    def test_serialize_primitive_compound_types(self):
        class A:
            pass

        B = Alternative("B", X={'a': A})

        ts = TypeSet({'A': A, 'B': B})

        for t in [  ConstDict(int, float), 
                    NamedTuple(x=int, y=str), 
                    TupleOf(bool), 
                    Tuple(int,int,bool),
                    OneOf(int,float),
                    OneOf(1,2,3,"hi",b"goodbye"),
                    TupleOf(NamedTuple(x=int)),
                    TupleOf(object),
                    TupleOf(A),
                    TupleOf(B)
                    ]:
            self.assertIs(ts.deserialize(ts.serialize(t)), t)


