from enum import Enum, auto
from .linkedList import LinkedList
from .bounds import DomainOperationResult
from .constraintOperation import ConstraintOperationResult
from .expression import Expression, Variable, Bounds
from .constraint import Constraint

class StateOperationResult(Enum):
    Solved = 1
    Unsatisfiable = 2
    TimedOut = 3

class State:
    @staticmethod
    def from_whole_expression(constraints):
        references, constraints = Constraint.replace_by_reference(constraints)
        return State(references.values(), constraints)

    def __init__(self, variables, constraints):
        self.depth = 0
        self.backtracks = 0
        self.last_solution = None
        self.solveable = False
        self.solved = False
        self.constraints = []
        self.variables = []
        self.solutions = []
        self.set_variables(variables)
        self.set_constraints(constraints)
    
    def set_constraints(self, constraints):
        solveable = True
        all_domains = [var.domain for var in self.variables]
        while True:
            for constraint in constraints:
                solveable = solveable and constraint.constraint_domains()
            var_domains = [var.bounds for var in self.variables]
            if var_domains == all_domains: break
            if not solveable: break
            all_domains = var_domains
        self.constraints = constraints
        self.solveable = solveable
        if self.solveable:
            if len(self.variables) == 0: self.solved = True
            elif all([var.instantiated() for var in self.variables]): self.solved = True
        else: self.solveable = False

    def set_variables(self, variables):
        self.variables = list(variables)
        for var in self.variables:
            var.set_state(self)

    def get_solved_state(self):
        if not self.solved: 
            raise Exception("Not all variables are solved by constraint propogation, when the solution prompted for solution")
        return {var.name:var for var in [var.clone() for var in self.variables]}

    def search_all_solutions(self):
        if not self.solveable: return
        if self.solved: return self.get_solved_state()
        unassigned_vars = LinkedList.from_list(self.variables) if self.last_solution == None else LinkedList()
        instantiated_vars = list(map(lambda _: None, range(len(self.variables)))) if self.last_solution == None else self.last_solution
        search_result = {"result": StateOperationResult.Unsatisfiable}

        while True:
            if self.depth == -1: break
            if self.depth == len(instantiated_vars):
                self.depth -= 1
                self.backtrack(unassigned_vars, instantiated_vars)
                self.depth += 1
            elif self.constraints_violated():
                break

            if self.search(search_result, unassigned_vars, instantiated_vars):
                self.solutions.append(self.clone_last_solution())
        return StateOperationResult.Unsatisfiable if len(self.solutions) == 0 else StateOperationResult.Solved

    def iterate_all_solutions(self):
        if not self.solveable: return
        if self.solved:
            yield self.get_solved_state()
            return

        unassigned_vars = LinkedList.from_list(self.variables) if self.last_solution == None else LinkedList()
        instantiated_vars = list(map(lambda _: None, range(len(self.variables)))) if self.last_solution == None else self.last_solution
        search_result = {"result": StateOperationResult.Unsatisfiable}

        while True:
            if self.depth == -1: break
            if self.depth == len(instantiated_vars):
                yield self.clone_last_solution()
                self.depth -= 1
                self.backtrack(unassigned_vars, instantiated_vars)
                self.depth += 1
            elif self.constraints_violated():
                break

            if self.search(search_result, unassigned_vars, instantiated_vars):
                self.solutions.append(self.clone_last_solution())

    def search(self, *args):
        if not self.solveable: return
        if self.solved: return self.get_solved_state()
        methods = {
            0: self.search_from_nothing,
            3: self.search_from_both_vars
        }
        return methods[len(args)](*args)

    def search_from_nothing(self):
        unassigned_vars = LinkedList.from_list(self.variables) if self.last_solution == None else LinkedList()
        instantiated_vars = list(map(lambda _: None, range(len(self.variables)))) if self.last_solution == None else self.last_solution
        search_result = {"result": StateOperationResult.Unsatisfiable}

        if self.depth == len(instantiated_vars):
            self.depth -= 1
            self.backtrack(unassigned_vars, instantiated_vars)
            self.depth += 1
        elif self.constraints_violated():
            return search_result
        if self.search(search_result, unassigned_vars, instantiated_vars):
            self.solutions.append(self.clone_last_solution())
        return search_result["result"]

    def search_from_both_vars(self, search_res_ref, unassigned_vars, instantiated_vars):
        search_res_ref["result"] = StateOperationResult.Unsatisfiable
        while True:
            if self.depth == len(self.variables):
                search_res_ref["result"] = StateOperationResult.Solved
                self.last_solution = instantiated_vars[:]
                return True

            instantiated_vars[self.depth] = self.get_most_constrained_variable(unassigned_vars)

            instantiation_res_ref = {"result": None}
            var = instantiated_vars[self.depth]
            var.instantiate(self.depth, instantiation_res_ref)

            if instantiation_res_ref["result"] != DomainOperationResult.InstantiateSuccessful:
                self.depth -= 1
                return False

            if self.constraints_violated() or any(map(lambda v: v.size() == 0, unassigned_vars)):
                if not self.backtrack(unassigned_vars, instantiated_vars):
                    return False

            self.depth += 1

    def clone_last_solution(self):
        unsorted = map(lambda v: (v.name, v), map(lambda a: a.clone(), self.last_solution))
        return {k:v for k, v in sorted(unsorted, key=lambda tup: tup[0])}

    def backtrack(self, unassigned_vars: LinkedList, instantiated_vars):
        remove_result = {"result": None}
        while True:
            if self.depth < 0: return False
            unassigned_vars.prepend(instantiated_vars[self.depth])
            self.backtrack_variable(instantiated_vars[self.depth], remove_result)
            if remove_result["result"] != DomainOperationResult.EmptyDomain: break
        return True

    def constraints_violated(self):
        for constraint in filter(lambda c: c.state_changed(), self.constraints):
            res_ref = {"result": None}
            constraint.propogate(res_ref)
            if (res_ref["result"] & ConstraintOperationResult.Violated) == ConstraintOperationResult.Violated:
                return True
            constraint.check(res_ref)
            if (res_ref["result"] & ConstraintOperationResult.Violated) == ConstraintOperationResult.Violated:
                return True
        return False

    def get_most_constrained_variable(self, lst):
        temp = lst.head.head
        node = lst.head.head

        while node != None:
            if node.value.size() < temp.value.size():
                temp = node

            if temp.value.size() == 1: break

            node = node.tail

        lst.remove(temp)
        return temp

    def backtrack_variable(self, var_prune, result):
        self.backtracks += 1
        value = var_prune.instantiated_value()
        for var in self.variables:
            var.backtrack(self.depth)
        self.depth -= 1
        var_prune.actual_remove(value, self.depth, result)