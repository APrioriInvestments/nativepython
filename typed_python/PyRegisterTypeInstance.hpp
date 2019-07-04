/******************************************************************************
   Copyright 2017-2019 Nativepython Authors

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

#pragma once

#include "PyInstance.hpp"
#include "PromotesTo.hpp"
#include <cmath>
inline int64_t bitInvert(int64_t in) { return ~in; }
inline int32_t bitInvert(int32_t in) { return ~in; }
inline int16_t bitInvert(int16_t in) { return ~in; }
inline int8_t bitInvert(int8_t in) { return ~in; }
inline uint64_t bitInvert(uint64_t in) { return ~in; }
inline uint32_t bitInvert(uint32_t in) { return ~in; }
inline uint16_t bitInvert(uint16_t in) { return ~in; }
inline uint8_t bitInvert(uint8_t in) { return ~in; }
inline bool bitInvert(bool in) { return !in; }

//this never gets called, but we need it for the compiler to be happy
inline float bitInvert(float in) { return 0.0; }
inline double bitInvert(double in) { return 0.0; }


template<class T>
static PyObject* registerValueToPyValue(T val) {
    static Type* typeObj = GetRegisterType<T>()();

    return PyInstance::extractPythonObject((instance_ptr)&val, typeObj);
}

//implement mod the same way python does for unsigned integers.
inline int64_t pyMod(uint64_t l, uint64_t r) {
    if (r == 0) {
        PyErr_Format(PyExc_ZeroDivisionError, "Divide by zero");
        throw PythonExceptionSet();
    }

    return l % r;
}

//implement mod the same way python does for signed integers
inline int64_t pyMod(int64_t l, int64_t r) {
    if (r == 1 || r == -1 || l == 0) {
        return 0;
    }

    if (r == 0) {
        PyErr_Format(PyExc_ZeroDivisionError, "Divide by zero");
        throw PythonExceptionSet();
    }

    if (r < 0) {
        if (l < 0) {
            return -((-l) % (-r));
        }
        return -((-r + ((-l) % -r)) % -r);
    }

    if (l < 0) {
        return (r + (l % r)) % r;
    }

    return l % r;
}

//implement mod the same way python does for floats and doubles
template<class T>
T pyModFloat(T l, T r) {
    if (l == 0.0) {
        return 0.0;
    }
    if (r == 0.0) {
        PyErr_Format(PyExc_ZeroDivisionError, "Divide by zero");
        throw PythonExceptionSet();
    }

    if (r < 0.0) {
        if (l < 0.0) {
            return -(fmod(-l, -r));
        }
        T res = fmod(l, -r);
        if (res != 0.0)
            res += r;
        return res;
    }

    if (l <= 0.0) {
        T res = fmod(-l, r);
        if (res > 0.0)
            res = r - res;
        return res;
    }

    return fmod(l, r);
}

inline int32_t pyMod(int32_t l, int32_t r) { return (int32_t)pyMod((int64_t)l, (int64_t)r); }
inline int16_t pyMod(int16_t l, int16_t r) { return (int16_t)pyMod((int64_t)l, (int64_t)r); }
inline int8_t pyMod(int8_t l, int8_t r) { return (int8_t)pyMod((int64_t)l, (int64_t)r); }

inline uint32_t pyMod(uint32_t l, uint32_t r) { return (uint32_t)pyMod((uint64_t)l, (uint64_t)r); }
inline uint16_t pyMod(uint16_t l, uint16_t r) { return (uint16_t)pyMod((uint64_t)l, (uint64_t)r); }
inline uint8_t pyMod(uint8_t l, uint8_t r) { return (uint8_t)pyMod((uint64_t)l, (uint64_t)r); }

inline bool pyMod(bool l, bool r) { return 0; }
inline float pyMod(float l, float r) { return pyModFloat(l, r); }
inline double pyMod(double l, double r) { return pyModFloat(l, r); }

inline int64_t pyAnd(int8_t l, int8_t r) { return l & r; }
inline int64_t pyAnd(uint8_t l, uint8_t r) { return l & r; }
inline int64_t pyAnd(int16_t l, int16_t r) { return l & r; }
inline int64_t pyAnd(uint16_t l, uint16_t r) { return l & r; }
inline int64_t pyAnd(int32_t l, int32_t r) { return l & r; }
inline int64_t pyAnd(uint32_t l, uint32_t r) { return l & r; }
inline int64_t pyAnd(int64_t l, int64_t r) { return l & r; }
inline int64_t pyAnd(uint64_t l, uint64_t r) { return l & r; }
inline int64_t pyAnd(float l, float r) {
    PyErr_Format(PyExc_TypeError, "'&' not supported for floating-point types");
    throw PythonExceptionSet();
}
inline int64_t pyAnd(double l, double r) {
    PyErr_Format(PyExc_TypeError, "'&' not supported for floating-point types");
    throw PythonExceptionSet();
}

inline int64_t pyOr(int8_t l, int8_t r) { return l | r; }
inline int64_t pyOr(uint8_t l, uint8_t r) { return l | r; }
inline int64_t pyOr(int16_t l, int16_t r) { return l | r; }
inline int64_t pyOr(uint16_t l, uint16_t r) { return l | r; }
inline int64_t pyOr(int32_t l, int32_t r) { return l | r; }
inline int64_t pyOr(uint32_t l, uint32_t r) { return l | r; }
inline int64_t pyOr(int64_t l, int64_t r) { return l | r; }
inline int64_t pyOr(uint64_t l, uint64_t r) { return l | r; }
inline int64_t pyOr(float l, float r) {
    PyErr_Format(PyExc_TypeError, "'|' not supported for floating-point types");
    throw PythonExceptionSet();
}
inline int64_t pyOr(double l, double r) {
    PyErr_Format(PyExc_TypeError, "'|' not supported for floating-point types");
    throw PythonExceptionSet();
}

inline int64_t pyXor(int8_t l, int8_t r) { return l ^ r; }
inline int64_t pyXor(uint8_t l, uint8_t r) { return l ^ r; }
inline int64_t pyXor(int16_t l, int16_t r) { return l ^ r; }
inline int64_t pyXor(uint16_t l, uint16_t r) { return l ^ r; }
inline int64_t pyXor(int32_t l, int32_t r) { return l ^ r; }
inline int64_t pyXor(uint32_t l, uint32_t r) { return l ^ r; }
inline int64_t pyXor(int64_t l, int64_t r) { return l ^ r; }
inline int64_t pyXor(uint64_t l, uint64_t r) { return l ^ r; }
inline int64_t pyXor(float l, float r) {
    PyErr_Format(PyExc_TypeError, "'^' not supported for floating-point types");
    throw PythonExceptionSet();
}
inline int64_t pyXor(double l, double r) {
    PyErr_Format(PyExc_TypeError, "'^' not supported for floating-point types");
    throw PythonExceptionSet();
}

inline int64_t pyLshift(int64_t l, int64_t r) {
    if (r < 0) {
        PyErr_Format(PyExc_ValueError, "negative shift count");
        throw PythonExceptionSet();
    }
    if ((l == 0 && r > SSIZE_MAX) || (l != 0 && r >= 1024)) { // 1024 is arbitrary
        PyErr_Format(PyExc_ValueError, "shift count too large");
        throw PythonExceptionSet();
    }
    return (l >= 0) ? l << r : -((-l) << r);
}
inline uint64_t pyLshift(uint64_t l, uint64_t r) {
    if ((l == 0 && r > SSIZE_MAX) || (l != 0 && r >= 1024)) { // 1024 is arbitrary
        PyErr_Format(PyExc_ValueError, "shift count too large");
        throw PythonExceptionSet();
    }
    return l << r;
}
inline int64_t pyLshift(int32_t l, int32_t r) { return pyLshift((int64_t)l, (int64_t)r); }
inline int64_t pyLshift(int16_t l, int16_t r) { return pyLshift((int64_t)l, (int64_t)r); }
inline int64_t pyLshift(int8_t l, int8_t r) { return pyLshift((int64_t)l, (int64_t)r); }
inline uint64_t pyLshift(uint32_t l, uint32_t r) { return pyLshift((uint64_t)l, (uint64_t)r); }
inline uint64_t pyLshift(uint16_t l, uint16_t r) { return pyLshift((uint64_t)l, (uint64_t)r); }
inline uint64_t pyLshift(uint8_t l, uint8_t r) { return pyLshift((uint64_t)l, (uint64_t)r); }
inline int64_t pyLshift(float l, float r) {
    PyErr_Format(PyExc_TypeError, "'<<' not supported for floating-point types");
    throw PythonExceptionSet();
}
inline int64_t pyLshift(double l, double r) {
    PyErr_Format(PyExc_TypeError, "'<<' not supported for floating-point types");
    throw PythonExceptionSet();
}

inline uint64_t pyRshift(uint64_t l, uint64_t r) {
    if (r > SSIZE_MAX) {
        PyErr_Format(PyExc_ValueError, "shift count too large");
        throw PythonExceptionSet();
    }
    if (r == 0)
        return l;
    if (r >= 64)
        return 0;
    return l >> r;
}
inline int64_t pyRshift(int64_t l, int64_t r) {
    if (r < 0) {
        PyErr_Format(PyExc_ValueError, "negative shift count");
        throw PythonExceptionSet();
    }
    if (r > SSIZE_MAX) {
        PyErr_Format(PyExc_ValueError, "shift count too large");
        throw PythonExceptionSet();
    }
    if (r == 0)
        return l;
    if (l >= 0)
        return l >> r;
    int64_t ret = (-l) >> r;
    if (ret == 0)
        return -1;
    if (l == -l)  // int64_min case
        return ret;
    return -ret;
}
inline int64_t pyRshift(int8_t l, int8_t r) { return pyRshift((int64_t)l, (int64_t)r); }
inline int64_t pyRshift(int16_t l, int16_t r) { return pyRshift((int64_t)l, (int64_t)r); }
inline int64_t pyRshift(int32_t l, int32_t r) { return pyRshift((int64_t)l, (int64_t)r); }
inline int64_t pyRshift(uint8_t l, uint8_t r) { return pyRshift((uint64_t)l, (uint64_t)r); }
inline int64_t pyRshift(uint16_t l, uint16_t r) { return pyRshift((uint64_t)l, (uint64_t)r); }
inline int64_t pyRshift(uint32_t l, uint32_t r) { return pyRshift((uint64_t)l, (uint64_t)r); }
inline int64_t pyRshift(float l, float r) {
    PyErr_Format(PyExc_TypeError, "'>>' not supported for floating-point types");
    throw PythonExceptionSet();
}
inline int64_t pyRshift(double l, double r) {
    PyErr_Format(PyExc_TypeError, "'>>' not supported for floating-point types");
    throw PythonExceptionSet();
}

inline float pyFloatDiv(bool l, bool r)          { return ((float)l) / (float)r; }
inline float pyFloatDiv(uint8_t l, uint8_t r)    { return ((float)l) / (float)r; }
inline float pyFloatDiv(uint16_t l, uint16_t r)  { return ((float)l) / (float)r; }
inline float pyFloatDiv(uint32_t l, uint32_t r)  { return ((float)l) / (float)r; }
inline double pyFloatDiv(uint64_t l, uint64_t r) { return ((double)l) / (double)r; }
inline float pyFloatDiv(int8_t l, int8_t r)      { return ((float)l) / (float)r; }
inline float pyFloatDiv(int16_t l, int16_t r)    { return ((float)l) / (float)r; }
inline float pyFloatDiv(int32_t l, int32_t r)    { return ((float)l) / (float)r; }
inline double pyFloatDiv(int64_t l, int64_t r)   { return ((double)l) / (double)r; }
inline float pyFloatDiv(float l, float r)        { return l / r; }
inline double pyFloatDiv(double l, double r)     { return l / r; }

inline int64_t pyFloorDiv(int64_t l, int64_t r)   {
    if (r == 0) {
        PyErr_Format(PyExc_TypeError, "pyFloorDiv by 0");
        throw PythonExceptionSet();
    }
    if (l < 0 && l == -l && r == -1) {
        // overflow because int64_min / -1 > int64_max
        return l;
    }

    if ((l>0 && r>0) || (l<0 && r<0)) { //same signs
        return l / r;
    }
    // opposite signs
    return (l % r) ? l / r - 1 : l / r;
}
inline int32_t pyFloorDiv(int32_t l, int32_t r)    { return pyFloorDiv((int64_t)l, (int64_t)r); }
inline int16_t pyFloorDiv(int16_t l, int16_t r)    { return pyFloorDiv((int64_t)l, (int64_t)r); }
inline int8_t pyFloorDiv(int8_t l, int8_t r)       { return pyFloorDiv((int64_t)l, (int64_t)r); }
inline uint64_t pyFloorDiv(uint64_t l, uint64_t r) { return l / r; }
inline uint32_t pyFloorDiv(uint32_t l, uint32_t r) { return l / r; }
inline uint16_t pyFloorDiv(uint16_t l, uint16_t r) { return l / r; }
inline uint8_t pyFloorDiv(uint8_t l, uint8_t r)    { return l / r; }
inline bool pyFloorDiv(bool l, bool r)             { return l / r; }


inline float pyFloorDiv(float l, float r)        { return std::floor(l / r); }
inline double pyFloorDiv(double l, double r)     { return std::floor(l / r); }

inline double pyPow(int8_t l, int8_t r) { return std::pow(l,r); }
inline double pyPow(int16_t l, int16_t r) { return std::pow(l,r); }
inline double pyPow(int32_t l, int32_t r) { return std::pow(l,r); }
inline double pyPow(int64_t l, int64_t r) { return std::pow(l,r); }
inline double pyPow(uint8_t l, uint8_t r) { return std::pow(l,r); }
inline double pyPow(uint16_t l, uint16_t r) { return std::pow(l,r); }
inline double pyPow(uint32_t l, uint32_t r) { return std::pow(l,r); }
inline double pyPow(uint64_t l, uint64_t r) { return std::pow(l,r); }
inline double pyPow(float l, float r) { return std::pow(l,r); }
inline double pyPow(double l, double r) { return std::pow(l,r); }

template<class T>
static PyObject* pyOperatorConcreteForRegisterPromoted(T self, T other, const char* op, const char* opErr) {
    if (strcmp(op, "__add__") == 0) {
        return registerValueToPyValue(T(self+other));
    }

    if (strcmp(op, "__sub__") == 0) {
        return registerValueToPyValue(T(self-other));
    }

    if (strcmp(op, "__mul__") == 0) {
        return registerValueToPyValue(T(self*other));
    }

    if (strcmp(op, "__and__") == 0) {
        return registerValueToPyValue(T(pyAnd(self,other)));
    }

    if (strcmp(op, "__or__") == 0) {
        return registerValueToPyValue(T(pyOr(self,other)));
    }

    if (strcmp(op, "__xor__") == 0) {
        return registerValueToPyValue(T(pyXor(self,other)));
    }

    if (strcmp(op, "__lshift__") == 0) {
        return registerValueToPyValue(T(pyLshift(self,other)));
    }

    if (strcmp(op, "__rshift__") == 0) {
        return registerValueToPyValue(T(pyRshift(self,other)));
    }

    if (strcmp(op, "__pow__") == 0) {
        return registerValueToPyValue(T(pyPow(self,other)));
    }

    if (strcmp(op, "__div__") == 0) {
        if (other == 0) {
            PyErr_Format(PyExc_ZeroDivisionError, "Divide by zero");
            throw PythonExceptionSet();
        }
        return registerValueToPyValue(pyFloatDiv(self, other));
    }

    if (strcmp(op, "__floordiv__") == 0) {
        if (other == 0) {
            PyErr_Format(PyExc_ZeroDivisionError, "Divide by zero");
            throw PythonExceptionSet();
        }
        return registerValueToPyValue(T(pyFloorDiv(self,other)));
    }

    if (strcmp(op, "__mod__") == 0) {
        if (other == 0) {
            PyErr_Format(PyExc_ZeroDivisionError, "Divide by zero");
            throw PythonExceptionSet();
        }

        return registerValueToPyValue(T(pyMod(self, other)));
    }

    return incref(Py_NotImplemented);
}

template<class T, class T2>
static PyObject* pyOperatorConcreteForRegister(T self, T2 other, const char* op, const char* opErr) {
    typedef typename PromotesTo<T, T2>::result_type target_type;
    if (strcmp(op, "__div__") == 0) {
        typedef typename PromotesTo<target_type, float>::result_type div_target_type;
        return pyOperatorConcreteForRegisterPromoted(div_target_type(self), div_target_type(other), op, opErr);
    }

    return pyOperatorConcreteForRegisterPromoted(target_type(self), target_type(other), op, opErr);
}

template<class T>
class PyRegisterTypeInstance : public PyInstance {
public:
    typedef RegisterType<T> modeled_type;

    T get() { return *(T*)dataPtr(); }

    static void copyConstructFromPythonInstanceConcrete(RegisterType<T>* eltType, instance_ptr tgt, PyObject* pyRepresentation, bool isExplicit) {
        Type::TypeCategory cat = eltType->getTypeCategory();

        if (Type* other = extractTypeFrom(pyRepresentation->ob_type)) {
            Type::TypeCategory otherCat = other->getTypeCategory();

            if (otherCat == cat || isExplicit) {
                if (otherCat == Type::TypeCategory::catUInt64) {
                    ((T*)tgt)[0] = ((PyRegisterTypeInstance<uint64_t>*)pyRepresentation)->get();
                    return;
                }
                if (otherCat == Type::TypeCategory::catUInt32) {
                    ((T*)tgt)[0] = ((PyRegisterTypeInstance<uint32_t>*)pyRepresentation)->get();
                    return;
                }
                if (otherCat == Type::TypeCategory::catUInt16) {
                    ((T*)tgt)[0] = ((PyRegisterTypeInstance<uint16_t>*)pyRepresentation)->get();
                    return;
                }
                if (otherCat == Type::TypeCategory::catUInt8) {
                    ((T*)tgt)[0] = ((PyRegisterTypeInstance<uint8_t>*)pyRepresentation)->get();
                    return;
                }
                if (otherCat == Type::TypeCategory::catInt64) {
                    ((T*)tgt)[0] = ((PyRegisterTypeInstance<int64_t>*)pyRepresentation)->get();
                    return;
                }
                if (otherCat == Type::TypeCategory::catInt32) {
                    ((T*)tgt)[0] = ((PyRegisterTypeInstance<int32_t>*)pyRepresentation)->get();
                    return;
                }
                if (otherCat == Type::TypeCategory::catInt16) {
                    ((T*)tgt)[0] = ((PyRegisterTypeInstance<int16_t>*)pyRepresentation)->get();
                    return;
                }
                if (otherCat == Type::TypeCategory::catInt8) {
                    ((T*)tgt)[0] = ((PyRegisterTypeInstance<int8_t>*)pyRepresentation)->get();
                    return;
                }
                if (otherCat == Type::TypeCategory::catBool) {
                    ((T*)tgt)[0] = ((PyRegisterTypeInstance<bool>*)pyRepresentation)->get();
                    return;
                }
                if (otherCat == Type::TypeCategory::catFloat64) {
                    ((T*)tgt)[0] = ((PyRegisterTypeInstance<double>*)pyRepresentation)->get();
                    return;
                }
                if (otherCat == Type::TypeCategory::catFloat32) {
                    ((T*)tgt)[0] = ((PyRegisterTypeInstance<float>*)pyRepresentation)->get();
                    return;
                }
            }
        }

        if (isExplicit) {
            //if this is an explicit cast, use python's internal type conversion
            //mechanisms, which will call methods like __bool__, __int__, or __float__ on
            //objects that have conversions defined.
            if (cat == Type::TypeCategory::catBool) {
                int result = PyObject_IsTrue(pyRepresentation);
                if (result == -1) {
                    throw PythonExceptionSet();
                }

                ((T*)tgt)[0] = (result == 1);
                return;
            }
            if (isInteger(cat)) {
                long l = PyLong_AsLong(pyRepresentation);
                if (l == -1 && PyErr_Occurred()) {
                    if (cat == Type::TypeCategory::catUInt64) {
                        PyErr_Clear();
                        unsigned long u = PyLong_AsUnsignedLong(pyRepresentation);
                        if (u == (unsigned long)(-1) && PyErr_Occurred())
                            throw PythonExceptionSet();
                        ((T*)tgt)[0] = u;
                        return;
                    }
                    throw PythonExceptionSet();
                }

                ((T*)tgt)[0] = l;
                return;
            }

            if (isFloat(cat)) {
                double d = PyFloat_AsDouble(pyRepresentation);
                if (d == -1.0 && PyErr_Occurred()) {
                    throw PythonExceptionSet();
                }

                ((T*)tgt)[0] = d;
                return;
            }
        } else {
            //if not explicit, we need to only convert types that have a direct
            //correspondence
            if (cat == Type::TypeCategory::catBool) {
                if (PyBool_Check(pyRepresentation)) {
                    int result = PyObject_IsTrue(pyRepresentation);
                    if (result == -1) {
                        throw PythonExceptionSet();
                    }

                    ((T*)tgt)[0] = (result == 1);
                    return;
                }
            }

            if (cat == Type::TypeCategory::catUInt64) {
                if (PyLong_CheckExact(pyRepresentation)) {
                    ((T*)tgt)[0] = PyLong_AsUnsignedLong(pyRepresentation);
                    return;
                }
            }

            if (isInteger(cat)) {
                if (PyLong_CheckExact(pyRepresentation)) {
                    ((T*)tgt)[0] = PyLong_AsLong(pyRepresentation);
                    return;
                }
            }

            if (isFloat(cat)) {
                if (PyFloat_Check(pyRepresentation)) {
                    ((T*)tgt)[0] = PyFloat_AsDouble(pyRepresentation);
                    return;
                }
            }
        }

        PyInstance::copyConstructFromPythonInstanceConcrete(eltType, tgt, pyRepresentation, isExplicit);
    }

    static bool isUnsigned(Type::TypeCategory cat) {
        return (cat == Type::TypeCategory::catUInt64 ||
                cat == Type::TypeCategory::catUInt32 ||
                cat == Type::TypeCategory::catUInt16 ||
                cat == Type::TypeCategory::catUInt8 ||
                cat == Type::TypeCategory::catBool
                );
    }
    static bool isInteger(Type::TypeCategory cat) {
        return (cat == Type::TypeCategory::catInt64 ||
                cat == Type::TypeCategory::catInt32 ||
                cat == Type::TypeCategory::catInt16 ||
                cat == Type::TypeCategory::catInt8 ||
                cat == Type::TypeCategory::catUInt64 ||
                cat == Type::TypeCategory::catUInt32 ||
                cat == Type::TypeCategory::catUInt16 ||
                cat == Type::TypeCategory::catUInt8
                );
    }

    static bool isFloat(Type::TypeCategory cat) {
        return (cat == Type::TypeCategory::catFloat64 ||
                cat == Type::TypeCategory::catFloat32
                );
    }

    static bool pyValCouldBeOfTypeConcrete(modeled_type* t, PyObject* pyRepresentation, bool isExplicit) {
        if (isFloat(t->getTypeCategory()))  {
            if (PyFloat_Check(pyRepresentation)) {
                return true;
            }

            if (!isExplicit) {
                return false;
            }

            if (!pyRepresentation->ob_type->tp_as_number) {
                return false;
            }

            return pyRepresentation->ob_type->tp_as_number->nb_float != nullptr;
        }

        if (isInteger(t->getTypeCategory()))  {
            if (PyLong_Check(pyRepresentation)) {
                return true;
            }

            if (!isExplicit) {
                return false;
            }

            if (!pyRepresentation->ob_type->tp_as_number) {
                return false;
            }

            return pyRepresentation->ob_type->tp_as_number->nb_int != nullptr;

        }

        if (t->getTypeCategory() == Type::TypeCategory::catBool) {
            if (isExplicit) {
                return true;
            }

            return PyBool_Check(pyRepresentation);
        }

        if (Type* otherT = extractTypeFrom(pyRepresentation->ob_type)) {
            Type::TypeCategory otherCat = otherT->getTypeCategory();

            if (isInteger(otherCat) || isFloat(otherCat) || otherCat == Type::TypeCategory::catBool) {
                return true;
            }
        }

        return false;
    }

    static PyObject* extractPythonObjectConcrete(RegisterType<T>* t, instance_ptr data) {
        if (t->getTypeCategory() == Type::TypeCategory::catInt64) {
            return PyLong_FromLong(*(int64_t*)data);
        }
        if (t->getTypeCategory() == Type::TypeCategory::catFloat64) {
            return PyFloat_FromDouble(*(double*)data);
        }
        if (t->getTypeCategory() == Type::TypeCategory::catBool) {
            return incref(*(bool*)data ? Py_True : Py_False);
        }
        return NULL;
    }

    PyObject* pyUnaryOperatorConcrete(const char* op, const char* opErr) {
        Type::TypeCategory cat = type()->getTypeCategory();

        if (strcmp(op, "__float__") == 0) {
            return PyFloat_FromDouble(*(T*)dataPtr());
        }
        if (strcmp(op, "__int__") == 0) {
            if (cat == Type::TypeCategory::catUInt64) {
                return PyLong_FromUnsignedLong(*(T*)dataPtr());
            }
            return PyLong_FromLong(*(T*)dataPtr());
        }
        if (strcmp(op, "__neg__") == 0) {
            T val = *(T*)dataPtr();
            val = -val;
            return extractPythonObject((instance_ptr)&val, type());
        }
        if (strcmp(op, "__inv__") == 0 && isInteger(type()->getTypeCategory())) {
            T val = *(T*)dataPtr();
            val = bitInvert(val);
            return extractPythonObject((instance_ptr)&val, type());
        }
        if (strcmp(op, "__index__") == 0 && isInteger(type()->getTypeCategory())) {
            int64_t val = *(T*)dataPtr();
            return PyLong_FromLong(val);
        }

        return PyInstance::pyUnaryOperatorConcrete(op, opErr);
    }

    PyObject* pyOperatorConcrete(PyObject* rhs, const char* op, const char* opErr) {
        if (PyLong_CheckExact(rhs)) {
            long l = PyLong_AsLong(rhs);
            if (l == -1 && PyErr_Occurred()) {
                PyErr_Clear();
                unsigned long u = PyLong_AsUnsignedLong(rhs);
                if (u == (unsigned long)(-1) && PyErr_Occurred())
                    throw PythonExceptionSet();
                return pyOperatorConcreteForRegister<T, uint64_t>(*(T*)dataPtr(), u, op, opErr);
            }
            return pyOperatorConcreteForRegister<T, int64_t>(*(T*)dataPtr(), l, op, opErr);
        }
        if (PyBool_Check(rhs)) {
            return pyOperatorConcreteForRegister<T, bool>(*(T*)dataPtr(), rhs == Py_True ? true : false, op, opErr);
        }
        if (PyFloat_CheckExact(rhs)) {
            return pyOperatorConcreteForRegister<T, double>(*(T*)dataPtr(), PyFloat_AsDouble(rhs), op, opErr);
        }

        Type* rhsType = extractTypeFrom(rhs->ob_type);

        if (rhsType) {
            if (rhsType->getTypeCategory() == Type::TypeCategory::catBool) { return pyOperatorConcreteForRegister<T, bool>(*(T*)dataPtr(), *(bool*)((PyInstance*)rhs)->dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catInt8) { return pyOperatorConcreteForRegister<T, int8_t>(*(T*)dataPtr(), *(int8_t*)((PyInstance*)rhs)->dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catInt16) { return pyOperatorConcreteForRegister<T, int16_t>(*(T*)dataPtr(), *(int16_t*)((PyInstance*)rhs)->dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catInt32) { return pyOperatorConcreteForRegister<T, int32_t>(*(T*)dataPtr(), *(int32_t*)((PyInstance*)rhs)->dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catInt64) { return pyOperatorConcreteForRegister<T, int64_t>(*(T*)dataPtr(), *(int64_t*)((PyInstance*)rhs)->dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catUInt8) { return pyOperatorConcreteForRegister<T, uint8_t>(*(T*)dataPtr(), *(uint8_t*)((PyInstance*)rhs)->dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catUInt16) { return pyOperatorConcreteForRegister<T, uint16_t>(*(T*)dataPtr(), *(uint16_t*)((PyInstance*)rhs)->dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catUInt32) { return pyOperatorConcreteForRegister<T, uint32_t>(*(T*)dataPtr(), *(uint32_t*)((PyInstance*)rhs)->dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catUInt64) { return pyOperatorConcreteForRegister<T, uint64_t>(*(T*)dataPtr(), *(uint64_t*)((PyInstance*)rhs)->dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catFloat32) { return pyOperatorConcreteForRegister<T, float>(*(T*)dataPtr(), *(float*)((PyInstance*)rhs)->dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catFloat64) { return pyOperatorConcreteForRegister<T, double>(*(T*)dataPtr(), *(double*)((PyInstance*)rhs)->dataPtr(), op, opErr); }
        }

        return PyInstance::pyOperatorConcrete(rhs, op, opErr);
    }

    PyObject* pyOperatorConcreteReverse(PyObject* rhs, const char* op, const char* opErr) {
        if (PyLong_CheckExact(rhs)) {
            long l = PyLong_AsLong(rhs);
            if (l == -1 && PyErr_Occurred()) {
                PyErr_Clear();
                unsigned long u = PyLong_AsUnsignedLong(rhs);
                if (u == (unsigned long)(-1) && PyErr_Occurred())
                    throw PythonExceptionSet();
                return pyOperatorConcreteForRegister<uint64_t, T>(u, *(T*)dataPtr(), op, opErr);
            }
            return pyOperatorConcreteForRegister<int64_t, T>(l, *(T*)dataPtr(), op, opErr);
        }
        if (PyBool_Check(rhs)) {
            return pyOperatorConcreteForRegister<bool, T>(rhs == Py_True ? true : false, *(T*)dataPtr(), op, opErr);
        }
        if (PyFloat_CheckExact(rhs)) {
            return pyOperatorConcreteForRegister<double, T>(PyFloat_AsDouble(rhs), *(T*)dataPtr(), op, opErr);
        }

        Type* rhsType = extractTypeFrom(rhs->ob_type);

        if (rhsType) {
            if (rhsType->getTypeCategory() == Type::TypeCategory::catBool) { return pyOperatorConcreteForRegister<bool, T>(*(bool*)((PyInstance*)rhs)->dataPtr(), *(T*)dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catInt8) { return pyOperatorConcreteForRegister<int8_t, T>(*(int8_t*)((PyInstance*)rhs)->dataPtr(), *(T*)dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catInt16) { return pyOperatorConcreteForRegister<int16_t, T>(*(int16_t*)((PyInstance*)rhs)->dataPtr(), *(T*)dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catInt32) { return pyOperatorConcreteForRegister<int32_t, T>(*(int32_t*)((PyInstance*)rhs)->dataPtr(), *(T*)dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catInt64) { return pyOperatorConcreteForRegister<int64_t, T>(*(int64_t*)((PyInstance*)rhs)->dataPtr(), *(T*)dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catUInt8) { return pyOperatorConcreteForRegister<uint8_t, T>(*(uint8_t*)((PyInstance*)rhs)->dataPtr(), *(T*)dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catUInt16) { return pyOperatorConcreteForRegister<uint16_t, T>(*(uint16_t*)((PyInstance*)rhs)->dataPtr(), *(T*)dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catUInt32) { return pyOperatorConcreteForRegister<uint32_t, T>(*(uint32_t*)((PyInstance*)rhs)->dataPtr(), *(T*)dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catUInt64) { return pyOperatorConcreteForRegister<uint64_t, T>(*(uint64_t*)((PyInstance*)rhs)->dataPtr(), *(T*)dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catFloat32) { return pyOperatorConcreteForRegister<float, T>(*(float*)((PyInstance*)rhs)->dataPtr(), *(T*)dataPtr(), op, opErr); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catFloat64) { return pyOperatorConcreteForRegister<double, T>(*(double*)((PyInstance*)rhs)->dataPtr(), *(T*)dataPtr(), op, opErr); }
        }

        return PyInstance::pyOperatorConcrete(rhs, op, opErr);
    }


    //compare two register types directly given the python
    //comparison operator 'pyComparisonOp'. We follow numpy's comparisons here,
    //where we use a signed compare anytime _either_ value is signed, which
    //is different than c++.
    template<class other_t>
    static bool pyCompare(T lhs, other_t rhs, int pyComparisonOp) {
        typedef typename PromotesTo<T, other_t>::result_type PT;

        if (pyComparisonOp == Py_EQ) { return ((PT)lhs) == ((PT)rhs); }
        if (pyComparisonOp == Py_NE) { return ((PT)lhs) != ((PT)rhs); }
        if (pyComparisonOp == Py_LT) { return ((PT)lhs) < ((PT)rhs); }
        if (pyComparisonOp == Py_GT) { return ((PT)lhs) > ((PT)rhs); }
        if (pyComparisonOp == Py_LE) { return ((PT)lhs) <= ((PT)rhs); }
        if (pyComparisonOp == Py_GE) { return ((PT)lhs) >= ((PT)rhs); }
        return false;
    }

    static bool compare_to_python_concrete(Type* t, instance_ptr self, PyObject* other, bool exact, int pyComparisonOp) {
        if (PyBool_Check(other)) { return pyCompare(*(T*)self, other == Py_True ? true : false, pyComparisonOp); }
        if (PyLong_Check(other)) {
            long l = PyLong_AsLong(other);
            if (l == -1 && PyErr_Occurred()) {
                PyErr_Clear();
                unsigned long u = PyLong_AsUnsignedLong(other);
                if (u == (unsigned long)(-1) && PyErr_Occurred())
                    throw PythonExceptionSet();
                return pyCompare(*(T*)self, u, pyComparisonOp);
            }
            return pyCompare(*(T*)self, l, pyComparisonOp);
        }
        if (PyFloat_Check(other)) { return pyCompare(*(T*)self, PyFloat_AsDouble(other), pyComparisonOp); }

        Type* rhsType = extractTypeFrom(other->ob_type);

        if (rhsType) {
            if (rhsType->getTypeCategory() == Type::TypeCategory::catBool) { return pyCompare(*(T*)self, *(bool*)((PyInstance*)other)->dataPtr(), pyComparisonOp); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catInt8) { return pyCompare(*(T*)self, *(int8_t*)((PyInstance*)other)->dataPtr(), pyComparisonOp); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catInt16) { return pyCompare(*(T*)self, *(int16_t*)((PyInstance*)other)->dataPtr(), pyComparisonOp); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catInt32) { return pyCompare(*(T*)self, *(int32_t*)((PyInstance*)other)->dataPtr(), pyComparisonOp); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catInt64) { return pyCompare(*(T*)self, *(int64_t*)((PyInstance*)other)->dataPtr(), pyComparisonOp); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catUInt8) { return pyCompare(*(T*)self, *(uint8_t*)((PyInstance*)other)->dataPtr(), pyComparisonOp); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catUInt16) { return pyCompare(*(T*)self, *(uint16_t*)((PyInstance*)other)->dataPtr(), pyComparisonOp); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catUInt32) { return pyCompare(*(T*)self, *(uint32_t*)((PyInstance*)other)->dataPtr(), pyComparisonOp); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catUInt64) { return pyCompare(*(T*)self, *(uint64_t*)((PyInstance*)other)->dataPtr(), pyComparisonOp); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catFloat32) { return pyCompare(*(T*)self, *(float*)((PyInstance*)other)->dataPtr(), pyComparisonOp); }
            if (rhsType->getTypeCategory() == Type::TypeCategory::catFloat64) { return pyCompare(*(T*)self, *(double*)((PyInstance*)other)->dataPtr(), pyComparisonOp); }
        }

        return PyInstance::compare_to_python_concrete(t, self, other, exact, pyComparisonOp);
    }

    static void mirrorTypeInformationIntoPyTypeConcrete(RegisterType<T>* type, PyTypeObject* pyType) {
        //expose 'ElementType' as a member of the type object
        PyDict_SetItemString(pyType->tp_dict, "IsFloat",
            isFloat(type->getTypeCategory()) ? Py_True : Py_False
            );
        PyDict_SetItemString(pyType->tp_dict, "IsInteger",
            isInteger(type->getTypeCategory()) ? Py_True : Py_False
            );
        PyDict_SetItemString(pyType->tp_dict, "IsSignedInt",
            isInteger(type->getTypeCategory()) && !isUnsigned(type->getTypeCategory()) ? Py_True : Py_False
            );
        PyDict_SetItemString(pyType->tp_dict, "IsUnsignedInt",
            isUnsigned(type->getTypeCategory()) ? Py_True : Py_False
            );
        PyDict_SetItemString(pyType->tp_dict, "Bits",
            PyLong_FromLong(
                type->getTypeCategory() == Type::TypeCategory::catBool ? 1 :
                type->getTypeCategory() == Type::TypeCategory::catInt8 ? 8 :
                type->getTypeCategory() == Type::TypeCategory::catInt16 ? 16 :
                type->getTypeCategory() == Type::TypeCategory::catInt32 ? 32 :
                type->getTypeCategory() == Type::TypeCategory::catInt64 ? 64 :
                type->getTypeCategory() == Type::TypeCategory::catUInt8 ? 8 :
                type->getTypeCategory() == Type::TypeCategory::catUInt16 ? 16 :
                type->getTypeCategory() == Type::TypeCategory::catUInt32 ? 32 :
                type->getTypeCategory() == Type::TypeCategory::catUInt64 ? 64 :
                type->getTypeCategory() == Type::TypeCategory::catFloat32 ? 32 :
                type->getTypeCategory() == Type::TypeCategory::catFloat64 ? 64 : -1
                )
            );
    }
};

