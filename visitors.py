import ast
import utils
from nodes import Var, Term, Fact, Conjuction, Goals, Rule, Rules
from functools import *

def make_expr(env): return TermCreator().visit(env)

def make_code_and_validate_nodes(target_name, body, nodes_path, solver_path, include_imports=False):
    validator = SyntaxValidator()
    list(map(validator.visit, body))
    visitor = FullTransformerVisitor()
    visitor.initialize()
    list(map(visitor.visit, body))
    rules = make_expr(visitor.env)
    goalCreator = GoalCreator()
    rules = GoalCreator().visit(rules)
    arity_checker = CorrectArgumentRules(rules)
    arity_checker.visit_all(rules)
    python_code_rules = RulesToPython().visit(rules)
    python_code = ""
    if include_imports:
        python_code += f"from {nodes_path} import Var, Term, Fact, Goals, Rule, Rules\n"
    python_code += f"\n{target_name} = {solver_path}({python_code_rules})\n"
    return ast.parse(python_code)

class NodeFinderVistor(ast.NodeTransformer):
    def initialize(self, nodes_path, solver):
        self.nodes_path = nodes_path
        self.solver_path = solver
        self.imported = False
        return self

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "SocraticQuery" and len(node.args) == 1:
            query = node.args[0]
            validator = SyntaxValidator()
            validator.visit(query)
            expr = ExprVisitor().visit(query)
            goal_expr = GoalCreator().visit(expr)
            numbered_term_expr = TermCreator().visit(expr)
            return ast.parse(RulesToPython().visit(numbered_term_expr))
        return self.generic_visit(node)

    def visit_With(self, node: ast.With):
        if not (len(node.items) == 1 and isinstance(node.items[0].context_expr, ast.Compare)):
            return self.generic_visit(node)
        comp_expr = node.items[0].context_expr
        if len(comp_expr.comparators) != 1 or len(comp_expr.ops) != 1 or (not isinstance(comp_expr.ops[0], ast.In)):
            return self.generic_visit(node)
        right = comp_expr.comparators[0]
        left = comp_expr.left
        if not (isinstance(left, ast.Name) and right.id == "SocraticSolver" and isinstance(right, ast.Name)):
            return self.generic_visit(node)
        imported = self.imported
        self.imported = True
        return make_code_and_validate_nodes(left.id, node.body, self.nodes_path, self.solver_path, include_imports=not imported)

class ExprVisitor(ast.NodeVisitor):
    def visit_BinOp(self, node: ast.BinOp):
        right = self.visit(node.right)
        left = self.visit(node.left)
        return Conjuction(left, right)

    def visit_Subscript(self, node: ast.Subscript):
        if isinstance(node.slice.value, ast.Subscript): args = [self.visit(node.slice.value)]
        else: args = list(map(self.visit, [node.slice.value] if isinstance(node.slice.value, ast.Name) else node.slice.value.elts))
        name = node.value.id
        return Fact(name, args)

    def visit_Name(self, node: ast.Name):
        return utils.make_id(node.id)

class FullTransformerVisitor(ast.NodeVisitor):
    _fields = ["env"]

    def initialize(self):
        self.env = Rules()
        self.expr_visitor = ExprVisitor()
        return self

    def visit_Subscript(self, node: ast.Subscript):
        visited = self.expr_visitor.visit(node)
        self.env.add(f"{node.value.id}/{str(len(visited))}", Rule(visited))

    def visit_Assign(self, node: ast.Assign):
        target = node.targets[0]
        fact = self.expr_visitor.visit(target)
        query = self.expr_visitor.visit(node.value)
        rule = Rule(fact, query)
        self.env.add(f"{fact.name}/{str(len(fact))}", rule)

    def __str__(self):
        return str(self.env)

