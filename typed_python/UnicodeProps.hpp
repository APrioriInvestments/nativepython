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

#include <Python.h>

// Include information about which unicode characters are considered 'alphanumeric'
// etc, so we can match the various string functions. This behavior is dependent on which
// python version we're using, so we have different includes for different versions. These are
// generated by using 'pyenv' to build the relevant version, and then executing 'unicodeprops.py'
// to generate the file. we could do this in setup.py, but that just seems overly complicated
// and brittle.

#if PY_MINOR_VERSION == 6
#  include "UnicodeProps_3.6.7.hpp"
#else
#  include "UnicodeProps_3.7.4.hpp"
#endif
