/******************************************************************************
   Copyright 2017-2019 typed_python Authors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
******************************************************************************/

#include "PyFunctionInstance.hpp"
#include "FunctionCallArgMapping.hpp"
#include "TypedClosureBuilder.hpp"

Function* PyFunctionInstance::type() {
    return (Function*)extractTypeFrom(((PyObject*)this)->ob_type);
}

// static
PyObject* PyFunctionInstance::prepareArgumentToBePassedToCompiler(PyObject* o) {
    TypedClosureBuilder builder;

    if (builder.isFunctionObject(o)) {
        return incref(builder.convert(o));
    }

    return incref(o);
}

// static
std::pair<bool, PyObject*>
PyFunctionInstance::tryToCallAnyOverload(const Function* f, instance_ptr funcClosure, PyObject* self,
                                         PyObject* args, PyObject* kwargs) {
    //if we are an entrypoint, map any untyped function arguments to typed functions
    PyObjectHolder mappedArgs;
    PyObjectHolder mappedKwargs;

    if (f->isEntrypoint()) {
        mappedArgs.steal(PyTuple_New(PyTuple_Size(args)));

        for (long k = 0; k < PyTuple_Size(args); k++) {
            PyTuple_SetItem(mappedArgs, k, prepareArgumentToBePassedToCompiler(PyTuple_GetItem(args, k)));
        }

        mappedKwargs.steal(PyDict_New());

        if (kwargs) {
            PyObject *key, *value;
            Py_ssize_t pos = 0;

            while (PyDict_Next(kwargs, &pos, &key, &value)) {
                PyObjectStealer mapped(prepareArgumentToBePassedToCompiler(value));
                PyDict_SetItem(mappedKwargs, key, mapped);
            }
        }
    } else {
        mappedArgs.set(args);
        mappedKwargs.set(kwargs);
    }

    //first try to match arguments with no explicit conversion.
    //if that fails, try explicit conversion
    for (long tryToConvertExplicitly = 0; tryToConvertExplicitly <= 1; tryToConvertExplicitly++) {
        for (long overloadIx = 0; overloadIx < f->getOverloads().size(); overloadIx++) {
            std::pair<bool, PyObject*> res =
                PyFunctionInstance::tryToCallOverload(
                    f, funcClosure, overloadIx, self,
                    mappedArgs, mappedKwargs, tryToConvertExplicitly
                );

            if (res.first) {
                return res;
            }
        }
    }

    std::string argTupleTypeDesc = PyFunctionInstance::argTupleTypeDescription(self, args, kwargs);

    PyErr_Format(
        PyExc_TypeError, "Cannot find a valid overload of '%s' with arguments of type %s",
        f->name().c_str(),
        argTupleTypeDesc.c_str()
        );

    return std::pair<bool, PyObject*>(false, nullptr);
}

