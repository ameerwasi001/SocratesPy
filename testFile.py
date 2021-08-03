from knowledgeBase import KnowledgeBase
from unificationVisitor import Substitutions
import utils

x = 4
k = ""

from knowledgeBase import KnowledgeBase
from unificationVisitor import Substitutions
import utils

x = 4
k = ""

with love_rules in SocraticSolver:
    loves[miles, sara]
    loves[tom, simon]
    loves[tom, tom]
    narcissist[X] = loves[X, X]

for unifier in love_rules.lookup(Fact("narcissist", [Var("O")])):
    rx = utils.str_dict(Substitutions.resolve(unifier.env))
    print(rx)

print(" ---- Mortality -----")

with mortality_rules in SocraticSolver:
    human[socrates]
    human[miles]
    boy[simon]
    adult[sara]
    mortal[X] = human[X]
    mortal[Z] = boy[Z]
    mortal[X] = adult[X]


for unifier in mortality_rules.lookup(Fact("mortal", [Var("O")])):
    rx = utils.str_dict(Substitutions.resolve(unifier.env))
    print(rx)
