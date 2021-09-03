from .expression import Expression, Variable, Bounds
from .constraintOperation import ConstraintOperationResult

class Constraint(Expression):
    @staticmethod
    def replace_by_reference(exprs):
        base_dict = {}
        def replace_one_by_reference(expr):
            if isinstance(expr, Variable):
                if expr.name in base_dict:
                    return base_dict[expr.name]
                base_dict[expr.name] = expr
                return expr
            elif not (expr.integer is None):
                return expr
            else:
                new_expr = Expression()
                new_expr.left = expr.left
                new_expr.op = expr.op
                new_expr.right = expr.right
                new_expr.bounds = expr.bounds
                new_expr.evaluate = expr.evaluate
                new_expr.remove = expr.remove
                new_expr.evaluate_bounds = expr.evaluate_bounds
                new_expr.propagator = expr.propagator
                new_expr.integer = expr.integer
                new_expr.left = replace_one_by_reference(expr.left)
                new_expr.right = replace_one_by_reference(expr.right)
                return new_expr
        new_constraints = []
        for constraint in exprs:
            new_constraints.append(Constraint(replace_one_by_reference(constraint)))
        return (base_dict, new_constraints)

    def __init__(self, expression):
        super().__init__()
        self.left = expression.left
        self.op = expression.op
        self.right = expression.right
        self.bounds = expression.bounds
        self.evaluate = expression.evaluate
        self.remove = expression.remove
        self.evaluate_bounds = expression.evaluate_bounds
        self.propagator = expression.propagator
        self.integer = expression.integer

        var_set_dict = {}
        self.construct_variable_list(expression, var_set_dict)
        self.variable_list = list(var_set_dict.values())
        self.domain_list = list(map(lambda _: None, range(0, len(self.variable_list))))

    def construct_variable_list(self, expr, var_dict):
        if isinstance(expr.left, Variable):
            var_dict[expr.left.name] = expr.left
        elif isinstance(expr.left, Expression):
            self.construct_variable_list(expr.left, var_dict)
        if isinstance(expr.right, Variable):
            var_dict[expr.right.name] = expr.right
        elif isinstance(expr.right, Expression):
            self.construct_variable_list(expr.right, var_dict)
    
    def check(self, res_ref):
        for i in range(len(self.variable_list)):
            self.domain_list[i] = self.variable_list[i].domain
        if any(map(lambda v: not v.instantiated(), self.variable_list)):
            res_ref["result"] = ConstraintOperationResult.Undecided
            return
        try:
            res_ref["result"] = ConstraintOperationResult.Satisfied if self.value != 0 else ConstraintOperationResult.Violated
        except ZeroDivisionError:
            res_ref["result"] = ConstraintOperationResult.Violated

    def propogate(self, *args):
        if len(args) == 1:
            enforce = Bounds(1, 1)
            res_ref = args[0]
            while True:
                Expression.propogate(self, enforce, res_ref)
                res_ref["result"] &= ConstraintOperationResult.Propogated
                if res_ref["result"] != ConstraintOperationResult.Propogated:
                    break
        else:
            Expression.propogate(self, *args)

    def constraint_domains(self):
        enforce = Bounds(1, 1)
        res_dict = {"result": None}
        self.propogate({"result": None})
        for var in self.variable_list:
            var.bounds.update_assoc_domain()
            while len(var.domain_stack) > 1:
                var.domain_stack.pop()
        Expression.propogate(self, enforce, res_dict)
        return (res_dict["result"] & ConstraintOperationResult.Violated) != ConstraintOperationResult.Violated

    def state_changed(self):
        x = len([var for index, var in enumerate(self.variable_list) if var.domain != self.domain_list[index]]) != 0
        return x
