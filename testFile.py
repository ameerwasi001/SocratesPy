from knowledgeBase import KnowledgeBase
from unificationVisitor import Substitutions
import utils

with lovely_rules in SocraticSolver:
    loves[hanna, miles]
    loves[simon, sara]
    loves[tom, tom]
    # loves[A, B] = loves[B, A]
    narcissist[X] = loves[X, X]

for sub in lovely_rules.lookup(Fact("loves", [Var("Y"), Var("Z")])):
    print(sub)

print("# Narcissist")

for sub in lovely_rules.lookup(Fact("narcissist", [Var("Y")])):
    print(sub)

print("---~~Mortality~~---")

with mortality_rules in SocraticSolver:
    human[miles]
    human[socrates]
    mortal[X] = human[X]


for sub in mortality_rules.lookup(Fact("mortal", [Var("O")])):
    # rx = utils.str_dict(Substitutions.optionally_resolve(unifier.env))
    print(sub)

print("---~~Addition~~---")
with addition_rules in SocraticSolver:
    add[z, X, X]
    add[s[X], Y, s[Z]] = add[X, Y, Z]

for sub in addition_rules.lookup(Fact("add", [Fact("s", [Fact("s", [Term("z")])]), Fact("s", [Fact("s", [Term("z")])]), Var("A")])):
    # rx = utils.str_dict(Substitutions.optionally_resolve(unifier.env))
    print(sub)