// static
std::pair<bool, PyObject*> PyFunctionInstance::tryToCallOverload(
        const Function* f,
        instance_ptr functionClosure,
        long overloadIx,
        PyObject* self,
        PyObject* args,
        PyObject* kwargs,
        bool convertExplicitly
) {
    const Function::Overload& overload(f->getOverloads()[overloadIx]);

    FunctionCallArgMapping mapping(overload);

    if (self) {
        mapping.pushPositionalArg(self);
    }

    for (long k = 0; k < PyTuple_Size(args); k++) {
        mapping.pushPositionalArg(PyTuple_GetItem(args, k));
    }

    if (kwargs) {
        PyObject *key, *value;
        Py_ssize_t pos = 0;

        while (PyDict_Next(kwargs, &pos, &key, &value)) {
            if (!PyUnicode_Check(key)) {
                PyErr_SetString(PyExc_TypeError, "Keywords arguments must be strings.");
                return std::make_pair(true, nullptr);
            }

            mapping.pushKeywordArg(PyUnicode_AsUTF8(key), value);
        }
    }

    mapping.finishedPushing();

    if (!mapping.isValid()) {
        return std::make_pair(false, nullptr);
    }

    //first, see if we can short-circuit without producing temporaries, which
    //can be slow.
    for (long k = 0; k < overload.getArgs().size(); k++) {
        auto arg = overload.getArgs()[k];

        if (arg.getIsNormalArg() && arg.getTypeFilter()) {
            if (!PyInstance::pyValCouldBeOfType(arg.getTypeFilter(), mapping.getSingleValueArgs()[k], convertExplicitly)) {
                return std::pair<bool, PyObject*>(false, (PyObject*)nullptr);
            }
        }
    }

    //perform argument coercion
    mapping.applyTypeCoercion(convertExplicitly);

    if (!mapping.isValid()) {
        return std::make_pair(false, nullptr);
    }

    PyObjectHolder result;

    bool hadNativeDispatch = false;

    if (!native_dispatch_disabled) {
        auto tried_and_result = dispatchFunctionCallToNative(f, functionClosure, overloadIx, mapping);
        hadNativeDispatch = tried_and_result.first;
        result.steal(tried_and_result.second);
    }

    if (!hadNativeDispatch) {
        PyObjectStealer argTup(mapping.buildPositionalArgTuple());
        PyObjectStealer kwargD(mapping.buildKeywordArgTuple());
        PyObjectStealer funcObj(
            overload.buildFunctionObj(
                f->getClosureType(),
                functionClosure
            )
        );

        result.steal(PyObject_Call((PyObject*)funcObj, (PyObject*)argTup, (PyObject*)kwargD));
    }

    //exceptions pass through directly
    if (!result) {
        return std::make_pair(true, result);
    }

    //force ourselves to convert to the native type
    if (overload.getReturnType()) {
        try {
            PyObject* newRes = PyInstance::initializePythonRepresentation(overload.getReturnType(), [&](instance_ptr data) {
                copyConstructFromPythonInstance(overload.getReturnType(), data, result, true);
            });

            return std::make_pair(true, newRes);
        } catch (std::exception& e) {
            PyErr_SetString(PyExc_TypeError, e.what());
            return std::make_pair(true, (PyObject*)nullptr);
        }
    }

    return std::make_pair(true, incref(result));
}

std::pair<bool, PyObject*> PyFunctionInstance::tryToCall(const Function* f, instance_ptr closure, PyObject* arg0, PyObject* arg1, PyObject* arg2) {
    PyObjectStealer argTuple(
        (arg0 && arg1 && arg2) ?
            PyTuple_Pack(3, arg0, arg1, arg2) :
        (arg0 && arg1) ?
            PyTuple_Pack(2, arg0, arg1) :
        arg0 ?
            PyTuple_Pack(1, arg0) :
            PyTuple_Pack(0)
        );
    return PyFunctionInstance::tryToCallAnyOverload(f, closure, nullptr, argTuple, nullptr);
}

// static
std::pair<bool, PyObject*> PyFunctionInstance::dispatchFunctionCallToNative(
        const Function* f,
        instance_ptr functionClosure,
        long overloadIx,
        const FunctionCallArgMapping& mapper
    ) {
    const Function::Overload& overload(f->getOverloads()[overloadIx]);

    for (const auto& spec: overload.getCompiledSpecializations()) {
        auto res = dispatchFunctionCallToCompiledSpecialization(
            overload,
            f->getClosureType(),
            functionClosure,
            spec,
            mapper
        );

        if (res.first) {
            return res;
        }
    }

    if (f->isEntrypoint()) {
        // package 'f' back up as an object and pass it to the closure-type-generator.
        // otherwise when we call this in the compiler, we'll have PyCell objects
        // instead of proper closures
        PyObjectStealer fAsObj(PyInstance::extractPythonObject(functionClosure, (Type*)f));
        PyObjectStealer fConvertedAsObj(prepareArgumentToBePassedToCompiler(fAsObj));

        // convert the object back to a function
        Type* convertedFType = PyInstance::extractTypeFrom(fConvertedAsObj->ob_type);
        if (!convertedFType || convertedFType->getTypeCategory() != Type::TypeCategory::catFunction) {
            throw std::runtime_error("prepareArgumentToBePassedToCompiler returned a non-function!");
        }

        Function* convertedF = (Function*)convertedFType;
        instance_ptr convertedFData = ((PyInstance*)(PyObject*)fConvertedAsObj)->dataPtr();

        static PyObject* runtimeModule = PyImport_ImportModule("typed_python.compiler.runtime");

        if (!runtimeModule) {
            throw std::runtime_error("Internal error: couldn't find typed_python.compiler.runtime");
        }

        PyObject* runtimeClass = PyObject_GetAttrString(runtimeModule, "Runtime");

        if (!runtimeClass) {
            throw std::runtime_error("Internal error: couldn't find typed_python.compiler.runtime.Runtime");
        }

        PyObject* singleton = PyObject_CallMethod(runtimeClass, "singleton", "");

        if (!singleton) {
            if (PyErr_Occurred()) {
                PyErr_Clear();
            }

            throw std::runtime_error("Internal error: couldn't call typed_python.compiler.runtime.Runtime.singleton");
        }

        PyObjectStealer arguments(mapper.extractFunctionArgumentValues());

        PyObject* res = PyObject_CallMethod(
            singleton,
            "compileFunctionOverload",
            "OlO",
            PyInstance::typePtrToPyTypeRepresentation((Type*)convertedF),
            overloadIx,
            (PyObject*)arguments
        );

        if (!res) {
            throw PythonExceptionSet();
        }

        decref(res);

        const Function::Overload& convertedOverload(convertedF->getOverloads()[overloadIx]);

        for (const auto& spec: convertedOverload.getCompiledSpecializations()) {
            auto res = dispatchFunctionCallToCompiledSpecialization(
                convertedOverload,
                convertedF->getClosureType(),
                convertedFData,
                spec,
                mapper
            );

            if (res.first) {
                return res;
            }
        }

        throw std::runtime_error("Compiled but then failed to dispatch!");
    }

    return std::pair<bool, PyObject*>(false, (PyObject*)nullptr);
}

