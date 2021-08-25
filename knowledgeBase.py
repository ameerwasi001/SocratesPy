import utils
from visitors import RulesVisitor
from sys import stderr
from functools import reduce
from multipleDispatch import MultipleDispatch
from unificationVisitor import Unifier, UniqueVariableSubstitutor, Substitutions, Substituter, RemoveNumberedExprVisitor
from nodes import Var, Term, Conjuction, Fact, Goals, Rule, Rules

class KnowledgeBase:
    def __init__(self, knowledge):
        self.knowledge = knowledge    

    def lookup(self, node): 
        for res in Query(self).lookup(node):
            unifier = Unifier()
            if unifier.unify(node, res) == None: stderr.write("Internal Error: Incomplete substitution\n")
            returning_subs = {k:RemoveNumberedExprVisitor().visit(v) for k,v in unifier.env.substitutions.items()}
            returning_unifier = unifier.clone()
            returning_unifier.env.substitutions = returning_subs
            yield (returning_unifier, RemoveNumberedExprVisitor().visit(Substituter(returning_unifier.env).visit(node)))

class Query:
    def __init__(self, knowledge):
        self.knowledge_base = knowledge
        self.unique_substitutor = UniqueVariableSubstitutor()

    def lookup(self, node):
        self.unique_substitutor.clear_vars()
        return getattr(self, f"lookup_{type(node).__name__}")(node)

    def lookup_Goals(self, goals: Goals):
        def solutions(index: int, unifier: Unifier):
            if index < len(goals.goals):
                goal = goals.goals[index]
                for item in self.lookup(Substituter(unifier.env).visit(goal)):
                    new_unifier = Unifier()
                    if not new_unifier.unify(goal, item): continue
                    unified = Unifier.merge(Unifier.inheriting(unifier), new_unifier)
                    if unified != None:
                        yield from solutions(index+1, unified)
            else:
                yield Substituter(unifier.env).visit(goals)
        yield from solutions(0, Unifier())

    def lookup_Fact(self, fact: Fact):
        possibilities = self.knowledge_base.knowledge.get(fact.name)
        if possibilities == None: return None
        for rule in possibilities:
            fresh = self.unique_substitutor.substitute(rule)
            unifier = Unifier()
            match = unifier.unify(fresh.fact, fact)
            if match:
                new_fact = Substituter(unifier.env).visit(fresh.fact)
                if fresh.condition == None: yield new_fact
                else:
                    body = Substituter(unifier.env).visit(fresh.condition)
                    for item in self.lookup(body):
                        new_unifier = Unifier()
                        unification = new_unifier.unify(body, item)
                        if unification == None or unification == False: continue
                        yield Substituter(new_unifier.env).visit(new_fact)