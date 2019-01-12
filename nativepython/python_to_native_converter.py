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

import typed_python.python_ast as python_ast
import typed_python.ast_util as ast_util

import nativepython
import nativepython.native_ast as native_ast
from nativepython.type_wrappers.none_wrapper import NoneWrapper
from nativepython.python_object_representation import pythonObjectRepresentation, typedPythonTypeToTypeWrapper
from nativepython.typed_expression import TypedExpression
from nativepython.conversion_exception import ConversionException
from nativepython.function_conversion_context import FunctionConversionContext, FunctionOutput

NoneExprType = NoneWrapper()

from typed_python import *

typeWrapper = lambda t: nativepython.python_object_representation.typedPythonTypeToTypeWrapper(t)

class TypedCallTarget(object):
    def __init__(self, named_call_target, input_types, output_type):
        super().__init__()

        self.named_call_target = named_call_target
        self.input_types = input_types
        self.output_type = output_type

    def call(self, *args):
        return native_ast.CallTarget.Named(target=self.named_call_target).call(*args)

    @property
    def name(self):
        return self.named_call_target.name

    def __str__(self):
        return "TypedCallTarget(name=%s,inputs=%s,outputs=%s)" % (
            self.name,
            [str(x) for x in self.input_types],
            str(self.output_type)
            )

