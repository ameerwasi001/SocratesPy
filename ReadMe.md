# SocratesPy
Embedded constraint logic programming for python written in native python, by using python's versatile native syntax. This library utilizes the subscript syntax of python to preserve closer connection with prolog and internally transforms that into a data structure that is then easily and efficiently, extensible and interpolable from native python. It's about time, I introduce SocratesPy's syntax.

## How to use this library
This library can work in two ways but only the first one is implemented right now, and the one that's implemented is transpiling a python file(for instance testFile.py) to another file(for instance transpiledTestFile.py), and you should use this command for this `[this repo's main.py] testFile.py transpiledTestFile.py`.

The second method is mre interesting and would allow for all of the compilation to be done at runtime but that still remains unimplemented.

## Syntax
To begin writing a knowledgebase, you must first write
```
with rules in SocraticSolver:
```
where `SocraticSolver` is always constant and used to denote that this is a beginning of a new knowledgebase and rules is the variable to which this knowledgebase is assigned to. After this, you'd want to add your rules to your knowledgebase, and here's how you'd do that, let's now begin to examine the syntax of rules, facts, and atoms.
```
with rules in SocraticSolver:
    human[socrates]
    human[plato]
```
So, now you could query this knowledgebase like this.
```
for _, rule in rules.lookup(SocraticQuery(human[socrates])):
    print(rule)
```
Every iteration yields a unifier(more on that later) and a matched rule. This rule in this case yields just a `human[socrates]`. Now let's examine a slightly more advance knowledgebase.
```
with rules in SocraticSolver:
    human[socrates]
    human[plato]
    mortal[X] = human[X]
```
Here `mortal[X] = human[X]` means everything that is a human is a mortal. Now you could query
```
for _, rule in rules.lookup(SocraticQuery(mortal[socrates])):
    print(rule)
```
which would yield `mortal[socrates]` but what happens when you query
```
for _, rule in rules.lookup(SocraticQuery(mortal[A])):
    print(rule)
```
is more interesting, since it would now print
```
mortal(socrates)
mortal(plato)
```
Since this is not a tutorial for logic programming, I would dive straight into conjunctions.
```
fish[tuna]
fish[salmon]
fish[platypus]

mammal[elephant]
mammal[platypus]
mammal[whale]

weird[X] = mammal[X] & fish[X]
```
Here the `&` denotes conjunction meaning both of these things must be true, here it means that X is weird if and only if X is a mammal and a fish. Now you could query something like this
```
for unifier, rule in rules.lookup(SocraticQuery(weird[Z])):
    print(rule)
```
which yields `weird[platypus]`. At this point we have covered most of the syntax and more examples would easily be found in `testFile.py`.

## Integers and Constraints
This library features a pure python constraint solver with constraint propagation and backtracking that currently only provides constraints on integers but not on lists. This constraint solver only works in finite domains and numbers by default are restricted to 0..255 but soon enough there will be an option to change that. It is important to note that search is automatically performed if constraints alone fail at providing a complete solution. Here's how you'd use it to find all numbers that, when multiplied results 50 in certain bounds.
```
multiplyTo50[A, B] = (A > 0) & (B > 0) & (A*B == 50)
```
Which looked up using the ususal methods would yield
```
multiplyTo50(1, 50)
multiplyTo50(2, 25)
multiplyTo50(5, 10)
multiplyTo50(10, 5)
multiplyTo50(25, 2)
multiplyTo50(50, 1)
```
There exist more sophisticated examples that exist in `testFile.py`. Note, that the only operators available right now are `+`, `-`, `*`, `/`, `>`, `==`, and `>=`.

## The Unifier
The unifier is the object that contains the substitutions that when applied would transform your original query into your result. You can see this information as a bunch of equations like this
```
utils.dict_as_eqs(Substitutions.optionally_resolve(unifier.env))
```
`utils.dict_as_eqs` is a utility function that represents a dictionary as a bunch of equations, for instance it would, given the dictionary `{a: 5, x: 12}` return `a = 5, x = 12`. Here `Substitutions` class having the method `optionally_resolve` would resolve this unifier's environment(which is where the actual relations and data is stored) but does not raise an exception when a unbounded relation is encountered.

Getting defined variables is also easy
```
unifier.env.get_variable("Z")
```
which with the aforementioned query and knowledgebase, would return `platypus`. Again a few examples can be seen in `testFile.py`.
