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

from typed_python._types import Int8, NoneType, TupleOf
import typed_python._types as _types

import unittest
import time

class NativeTypesTests(unittest.TestCase):
    def test_objects_are_singletons(self):
        self.assertTrue(Int8() is Int8())
        self.assertTrue(NoneType() is NoneType())

    def test_object_bytecounts(self):
        self.assertEqual(NoneType().bytecount(), 0)
        self.assertEqual(Int8().bytecount(), 1)

    def test_type_stringification(self):
        for t in ['Int8', 'NoneType']:
            self.assertEqual(str(getattr(_types,t)()), "<class '%s'>" % t)

    def test_tuple_of(self):
        tupleOfInt = TupleOf(int)
        i = tupleOfInt(())
        i = tupleOfInt((1,2,3))

        self.assertEqual(len(i), 3)
        self.assertEqual(tuple(i), (1,2,3))

        for x in range(10):
            self.assertEqual(tuple(tupleOfInt(tuple(range(x)))), tuple(range(x)))

    def test_tuple_of_tuple_of(self):
        tupleOfInt = TupleOf(int)
        tupleOfTupleOfInt = TupleOf(tupleOfInt)

        pyVersion = (1,2,3),(1,2,3,4)
        nativeVersion = tupleOfTupleOfInt(pyVersion)

        self.assertEqual(len(nativeVersion), 2)
        self.assertEqual(len(nativeVersion[0]), 3)
        self.assertEqual(tuple(tuple(x) for x in nativeVersion), pyVersion)

        bigTup = tupleOfInt(list(range(1000)))

        t0 = time.time()
        t = (bigTup,bigTup,bigTup,bigTup,bigTup)
        for i in range(1000000):
            tupleOfTupleOfInt(t)
        print(time.time() - t0, " to do 1mm")

        #like 5mm/sec
        self.assertTrue(time.time() - t0 < 1.0)