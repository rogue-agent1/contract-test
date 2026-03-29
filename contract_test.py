#!/usr/bin/env python3
"""Consumer-driven contract testing for API compatibility."""
import sys, json, re

class Contract:
    def __init__(self, consumer, provider):
        self.consumer,self.provider = consumer,provider
        self.interactions = []
    def add_interaction(self, description, request, expected_response):
        self.interactions.append({"description":description,"request":request,"expected":expected_response})

class ContractVerifier:
    def __init__(self): self.results = []
    def verify(self, contract, provider_fn):
        for interaction in contract.interactions:
            actual = provider_fn(interaction["request"])
            expected = interaction["expected"]
            errors = self._compare(expected, actual)
            passed = len(errors) == 0
            self.results.append({"description":interaction["description"],"passed":passed,"errors":errors})
        return all(r["passed"] for r in self.results)
    def _compare(self, expected, actual, path="$"):
        errors = []
        if isinstance(expected, dict):
            for key in expected:
                if key not in actual: errors.append(f"{path}.{key}: missing")
                else: errors.extend(self._compare(expected[key], actual[key], f"{path}.{key}"))
        elif isinstance(expected, type):
            if not isinstance(actual, expected): errors.append(f"{path}: expected {expected.__name__}, got {type(actual).__name__}")
        elif expected != actual:
            errors.append(f"{path}: expected {expected}, got {actual}")
        return errors

class MockProvider:
    def __init__(self): self.stubs = {}
    def stub(self, method, path, response):
        self.stubs[(method, path)] = response
    def handle(self, request):
        key = (request.get("method","GET"), request.get("path","/"))
        return self.stubs.get(key, {"status":404,"body":{}})

def main():
    contract = Contract("frontend", "user-service")
    contract.add_interaction("get user by id",
        {"method":"GET","path":"/users/1"},
        {"status":200,"body":{"id":int,"name":str,"email":str}})
    contract.add_interaction("create user",
        {"method":"POST","path":"/users"},
        {"status":201,"body":{"id":int}})
    mock = MockProvider()
    mock.stub("GET","/users/1",{"status":200,"body":{"id":1,"name":"Alice","email":"alice@test.com"}})
    mock.stub("POST","/users",{"status":201,"body":{"id":2}})
    verifier = ContractVerifier()
    passed = verifier.verify(contract, mock.handle)
    print(f"  Contract verified: {passed}")
    for r in verifier.results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['description']}")
        for e in r["errors"]: print(f"    - {e}")

if __name__ == "__main__": main()
