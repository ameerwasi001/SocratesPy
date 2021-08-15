from knowledgeBase import KnowledgeBase
from visitors import make_expr
from unificationVisitor import Substitutions
import utils

with lovely_rules in SocraticSolver:
    loves[hanna, miles]
    loves[tom, tom]
    loves[simon, sara]
    # loves[A, B] = loves[B, A]
    narcissist[X] = loves[X, X]

for _, sub in lovely_rules.lookup(make_expr(Fact("loves", [Var("M"), Var("Z")]))):
    print(sub)

print("# Narcissist")

for _, sub in lovely_rules.lookup(make_expr(Fact("narcissist", [Var("Y")]))):
    print(sub)

print("---~~Mortality~~---")

with mortality_rules in SocraticSolver:
    human[miles]
    human[samael]
    male[samael]
    human[socrates]
    mortal[X] = human[X]
    mortal[Z] = boy[Z]
    boy[A] = male[A] & human[A]

for _, sub in mortality_rules.lookup(make_expr(Fact("mortal", [Var("O")]))):
    print(sub)

print("---~~Addition~~---")
with addition_rules in SocraticSolver:
    add[z, X, X]
    add[s[X], Y, s[Z]] = add[X, Y, Z]

for unifier, sub in addition_rules.lookup(make_expr(Fact("add", [Fact("s", [Fact("s", [Term("z")])]), Var("A"), Fact("s", [Fact("s", [Fact("s", [Fact("s", [Fact("s", [Term("z")])])])])])]))):
    print(utils.str_dict(Substitutions.optionally_resolve(unifier.env)), "results in", sub)

for _, sub in addition_rules.lookup(make_expr(Fact("add", [Var("A"), Fact("s/1", [Var("A")]), Fact("s/1", [Fact("s/1", [Fact("s/1", [Term("z")])])])]))):
    print(sub)

print("---~~List~~---")
with lst_rules in SocraticSolver:
    lst[nil]
    lst[cons[L, X]] = lst[X]

    lst_member[X, cons[X, M]]
    lst_member[X, cons[P, TAIL]] = lst_member[X, TAIL]

    lst_concat[nil, L, L]
    lst_concat[cons[X1, L1], L2, cons[X1, L3]] = lst_concat[L1, L2, L3]

lst1 = Fact("cons", [Term("x"), Fact("cons", [Term("y"), Term("nil")])])
lst2 = Fact("cons", [Term("a"), Fact("cons", [Term("b"), Term("nil")])])

for _, sub in lst_rules.lookup(make_expr(Fact("lst_member", [Term("x"), lst1]))):
    print(sub)

print("# Concatenation")
for unifier, _ in lst_rules.lookup(make_expr(Fact("lst_concat", [lst1, lst2, Var("Res")]))):
    print(utils.dict_as_eqs(Substitutions.optionally_resolve(unifier.env)))