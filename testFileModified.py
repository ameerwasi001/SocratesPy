
from knowledgeBase import KnowledgeBase
from unificationVisitor import Substitutions
import utils
from nodes import Var, Term, Fact, Goals, Rule, Rules
lovely_rules = KnowledgeBase({'loves': [Rule(Fact('loves', [Term('hanna'), Term('miles')]), None), Rule(Fact('loves', [Term('tom'), Term('tom')]), None), Rule(Fact('loves', [Term('simon'), Term('sara')]), None)], 'narcissist': [Rule(Fact('narcissist', [Var('X')]), Fact('loves', [Var('X'), Var('X')]))]})
for (_, sub) in lovely_rules.lookup(Fact('loves', [Var('M'), Var('Z')])):
    print(utils.str_dict(Substitutions.optionally_resolve(_.env)), sub)
print('# Narcissist')
for (_, sub) in lovely_rules.lookup(Fact('narcissist', [Var('Y')])):
    print(sub)
print('---~~Mortality~~---')
from nodes import Var, Term, Fact, Goals, Rule, Rules
mortality_rules = KnowledgeBase({'human': [Rule(Fact('human', [Term('miles')]), None), Rule(Fact('human', [Term('socrates')]), None)], 'boy': [Rule(Fact('boy', [Term('samael')]), None)], 'mortal': [Rule(Fact('mortal', [Var('X')]), Fact('human', [Var('X')])), Rule(Fact('mortal', [Var('Z')]), Fact('boy', [Var('Z')]))]})
for (_, sub) in mortality_rules.lookup(Fact('mortal', [Var('O')])):
    print(sub)
print('---~~Addition~~---')
from nodes import Var, Term, Fact, Goals, Rule, Rules
addition_rules = KnowledgeBase({'add': [Rule(Fact('add', [Term('z'), Var('X'), Var('X')]), None), Rule(Fact('add', [Fact('s', [Var('X')]), Var('Y'), Fact('s', [Var('Z')])]), Fact('add', [Var('X'), Var('Y'), Var('Z')]))]})
for (unifier, sub) in addition_rules.lookup(Fact('add', [Fact('s', [Fact('s', [Term('z')])]), Var('A'), Fact('s', [Fact('s', [Fact('s', [Fact('s', [Fact('s', [Term('z')])])])])])])):
    print(utils.str_dict(Substitutions.optionally_resolve(unifier.env)), 'results in', sub)
for (_, sub) in addition_rules.lookup(Fact('add', [Var('A'), Fact('s', [Var('A')]), Fact('s', [Fact('s', [Fact('s', [Term('z')])])])])):
    print(sub)
