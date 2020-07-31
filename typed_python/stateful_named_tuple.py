from typed_python import NamedTuple, Class, Member
from typed_python.macro import Macro


def StatefulNamedTuple(T=None, **kwargs):
    if T is None:
        return _StatefulNamedTuple(NamedTuple(**kwargs))
    return _StatefulNamedTuple(T)


@Macro
def _StatefulNamedTuple(T):
    nameToType = {name: typ for name, typ in zip(T.ElementNames, T.ElementTypes)}

    name = "Stateful" + T.__name__
    output = []
    output.append("class StatefulNamedTuple_(Class, __name__=name):")
    for fieldName in nameToType:
        output.append(f"    {fieldName}=Member(nameToType['{fieldName}'])")
    output.append("    def __init__(")
    output.append("        self,")
    for fieldName in nameToType:
        output.append(f"        {fieldName},")
    output.append("    ):")
    for fieldName in nameToType:
        output.append(f"        self.{fieldName} = {fieldName}")
    output.append(f"return StatefulNamedTuple_")

    return {
        "sourceText": output,
        "locals": {
            "nameToType": nameToType,
            "name": name,
            "Class": Class,
            "Member": Member,
        }
    }
