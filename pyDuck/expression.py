from enum import Enum
from .bounds import DomainOperationResult, Domain
from .constraintOperation import ConstraintOperationResult

class Bounds:
    def __init__(self, l, u, assoc_domain_stack=None):
        self.lower_bound = l
        self.upper_bound = u
        self.assoc_domain_stack = assoc_domain_stack

    def update_assoc_domain(self):
        if self.assoc_domain_stack is None: return
        for domInt in self.assoc_domain_stack:
            domain = domInt.domain
            for value in domain.clone():
                domain.upper_bound = self.upper_bound
                domain.lower_bound = self.lower_bound

    def __eq__(self, other):
        if not isinstance(other, Bounds): return False
        return self.lower_bound == other.lower_bound and other.upper_bound == self.upper_bound

    def __str__(self):
        return f"{str(self.lower_bound)} .. {str(self.upper_bound)}"

class Operators(Enum):
    PLUS = 1
    MINUS = 2
    MULTIPLY = 3
    EE = 4
    GT = 5
    LT = 6
    GTE = 7

class Expression:
    def initialize_from_nothing(self): pass

    def initialize_from_int(self, integer):
        self.integer = integer
        self.bounds = Bounds(integer, integer)
        self.remove = lambda _: DomainOperationResult.ElementNotInDomain

    def initialize_from_bin(self, left, right):
        self.left = left
        self.right = right

    def initialize_from_internal_data(self, var, evaluate, evaluate_bounds, propagator):
        self.left = var
        self.evaluate = evaluate
        self.evaluate_bounds = evaluate_bounds
        self.propagator = propagator

    def __init__(self, *args):
        self.op = None
        self.integer = None
        self.bounds = None
        self.remove = None
        self.left = None
        self.right = None
        self.evaluate = None
        self.evaluate_bounds = None
        self.propagator = None
        constructors = {
                0: self.initialize_from_nothing, 
                1: self.initialize_from_int, 
                2: self.initialize_from_bin, 
                4: self.initialize_from_internal_data
            }
        constructors[len(args)](*args)

    def __add__(self, other):
        def evaluateBounds(l, r):
            leftBounds = l.get_updated_bounds()
            rightBounds = r.get_updated_bounds()
            return Bounds(
				leftBounds.lower_bound + rightBounds.lower_bound,
				leftBounds.upper_bound + rightBounds.upper_bound
			)

        def propogator(first, second, enforce):
            result = ConstraintOperationResult.Undecided
            if first.bounds.lower_bound < enforce.lower_bound - second.bounds.upper_bound:
                first.bounds.lower_bound = enforce.lower_bound - second.bounds.upper_bound
                result = ConstraintOperationResult.Propogated

            if first.bounds.upper_bound > enforce.upper_bound - second.bounds.lower_bound:
                first.bounds.upper_bound = enforce.upper_bound - second.bounds.lower_bound
                result = ConstraintOperationResult.Propogated

            if second.bounds.lower_bound < enforce.lower_bound - first.bounds.upper_bound:
                second.bounds.lower_bound = enforce.lower_bound - first.bounds.upper_bound
                result = ConstraintOperationResult.Propogated
            
            if second.bounds.upper_bound > enforce.upper_bound - first.bounds.lower_bound:
                second.bounds.upper_bound = enforce.upper_bound - first.bounds.lower_bound
                result = ConstraintOperationResult.Propogated

            if first.bounds.lower_bound > first.bounds.upper_bound or second.bounds.lower_bound > second.bounds.upper_bound:
                result = ConstraintOperationResult.Violated

            return result

        expr = Expression(self, other)
        expr.op = Operators.PLUS
        expr.evaluate = lambda l, r: l.value + r.value
        expr.evaluate_bounds = evaluateBounds
        expr.propagator = propogator
        return expr

    def __sub__(self, other):
        def evaluateBounds(l, r):
            leftBounds = l.get_updated_bounds()
            rightBounds = r.get_updated_bounds()
            return Bounds(
				leftBounds.lower_bound - rightBounds.upper_bound,
				leftBounds.upper_bound - rightBounds.lower_bound
			)

        def propogator(first, second, enforce):
            result = ConstraintOperationResult.Undecided
            if first.bounds.lower_bound < enforce.lower_bound + second.bounds.lower_bound:
                first.bounds.lower_bound = enforce.lower_bound + second.bounds.lower_bound
                result = ConstraintOperationResult.Propogated

            if first.bounds.upper_bound > enforce.upper_bound + second.bounds.upper_bound:
                first.bounds.upper_bound = enforce.upper_bound + second.bounds.upper_bound
                result = ConstraintOperationResult.Propogated

            if second.bounds.lower_bound < first.bounds.lower_bound - enforce.upper_bound:
                second.bounds.lower_bound = first.bounds.lower_bound - enforce.upper_bound
                result = ConstraintOperationResult.Propogated
            
            if second.bounds.upper_bound > first.bounds.upper_bound - enforce.lower_bound:
                second.bounds.upper_bound = first.bounds.upper_bound - enforce.lower_bound
                result = ConstraintOperationResult.Propogated
            
            if first.bounds.lower_bound > first.bounds.upper_bound or second.bounds.lower_bound > second.bounds.upper_bound:
                result = ConstraintOperationResult.Violated

            return result

        expr = Expression(self, other)
        expr.evaluate = lambda l, r: l.value - r.value
        expr.op = Operators.MINUS
        expr.evaluate_bounds = evaluateBounds
        expr.propagator = propogator
        return expr

    def __mul__(self, other):
        def evaluateBounds(l, r):
            leftBounds = l.get_updated_bounds()
            rightBounds = r.get_updated_bounds()
            return Bounds(
				leftBounds.lower_bound * rightBounds.lower_bound,
				leftBounds.upper_bound * rightBounds.upper_bound
			)

        def one_if_zero(v): return 1 if v == 0 else v

        def propogator(first, second, enforce):
            result = ConstraintOperationResult.Undecided

            if first.bounds.lower_bound < enforce.lower_bound // one_if_zero(second.bounds.upper_bound):
                first.bounds.lower_bound = enforce.lower_bound // one_if_zero(second.bounds.upper_bound)
                result = ConstraintOperationResult.Propogated

            if first.bounds.upper_bound > enforce.upper_bound // one_if_zero(second.bounds.lower_bound):
                first.bounds.upper_bound = enforce.upper_bound // one_if_zero(second.bounds.lower_bound)
                result = ConstraintOperationResult.Propogated

            if second.bounds.lower_bound < enforce.lower_bound // one_if_zero(first.bounds.upper_bound):
                second.bounds.lower_bound = enforce.lower_bound // one_if_zero(first.bounds.upper_bound)
                result = ConstraintOperationResult.Propogated

            if second.bounds.upper_bound > enforce.upper_bound // one_if_zero(first.bounds.lower_bound):
                second.bounds.upper_bound = enforce.upper_bound // one_if_zero(first.bounds.lower_bound)
                result = ConstraintOperationResult.Propogated

            if first.bounds.lower_bound > first.bounds.upper_bound or second.bounds.lower_bound > second.bounds.upper_bound:
                result = ConstraintOperationResult.Violated

            return result

        expr = Expression(self, other)
        expr.op = Operators.MULTIPLY
        expr.evaluate = lambda l, r: l.value * r.value
        expr.evaluate_bounds = evaluateBounds
        expr.propagator = propogator
        return expr

    def __truediv__(self, other):
        def evaluateBounds(l, r):
            leftBounds = l.get_updated_bounds()
            rightBounds = r.get_updated_bounds()
            return Bounds(
				leftBounds.lower_bound // rightBounds.upper_bound,
				leftBounds.upper_bound if rightBounds.lower_bound == 0 else leftBounds.upper_bound // rightBounds.lower_bound
			)

        def propogator(first, second, enforce):
            result = ConstraintOperationResult.Undecided

            if first.bounds.lower_bound < second.bounds.lower_bound * enforce.lower_bound:
                first.bounds.lower_bound = second.bounds.lower_bound * enforce.lower_bound
                result = ConstraintOperationResult.Propogated

            if first.bounds.upper_bound > second.bounds.upper_bound * enforce.upper_bound:
                first.bounds.upper_bound = second.bounds.upper_bound * enforce.upper_bound
                result = ConstraintOperationResult.Propogated

            if enforce.upper_bound == 0:
                return result

            if second.bounds.lower_bound < first.bounds.lower_bound // enforce.upper_bound:
                second.bounds.lower_bound = first.bounds.lower_bound // enforce.upper_bound
                result = ConstraintOperationResult.Propogated

            if enforce.lower_bound == 0:
                return result

            if second.bounds.upper_bound > first.bounds.upper_bound // enforce.lower_bound:
                second.bounds.upper_bound = first.bounds.upper_bound // enforce.lower_bound
                result = ConstraintOperationResult.Propogated

            if first.bounds.lower_bound > first.bounds.upper_bound or second.bounds.lower_bound > second.bounds.upper_bound:
                result = ConstraintOperationResult.Violated

            return result


        expr = Expression(self, other)
        expr.op = Operators.MULTIPLY
        expr.evaluate = lambda l, r: l.value // r.value
        expr.evaluate_bounds = evaluateBounds
        expr.propagator = propogator
        return expr

    def __eq__(self, other):
        def evaluateBounds(l, r):
            leftBounds = l.get_updated_bounds()
            rightBounds = r.get_updated_bounds()
            return Bounds(
				1 if leftBounds.lower_bound == leftBounds.upper_bound and rightBounds.lower_bound == rightBounds.upper_bound and leftBounds.lower_bound == rightBounds.lower_bound else 0,
				0 if leftBounds.upper_bound < rightBounds.lower_bound or leftBounds.lower_bound > rightBounds.upper_bound else 1
			)

        def propogator(first, second, enforce):
            result = ConstraintOperationResult.Undecided

            if enforce.lower_bound == 0 and enforce.lower_bound < enforce.upper_bound:
                return result

            if enforce.lower_bound > 0:
                if first.bounds.lower_bound < second.bounds.lower_bound:
                    first.bounds.lower_bound = second.bounds.lower_bound
                    result = ConstraintOperationResult.Propogated

                elif second.bounds.lower_bound < first.bounds.lower_bound:
                    second.bounds.lower_bound = first.bounds.lower_bound
                    result = ConstraintOperationResult.Propogated

                if first.bounds.upper_bound < second.bounds.upper_bound:
                    second.bounds.upper_bound = first.bounds.upper_bound
                    result = ConstraintOperationResult.Propogated

                elif second.bounds.upper_bound < first.bounds.upper_bound:
                    first.bounds.upper_bound = second.bounds.upper_bound
                    result = ConstraintOperationResult.Propogated

            if first.bounds.lower_bound > first.bounds.upper_bound or second.bounds.lower_bound > second.bounds.upper_bound:
                result = ConstraintOperationResult.Violated

            return result
		
        expr = Expression(self, other)
        expr.op = Operators.EE
        expr.evaluate = lambda l, r: 1 if l.value == r.value else 0
        expr.evaluate_bounds = evaluateBounds
        expr.propagator = propogator
        return expr

    def __gt__(self, other):
        def evaluateBounds(l, r):
            leftBounds = l.get_updated_bounds()
            rightBounds = r.get_updated_bounds()
            return Bounds(
				1 if leftBounds.lower_bound > rightBounds.upper_bound else 0,
				1 if leftBounds.upper_bound > leftBounds.lower_bound else 0
			)

        def propogator(first, second, enforce):
            result = ConstraintOperationResult.Undecided

            if enforce.lower_bound == 0 and enforce.lower_bound < enforce.upper_bound:
                return result

            if enforce.lower_bound > 0:
                if first.bounds.lower_bound <= second.bounds.lower_bound:
                    first.bounds.lower_bound = second.bounds.lower_bound + 1
                    result = ConstraintOperationResult.Propogated
                if second.bounds.upper_bound >= first.bounds.upper_bound:
                    second.bounds.upper_bound = first.bounds.upper_bound - 1
                    result = ConstraintOperationResult.Propogated
                if first.bounds.upper_bound <= second.bounds.lower_bound:
                    result = ConstraintOperationResult.Violated
            elif enforce.upper_bound == 0:
                if second.bounds.lower_bound < first.bounds.lower_bound:
                    second.bounds.lower_bound = first.bounds.lower_bound
                    result = ConstraintOperationResult.Propogated

                if first.bounds.upper_bound > second.bounds.upper_bound:
                    first.bounds.upper_bound = second.bounds.upper_bound
                    result = ConstraintOperationResult.Propogated

                if first.bounds.lower_bound > second.bounds.upper_bound:
                    result = ConstraintOperationResult.Violated

            if first.bounds.lower_bound > first.bounds.upper_bound or second.bounds.lower_bound > second.bounds.upper_bound:
                result = ConstraintOperationResult.Violated

            return result

        expr = Expression(self, other)
        expr.op = Operators.GT
        expr.evaluate = lambda l, r: 1 if l.value > r.value else 0
        expr.evaluate_bounds = evaluateBounds
        expr.propagator = propogator
        return expr

    def __ge__(self, other):
        def evaluateBounds(l, r):
            leftBounds = l.get_updated_bounds()
            rightBounds = r.get_updated_bounds()
            return Bounds(
				1 if leftBounds.lower_bound >= rightBounds.upper_bound else 0,
				1 if leftBounds.upper_bound >= leftBounds.lower_bound else 0
			)

        def propogator(first, second, enforce):
            result = ConstraintOperationResult.Undecided

            if enforce.lower_bound == 0 and enforce.lower_bound < enforce.upper_bound:
                return result

            if enforce.lower_bound > 0:
                if first.bounds.lower_bound < second.bounds.lower_bound:
                    first.bounds.lower_bound = second.bounds.lower_bound
                    result = ConstraintOperationResult.Propogated

                if second.bounds.upper_bound > first.bounds.upper_bound:
                    second.bounds.upper_bound = first.bounds.upper_bound
                    result = ConstraintOperationResult.Propogated

                if first.bounds.upper_bound < second.bounds.lower_bound:
                    result = ConstraintOperationResult.Violated

            elif enforce.upper_bound == 0:
                if (second.bounds.lower_bound <= first.bounds.lower_bound):
                    second.bounds.lower_bound = first.bounds.lower_bound + 1
                    result = ConstraintOperationResult.Propogated

                if (first.bounds.upper_bound >= second.bounds.upper_bound):
                    first.bounds.upper_bound = second.bounds.upper_bound - 1
                    result = ConstraintOperationResult.Propogated

                if (first.bounds.lower_bound >= second.bounds.upper_bound):
                    result = ConstraintOperationResult.Violated

            if first.bounds.lower_bound > first.bounds.upper_bound or second.bounds.lower_bound > second.bounds.upper_bound:
                result = ConstraintOperationResult.Violated

            return result

        expr = Expression(self, other)
        expr.op = Operators.GTE
        expr.evaluate = lambda l, r: 1 if l.value >= r.value else 0
        expr.evaluate_bounds = evaluateBounds
        expr.propagator = propogator
        return expr

    def __lt__(self, other):
        def evaluateBounds(l, r):
            leftBounds = l.get_updated_bounds()
            rightBounds = r.get_updated_bounds()
            return Bounds(
				1 if leftBounds.upper_bound < rightBounds.lower_bound else 0,
				1 if leftBounds.lower_bound < leftBounds.upper_bound else 0
			)

        def propogator(first, second, enforce):
            result = ConstraintOperationResult.Undecided
            if enforce.lower_bound == 0 and enforce.lower_bound < enforce.upper_bound: 
                return result

            if enforce.lower_bound > 0:
                if second.bounds.lower_bound <= first.bounds.lower_bound:
                    second.bounds.lower_bound = first.bounds.lower_bound + 1
                    result = ConstraintOperationResult.Propogated

                if first.bounds.upper_bound >= second.bounds.upper_bound:
                    first.bounds.upper_bound = second.bounds.upper_bound - 1
                    result = ConstraintOperationResult.Propogated

                if first.bounds.lower_bound >= second.bounds.upper_bound:
                    result = ConstraintOperationResult.Violated

            elif enforce.upper_bound == 0:
                if first.bounds.lower_bound < second.bounds.lower_bound:
                    first.bounds.lower_bound = second.bounds.lower_bound
                    result = ConstraintOperationResult.Propogated

                if second.bounds.upper_bound > first.bounds.upper_bound:
                    second.bounds.upper_bound = first.bounds.upper_bound
                    result = ConstraintOperationResult.Propogated

                if first.bounds.upper_bound < second.bounds.lower_bound:
                    result = ConstraintOperationResult.Violated

            if first.bounds.lower_bound > first.bounds.upper_bound or second.bounds.lower_bound > second.bounds.upper_bound:
                result = ConstraintOperationResult.Violated

            return result

        expr = Expression(self, other)
        expr.op = Operators.LT
        expr.evaluate = lambda l, r: 1 if l.value < r.value else 0
        expr.evaluate_bounds = evaluateBounds
        expr.propagator = propogator
        return expr

    @property
    def value(self):
        if self.evaluate is None:
            if isinstance(self.left, Variable):
                return self.left.value
            else:
                return self.integer
        return self.evaluate(self.left, self.right)

    @property
    def is_bound(self):
        if self.left is None and self.right is None:
            return True
        return self.left.is_bound if self.right is None else self.left.is_bound and self.right.is_bound

    def get_updated_bounds(self):
        if self.evaluate is None:
            if isinstance(self.left, Variable): self.bounds = self.left.get_updated_bounds()
            return self.bounds
        self.bounds = self.evaluate_bounds(self.left, self.right)
        return self.bounds

    def propogate(self, enforce_bounds, resDict):
        self.left.get_updated_bounds()
        if not (self.right is None):
            self.right.get_updated_bounds()
        propogated = False
        intermediate_result = self.propagator(self.left, self.right, enforce_bounds)
        while intermediate_result == ConstraintOperationResult.Propogated:
            left_res = {"result": ConstraintOperationResult.Undecided}
            right_res = {"result": ConstraintOperationResult.Undecided}
            if not self.left.is_bound:
                self.left.propogate(self.left.bounds, left_res)
            if (not (self.right is None)) and (not self.right.is_bound):
                self.right.propogate(self.right.bounds, right_res)
            intermediate_result = (left_res["result"] | right_res["result"]) & ConstraintOperationResult.Propogated
            if intermediate_result != ConstraintOperationResult.Propogated: continue
            propogated = True
            intermediate_result = self.propagator(self.left, self.right, enforce_bounds)
        if intermediate_result == ConstraintOperationResult.Violated: resDict["result"] = ConstraintOperationResult.Violated
        else: resDict["result"] = ConstraintOperationResult.Propogated if propogated else ConstraintOperationResult.Undecided

    def __repr__(self):
        if not (self.integer is None): return str(self.integer)
        return "(" + repr(self.left) + " " + str(self.op) + " " + repr(self.right) + ")"

    def __str__(self):
        if not (self.integer is None): return str(self.integer)
        return "(" + str(self.left) + " " + str(self.op) + " " + str(self.right) + ")"

