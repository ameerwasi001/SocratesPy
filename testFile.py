x = 4
k = ""

with rules in SocraticSolver:
    human[socrates]
    human[miles]
    mortal[X, Y] = human[mortal[Y, human[X]]]