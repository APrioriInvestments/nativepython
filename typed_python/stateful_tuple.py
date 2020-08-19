from typed_python.macro import Macro
from typed_python import Class, Final, Member, Tuple


@Macro
def StatefulTuple(*args, TupleType=None):
    if TupleType is None:
        T = Tuple(*args)
    else:
        assert not args
        T = TupleType

    types = T.ElementTypes

    name = "Stateful" + T.__name__

    output = []

    output.append("class StatefulTuple_(Class, Final, __name__=name):")
    for i in range(len(types)):
        output.append(f"    f{i} = Member(types[{i}])")
    output.append("    def __getitem__(self, ix):")
    for i in range(len(types)):
        output.append(f"        if ix == {i}:")
        output.append(f"            return self.f{i}")
    output.append("    def __setitem__(self, ix, v):")
    for i in range(len(types)):
        output.append(f"        if ix == {i}:")
        output.append(f"            self.f{i} = v")
        output.append("            return")
    output.append("    def write(self):")
    output.append("        return T((")
    for i in range(len(types)):
        output.append(f"            self.f{i},")
    output.append("        ))")
    output.append("return StatefulTuple_")

    return {
        "sourceText": output,
        "locals": {
            "T": T,
            "types": types,
            "name": name,
            "Class": Class,
            "Final": Final,
            "Member": Member,
        }
    }