class DomInt:
    def __init__(self, domain, depth):
        self.domain = domain
        self.depth = depth
    
    def clone(self):
        clone = self.domain.clone()
        domain_int = DomInt(clone, self.depth)
        return domain_int
    
    def __str__(self):
        return f"DomInt({str(self.depth)}, {str(self.domain)})"

class Variable(Expression):
    def initialize_from_nothing(self): pass

    def initialize_from_string_and_list(self, name, elems):
        self.name = name
        self.domain_stack = []
        self.domain_stack.append(DomInt(Domain.CreateDomain(elems), -1))

    def initialize_from_string_and_both_bounds(self, name, lower_bound, upper_bound):
        self.name = name
        self.domain_stack = []
        self.domain_stack.append(DomInt(Domain.CreateDomain(lower_bound, upper_bound), -1))

    def __init__(self, *args):
        super().__init__()
        self.domain_stack = None
        self.state = None
        self.name = None
        self.bounds = None
        constructors = {
                0: self.initialize_from_nothing, 
                2: self.initialize_from_string_and_list, 
                3: self.initialize_from_string_and_both_bounds
            }
        constructors[len(args)](*args)

    @property
    def domain(self):
        domain = self.domain_stack[-1].domain
        return domain

    def clone(self):
        var = Variable()
        var.domain_stack = [x.clone() for x in self.domain_stack]
        var.state = self.state
        var.name = self.name
        var.bounds = self.bounds
        return var

    def remove(self, prune):
        res_ref = {"result": None}
        self.actual_remove(prune, res_ref)
        return res_ref["result"]

    @property
    def instantiated_value(self):
        return self.domain.instantiated_value
    
    def instantiate(self, *args):
        methods = {
                2: self.instantiate_from_nothing,
                3: self.initialize_from_two_int
            }
        methods[len(args)](*args)

    def instantiate_from_nothing(self, depth, res_ref):
        instantiated_domain = self.domain.clone()
        instantiated_domain.instantiate(res_ref)
        if res_ref["result"] != DomainOperationResult.InstantiateSuccessful: return
        self.domain_stack.append(DomInt(instantiated_domain, depth))

    def initialize_from_two_int(self, value, depth, res_ref):
        instantiated_domain = self.domain.clone()
        instantiated_domain.instantiate(value, res_ref)
        if res_ref["result"] != DomainOperationResult.InstantiateSuccessful: return
        self.domain_stack.append(DomInt(instantiated_domain, depth))
    
    def backtrack(self, from_depth):
        while self.domain_stack[-1].depth >= from_depth:
            self.domain_stack.pop()

    def actual_remove(self, *args):
        methods = {
                2: self.remove_using_int,
                3: self.remove_using_two_int
            }
        methods[len(args)](*args)

    def remove_using_two_int(self, value, depth, res_ref):
        if self.domain_stack[-1].depth != depth:
            self.domain_stack.append(DomInt(self.domain.clone(), depth))
            self.domain.remove(value, res_ref)
            if res_ref["result"] == DomainOperationResult.ElementNotInDomain: self.domain_stack.pop()
        else:
            self.domain.remove(value, res_ref)

    def remove_using_int(self, value, res_ref):
        if self.instantiated() or value > self.domain.upper_bound or value < self.domain.lower_bound:
            res_ref["result"] = DomainOperationResult.ElementNotInDomain
        self.actual_remove(value, self.state.depth, res_ref)

    def instantiated(self):
        return self.domain.instantiated()
    
    def size(self):
        return self.domain.size
    
    def set_state(self, state):
        self.state = state
    
    def compare_to(self, otherVar):
        return self.size() - otherVar.size()

    @property
    def value(self):
        return self.instantiated_value()

    @property
    def is_bound(self):
        return self.instantiated()

    def get_updated_bounds(self):
        self.bounds = Bounds(self.domain.lower_bound, self.domain.upper_bound, assoc_domain_stack=self.domain_stack)
        return self.bounds

    def propogate(self, enforce_bounds, res_ref):
        res_ref["result"] = ConstraintOperationResult.Undecided

        if self.state is None: return

        domain_int_stack = self.domain_stack[-1]
        is_domain_new = False
        propagated_domain = None

        if domain_int_stack.depth == self.state.depth:
            propagated_domain = domain_int_stack.domain
        else:
            is_domain_new = True
            propagated_domain = domain_int_stack.domain.clone()
            self.domain_stack.append(DomInt(propagated_domain, self.state.depth))

        domainResult = {"result": DomainOperationResult.RemoveSuccessful}

        while enforce_bounds.lower_bound > propagated_domain.lower_bound and domainResult["result"] == DomainOperationResult.RemoveSuccessful:
            propagated_domain.remove(propagated_domain.lower_bound, domainResult)
            res_ref["result"] = ConstraintOperationResult.Propogated

        while enforce_bounds.upper_bound < propagated_domain.upper_bound and domainResult["result"] == DomainOperationResult.RemoveSuccessful:
            propagated_domain.remove(propagated_domain.upper_bound, domainResult)
            res_ref["result"] = ConstraintOperationResult.Propogated

        if is_domain_new and res_ref["result"] != ConstraintOperationResult.Propogated:
            self.domain_stack.pop()

    def __repr__(self):
        return self.name

    def __str__(self):
        if self.is_bound:
            return self.name + " -> " + str(self.instantiated_value())
        return self.name + " -> " + str(self.domain)