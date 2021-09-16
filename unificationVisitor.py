import utils
from visitors import RulesVisitor
from exceptions import SocraticSyntaxError, UnresolvedRelationException, UndefinedVariableException, InternalErrorException
from multipleDispatch import MultipleDispatch
from nodes import Var, Term, BinOp, Fact, Goals, Rule, Rules
from pyDuck import Expression, Variable, Constraint, State

class DisjointOrderedSets:
    def __init__(self):
        self.sets = set()

    def add_relation(self, given_tup, given_set):
        for rel_order, rel in frozenset(self.sets):
            if len(rel.intersection(frozenset(given_set))) != 0:
                self.sets.remove((rel_order, rel))
                self.sets.add((rel_order + given_tup, frozenset().union(rel, frozenset(given_set))))
                return True
        self.sets.add((given_tup, frozenset(given_set)))
        return True

    def merge(self, other, unifier):
        for rel_order, rel in other.sets:
            self.add_relation(rel_order, rel)
        x = self.verify_relations(unifier.env, unifier)
        return x

    def get_relation_involving(self, var: str):
        for _, set_ in self.sets:
            if var in set_: return set_
        return None

    def verify_relation(self, env, rel, unifier):
        val = None
        for k in rel:
            if val == None:
                val = env.get_variable(k)
            else:
                new_val = env.get_variable(k)
                if new_val == None: continue
                x = unifier.unify(val, new_val)
                if not x: return False
        return True

    def verify_relations(self, env, unifier):
        for _, rel in frozenset(self.sets):
            if not self.verify_relation(env, rel, unifier): return False
        return True

    def clone(self):
        rels = DisjointOrderedSets()
        rels.sets = {(tuple(x for x in xs), frozenset({k for k in rel})) for xs, rel in self.sets}
        return rels

    def define_all(self, env, raises=True, preferred_hyphens=False):
        definitions = {}
        for _, rel in self.sets:
            defined = None
            last = None
            for k in rel:
                val = env.get_variable(k)
                last = k
                if val != None:
                    defined = val
                    if not (preferred_hyphens and ("-" in defined)):
                        break
            if defined == None:
                if raises: raise UnresolvedRelationException(rel)
                else: defined = Var(last)
            for k in rel:
                definitions[k] = defined
        return definitions

    def __str__(self):
        ls = ["{" + ", ".join([str(x) for x in s]) + "}" for _, s in self.sets]
        return "Relations: " + ", ".join(ls)

class Substitutions:
    @staticmethod
    def resolve(this):
        resolver = Resolver(this)
        resolutions = dict(this.relations.define_all(this, preferred_hyphens=True), **this.substitutions)
        return {k:resolver.visit(v) for k, v in resolutions.items()}

    @staticmethod
    def optionally_resolve(this):
        substituter = Substituter(this)
        subs = dict(this.relations.define_all(this, raises=False, preferred_hyphens=True), **this.substitutions)
        return {k:substituter.visit(v) for k, v in subs.items()}

    def __init__(self):
        self.substitutions = {}
        self.relations = DisjointOrderedSets()

    def add_variable(self, unifier, var: str, other):
        val = self.get_variable(var)
        if val == None:
            self.substitutions[var] = other
            return True
        if not unifier.unify(val, other): return False
        self.substitutions[var] = other
        return True

    def add_relation(self, unifier, a: str, b: str):
        self.relations.add_relation((a, b), frozenset({a, b}))
        if len({a, b}) > 1:
            return self.relations.verify_relations(self, unifier)
        return True

    def get_variable(self, var: str):
        val = self.substitutions.get(var)
        if val == None:
            rel = self.relations.get_relation_involving(var)
            if rel == None: return None
            for k in rel:
                val = self.substitutions.get(k)
                if val == None: continue
                return val
            return None
        return val

    def resolve_variable(self, var: str):
        val = self.get_variable(var)
        if val == None:
            for order, set_ in self.relations.sets:
                if var in set_: return order[0]
        return val

    def merge(self, other, unifier):
        for k, v in other.substitutions.items():
            x = self.add_variable(unifier, k, v)
            if not x: return False
        return self.relations.merge(other.relations, unifier)

    def clone(self):
        subs = Substitutions()
        subs.substitutions = {k:v for k, v in self.substitutions.items()}
        subs.relations = self.relations.clone()
        return subs

    def __str__(self):
        return ("Substitutions: " +
            ", ".join([f"{str(a)}: {str(b)}" for a, b in self.substitutions.items()])
            + ("" if len(self.relations.sets) == 0 else " || " + str(self.relations)))