std::pair<bool, PyObject*> PyFunctionInstance::dispatchFunctionCallToCompiledSpecialization(
                                                        const Function::Overload& overload,
                                                        Type* closureType,
                                                        instance_ptr closureData,
                                                        const Function::CompiledSpecialization& specialization,
                                                        const FunctionCallArgMapping& mapper
                                                        ) {
    Type* returnType = specialization.getReturnType();

    if (!returnType) {
        throw std::runtime_error("Malformed function specialization: missing a return type.");
    }

    std::vector<Instance> instances;

    // first, see if we can short-circuit
    for (long k = 0; k < overload.getArgs().size(); k++) {
        auto arg = overload.getArgs()[k];
        if (arg.getIsNormalArg()) {
            Type* argType = specialization.getArgTypes()[k];

            if (!PyInstance::pyValCouldBeOfType(argType, mapper.getSingleValueArgs()[k], false)) {
                return std::pair<bool, PyObject*>(false, (PyObject*)nullptr);
            }
        }
    }

    for (long k = 0; k < overload.getArgs().size(); k++) {
        auto arg = overload.getArgs()[k];
        Type* argType = specialization.getArgTypes()[k];

        std::pair<Instance, bool> res = mapper.extractArgWithType(k, argType);

        if (res.second) {
            instances.push_back(res.first);
        } else {
            return std::pair<bool, PyObject*>(false, (PyObject*)nullptr);
        }
    }

    Instance result = Instance::createAndInitialize(returnType, [&](instance_ptr returnData) {
        std::vector<Instance> closureCells;

        std::vector<instance_ptr> args;

        // we pass each closure variable first (sorted lexically), then the actual function arguments.
        for (auto nameAndPath: overload.getClosureVariableBindings()) {
            closureCells.push_back(nameAndPath.second.extractValueOrContainingClosure(closureType, closureData));
            args.push_back(closureCells.back().data());
        }

        for (auto& i: instances) {
            args.push_back(i.data());
        }

        auto functionPtr = specialization.getFuncPtr();

        PyEnsureGilReleased releaseTheGIL;

        try {
            functionPtr(returnData, &args[0]);
        }
        catch(...) {
            // exceptions coming out of compiled code always use the python interpreter
            throw PythonExceptionSet();
        }
    });

    return std::pair<bool, PyObject*>(true, (PyObject*)extractPythonObject(result.data(), result.type()));
}


