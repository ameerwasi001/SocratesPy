import utils
from visitors import RulesVisitor
from functools import reduce
from multipleDispatch import MultipleDispatch
from nodes import Var, Term, Fact, Goals, Rule, Rules

class DisjointOrderedSets:
    @staticmethod
    def normalizeUniques(this, uniques):
        disjoint_sets = DisjointOrderedSets()
        rels = {(tuple(uniques.get(x, x) for x in rel_order), frozenset({uniques.get(k, k) for k in rel})) for rel_order, rel in this.sets}
        for rel_order, rel in rels:
            disjoint_sets.add_relation(rel_order, rel)
        return disjoint_sets

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
                if raises: raise Exception(f"Could not resolve relation because none of {rel} has a known value")
                else: defined = last
            for k in rel:
                definitions[k] = defined
        return definitions

    def __str__(self):
        ls = ["{" + ", ".join([str(x) for x in s]) + "}" for _, s in self.sets]
        return "Relations: " + ", ".join(ls)

class Substitutions:
    @staticmethod
    def normalizeUniques(this, uniques):
        subs = Substitutions()
        uniques = {v:k for k, v in uniques.items()}
        subs.substitutions = {uniques.get(k, k):v for k, v in this.substitutions.items()}
        subs.relations = DisjointOrderedSets.normalizeUniques(this.relations, uniques)
        return subs

    @staticmethod
    def resolve(this):
        resolver = Resolver(this)
        resolutions = dict(this.relations.define_all(this), **this.substitutions)
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

    def visit_Conjuction(self, goals: Goals):
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
            raise Exception(f"Could not get variable {var}, since it has no definitions and is only related to {self.env.relations.sets}")
        return val

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

