from . import Variable, Expression, Constraint, State

x = Variable("x", 0, 255)
y = Variable("y", 0, 255)

state = State([x, y], [
    Constraint(Expression(6)-y == x*Expression(2)),
    Constraint(x+y > x*y),
    Constraint(y > Expression(0))
])

for solution in state.iterate_all_solutions():
    print(", ".join([f"{var} = {solution[var].value}" for var in solution.keys()]))

print("\n<<=====||=====>>\n")

n = Variable("n", 0, 255)
f = Variable("f", 0, 255)
n1 = Variable("n1", 0, 255)
f1 = Variable("f1", 0, 255)

state = State([n, f1, n1, f], [
    Constraint(n > Expression(0)),
    Constraint(f1 > Expression(0)),
    Constraint(f == Expression(24)),
    Constraint(n1 == n - Expression(1)),
    Constraint(f == n*f1)
])

for solution in state.iterate_all_solutions():
    print(", ".join([f"{var} = {solution[var].value}" for var in solution.keys()]))