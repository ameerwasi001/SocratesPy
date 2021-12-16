from enum import Enum

class DomainExceptionType(Enum):
    Negative = 0
    UnInstantiated = 1

class InvalidDomainException(Exception):
    def __init__(self, exception_type, domain) -> None:
        self.exception_type = exception_type
        self.domain = domain
        super().__init__(str(self))

    def __str__(self):
        if self.exception_type == DomainExceptionType.Negative: return "Negative Domain Sizes are invalid"
        elif self.exception_type == DomainExceptionType.UnInstantiated: return f"Trying to access InstantiatedValue of an uninstantiated domain {self.domain}"

    def repr(self): return str(self)

class UnsolvedException(Exception):
    def __init__(self) -> None:
        super().__init__(str(self))

    def __str__(self): 
        return "Not all variables are solved by constraint propogation, when the solution prompted for solution"

    def repr(self): return str(self)