class SyntaxValidator(ast.NodeVisitor):
    def __init__(self, *args, **kwargs):
        self.allowed_nodes = [
        ast.Expr,
        ast.BitAnd,
        ast.BinOp,
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
        if not isinstance(target, ast.Subscript):
            raise Exception("Target is only allowed to be a subscript or a name")
        if not isinstance(node.value, ast.Subscript):
            if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.BitAnd):
                self.visit(node.value.left)
                self.visit(node.value.right)
                return
            raise Exception("Assigments are only allowed to be subscripts or names")
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

class RulesVisitor:
    def visit(self, node, *args, **kwargs):
        return getattr(self, f"visit_{type(node).__name__}")(node, *args, **kwargs)

class TermCreator(RulesVisitor):
    def visit_Rules(self, rules: Rules):
        return Rules({k:list(map(self.visit, vs)) for k, vs in rules.env.items()})

    def visit_Rule(self, rule: Rule):
        return Rule(self.visit(rule.fact), None if rule.condition == None else self.visit(rule.condition))

    def visit_Fact(self, fact: Fact):
        if len(fact) == 0:
            return Term(fact.name)
        ls = list(map(self.visit, fact.args))
        return Fact(f"{fact.name}/{str(len(ls))}", ls)

    def visit_Conjuction(self, conjuction: Conjuction):
        return Conjuction(self.visit(conjuction.left), self.visit(conjuction.right))

    def visit_Var(self, var: Var): return var
    def visit_Term(self, term: Term): return term

class GoalCreator(RulesVisitor):
    def visit_Rules(self, rules: Rules):
        return Rules({k:list(map(self.visit, vs)) for k, vs in rules.env.items()})

    def visit_Rule(self, rule: Rule):
        return Rule(self.visit(rule.fact), None if rule.condition == None else self.visit(rule.condition))

    def visit_Fact(self, fact: Fact):
        if len(fact) == 0:
            return Term(fact.name)
        return Fact(fact.name, list(map(self.visit, fact.args)))

    def visit_Conjuction(self, conjuction: Conjuction):
        def conjuction_recursive_list(conjuction):
            if not isinstance(conjuction, Conjuction): return [conjuction]
            return conjuction_recursive_list(conjuction.left) + conjuction_recursive_list(conjuction.right)
        return Goals(conjuction_recursive_list(conjuction))

    def visit_Var(self, var: Var): return var
    def visit_Term(self, term: Term): return term

class CorrectArgumentRules(RulesVisitor):
    def __init__(self, env: Rules):
        self.env = {k:set([len(v.fact) for v in vs]) for k, vs in env.env.items()}
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
            return
        if not (len(fact) in vals):
            raise Exception(f"{str(len(fact))} is an invalid arity for {fact.name}")
        list(map(self.visit, fact.args))

    def visit_Goals(self, goals: Goals):
        list(map(self.visit, goals.goals))

    def visit_Var(self, node): pass
    def visit_Term(self, node): pass

class RulesToPython(RulesVisitor):
    def visit_Rules(self, rules: Rules):
        return "{" + ', '.join([f"'{k}': [{', '.join(list(map(self.visit, v)))}]" for (k, v) in rules.env.items()]) + "}"

    def visit_Rule(self, rule: Rule):
        return f"Rule({self.visit(rule.fact)}, {str(None) if rule.condition == None else self.visit(rule.condition)})"

    def visit_Fact(self, fact: Fact):
        name = "\"" + fact.name + "\""
        return f"Fact({name}, [{', '.join(list(map(self.visit, fact.args)))}])"

    def visit_Goals(self, goals: Goals):
        return f"Goals([{', '.join(list(map(self.visit, goals.goals)))}])"

    def visit_Conjuction(self, conjuction: Conjuction):
        return f"Conjuction({self.visit(conjuction.right)}, {self.visit(conjuction.left)})"

    def visit_Term(self, node):
        return f'Term("{node.name}")'

    def visit_Var(self, var: Var):
        return "Var(\"" + var.name + "\")"