class Unifier:
    @staticmethod
    def from_env(env):
        new_unifier = Unifier()
        new_unifier.env = env.clone()
        return new_unifier

    @staticmethod
    def inheriting(unifier):
        new_unifier = Unifier()
        new_unifier.env = unifier.env.clone()
        return new_unifier

    @staticmethod
    def merge(unifier1, unifier2):
        new_unifier = Unifier()
        if not new_unifier.env.merge(unifier1.env, new_unifier): return None
        if not new_unifier.env.merge(unifier2.env, new_unifier): return None
        return new_unifier

    def __init__(self):
        self.env = Substitutions()
        self.unify = MultipleDispatch()

        @self.unify.addCase(Term, Term)
        def _unify(t1, t2):
            return t1.name == t2.name

        @self.unify.addCase(Var, Var)
        def _unify(v1, v2):
            return self.env.add_relation(self, v1.name, v2.name)

        @self.unify.addCase(Fact, Fact)
        def _unify(f1, f2):
            if f1.name != f1.name: return False
            if len(f1) != len(f2): return False
            for a, b in zip(f1.args, f2.args):
                if not self.unify(a, b): return False
            return True

        @self.unify.addCase(BinOp, BinOp)
        def _unify(b1, b2):
            if b1.op != b2.op: return False
            if not self.unify(b1.left, b2.left): return False
            if not self.unify(b1.right, b2.right): return False
            return True

        @self.unify.addCase(Goals, Goals)
        def _unify(g1, g2):
            if len(g1) != len(g2): return False
            for a, b in zip(g1.goals, g2.goals):
                if not self.unify(a, b): return False
            return True

        @self.unify.defaultCase
        def _unify(t1, t2):
            if isinstance(t1, Var): return self.env.add_variable(self, t1.name, t2)
            elif isinstance(t2, Var): return self.env.add_variable(self, t2.name, t1)
            return False

    def clone(self):
        new_unifier = Unifier()
        new_unifier.env = self.env.clone()
        return new_unifier

    def __bool__(self): return True

class UniqueVariableSubstitutor(RulesVisitor):
    def __init__(self, subs=None, *args, **kwargs):
        if subs == None: subs = {}
        self.subs = subs
        sorted_keys = sorted(list(self.subs.keys()))
        self.current_max = 0 if len(sorted_keys) == 0 else sorted_keys[-1]
        super().__init__(*args, **kwargs)

    def clear_vars(self):
        self.subs.clear()

    def unique_var_name(self, name):
        self.current_max += 1
        self.subs[name] = f"V-{str(self.current_max)}"
        return self.subs[name]

    def visit_Term(self, term: Term): return term

    def visit_Var(self, var: Var):
        if not (var.name in self.subs):
            self.unique_var_name(var.name)
        return Var(self.subs[var.name])

    def visit_Fact(self, fact: Fact):
        return Fact(fact.name, list(map(self.visit, fact.args)))

    def visit_BinOp(self, bin_op: BinOp):
        return BinOp(self.visit(bin_op.left), bin_op.op, self.visit(bin_op.right))

    def visit_Goals(self, goals: Goals):
        return Goals(list(map(self.visit, goals.goals)))

    def visit_Rule(self, rule: Rule):
        return Rule(self.visit(rule.fact), None if rule.condition == None else self.visit(rule.condition))

    def substitute(self, given):
        new_node = self.visit(given)
        return new_node

