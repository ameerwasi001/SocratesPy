class SocraticSyntaxError(Exception):
    def __init__(self, desc):
        self.desc = desc
        super().__init__(str(desc))

    def __str__(self): return f"SyntaxError: {self.desc}"
    def __repr__(self): return str(self)

class UnresolvedRelationException(Exception):
    def __init__(self, rel):
        self.rel = rel
        super().__init__(str(self))

    def __str__(self): return f"Could not resolve relation because none of {self.rel} has a known value"
    def __repr__(self): return str(self)

class UndefinedVariableException(Exception):
    def __init__(self, name, rels):
        self.name = name
        self.rels = rels
        super().__init__(str(self))

    def __str__(self): return f"Could not get variable {self.name}, since it has no definitions and is only related to {self.rels}"

class InternalErrorException(Exception):
    def __init__(self, desc):
        self.desc = desc
        super().__init__(str(self))

    def __str__(self): return f"Internal Error: {self.desc}\nThis is likely not because of anything you did but was probably a bug in the SocratesPy itself"
    def __repr__(self): return str(self)