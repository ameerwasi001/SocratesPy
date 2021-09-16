class Var:
    def __init__(self, value):
        self.name = value

    def __str__(self):
        return "var " + self.name

    def __eq__(self, other):
        if not isinstance(other, Var): return False
        return self.name == other.name

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(str(self))

class Term:
    def __init__(self, value):
        self.name = value
    
    def __str__(self):
        return str(self.name)

    def __eq__(self, other):
        if not isinstance(other, Term): return False
        return self.name == other.name

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash("term "+str(self))

class Fact:
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __len__(self):
        return len(self.args)

    def __str__(self):
        return f"{self.name}({', '.join(list(map(str, self.args)))})" if len(self.args) > 0 else f"{self.name}"

    def __eq__(self, other):
        if not isinstance(other, Fact): return False
        return self.name == other.name and len(self.args) == len(other.args) and all([a == b for a, b in zip(self.args, other.args)])

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(str(self))

class Conjuction:
    def __init__(self, right, left):
        self.right = right
        self.left = left
    
    def __str__(self):
        return f"{str(self.right)} |&| {str(self.left)}"

    def __eq__(self, other):
        if not isinstance(other, Conjuction): return False
        return self.right == other.right and self.left == other.left

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(str(self))

class Goals:
    def __init__(self, _list):
        self.goals = _list

    def __len__(self):
        return len(self.goals)

    def __str__(self):
        return f"{' & '.join(map(str, self.goals))}"
    
    def __eq__(self, other):
        if not isinstance(other, Goals): return False
        return len(self.goals) == len(other.goals) and all([a == b for a, b in zip(self.goals, other.goals)])

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(str(self))

class Rule:
    def __init__(self, fact, condition=None):
        self.fact = fact
        self.condition = condition

    def __str__(self):
        return f"{str(self.fact)}" if self.condition == None else f"{str(self.fact)} :- {str(self.condition)}"

    def __eq__(self, other):
        if not isinstance(other, Rule): return False
        return self.fact == other.fact and self.condition == other.condition

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(str(self))

class BinOp:
    def __init__(self, a, op, b):
        self.left = a
        self.op = op
        self.right = b

    def __str__(self):
        return f"({str(self.left)} {self.op} {str(self.right)})"

    def __eq__(self, other):
        if not isinstance(other, BinOp): return False
        return self.right == other.right and self.op == other.op and self.left == other.left

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(str(self))

class Rules:
    def __init__(self, given=None):
        self.env = {} if given==None else given
    
    def add(self, name, thing):
        current = self.env.get(name)
        if current == None:
            self.env[name] = [thing]
        else:
            self.env[name].append(thing)

    def __str__(self):
        new_env = {}
        for k, v in self.env.items():
            new_env[k] = list(map(str, v))
        return str(new_env)