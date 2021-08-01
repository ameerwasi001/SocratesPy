import utils
from multipleDispatch import MultipleDispatch
from nodes import Var, Term, Fact, Rule, Rules

class DisjointSets:
    def __init__(self):
        self.sets = set()

    def add_relation(self, unifier, a: str, b: str):
        for set_ in frozenset(self.sets):
            if len(set_.intersection({a, b})) != 0:
                self.sets.remove(set_)
                self.sets.add(frozenset().union(set_, frozenset({a, b})))
                return True
        self.sets.add(frozenset({a, b}))
        return True

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

    def __str__(self):
        ls = ["{" + ", ".join([str(x) for x in s]) + "}" for s in self.sets]
        return "Relations: " + utils.tab_lines("\n".join(ls))

class Substitutions:
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
        self.relations.add_relation(unifier, a, b)
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

    def __str__(self):
        return ("Substitutions: " +
            utils.tab_lines("\n".join([f"{str(a)}: {str(b)}" for a, b in self.substitutions.items()])) 
            + "\n" + str(self.relations))

class Unifier:
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

unifier = Unifier()
t1 = Fact("mortal", [Var("X"), Var("X"), Var("M"), Var("M")])
t2 = Fact("mortal", [Var("Y"), Term("catastrophe"), Fact("kid", [Term("ameer")]), Fact("kid", [Var("G")])])
res = unifier.unify(t1, t2)
print(unifier.env)
print("G is",  unifier.env.get_variable("G"))
print(res)