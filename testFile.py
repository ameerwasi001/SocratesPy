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

for _, sub in lovely_rules.lookup(SocraticQuery(loves[M, Z])):
    print(sub)

print("# Narcissist")

for _, sub in lovely_rules.lookup(SocraticQuery(narcissist[Y])):
    print(sub)

print("---~~Living~~---")

with life_rules in SocraticSolver:
    human[miles]
    human[samael]
    male[samael]
    male[jordon]
    male[jim]
    human[socrates]
    mortal[X] = human[X]
    mortal[Z] = boy[Z]
    boy[A] = male[A] & human[A]

    parent[miles, samael]
    parent[sara, samael]
    parent[amanda, samael]
    parent[steven, jordon]
    parent[laura, jordon]
    parent[cassandra, jim]

    father[A, X] = parent[A, X] & male[X]

    sibiling[A, B] = father[A, X] & father[B, X]
    child[X, A] = father[A, X]

print("# Mortal")
for _, sub in life_rules.lookup(SocraticQuery(mortal[O])):
    print(sub)

print("# Sibilings")
for _, sub in life_rules.lookup(SocraticQuery(sibiling[sara, M])):
    print(sub)

print("# Children")
for _, sub in life_rules.lookup(SocraticQuery(child[jordon, C])):
    print(sub)

print("---~~Addition~~---")
with addition_rules in SocraticSolver:
    add[0, X, X]
    add[s[X], Y, s[Z]] = add[X, Y, Z]

for unifier, sub in addition_rules.lookup(SocraticQuery(add[s[s[0]], A, s[s[s[s[s[0]]]]]])):
    print(utils.str_dict(Substitutions.optionally_resolve(unifier.env)), "results in", sub)

for _, sub in addition_rules.lookup(SocraticQuery(add[A, s[A], s[s[s[0]]]])):
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
for unifier, _ in lst_rules.lookup(SocraticQuery(lst_concat[cons[x, cons[y, nil]], cons[a, cons[b, nil]], Res])):
    print(utils.dict_as_eqs(Substitutions.optionally_resolve(unifier.env)))