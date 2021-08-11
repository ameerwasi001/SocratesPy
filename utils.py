import ast
import nodes

def fst(t):
    (a, _) = t
    return a

def snd(t):
    (_, b) = t
    return b

def make_id(s: str):
    return nodes.Fact(s, []) if s[0].islower() else nodes.Var(s)

def make_fact(node):
    if isinstance(node.slice.value, ast.Name):
        return nodes.Fact(node.value.id, [make_id(node.slice.value.id)])
    return nodes.Fact(node.value.id, list(map(lambda a: make_id(a.id), node.slice.value.elts)))

def tab_lines(lines: str):
    x = ""
    for line in lines.splitlines():
        x += "\n " + line
    return x

def remove_arity_from_name(name):
    new_name = ""
    for c in name:
        if c == "/": break
        new_name += c
    return new_name

def str_dict(d):
    return "{" + ", ".join([str(k) + ": " + str(v) for k, v in d.items()]) + "}"