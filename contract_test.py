#!/usr/bin/env python3
"""contract_test - Design by contract: preconditions, postconditions, invariants."""
import sys, functools

class ContractError(Exception):
    pass

def requires(*conditions):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for cond in conditions:
                if not cond(*args, **kwargs):
                    raise ContractError(f"Precondition failed for {func.__name__}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def ensures(condition):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if not condition(result, *args, **kwargs):
                raise ContractError(f"Postcondition failed for {func.__name__}")
            return result
        return wrapper
    return decorator

def invariant(check):
    def decorator(cls):
        orig_init = cls.__init__
        def new_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            if not check(self):
                raise ContractError(f"Invariant violated after __init__")
        cls.__init__ = new_init
        for name in list(vars(cls)):
            method = getattr(cls, name)
            if callable(method) and not name.startswith("_"):
                def make_wrapper(m):
                    @functools.wraps(m)
                    def wrapper(self, *args, **kwargs):
                        result = m(self, *args, **kwargs)
                        if not check(self):
                            raise ContractError(f"Invariant violated after {m.__name__}")
                        return result
                    return wrapper
                setattr(cls, name, make_wrapper(method))
        return cls
    return decorator

def test():
    @requires(lambda x, y: y != 0)
    @ensures(lambda result, x, y: abs(result * y - x) < 1e-9)
    def safe_div(x, y):
        return x / y

    assert safe_div(10, 2) == 5.0
    try:
        safe_div(10, 0)
        assert False
    except ContractError:
        pass

    @invariant(lambda self: self.balance >= 0)
    class Account:
        def __init__(self, balance):
            self.balance = balance
        def deposit(self, amount):
            self.balance += amount
        def withdraw(self, amount):
            self.balance -= amount

    a = Account(100)
    a.deposit(50)
    assert a.balance == 150
    try:
        a.withdraw(200)
        assert False
    except ContractError:
        pass

    print("OK: contract_test")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Usage: contract_test.py test")
