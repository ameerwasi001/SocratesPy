from knowledgeBase import KnowledgeBase
from unificationVisitor import Substitutions
import utils

with lovely_rules in SocraticSolver:
    loves[hanna, miles]
    loves[tom, tom]
    loves[simon, sara]
    # loves[A, B] = loves[B, A]
    narcissist[X] = loves[X, X]

for _, sub in lovely_rules.lookup(Fact("loves", [Var("M"), Var("Z")])):
    print(sub)

print("# Narcissist")

for _, sub in lovely_rules.lookup(Fact("narcissist", [Var("Y")])):
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

for _, sub in mortality_rules.lookup(Fact("mortal", [Var("O")])):
    print(sub)

print("---~~Addition~~---")
with addition_rules in SocraticSolver:
    add[z, X, X]
    add[s[X], Y, s[Z]] = add[X, Y, Z]

for unifier, sub in addition_rules.lookup(Fact("add", [Fact("s", [Fact("s", [Term("z")])]), Var("A"), Fact("s", [Fact("s", [Fact("s", [Fact("s", [Fact("s", [Term("z")])])])])])])):
    print(utils.str_dict(Substitutions.optionally_resolve(unifier.env)), "results in", sub)

for _, sub in addition_rules.lookup(Fact("add", [Var("A"), Fact("s", [Var("A")]), Fact("s", [Fact("s", [Fact("s", [Term("z")])])])])):
    print(sub)