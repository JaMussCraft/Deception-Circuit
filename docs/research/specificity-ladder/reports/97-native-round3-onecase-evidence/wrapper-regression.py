from pathlib import Path
import ast, functools, time, types
source = Path(__file__).with_name("report97-native-onecase-instrumented.py")
node = next(n for n in ast.parse(source.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == "wrap")
namespace = dict(functools=functools, time=time, mark=lambda *a, **kw: None)
exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), namespace)
a = lambda: "a"
b = lambda: "b"
owner = types.SimpleNamespace(a=a, b=b)
namespace["wrap"](owner, "a")
namespace["wrap"](owner, "b")
assert (owner.a(), owner.b()) == ("a", "b")
assert owner.a.__wrapped__ is a and owner.b.__wrapped__ is b
print("PASS: separate original callables; no late binding or recursive adapter")
