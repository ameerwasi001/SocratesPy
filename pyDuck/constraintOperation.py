from enum import Enum, Flag, auto

class ConstraintOperationResult(Flag):
    Satisfied = 0x1
    Violated = 0x2
    Undecided = 0x4
    Propogated = 0x8