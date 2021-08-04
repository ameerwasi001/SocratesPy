import utils
from visitors import RulesVisitor
from functools import reduce
from multipleDispatch import MultipleDispatch
from unificationVisitor import Unifier, UniqueVariableSubstitutor, Substitutions, Substituter, normalizeUniqueSubstitutions
from nodes import Var, Term, Conjuction, Fact, Rule, Rules

class KnowledgeBase:
    def __init__(self, knowledge):
        self.knowledge = knowledge    

    def lookup(self, node): yield from Query(self).lookup(node)

class Query:
    def __init__(self, knowledge):
        self.knowledge_base = knowledge
        self.unique_substitutor = UniqueVariableSubstitutor()

    def lookup(self, node):
        self.unique_substitutor.clear_vars()
        return getattr(self, f"lookup_{type(node).__name__}")(node)

    def lookup_Fact(self, fact: Fact):
        possibilities = self.knowledge_base.knowledge.get(fact.name)
        if possibilities == None: return None
        for rule in possibilities:
            fresh = self.unique_substitutor.visit(rule)
            unifier = Unifier()
            match = unifier.unify(fresh.fact, fact)
            if match:
                new_fact = Substituter().visit(fresh.fact, unifier.env)
                if fresh.condition == None: yield new_fact
                else:
                    body = Substituter().visit(fresh.condition, unifier.env)
                    for item in self.lookup(body):
                        new_unifier = Unifier()
                        unification = new_unifier.unify(body, item)
                        if unification == None or unification == False: continue
                        yield Substituter().visit(new_fact, new_unifier.env)