// static
PyObject* PyFunctionInstance::createOverloadPyRepresentation(Function* f) {
    static PyObject* internalsModule = PyImport_ImportModule("typed_python.internals");

    if (!internalsModule) {
        throw std::runtime_error("Internal error: couldn't find typed_python.internals");
    }

    static PyObject* funcOverload = PyObject_GetAttrString(internalsModule, "FunctionOverload");

    if (!funcOverload) {
        throw std::runtime_error("Internal error: couldn't find typed_python.internals.FunctionOverload");
    }

    static PyObject* closureVariableCellLookupSingleton = PyObject_GetAttrString(internalsModule, "CellAccess");

    if (!closureVariableCellLookupSingleton) {
        throw std::runtime_error("Internal error: couldn't find typed_python.internals.CellAccess");
    }

    PyObjectStealer overloadTuple(PyTuple_New(f->getOverloads().size()));

    for (long k = 0; k < f->getOverloads().size(); k++) {
        auto& overload = f->getOverloads()[k];

        PyObjectStealer pyIndex(PyLong_FromLong(k));

        PyObjectStealer pyGlobalCellDict(PyDict_New());

        for (auto nameAndCell: overload.getFunctionGlobalsInCells()) {
            PyDict_SetItemString(pyGlobalCellDict, nameAndCell.first.c_str(), nameAndCell.second);
        }

        PyObjectStealer pyClosureVarsDict(PyDict_New());

        for (auto nameAndClosureVar: overload.getClosureVariableBindings()) {
            PyObjectStealer bindingObj(PyList_New(0));
            for (long k = 0; k < nameAndClosureVar.second.size(); k++) {
                ClosureVariableBindingStep step = nameAndClosureVar.second[k];

                if (step.isFunction()) {
                    PyList_Append(bindingObj, (PyObject*)typePtrToPyTypeRepresentation(step.getFunction()));
                } else
                if (step.isNamedField()) {
                    PyObjectStealer nameAsObj(PyUnicode_FromString(step.getNamedField().c_str()));
                    PyList_Append(bindingObj, nameAsObj);
                } else
                if (step.isIndexedField()) {
                    PyObjectStealer indexAsObj(PyLong_FromLong(step.getIndexedField()));
                    PyList_Append(bindingObj, indexAsObj);
                } else
                if (step.isCellAccess()) {
                    PyList_Append(bindingObj, closureVariableCellLookupSingleton);
                } else {
                    throw std::runtime_error("Corrupt ClosureVariableBindingStep encountered");
                }
            }

            PyDict_SetItemString(pyClosureVarsDict, nameAndClosureVar.first.c_str(), bindingObj);
        }

        PyObjectStealer pyOverloadInst(
            //PyObject_CallFunctionObjArgs is a macro, so we have to force all the 'stealers'
            //to have type (PyObject*)
            PyObject_CallFunctionObjArgs(
                funcOverload,
                typePtrToPyTypeRepresentation(f),
                (PyObject*)pyIndex,
                (PyObject*)overload.getFunctionCode(),
                (PyObject*)overload.getFunctionGlobals(),
                (PyObject*)pyGlobalCellDict,
                (PyObject*)pyClosureVarsDict,
                overload.getReturnType() ? (PyObject*)typePtrToPyTypeRepresentation(overload.getReturnType()) : Py_None,
                NULL
                )
            );

        if (pyOverloadInst) {
            for (auto arg: f->getOverloads()[k].getArgs()) {
                PyObjectStealer res(
                    PyObject_CallMethod(
                        (PyObject*)pyOverloadInst,
                        "addArg",
                        "sOOOO",
                        arg.getName().c_str(),
                        arg.getDefaultValue() ? PyTuple_Pack(1, arg.getDefaultValue()) : Py_None,
                        arg.getTypeFilter() ? (PyObject*)typePtrToPyTypeRepresentation(arg.getTypeFilter()) : Py_None,
                        arg.getIsStarArg() ? Py_True : Py_False,
                        arg.getIsKwarg() ? Py_True : Py_False
                        )
                    );

                if (!res) {
                    PyErr_PrintEx(0);
                }
            }

            PyTuple_SetItem(overloadTuple, k, incref(pyOverloadInst));
        } else {
            PyErr_PrintEx(0);
            PyTuple_SetItem(overloadTuple, k, incref(Py_None));
        }
    }

    return incref(overloadTuple);
}

PyObject* PyFunctionInstance::tp_call_concrete(PyObject* args, PyObject* kwargs) {
    return PyFunctionInstance::tryToCallAnyOverload(type(), dataPtr(), nullptr, args, kwargs).second;
}

