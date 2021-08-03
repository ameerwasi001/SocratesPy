import utils
from visitors import RulesVisitor
from functools import reduce
from multipleDispatch import MultipleDispatch
from nodes import Var, Term, Conjuction, Fact, Rule, Rules

class DisjointSets:
    @staticmethod
    def normalizeUniques(this, uniques):
        disjoint_sets = DisjointSets()
        disjoint_sets.sets = {frozenset({uniques.get(k, k) for k in set_}) for set_ in this.sets}
        return disjoint_sets

    def __init__(self):
        self.sets = set()

    def add_relation(self, given_set):
        for set_ in frozenset(self.sets):
            if len(set_.intersection(given_set)) != 0:
                self.sets.remove(set_)
                self.sets.add(frozenset().union(set_, frozenset(given_set)))
                return True
        self.sets.add(frozenset(given_set))
        return True

    def merge(self, other, unifier):
        for set_ in other.sets:
            self.add_relation(set_)
        x = self.verify_relations(unifier.env, unifier)
        return x

    def get_relation_involving(self, var: str):
        for set_ in self.sets:
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
        for rel in self.sets:
            if not self.verify_relation(env, rel, unifier): return False
        return True

    def clone(self):
        rels = DisjointSets()
        rels.sets = {frozenset({k for k in rel}) for rel in self.sets}
        return rels

    def define_all(self, env):
        definitions = {}
        for rel in self.sets:
            defined = None
            for k in rel:
                val = env.get_variable(k)
                if val != None:
                    defined = val
                    break
            if defined == None:
                raise Exception(f"Could not resolve relation because none of {rel} has a known value")
            for k in rel:
                definitions[k] = defined
        return definitions

    def __str__(self):
        ls = ["{" + ", ".join([str(x) for x in s]) + "}" for s in self.sets]
        return "Relations: " + utils.tab_lines("\n".join(ls))

class Substitutions:
    @staticmethod
    def normalizeUniques(this, uniques):
        subs = Substitutions()
        uniques = {v:k for k, v in uniques.items()}
        subs.substitutions = {uniques[k]:v for k, v in this.substitutions.items()}
        subs.relations = DisjointSets.normalizeUniques(this.relations, uniques)
        return subs

    @staticmethod
    def resolve(this):
        resolver = Resolver()
        resolutions = dict(this.relations.define_all(this), **this.substitutions)
        return {k:resolver.visit(v, this) for k, v in resolutions.items()}

    def __init__(self):
        self.substitutions = {}
        self.relations = DisjointSets()

    def add_variable(self, unifier, var: str, other):
        val = self.get_variable(var)
        if val == None:
            self.substitutions[var] = other
            return True
        if not unifier.unify(val, other): return False
        self.substitutions[var] = other
        return True

    def add_relation(self, unifier, a: str, b: str):
        self.relations.add_relation({a, b})
        return self.relations.verify_relations(self, unifier)

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
            utils.tab_lines("\n".join([f"{str(a)}: {str(b)}" for a, b in self.substitutions.items()])) 
            + ("" if len(self.relations.sets) == 0 else "\n" + str(self.relations)))

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

    def unique_var_name(self, name):
        self.current_max += 1
        self.subs[name] = "V-" + str(self.current_max)
        return self.subs[name]

    def visit_Term(self, term: Term): return term

    def visit_Var(self, var: Var):
        if not (var.name in self.subs):
            self.unique_var_name(var.name)
        return Var(self.subs[var.name])

    def visit_Fact(self, fact: Fact):
        return Fact(fact.name, list(map(self.visit, fact.args)))

    def visit_Conjuction(self, conjuction: Conjuction):
        return Conjuction(self.visit(conjuction.right), self.visit(conjuction.left))

    def visit_Rule(self, rule: Rule):
        return Rule(self.visit(rule.fact), None if rule.condition == None else self.visit(rule.condition))

    def substitute(self, given):
        new_node = self.visit(given)
        return (new_node, self.subs)

class Resolver(RulesVisitor):
    def visit_Term(self, term: Term, env: Substitutions): return term

    def visit_Var(self, var: Var, env: Substitutions):
        val = env.get_variable(var.name)
        if val == None:
            raise Exception(f"Could not get variable {var}, since it has no definitions and is only related to {env.relations.sets}")
        return val

    def visit_Fact(self, fact: Fact, env: Substitutions):
        return Fact(fact.name, list(map(lambda node: self.visit(node, env), fact.args)))

    def visit_Conjuction(self, conjuction: Conjuction, env: Substitutions):
        return Conjuction(self.visit(conjuction.right, env), self.visit(conjuction.left, env))

    def visit_Rule(self, rule: Rule, env: Substitutions):
        return Rule(self.visit(rule.fact, env), None if rule.condition == None else self.visit(rule.condition, env))

def normalizeUniqueSubstitutions(subs, given):
    new_subs = {v:k for k, v in subs.items()}
    substitutor = UniqueVariableSubstitutor(new_subs)
    return utils.fst(substitutor.substitute(given))

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
#     print(utils.str_dict(Substitutions.resolve(new_unifier.env)))