
x = 4
k = ''
from nodes import Var, Term, Fact, Rule, Rules
rules = Solver({'human': [Rule(Fact('human', [Term('socrates')]), None), Rule(Fact('human', [Term('miles')]), None)], 'mortal': [Rule(Fact('mortal', [Var('X'), Var('Y')]), Fact('human', [Fact('mortal', [Var('Y'), Fact('human', [Var('X')])])]))]})