std::string PyFunctionInstance::argTupleTypeDescription(PyObject* self, PyObject* args, PyObject* kwargs) {
    std::ostringstream outTypes;
    outTypes << "(";
    bool first = true;

    if (self) {
        outTypes << self->ob_type->tp_name;
        first = false;
    }

    for (long k = 0; k < PyTuple_Size(args); k++) {
        if (!first) {
            outTypes << ",";
        } else {
            first = false;
        }
        outTypes << PyTuple_GetItem(args,k)->ob_type->tp_name;
    }
    if (kwargs) {
        PyObject *key, *value;
        Py_ssize_t pos = 0;

        while (kwargs && PyDict_Next(kwargs, &pos, &key, &value)) {
            if (!first) {
                outTypes << ",";
            } else {
                first = false;
            }
            outTypes << PyUnicode_AsUTF8(key) << "=" << value->ob_type->tp_name;
        }
    }

    outTypes << ")";

    return outTypes.str();
}

void PyFunctionInstance::mirrorTypeInformationIntoPyTypeConcrete(Function* inType, PyTypeObject* pyType) {
    //expose a list of overloads
    PyObjectStealer overloads(createOverloadPyRepresentation(inType));

    PyDict_SetItemString(
        pyType->tp_dict,
        "__name__",
        PyUnicode_FromString(inType->name().c_str())
    );

    PyDict_SetItemString(
        pyType->tp_dict,
        "__qualname__",
        PyUnicode_FromString(inType->name().c_str())
    );

    PyDict_SetItemString(
        pyType->tp_dict,
        "overloads",
        overloads
    );

    PyDict_SetItemString(
        pyType->tp_dict,
        "ClosureType",
        PyInstance::typePtrToPyTypeRepresentation(inType->getClosureType())
    );

    PyDict_SetItemString(
        pyType->tp_dict,
        "isEntrypoint",
        inType->isEntrypoint() ? Py_True : Py_False
    );
}

int PyFunctionInstance::pyInquiryConcrete(const char* op, const char* opErrRep) {
    // op == '__bool__'
    return 1;
}

/* static */
PyObject* PyFunctionInstance::extractPyFun(PyObject* funcObj, PyObject* args, PyObject* kwargs) {
    static const char *kwlist[] = {"overloadIx", NULL};

    long overloadIx;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "l", (char**)kwlist, &overloadIx)) {
        return nullptr;
    }

    Function* fType = (Function*)((PyInstance*)(funcObj))->type();

    if (overloadIx < 0 || overloadIx >= fType->getOverloads().size()) {
        PyErr_SetString(PyExc_IndexError, "Overload index out of bounds");
        return nullptr;
    }

    return translateExceptionToPyObject([&]() {
        return fType->getOverloads()[overloadIx].buildFunctionObj(
            fType->getClosureType(),
            ((PyInstance*)funcObj)->dataPtr()
        );
    });
}

/* static */
PyObject* PyFunctionInstance::getClosure(PyObject* funcObj, PyObject* args, PyObject* kwargs) {
    static const char *kwlist[] = {NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "", (char**)kwlist)) {
        return nullptr;
    }

    Function* fType = (Function*)((PyInstance*)(funcObj))->type();

    return PyInstance::extractPythonObject(((PyInstance*)funcObj)->dataPtr(), fType->getClosureType());
}

/* static */
PyObject* PyFunctionInstance::withEntrypoint(PyObject* funcObj, PyObject* args, PyObject* kwargs) {
    static const char *kwlist[] = {"isEntrypoint", NULL};
    int isWithEntrypoint;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "p", (char**)kwlist, &isWithEntrypoint)) {
        return nullptr;
    }

    Function* resType = (Function*)((PyInstance*)(funcObj))->type();

    resType = resType->withEntrypoint(isWithEntrypoint);

    return PyInstance::extractPythonObject(((PyInstance*)funcObj)->dataPtr(), resType);
}

