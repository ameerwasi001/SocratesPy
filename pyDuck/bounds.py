from fixedint import UInt32, UInt64
from enum import Enum, auto

class DomainOperationResult(Enum):
    EmptyDomain = 0
    ElementNotInDomain = 1
    RemoveSuccessful = 2
    InstantiateSuccessful = 3

class Domain:
    def initialize_from_nothing(self):
        new_bounds = Domain(1)
        self.internalize(new_bounds)

    def initialize_from_one_int(self, domain_size):
        if domain_size < 0: raise Exception("Negative Domain Sizes are invalid")
        self._lower_bound = 0
        self._upper_bound = domain_size
        self._size = self._upper_bound - self._lower_bound + 1
        self.domain = list(map(UInt32, range(0, (domain_size + 1) // self.BITS_PER_DATATYPE if (domain_size + 1) % self.BITS_PER_DATATYPE == 0
             else (domain_size + 1) // self.BITS_PER_DATATYPE + 1)))
        for i in range(len(self.domain)):
            self.domain[i] = self.ALLSET
        if (domain_size + 1) % self.BITS_PER_DATATYPE == 0:
            self.domain[len(self.domain) - 1] = self.ALLSET
        else:
            for i in range(len(self.domain)):
                self.domain[len(self.domain) - 1] |= UInt32(0x1 << i)

    def initialize_from_two_int(self, lower_bound, upper_bound):
        self.internalize(Domain(upper_bound + (-lower_bound if lower_bound < 0 else 0)))
        if self._lower_bound < 0: self.offset = -self._lower_bound
        self._lower_bound = max((lower_bound, 0))
        self.size = upper_bound - lower_bound + 1
        count = 0
        while count < lower_bound:
            self.remove_from_domain(count)
            count += 1

    def internalize(self, bounds):
        self._lower_bound = bounds._lower_bound
        self._upper_bound = bounds._upper_bound
        self.domain = bounds.domain
        self._size = bounds._size
        self.offset = bounds.offset

    @property
    def lower_bound(self):
        return self._lower_bound - self.offset

    @lower_bound.setter
    def lower_bound(self, value):
        self._lower_bound = value

    @property
    def upper_bound(self):
        return self._upper_bound - self.offset

    @upper_bound.setter
    def upper_bound(self, value):
        self._upper_bound = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    def __init__(self, *args):
        self.ALLSET = UInt32(0xFFFFFFFF)
        self.BITS_PER_DATATYPE = 8*4
        self.domain = None
        self._lower_bound = None
        self._upper_bound = None
        self.size = None
        self.offset = 0

        constructors = {
                0: self.initialize_from_nothing, 
                1: self.initialize_from_one_int,
                2: self.initialize_from_two_int,
            }
        constructors[len(args)](*args)

    def __contains__(self, i):
        return self.is_in_domain(i)

    def is_in_domain(self, index):
        index += self.offset
        return (self.domain[(index + 1) // self.BITS_PER_DATATYPE - 1 if ((index + 1) % self.BITS_PER_DATATYPE == 0) else
				(index + 1) // self.BITS_PER_DATATYPE] & UInt64(0x1 << (index % self.BITS_PER_DATATYPE))) != 0

    def remove_from_domain(self, index):
        index += self.offset
        subscript = (index + 1) // self.BITS_PER_DATATYPE - 1 if ((index + 1) % self.BITS_PER_DATATYPE == 0) else (index + 1) // self.BITS_PER_DATATYPE
        self.domain[subscript] = self.domain[subscript] & UInt32(~(0x1 << (index % self.BITS_PER_DATATYPE)))
        return self.domain[subscript]

    def instantiated(self):
        return self._lower_bound == self._upper_bound

    def remove(self, elem, res_ref):
        res_ref["result"] = DomainOperationResult.EmptyDomain
        if elem < -self.offset or (not self.is_in_domain(elem)):
            res_ref["result"] = DomainOperationResult.ElementNotInDomain
            return

        self.remove_from_domain(elem)

        if self.size == 1:
            self.size = 0
            self._lower_bound = self._upper_bound + 1
            return

        if elem + self.offset == self._lower_bound:
            while self._lower_bound <= self._upper_bound and not self.is_in_domain(self._lower_bound - self.offset):
                self._lower_bound += 1
                self.size -= 1
        elif elem + self.offset == self._upper_bound:
            while self._upper_bound >= self._lower_bound and not self.is_in_domain(self._upper_bound - self.offset):
                self._upper_bound -= 1
                self.size -= 1

        if self._lower_bound > self._upper_bound or self.size == 0:
            return

        res_ref["result"] = DomainOperationResult.RemoveSuccessful

    def instantiate(self, *args):
        methods = {
                1: self.instantiate_from_nothing,
                2: self.instantiate_from_int,
            }
        methods[len(args)](*args)

    def instantiate_from_nothing(self, res_ref): self.instantiate_lowest(res_ref)
    def instantiate_from_int(self, value, res_ref):
        if not self.is_in_domain(value):
            res_ref["result"] = DomainOperationResult.ElementNotInDomain
            return
        self.size = 1
        self._upper_bound = value - self.offset
        self._lower_bound = self._upper_bound
        res_ref["result"] = DomainOperationResult.InstantiateSuccessful

    def instantiate_lowest(self, res_ref):
        if not self.is_in_domain(self._lower_bound - self.offset):
            res_ref["result"] = DomainOperationResult.ElementNotInDomain;
            return;
        self.size = 1;
        self._upper_bound = self._lower_bound;
        res_ref["result"] = DomainOperationResult.InstantiateSuccessful;

    def clone(self):
        clone = Domain()
        clone.domain = self.domain[:]
        clone._lower_bound = self._lower_bound
        clone._upper_bound = self._upper_bound
        clone.size = self.size
        clone.offset = self.offset
        return clone

    @staticmethod
    def CreateDomain(*args):
        methods = {
                1: Domain.CreateDomainFromElems,
                2: Domain.CreateDomainFromTwoInts,
            }
        return methods[len(args)](*args)

    @staticmethod
    def CreateDomainFromElems(elems):
        lower_bound = min(elems)
        upper_bound = max(elems)
        domain_impl = Domain(lower_bound, upper_bound)
        i = lower_bound
        while i <= upper_bound:
            if not (i in elems): domain_impl.remove_from_domain(i)
            i += 1
        return domain_impl

    @staticmethod
    def CreateDomainFromTwoInts(lower_bound, upper_bound):
        if lower_bound > upper_bound: raise Exception("Negative Domain Sizes are invalid")
        domain_impl = Domain(lower_bound, upper_bound)
        return domain_impl

    def instantiated_value(self):
        if not self.instantiated(): raise Exception("Trying to access InstantiatedValue of an uninstantiated domain.")
        return self._lower_bound - self.offset

    def __eq__(self, other):
        if isinstance(other, Domain):
            return self.__dict__ == other.__dict__
        return False

    def __neq__(self, other):
        return not self == other

    def __iter__(self):
        i = self._lower_bound - self.offset
        while i <= self._upper_bound - self.offset:
            if self.is_in_domain(i): yield i
            i += 1

    def __str__(self):
        return "[" + ", ".join(map(str, iter(self))) + "]"
