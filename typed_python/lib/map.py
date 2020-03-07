#   Copyright 2020 typed_python Authors
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

from typed_python._types import Tuple, NamedTuple, OneOf
from typed_python.compiler.type_wrappers.compilable_builtin import CompilableBuiltin
import typed_python.compiler

typeWrapper = lambda t: typed_python.compiler.python_object_representation.typedPythonTypeToTypeWrapper(t)


class Map(CompilableBuiltin):
    def __eq__(self, other):
        return isinstance(other, Map)

    def __hash__(self):
        return hash("Map")

    def __call__(self, f, tup):
        if isinstance(tup, (Tuple, NamedTuple)):
            return self.mapTuple(f, tup)

        raise TypeError("Currently, 'map' only works on typed python Tuple or NamedTuple objects")

    def mapTuple(self, f, tup):
        outElts = []

        for elt in tup:
            outElts.append(f(elt))

        outTypes = [type(elt) for elt in outElts]

        if isinstance(tup, NamedTuple):
            return NamedTuple(**{tup.ElementNames[i]: outTypes[i] for i in range(len(outTypes))})(outElts)
        else:
            return Tuple(*outTypes)(outElts)

    def convert_call(self, context, expr, args, kwargs):
        if len(args) != 2 or len(kwargs):
            context.pushException(TypeError, "map takes two positional arguments: 'f' and 'iterable'")
            return

        argT = args[1].expr_type.typeRepresentation

        if isinstance(argT, type) and issubclass(argT, (NamedTuple, Tuple)):
            return self.convert_call_on_tuple(context, args[0], args[1])

        context.pushException(TypeError, "Currently, 'map' only works on typed python Tuple or NamedTuple objects")

    def convert_call_on_tuple(self, context, fArg, tupArg):
        resArgs = []
        resTypes = []

        argT = tupArg.expr_type.typeRepresentation

        for i in range(len(argT.ElementTypes)):
            resArgs.append(fArg.convert_call((tupArg.refAs(i),), {}))

            if resArgs[-1] is None:
                return None

            resTypes.append(resArgs[-1].expr_type.interpreterTypeRepresentation)

            assert not issubclass(resTypes[-1], OneOf), "OneOf types not supported in compiled 'map'"

        if issubclass(argT, NamedTuple):
            outTupType = NamedTuple(**{argT.ElementNames[i]: resTypes[i] for i in range(len(resTypes))})
        else:
            outTupType = Tuple(*resTypes)

        return typeWrapper(outTupType).createFromArgs(context, resArgs)


map = Map()
