
from knowledgeBase import KnowledgeBase
from unificationVisitor import Substitutions
import utils
x = 4
k = ''
from knowledgeBase import KnowledgeBase
from unificationVisitor import Substitutions
import utils
x = 4
k = ''
from nodes import Var, Term, Fact, Conjuction, Rule, Rules
love_rules = KnowledgeBase({'loves': [Rule(Fact('loves', [Term('miles'), Term('sara')]), None), Rule(Fact('loves', [Term('tom'), Term('simon')]), None), Rule(Fact('loves', [Term('tom'), Term('tom')]), None)], 'narcissist': [Rule(Fact('narcissist', [Var('X')]), Fact('loves', [Var('X'), Var('X')]))]})
for unifier in love_rules.lookup(Fact('narcissist', [Var('O')])):
    rx = utils.str_dict(Substitutions.resolve(unifier.env))
    print(rx)
print(' ---- Mortality -----')
from nodes import Var, Term, Fact, Conjuction, Rule, Rules
mortality_rules = KnowledgeBase({'human': [Rule(Fact('human', [Term('socrates')]), None), Rule(Fact('human', [Term('miles')]), None)], 'boy': [Rule(Fact('boy', [Term('simon')]), None)], 'adult': [Rule(Fact('adult', [Term('sara')]), None)], 'mortal': [Rule(Fact('mortal', [Var('X')]), Fact('human', [Var('X')])), Rule(Fact('mortal', [Var('Z')]), Fact('boy', [Var('Z')])), Rule(Fact('mortal', [Var('X')]), Fact('adult', [Var('X')]))]})
for unifier in mortality_rules.lookup(Fact('mortal', [Var('O')])):
    rx = utils.str_dict(Substitutions.resolve(unifier.env))
    print(rx)