class RemoveNumberedExprVisitor(RulesVisitor):
    def visit_Rule(self, rule: Rule):
        return Rule(self.visit(rule.fact), None if rule.condition == None else self.visit(rule.condition))

    def visit_Fact(self, fact: Fact):
        if len(fact) == 0:
            return Term(fact.name)
        ls = list(map(self.visit, fact.args))
        return Fact(utils.remove_arity_from_name(fact.name), ls)

    def visit_Goals(self, goals: Goals):
        return Goals(list(map(self.visit, goals.goals)))

    def visit_Var(self, var: Var): return var
    def visit_Term(self, term: Term): return term

class Resolver(RulesVisitor):
    def __init__(self, env, _resolved_env=False):
        self.env = env if _resolved_env else substitute_environment(env)
        super().__init__()

    def visit_Term(self, term: Term): return term

    def visit_Var(self, var: Var):
        val = self.env.get_variable(var.name)
        if val == None:
            raise UndefinedVariableException(var, self.env.relations.sets)
        return val

    def visit_BinOp(self, bin_op: BinOp):
        return BinOp(self.visit(bin_op.left), bin_op.op, self.visit(bin_op.right))

    def visit_Fact(self, fact: Fact):
        return Fact(fact.name, list(map(self.visit, fact.args)))

    def visit_Goals(self, goals: Goals):
        return Goals(list(map(self.visit, goals.goals)))

    def visit_Rule(self, rule: Rule):
        return Rule(self.visit(rule.fact), None if rule.condition == None else self.visit(rule.condition))

class Substituter(Resolver):
    def visit_Var(self, var: Var):
        val = self.env.get_variable(var.name)
        if val == None:
            x = self.env.resolve_variable(var.name)
            if x == None: return Var(var.name)
            return Var(x)
        return val

def substitute_environment(env: Substitutions):
    new_env = env.clone()
    new_env.substitutions = {k:Substituter(env, _resolved_env=True).visit(v) for k,v in new_env.substitutions.items()}
    return new_env

class ConstraintGenerator(RulesVisitor):
    def __init__(self, domains: Substitutions, *args, **kwargs):
        self.domains = domains
        super().__init__(*args, **kwargs)

    def get_domain(self, name):
        domain = self.domains.get_variable(name)
        if not isinstance(domain, Term): return (0, 256)
        if not isinstance(domain.name, int): return (0, 256)
        return (domain.name, domain.name)

    def visit_Term(self, term: Term): return Expression(int(term.name))

    def visit_Var(self, var: Var):
        (lower, upper) = self.get_domain(var.name)
        return Variable(var.name, lower, upper)

    def visit_BinOp(self, bin_op: BinOp):
        left = self.visit(bin_op.left)
        right = self.visit(bin_op.right)
        op = bin_op.op
        visitation_map = {
            "==": lambda a, b: a == b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "+": lambda a, b: a + b,
            "-": lambda a, b: a - b,
            "*": lambda a, b: a * b,
            "/": lambda a, b: a / b,
        }
        if op in visitation_map: return visitation_map[op](left, right)
        else: raise SocraticSyntaxError(f"Unknown operator {op}")

    def visit_Fact(self, fact: Fact):
        raise InternalErrorException(f"{str(fact)} should not be here in a supposed constraint. Get your syntax validator in order.")

    def visit_Goals(self, goals: Goals):
        raise InternalErrorException(f"{str(goals)} should not be here in a supposed constraint. Get your syntax validator in order.")

    def visit_Rule(self, rule: Rule):
        return InternalErrorException(f"{str(rule)} should not be here in a supposed constraint. Get your syntax validator in order.")

    def generate_constraint(self, node):
        return Constraint(self.visit(node))

class TopLevelBinOpCounter(RulesVisitor):
    def visit_Term(self, term: Term): return 0
    def visit_Fact(self, fact: Fact): return 0
    def visit_Var(self, var: Var): return 0
    def visit_BinOp(self, bin_op: BinOp): return 1

    def visit_Goals(self, goals: Goals): return sum(map(self.visit, goals.goals))

    def visit_Rule(self, rule: Rule): return self.visit(rule.fact) + (0 if rule.condition == None else self.visit(rule.condition))

