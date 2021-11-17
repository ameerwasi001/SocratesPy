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
    human["Samael"]
    male["Samael"]
    male[jordon]
    male[jim]
    human[socrates]
    mortal[X] = human[X]
    mortal[Z] = boy[Z]
    boy[A] = male[A] & human[A]

    parent[miles, "Samael"]
    parent[sara, "Samael"]
    parent[amanda, "Samael"]
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
    lst[cons[_, X]] = lst[X]

    lst_length[Xs, L] = lst_length[Xs, 0, L]

    lst_length[nil, L, L]
    lst_length[cons[X, Xs], T, L] = (L>T) & (T1 == T+1) & lst_length[Xs, T1, L]

    lst_member[X, cons[X, _]]
    lst_member[X, cons[_, TAIL]] = lst_member[X, TAIL]

    lst_concat[nil, L, L]
    lst_concat[cons[X1, L1], L2, cons[X1, L3]] = lst_concat[L1, L2, L3]

    lst_reverse[nil, nil]
    lst_reverse[cons[H, T], RevList] = lst_reverse[T, RevT] & lst_concat[RevT, cons[H, nil], RevList]

lst1 = Fact("cons", [Term("x"), Fact("cons", [Term("y"), Term("nil")])])
lst2 = Fact("cons", [Term("a"), Fact("cons", [Term("b"), Term("nil")])])

for _, sub in lst_rules.lookup(make_expr(Fact("lst_member", [Term("x"), lst1]))):
    print(sub)

print("# Concatenation")
for unifier, _ in lst_rules.lookup(SocraticQuery(
    lst_concat[cons[x, cons[y, nil]], cons[a, cons[b, nil]], Res] & lst_reverse[Res, Rev]
    )):
    print(utils.dict_as_eqs(Substitutions.optionally_resolve(unifier.env)))

print("# Count Members")
for unifier, _ in lst_rules.lookup(SocraticQuery(lst_length[cons[a, cons[b, cons[c, nil]]], X])):
    print(utils.dict_as_eqs(Substitutions.optionally_resolve(unifier.env)))

print("---~~Numbers~~---")
with num_rules in SocraticSolver:
    semantic_trial[X, Y, Z] = (Y == X+1) & inc[Y, Z] & (Z == X+2)
    inc[X, Y] = Y == X+1

    fac[0, 1]
    fac[N, F] = (N > 0) & (F1 > 0) & (N1 == N-1) & (F == N*F1) & fac[N1, F1]

    safediv[A, B, X] = (A / B == X) & (B > 0) & (X >= 1)
    multiplyTo50[A, B] = (A*B == 50)

for _, sub in num_rules.lookup(SocraticQuery(semantic_trial[L, 8, N])):
    print(sub)

print("# Numbers that multiply upto 50")
for _, sub in num_rules.lookup(SocraticQuery(multiplyTo50[X, Y])):
    print(sub)

print("# Factorial")
for unifier, _ in num_rules.lookup(SocraticQuery(fac[4, F])):
    print(utils.dict_as_eqs(Substitutions.optionally_resolve(unifier.env)))