class PythonToNativeConverter(object):
    def __init__(self):
        object.__init__(self)
        self._names_for_identifier = {}
        self._definitions = {}
        self._targets = {}
        self._typeids = {}

        self._unconverted = set()

        self.verbose = False

    def get_typeid(self, t):
        if t in self._typeids:
            return self._typeids[t]

        self._typeids[t] = len(self._typeids) + 1024

        return self._typeids[t]

    def extract_new_function_definitions(self):
        res = {}

        for u in self._unconverted:
            res[u] = self._definitions[u]

            if self.verbose:
                print(self._targets[u])

        self._unconverted = set()

        return res

    def new_name(self, name, prefix="py."):
        suffix = None
        getname = lambda: prefix + name + ("" if suffix is None else ".%s" % suffix)
        while getname() in self._targets:
            suffix = 1 if not suffix else suffix+1
        return getname()

    def convert_function_ast(
                self,
                ast_arg,
                statements,
                input_types,
                local_variables,
                free_variable_lookup,
                output_type
                ):
        functionConverter = FunctionConversionContext(self, ast_arg, statements, input_types, output_type, free_variable_lookup)

        while True:
            #repeatedly try converting as long as the types keep getting bigger.
            nativeFunction = functionConverter.convertToNativeFunction()

            if functionConverter.typesAreUnstable():
                functionConverter.resetTypeInstabilityFlag()
            else:
                return nativeFunction

    def convert_lambda_ast(self, ast, input_types, local_variables, free_variable_lookup, output_type):
        return self.convert_function_ast(
            ast.args,
            [python_ast.Statement.Return(
                value=ast.body,
                line_number=ast.body.line_number,
                col_offset=ast.body.col_offset,
                filename=ast.body.filename
                )],
            input_types,
            local_variables,
            free_variable_lookup,
            output_type
            )

    def defineNativeFunction(self, name, identity, input_types, output_type, generatingFunction):
        """Define a native function if we haven't defined it before already.

            name - the name to actually give the function.
            identity - a unique identifier for this function to allow us to cache it.
            input_types - list of Wrapper objects for the incoming types
            output_ype - Wrapper object for the output type.
            generatingFunction - a function producing a native_function_definition

        returns a TypedCallTarget. 'generatingFunction' may call this recursively if it wants.
        """
        identity = ("native", identity)

        if identity in self._names_for_identifier:
            return self._targets[self._names_for_identifier[identity]]

        new_name = self.new_name(name, "runtime.")

        self._names_for_identifier[identity] = new_name

        native_input_types = [t.getNativePassingType() for t in input_types]

        if output_type.is_pass_by_ref:
            #the first argument is actually the output
            native_output_type = native_ast.Void
            native_input_types = [output_type.getNativePassingType()] + native_input_types
        else:
            native_output_type = output_type.getNativeLayoutType()

        self._targets[new_name] = TypedCallTarget(
            native_ast.NamedCallTarget(
                name=new_name,
                arg_types=native_input_types,
                output_type=native_output_type,
                external=False,
                varargs=False,
                intrinsic=False,
                can_throw=True
                ),
            input_types,
            output_type
            )

        self._definitions[new_name] = generatingFunction()
        self._unconverted.add(new_name)

        return self._targets[new_name]

    def define(self, identifier, name, input_types, output_type, native_function_definition):
        identifier = ("defined", identifier)

        if identifier in self._names_for_identifier:
            name = self._names_for_identifier[identifier]

            return self._targets[name]

        new_name = self.new_name(name)
        self._names_for_identifier[identifier] = new_name

        self._targets[new_name] = TypedCallTarget(
            native_ast.NamedCallTarget(
                name=new_name,
                arg_types=[x[1] for x in native_function_definition.args],
                output_type=native_function_definition.output_type,
                external=False,
                varargs=False,
                intrinsic=False,
                can_throw=True
                ),
            input_types,
            output_type
            )

        self._definitions[new_name] = native_function_definition
        self._unconverted.add(new_name)

        return self._targets[new_name]

    def callable_to_ast_and_vars(self, f):
        pyast = ast_util.pyAstFor(f)

        _, lineno = ast_util.getSourceLines(f)
        _, fname = ast_util.getSourceFilenameAndText(f)

        pyast = ast_util.functionDefOrLambdaAtLineNumber(pyast, lineno)

        pyast = python_ast.convertPyAstToAlgebraic(pyast, fname)

        freevars = dict(f.__globals__)

        if f.__closure__:
            for i in range(len(f.__closure__)):
                freevars[f.__code__.co_freevars[i]] = f.__closure__[i].cell_contents

        return pyast, freevars

    def generateCallConverter(self, callTarget):
        """Given a call target that's optimized for C-style dispatch, produce a (native) call-target that
        we can dispatch to from our C extension.

        we are given
            T f(A1, A2, A3 ...)
        and want to produce
            f(T*, X**)
        where X is the union of A1, A2, etc.

        returns the name of the defined native function
        """
        identifier = ("call_converter", callTarget.name)

        if identifier in self._names_for_identifier:
            return self._names_for_identifier[identifier]

        underlyingDefinition = self._definitions[callTarget.name]

        args = []
        for i in range(len(callTarget.input_types)):
            argtype = callTarget.input_types[i].getNativeLayoutType()

            untypedPtr = native_ast.var('input').ElementPtrIntegers(i).load()

            if callTarget.input_types[i].is_pass_by_ref:
                #we've been handed a pointer, and it's already a pointer
                args.append(untypedPtr.cast(argtype.pointer()))
            else:
                args.append(untypedPtr.cast(argtype.pointer()).load())

        if callTarget.output_type.is_pass_by_ref:
            body = callTarget.call(
                native_ast.var('return').cast(callTarget.output_type.getNativeLayoutType().pointer()),
                *args
                )
        else:
            body = callTarget.call(*args)

            if not callTarget.output_type.is_empty:
                body = native_ast.var('return').cast(callTarget.output_type.getNativeLayoutType().pointer()).store(body)

        body = native_ast.FunctionBody.Internal(body=body)

        definition = native_ast.Function(
            args=(
                ('return', native_ast.Type.Void().pointer()),
                ('input', native_ast.Type.Void().pointer().pointer())
                ),
            body=body,
            output_type=native_ast.Type.Void()
            )

        new_name = self.new_name(callTarget.name + ".dispatch")
        self._names_for_identifier[identifier] = new_name

        self._definitions[new_name] = definition
        self._unconverted.add(new_name)

        return new_name

    def convert(self, f, input_types, output_type):
        input_types = tuple([typedPythonTypeToTypeWrapper(i) for i in input_types])

        identifier = ("pyfunction", f, input_types)

        if identifier in self._names_for_identifier:
            name = self._names_for_identifier[identifier]
            return self._targets[name]

        pyast, freevars = self.callable_to_ast_and_vars(f)

        if isinstance(pyast, python_ast.Statement.FunctionDef):
            definition, output_type = \
                self.convert_function_ast(
                    pyast.args,
                    pyast.body,
                    input_types,
                    f.__code__.co_varnames,
                    freevars,
                    output_type
                    )
        else:
            assert pyast.matches.Lambda

            definition,output_type = self.convert_lambda_ast(pyast, input_types, f.__code__.co_varnames, freevars, output_type)

        assert definition is not None

        new_name = self.new_name(f.__name__)

        self._names_for_identifier[identifier] = new_name

        self._targets[new_name] = TypedCallTarget(
            native_ast.NamedCallTarget(
                name=new_name,
                arg_types=[x[1] for x in definition.args],
                output_type=definition.output_type,
                external=False,
                varargs=False,
                intrinsic=False,
                can_throw=True
                ),
            input_types,
            output_type
            )

        self._definitions[new_name] = definition
        self._unconverted.add(new_name)

        return self._targets[new_name]