/* static */
PyObject* PyFunctionInstance::overload(PyObject* funcObj, PyObject* args, PyObject* kwargs) {
    return translateExceptionToPyObject([&]() {
        if (kwargs && PyDict_Size(kwargs)) {
            throw std::runtime_error("Can't call 'overload' with kwargs");
        }

        if (PyTuple_Size(args) != 1) {
            throw std::runtime_error("'overload' expects one argument");
        }

        Function* ownType = (Function*)((PyInstance*)(funcObj))->type();
        instance_ptr ownClosure = ((PyInstance*)(funcObj))->dataPtr();

        if (!ownType || ownType->getTypeCategory() != Type::TypeCategory::catFunction) {
            throw std::runtime_error("Expected 'cls' to be a Function.");
        }

        PyObject* arg = PyTuple_GetItem(args, 0);

        Type* argT = PyInstance::extractTypeFrom(arg->ob_type);
        Instance otherFuncAsInstance;

        Function* otherType;
        instance_ptr otherClosure;

        if (!argT) {
            argT = PyInstance::unwrapTypeArgToTypePtr(arg);

            if (!argT && PyFunction_Check(arg)) {
                // unwrapTypeArgToTypePtr sets an exception if it can't convert.
                // we want to clear it so we can try the unwrapping directly.
                PyErr_Clear();

                PyObjectStealer name(PyObject_GetAttrString(arg, "__name__"));
                if (!name) {
                    throw PythonExceptionSet();
                }

                argT = convertPythonObjectToFunctionType(name, arg, false, false);
            }

            if (!argT) {
                throw PythonExceptionSet();
            }

            otherFuncAsInstance = Instance::createAndInitialize(
                argT,
                [&](instance_ptr ptr) {
                    PyInstance::copyConstructFromPythonInstance(argT, ptr, arg, true);
                }
            );

            otherType = (Function*)argT;
            otherClosure = otherFuncAsInstance.data();
        } else {
            if (argT->getTypeCategory() != Type::TypeCategory::catFunction) {
                throw std::runtime_error("'overload' requires arguments to be Function types");
            }
            otherType = (Function*)argT;
            otherClosure = ((PyInstance*)arg)->dataPtr();
        }

        Function* mergedType = Function::merge(ownType, otherType);

        // closures are packed in
        return PyInstance::initialize(mergedType, [&](instance_ptr p) {
            ownType->getClosureType()->copy_constructor(p, ownClosure);
            otherType->getClosureType()->copy_constructor(
                p + ownType->getClosureType()->bytecount(),
                otherClosure
            );
        });
    });
}

/* static */
PyObject* PyFunctionInstance::resultTypeFor(PyObject* funcObj, PyObject* args, PyObject* kwargs) {
    static PyObject* runtimeModule = PyImport_ImportModule("typed_python.compiler.runtime");

    if (!runtimeModule) {
        throw std::runtime_error("Internal error: couldn't find typed_python.compiler.runtime");
    }

    static PyObject* runtimeClass = PyObject_GetAttrString(runtimeModule, "Runtime");

    if (!runtimeClass) {
        throw std::runtime_error("Internal error: couldn't find typed_python.compiler.runtime.Runtime");
    }

    static PyObject* singleton = PyObject_CallMethod(runtimeClass, "singleton", "");

    if (!singleton) {
        if (PyErr_Occurred()) {
            PyErr_Clear();
        }

        throw std::runtime_error("Internal error: couldn't call typed_python.compiler.runtime.Runtime.singleton");
    }

    if (!kwargs) {
        static PyObject* emptyDict = PyDict_New();
        kwargs = emptyDict;
    }

    return PyObject_CallMethod(
        singleton,
        "resultTypeForCall",
        "OOO",
        funcObj,
        args,
        kwargs
    );
}

/* static */
PyMethodDef* PyFunctionInstance::typeMethodsConcrete(Type* t) {
    return new PyMethodDef[8] {
        {"overload", (PyCFunction)PyFunctionInstance::overload, METH_VARARGS | METH_KEYWORDS, NULL},
        {"withEntrypoint", (PyCFunction)PyFunctionInstance::withEntrypoint, METH_VARARGS | METH_KEYWORDS, NULL},
        {"resultTypeFor", (PyCFunction)PyFunctionInstance::resultTypeFor, METH_VARARGS | METH_KEYWORDS, NULL},
        {"extractPyFun", (PyCFunction)PyFunctionInstance::extractPyFun, METH_VARARGS | METH_KEYWORDS, NULL},
        {"getClosure", (PyCFunction)PyFunctionInstance::getClosure, METH_VARARGS | METH_KEYWORDS, NULL},
        {"withClosureType", (PyCFunction)PyFunctionInstance::withClosureType, METH_VARARGS | METH_KEYWORDS | METH_CLASS, NULL},
        {"withOverloadVariableBindings", (PyCFunction)PyFunctionInstance::withOverloadVariableBindings, METH_VARARGS | METH_KEYWORDS | METH_CLASS, NULL},
        {NULL, NULL}
    };
}

