from sys import stderr
from unificationVisitor import Unifier, UniqueVariableSubstitutor, Substitutions, Substituter, RemoveNumberedExprVisitor, HasUnhyphenatedVariable, TopLevelBinOpCounter, ConstraintGenerator, SystemEquations
from nodes import Var, Term, Conjuction, BinOp, Fact, Goals, Rule, Rules

class KnowledgeBase:
    def __init__(self, knowledge):
        self.knowledge = knowledge    

    def lookup(self, node):
        broken = False
        solution_set = set()
        for res in Query(self, False).lookup(node):
            unifier = Unifier()
            if unifier.unify(node, res) == None: stderr.write("Internal Error: Incomplete substitution\n")
            returning_subs = {k:RemoveNumberedExprVisitor().visit(v) for k,v in unifier.env.substitutions.items()}
            returning_unifier = unifier.clone()
            returning_unifier.env.substitutions = returning_subs
            new_res = Substituter(returning_unifier.env).visit(node)
            if HasUnhyphenatedVariable().visit(new_res):
                broken = True
                break
            un_numbered_res = RemoveNumberedExprVisitor().visit(new_res)
            solution_set.add(un_numbered_res)
            yield (returning_unifier, un_numbered_res)

        if broken:
            for res in Query(self, True).lookup(node):
                searching_unifier = Unifier()
                if searching_unifier.unify(node, res) == None: stderr.write("Internal Error: Incomplete substitution\n")
                searching_returning_subs = {k:RemoveNumberedExprVisitor().visit(v) for k,v in searching_unifier.env.substitutions.items()}
                searching_returning_unifier = searching_unifier.clone()
                searching_returning_unifier.env.substitutions = searching_returning_subs
                searching_new_res = Substituter(searching_returning_unifier.env).visit(node)
                searching_un_numbered_res = RemoveNumberedExprVisitor().visit(searching_new_res)
                if searching_un_numbered_res in solution_set: continue
                yield (searching_returning_unifier, searching_un_numbered_res)

class Query:
    def __init__(self, knowledge, search):
        self.knowledge_base = knowledge
        self.search = search
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
                    equations.add_equation(goal)
                    new_equations = equations.substituted(unifier.env)
                    propogation = new_equations.propogate()
                    if propogation is None: return
                    new_unifier = Unifier()
                    new_unifier.env.substitutions = propogation
                    unified = Unifier.merge(Unifier.inheriting(unifier), new_unifier)
                    if unified != None:
                        if self.search and len(equations) == max_constraints and max_constraints != 0 and (not equations.solved):
                            for solution in equations.solve():
                                substitutions = Substitutions()
                                substitutions.substitutions = solution
                                unified = Unifier.merge(Unifier.inheriting(unifier), Unifier.from_env(substitutions))
                                if unified == None: continue
                                yield from solutions(index+1, new_equations.given_env(unified.env), unified)
                        else: yield from solutions(index+1, new_equations.clone(), unified)
                else:
                    for item in self.lookup(Substituter(unifier.env).visit(goal)):
                        new_unifier = Unifier()
                        if not new_unifier.unify(goal, item): continue
                        unified = Unifier.merge(Unifier.inheriting(unifier), new_unifier)
                        if unified != None:
                            yield from solutions(index+1, equations.given_env(unified.env), unified)
            else:
                yield Substituter(unifier.env).visit(goals)
        yield from solutions(0, SystemEquations(Substitutions()), Unifier())

    def lookup_BinOp(self, binOp: BinOp):
        constraintGenerator = SystemEquations(Substitutions())
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