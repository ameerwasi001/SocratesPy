class Symbol:
    def __init__(self, value):
        self.name = value
    
    def __str__(self):
        return self.name

class Var(Symbol):
    def __init__(self, value):
        super().__init__(value)

    def __str__(self):
        return "var " + self.name

class Fact:
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __len__(self):
        return len(self.args)

    def __str__(self):
        return f"{self.name}({', '.join(list(map(str, self.args)))})" if len(self.args) > 0 else f"{self.name}"

class Rule:
    def __init__(self, fact, condition=None):
        self.fact = fact
        self.condition = condition

    def __str__(self):
        return f"{str(self.fact)}" if self.condition == None else f"{str(self.fact)} :- {str(self.condition)}"

class Rules:
    def __init__(self):
        self.env = {}
    
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