PyObject* PyFunctionInstance::withClosureType(PyObject* cls, PyObject* args, PyObject* kwargs) {
    static const char *kwlist[] = {"newType", NULL};

    PyObject* newType;

    if (!PyArg_ParseTupleAndKeywords(args, NULL, "O", (char**)kwlist, &newType)) {
        return nullptr;
    }

    Type* newTypeAsType = PyInstance::unwrapTypeArgToTypePtr(newType);

    if (!newTypeAsType) {
        PyErr_Format(PyExc_TypeError, "Expected a typed-python Type");
        return nullptr;
    }

    Type* selfType = PyInstance::unwrapTypeArgToTypePtr(cls);

    if (!selfType || selfType->getTypeCategory() != Type::TypeCategory::catFunction) {
        PyErr_Format(PyExc_TypeError, "Expected class to be a Function");
        return nullptr;
    }

    Function* fType = (Function*)selfType;

    return PyInstance::typePtrToPyTypeRepresentation(fType->replaceClosure(newTypeAsType));
}

PyObject* PyFunctionInstance::withOverloadVariableBindings(PyObject* cls, PyObject* args, PyObject* kwargs) {
    static const char *kwlist[] = {"overloadIx", "closureVarBindings", NULL};

    PyObject* pyBindingDict;
    long overloadIx;

    if (!PyArg_ParseTupleAndKeywords(args, NULL, "lO", (char**)kwlist, &overloadIx, &pyBindingDict)) {
        return nullptr;
    }

    Type* selfType = PyInstance::unwrapTypeArgToTypePtr(cls);

    if (!selfType || selfType->getTypeCategory() != Type::TypeCategory::catFunction) {
        PyErr_Format(PyExc_TypeError, "Expected class to be a Function");
        return nullptr;
    }

    Function* fType = (Function*)selfType;

    if (!PyDict_Check(pyBindingDict)) {
        PyErr_Format(PyExc_TypeError, "Expected 'closureVarBindings' to be a dict");
        return nullptr;
    }

    PyObject *key, *value;
    Py_ssize_t pos = 0;

    std::map<std::string, ClosureVariableBinding> bindingDict;

    return translateExceptionToPyObject([&]() {
        while (PyDict_Next(pyBindingDict, &pos, &key, &value)) {
            if (!PyUnicode_Check(key)) {
                PyErr_SetString(PyExc_TypeError, "closureVarBindings keys are supposed to be strings.");
                return (PyObject*)nullptr;
            }

            ClosureVariableBinding binding;

            iterate(value, [&](PyObject* step) {
                if (PyLong_Check(step)) {
                    binding = binding + ClosureVariableBindingStep(PyLong_AsLong(step));
                } else
                if (PyUnicode_Check(step)) {
                    binding = binding + ClosureVariableBindingStep(std::string(PyUnicode_AsUTF8(step)));
                } else
                if (PyType_Check(step) && ::strcmp(((PyTypeObject*)step)->tp_name, "CellAccess") == 0) {
                    binding = binding + ClosureVariableBindingStep::AccessCell();
                } else {
                    Type* t = PyInstance::unwrapTypeArgToTypePtr(step);
                    if (t) {
                        binding = binding + ClosureVariableBindingStep(t);
                    } else {
                        throw std::runtime_error("Invalid argument to closureVarBindings.");
                    }
                }
            });

            bindingDict[PyUnicode_AsUTF8(key)] = binding;
        }

        return PyInstance::typePtrToPyTypeRepresentation(
            fType->replaceOverloadVariableBindings(overloadIx, bindingDict)
        );
    });
}