class HasUnhyphenatedVariable(RulesVisitor):
    def visit_Rules(self, rules: Rules):
        return any([list(map(self.visit, vs)) for _, vs in rules.env.items()])

    def visit_Rule(self, rule: Rule):
        return self.visit(rule.fact) or self.visit(rule.condition)

    def visit_BinOp(self, bin_op: BinOp):
        return self.visit(bin_op.left) or self.visit(bin_op.right)

    def visit_Fact(self, fact: Fact):
        return any(map(self.visit, fact.args))

    def visit_Goals(self, goals: Goals):
        return any(map(self.visit, goals.goals))

    def visit_Var(self, var: Var):
        return (not ("-" in var.name))

    def visit_Term(self, _): return False

class SystemEquations:
    def __init__(self, env):
        self.eqs = []
        self.solved = True
        self.substitutor = Substituter(env)
        self.constraintGenerator = ConstraintGenerator(env.clone())

    def add_equation(self, eq):
        self.eqs.append(eq)

    def prepare_state(self):
        constraints = []
        for constraint in self.eqs:
            constraints.append(self.constraintGenerator.generate_constraint(self.substitutor.visit(constraint)))
        state = State.from_whole_expression(constraints)
        self.solved = state.solved
        return state

    def propogate(self):
        state = self.prepare_state()
        if not state.solveable: return None
        if state.solved: return {var_name: Term(var.value) for var_name, var in state.get_solved_state().items()}
        return {var.name: Term(int(var.value)) for var in state.variables if var.instantiated()}

    def solve(self):
        state = self.prepare_state()
        for solution in state.iterate_all_solutions():
            yield {k:Term(v.value) for k,v in solution.items()}

    def clone(self):
        sys = SystemEquations(self.constraintGenerator.domains.clone())
        sys.solved = self.solved
        sys.eqs = self.eqs[:]
        return sys

    def given_env(self, env):
        sys = SystemEquations(env)
        sys.solved = self.solved
        sys.eqs = self.eqs[:]
        return sys

    def substituted(self, env):
        new_sys = self.given_env(env)
        new_sys.eqs = [new_sys.substitutor.visit(eq) for eq in new_sys.eqs]
        return new_sys

    def __len__(self):
        return len(self.eqs)
    
    def __str__(self):
        return "{" + ", ".join(map(str, self.prepare_state().constraints)) + "}"

    def __repr__(self):
        return "{" + ", ".join(map(repr, self.prepare_state().constraints)) + "}"

# # Unification Basic test
# unifier = Unifier()
# t1 = Fact("mortal", [Var("X"), Var("X"), Var("M"), Var("M")])
# t2 = Fact("mortal", [Var("Y"), Term("catastrophe"), Fact("kid", [Term("ameer")]), Fact("kid", [Var("G")])])
# res = unifier.unify(t1, t2)
# print(utils.str_dict(Substitutions.resolve(unifier.env)))
# print("G is",  unifier.env.get_variable("G"))
# print("Unifies:", res)

# print(" ===~~-~~=== ")

# # Unification merge
# unifier1 = Unifier()
# tx1 = Fact("adult", [Term("miles"), Var("Y"), Term("zoha")])
# tx2 = Fact("adult", [Var("X"), Var("X"), Var("D")])
# res1 = unifier1.unify(tx1, tx2)

# unifier2 = Unifier()
# ty1 = Fact("boy", [Term("miles"), Var("S")])
# ty2 = Fact("boy", [Var("Z"), Var("D")])
# res2 = unifier2.unify(ty1, ty2)
# new_unifier = Unifier.merge(unifier1, unifier2)

# print("First one unifies:", res1, "and the second one:", res2)
# print("Both unify together:", bool(new_unifier))
# if new_unifier:
#     print(Substituter().visit(ty2, new_unifier.env))

