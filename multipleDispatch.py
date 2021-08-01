class MultipleDispatch:
    def __init__(self):
        self.cases = {}
        self.default = None

    def addCase(self, *nodes):
        def f(func):
            self.cases[tuple(nodes)] = func
        return f

    def defaultCase(self, f):
        self.default = f
        return f

    def dispatch(self, *args):
        types = tuple(map(type, args))
        current_case = self.cases.get(types)
        if current_case == None:
            if self.default == None: raise Exception("No method with types " + str(types) + " found, and no default exists")
            current_case = self.default
        return current_case(*args)

    def __call__(self, *args):
        return self.dispatch(*args)

    def __str__(self):
        return "{" + ", ".join([str(k) + ": " + f.__name__ for k, f in self.cases.items()]) + "}"
