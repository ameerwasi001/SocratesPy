
x = 4
k = ''
from nodes import Var, Fact, Rule, Rules
rules = Solver({'human': [Rule(Fact('human', [Fact('socrates', [])]), None), Rule(Fact('human', [Fact('miles', [])]), None)], 'mortal': [Rule(Fact('mortal', [Var('X'), Var('Y')]), Fact('human', [Fact('mortal', [Var('Y'), Var('X')])]))]})