Function* PyFunctionInstance::convertPythonObjectToFunctionType(
    PyObject* name,
    PyObject *funcObj,
    bool assumeClosuresGlobal,
    bool ignoreAnnotations
) {
    typedef std::tuple<PyObject*, bool, bool> key_type;

    key_type memoKey(funcObj, assumeClosuresGlobal, ignoreAnnotations);

    static std::map<key_type, Function*> memo;

    auto memo_it = memo.find(memoKey);

    if (memo_it != memo.end()) {
        return memo_it->second;
    }

    static PyObject* internalsModule = PyImport_ImportModule("typed_python.internals");

    if (!internalsModule) {
        PyErr_SetString(PyExc_TypeError, "Internal error: couldn't find typed_python.internals");
        return nullptr;
    }

    static PyObject* makeFunctionType = PyObject_GetAttrString(internalsModule, "makeFunctionType");

    if (!makeFunctionType) {
        PyErr_SetString(PyExc_TypeError, "Internal error: couldn't find typed_python.internals.makeFunctionType");
        return nullptr;
    }

    PyObjectStealer args(PyTuple_Pack(2, name, funcObj));
    PyObjectStealer kwargs(PyDict_New());

    if (assumeClosuresGlobal) {
        PyDict_SetItemString(kwargs, "assumeClosuresGlobal", Py_True);
    }

    if (ignoreAnnotations) {
        PyDict_SetItemString(kwargs, "ignoreAnnotations", Py_True);
    }

    PyObject* fRes = PyObject_Call(makeFunctionType, args, kwargs);

    if (!fRes) {
        return nullptr;
    }

    if (!PyType_Check(fRes)) {
        PyErr_SetString(PyExc_TypeError, "Internal error: expected typed_python.internals.makeFunctionType to return a type");
        return nullptr;
    }

    Type* actualType = PyInstance::extractTypeFrom((PyTypeObject*)fRes);

    if (!actualType || actualType->getTypeCategory() != Type::TypeCategory::catFunction) {
        PyErr_Format(PyExc_TypeError, "Internal error: expected makeFunctionType to return a Function. Got %S", fRes);
        return nullptr;
    }

    memo[memoKey] = (Function*)actualType;

    return (Function*)actualType;
}

/* static */
bool PyFunctionInstance::pyValCouldBeOfTypeConcrete(Function* type, PyObject* pyRepresentation, bool isExplicit) {
    if (!PyFunction_Check(pyRepresentation)) {
        return false;
    }

    if (type->getOverloads().size() != 1) {
        return false;
    }

    return type->getOverloads()[0].getFunctionCode() == PyFunction_GetCode(pyRepresentation);
}

/* static */
void PyFunctionInstance::copyConstructFromPythonInstanceConcrete(Function* type, instance_ptr tgt, PyObject* pyRepresentation, bool isExplicit) {
    if (!pyValCouldBeOfTypeConcrete(type, pyRepresentation, isExplicit)) {
        throw std::runtime_error("Can't convert to " + type->name());
    }

    if (!type->getClosureType()->isTuple()) {
        throw std::runtime_error("expected untyped closures to be Tuples");
    }

    Tuple* containingClosureType = (Tuple*)type->getClosureType();

    if (containingClosureType->bytecount() == 0) {
        // there's nothing to do.
        return;
    }

    if (containingClosureType->getTypes().size() != 1 || !containingClosureType->getTypes()[0]->isNamedTuple()) {
        throw std::runtime_error("expected a single overload in the untyped closure");
    }

    NamedTuple* closureType = (NamedTuple*)containingClosureType->getTypes()[0];

    PyObject* pyClosure = PyFunction_GetClosure(pyRepresentation);

    if (!pyClosure || !PyTuple_Check(pyClosure) || PyTuple_Size(pyClosure) != closureType->getTypes().size()) {
        throw std::runtime_error("Expected the pyClosure to have " + format(closureType->getTypes().size()) + " cells.");
    }

    closureType->constructor(tgt, [&](instance_ptr tgtCell, int index) {
        Type* closureTypeInst = closureType->getTypes()[index];

        PyObject* cell = PyTuple_GetItem(pyClosure, index);
        if (!cell) {
            throw PythonExceptionSet();
        }

        if (!PyCell_Check(cell)) {
            throw std::runtime_error("Expected function closure to be made up of cells.");
        }

        if (closureTypeInst->getTypeCategory() == Type::TypeCategory::catPyCell) {
            // our representation in the closure is itself a PyCell, so we just reference
            // the actual cell object.
            static PyCellType* pct = PyCellType::Make();
            pct->initializeFromPyObject(tgtCell, cell);
        } else {
            if (!PyCell_GET(cell)) {
                throw std::runtime_error("Cell for " + closureType->getNames()[index] + " was empty.");
            }

            PyInstance::copyConstructFromPythonInstance(
                closureType->getTypes()[index],
                tgtCell,
                PyCell_GET(cell),
                isExplicit
            );
        }
    });
}

/* static */
std::map<
    //unresolved functions and closure variables
    std::pair<std::map<Path, Function*>, std::map<Path, Type*> >,
    //the closure type and the resolved function types
    std::tuple<Type*, std::map<Path, size_t>, std::map<Path, Type*> >
> TypedClosureBuilder::sResolvedTypes;
