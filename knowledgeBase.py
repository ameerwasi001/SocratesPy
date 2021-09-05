import utils
from visitors import RulesVisitor
from sys import stderr
from functools import reduce
from multipleDispatch import MultipleDispatch
from unificationVisitor import Unifier, UniqueVariableSubstitutor, Substitutions, Substituter, RemoveNumberedExprVisitor, TopLevelBinOpCounter, ConstraintGenerator
from nodes import Var, Term, Conjuction, BinOp, Fact, Goals, Rule, Rules, SystemEquations
from pyDuck import State

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
        max_constraints = TopLevelBinOpCounter().visit(goals)
        def solutions(index: int, equations: SystemEquations, unifier: Unifier):
            if index < len(goals.goals):
                goal = goals.goals[index]

                if isinstance(goal, BinOp):
                    equations.add_equation(Substituter(unifier.env).visit(goal))
                    propogation = equations.propogate()
                    if propogation is None: return
                    new_unifier = Unifier()
                    new_unifier.env.substitutions = propogation
                    unified = Unifier.merge(Unifier.inheriting(unifier), new_unifier)
                    if unified != None:
                        if len(equations) == max_constraints and max_constraints != 0 and (not equations.solved):
                            for solution in equations.solve():
                                substitutions = Substitutions()
                                substitutions.substitutions = solution
                                unified = Unifier.merge(Unifier.inheriting(unifier), Unifier.from_env(substitutions))
                                if unified == None: continue
                                yield from solutions(index+1, equations.given_env(unified.env), unified)
                        else: yield from solutions(index+1, equations.clone(), unified)
                else:
                    for item in self.lookup(Substituter(unifier.env).visit(goal)):
                        new_unifier = Unifier()
                        if not new_unifier.unify(goal, item): continue
                        unified = Unifier.merge(Unifier.inheriting(unifier), new_unifier)
                        if unified != None:
                            yield from solutions(index+1, equations.given_env(unified.env), unified)
            else:
                yield Substituter(unifier.env).visit(goals)
        yield from solutions(0, SystemEquations(ConstraintGenerator, Substituter, Substitutions()), Unifier())

    def lookup_BinOp(self, binOp: BinOp):
        constraintGenerator = SystemEquations(ConstraintGenerator, Substituter, Substitutions())
        constraintGenerator.add_equation(binOp)
        for solution in constraintGenerator.solve():
            substitutions = Substitutions()
            substitutions.substitutions = solution
            new_fact = Substituter(substitutions).visit(binOp)
            yield new_fact

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
                        unified_fact = Substituter(new_unifier.env).visit(new_fact)
                        yield unified_fact