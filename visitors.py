import ast
import utils
from nodes import Var, Fact, Rule, Rules
from functools import *


class RulesVisitor:
    def visit(self, node: Rule):
        return getattr(self, f"visit_{type(node).__name__}")(node)

class CorrectArgumentRules(RulesVisitor):
    def __init__(self, env: Rules):
        fsts = map(utils.fst, env.env.items())
        snds = list(map(lambda xs: set(list(map(lambda x: len(x.fact), utils.snd(xs)))), env.env.items()))
        self.env = dict(zip(fsts, snds))
        super().__init__()

    def visit_all(self, env: Rules):
        for _, xs in env.env.items():
            for x in xs:
                self.visit(x)

    def visit_Rule(self, rule: Rule):
        self.visit(rule.fact)
        if rule.condition != None:
            self.visit(rule.condition)

    def visit_Fact(self, fact: Fact):
        vals = self.env.get(fact.name)
        if vals is None:
            raise Exception(f"{fact.name} is not an defined")
        if not (len(fact) in vals):
            raise Exception(f"{str(len(fact))} is an invalid arity for {fact.name}")

class RulesToPython(RulesVisitor):
    def visit_Rules(self, rules: Rules):
        return "{" + ', '.join(list(map(lambda kv: f"'{utils.fst(kv)}': [{', '.join(list(map(self.visit, utils.snd(kv))))}]", rules.env.items()))) + "}"

    def visit_Rule(self, rule: Rule):
        return f"Rule({self.visit(rule.fact)}, {str(None) if rule.condition == None else self.visit(rule.condition)})"

    def visit_Fact(self, fact: Fact):
        name = "\"" + fact.name + "\""
        return f"Fact({name}, [{', '.join(list(map(self.visit, fact.args)))}])"

    def visit_Var(self, var: Var):
        return "Var(\"" + var.name + "\")"

def make_id(a):
    return Fact(a, []) if a[0].islower() else Var(a)

def make_fact(node):
    if isinstance(node.slice.value, ast.Name):
        return Fact(node.value.id, [make_id(node.slice.value.id)])
    return Fact(node.value.id, list(map(lambda a: make_id(a.id), node.slice.value.elts)))

class ExprVisitor(ast.NodeVisitor):
    def visit_Subscript(self, node: ast.Subscript):
        if isinstance(node.slice.value, ast.Subscript): args = [self.visit(node.slice.value)]
        else: args = list(map(self.visit, [node.slice.value] if isinstance(node.slice.value, ast.Name) else node.slice.value.elts))
        name = node.value.id
        return Fact(name, args)

    def visit_Name(self, node: ast.Name):
        return make_id(node.id)

class FullVisitor(ast.NodeVisitor):
    _fields = ["env"]

    def initialize(self):
        self.env = Rules()
        self.expr_visitor = ExprVisitor()
        return self

    def visit_Subscript(self, node: ast.Subscript):
        self.env.add(node.value.id, Rule(self.expr_visitor.visit(node)))

    def visit_Assign(self, node: ast.Assign):
        target = node.targets[0]
        fact = self.expr_visitor.visit(target)
        query = self.expr_visitor.visit(node.value)
        rule = Rule(fact, query)
        self.env.add(fact.name, rule)

    def __str__(self):
        return str(self.env)

class SyntaxValidator(ast.NodeVisitor):
    def __init__(self, *args, **kwargs):
        self.allowed_nodes = [
        ast.Expr,
        ast.Assign,
        ast.Subscript,
        ast.Name
        ]
        super().__init__(*args, *kwargs)

    def visit(self, node):
        if any(list(map(lambda c: isinstance(node, c), self.allowed_nodes))): return super().visit(node)
        else: raise Exception("Only subscript and name nodes allowed")

    def visit_Assign(self, node: ast.Assign):
        if len(node.targets) != 1:
            raise Exception("Expected to only have one target")
        target = node.targets[0]
        if isinstance(target, ast.Tuple) and len(target.elts) != 1:
            raise Exception("Expected to only have one target")
        if not (isinstance(target, ast.Subscript) or isinstance(target, ast.Name)):
            raise Exception("Target is only allowed to be a subscript")
        if not (isinstance(node.value, ast.Subscript) or isinstance(node.value, ast.Name)):
            raise Exception("Assigments are only allowed to be subscripts")
        self.visit(target)
        self.visit(node.value)

    def visit_Name(self, node):
        if not node.id[0].islower():
            raise Exception("Expected an identfier starting with a lowercase letter")

    def visit_Subscript(self, node: ast.Subscript):
        if not (isinstance(node.value, ast.Name) and len(node.value.id) > 0 and node.value.id[0].islower()):
            raise Exception("Expected an identfier starting with a lowercase letter")
        if isinstance(node.slice.value, ast.Subscript):
            self.visit_Subscript(node.slice.value)
        elif not isinstance(node.slice.value, ast.Name):
            if not (isinstance(node.slice.value, ast.Tuple) and all(map(lambda a: self.visit, node.slice.value.elts))):
                raise Exception("Only names as subscripts are allowed")

class SelectiveVistor(ast.NodeTransformer):
    def initialize(self, nodes_path, solver):
        self.nodes_path = nodes_path
        self.solver_path = solver
        return self

    def visit_With(self, node: ast.With):
        if not (len(node.items) == 1 and isinstance(node.items[0].context_expr, ast.Compare)):
            return node
        comp_expr = node.items[0].context_expr
        if len(comp_expr.comparators) != 1 or len(comp_expr.ops) != 1 or (not isinstance(comp_expr.ops[0], ast.In)):
            return node
        right = comp_expr.comparators[0]
        left = comp_expr.left
        if not (isinstance(left, ast.Name) and right.id == "SocraticSolver" and isinstance(right, ast.Name)):
            return node
        target_name = left.id
        validator = SyntaxValidator()
        list(map(validator.visit, node.body))
        visitor = FullVisitor()
        visitor.initialize()
        list(map(visitor.visit, node.body))
        rules = visitor.env
        arity_checker = CorrectArgumentRules(rules)
        arity_checker.visit_all(rules)
        python_code_rules = RulesToPython().visit(rules)
        python_code = f"from {self.nodes_path} import Var, Fact, Rule, Rules\n"
        python_code += f"\n{target_name} = {self.solver_path}({python_code_rules})\n"
        return ast.parse(python_code)
