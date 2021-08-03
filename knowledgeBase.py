import utils
from visitors import RulesVisitor
from functools import reduce
from multipleDispatch import MultipleDispatch
from unificationVisitor import Unifier, UniqueVariableSubstitutor, Substitutions, normalizeUniqueSubstitutions
from nodes import Var, Term, Conjuction, Fact, Rule, Rules

class KnowledgeBase:
    def __init__(self, knowledge):
        self.knowledge = knowledge    

    def lookup(self, node): yield from Query(self).lookup(node, Unifier())

class Query:
    def __init__(self, knowledge):
        self.knowledge_base = knowledge
        self.substitutor = UniqueVariableSubstitutor()

    def lookup(self, node, unifier: Unifier):
        return getattr(self, f"lookup_{type(node).__name__}")(node, unifier)

    def lookup_Fact(self, fact: Fact, unifier: Unifier):
        possibilities = self.knowledge_base.knowledge.get(fact.name)
        if possibilities == None: return None
        (sub_rule, subs) = self.substitutor.substitute(fact)
        for possibility in possibilities:
            new_unifier = Unifier.inheriting(unifier)
            fact_unification = new_unifier.unify(possibility.fact, sub_rule)
            if fact_unification:
                x = Unifier.from_env(Substitutions.normalizeUniques(new_unifier.env, subs))
                if possibility.condition == None: yield x
                else:
                    yield from self.lookup(possibility.condition, Unifier.inheriting(new_unifier))
