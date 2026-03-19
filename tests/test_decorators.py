"""Tests for @contract and @invariant decorators."""

import unittest
import contractual
import contractual.config as cfg
from contractual import contract, invariant, Int, Float, Str
from contractual.exceptions import InvariantError, PostconditionError, PreconditionError


class TestContractParams(unittest.TestCase):
    def test_passes(self):
        @contract
        def f(x: Int > 0) -> int:
            return x

        self.assertEqual(f(1), 1)

    def test_precondition_raises(self):
        @contract
        def f(x: Int > 0) -> int:
            return x

        with self.assertRaises(PreconditionError) as ctx:
            f(0)
        self.assertIn("x=0", str(ctx.exception))

    def test_multiple_params(self):
        @contract
        def f(x: Int > 0, y: Float >= 0) -> float:
            return x + y

        self.assertEqual(f(1, 0.0), 1.0)
        with self.assertRaises(PreconditionError) as ctx:
            f(1, -1.0)
        self.assertIn("y=", str(ctx.exception))

    def test_unannotated_param_ignored(self):
        @contract
        def f(x: Int > 0, y) -> int:
            return x

        self.assertEqual(f(1, "anything"), 1)

    def test_default_args(self):
        @contract
        def f(x: Int > 0, y: Int > 0 = 5) -> int:
            return x + y

        self.assertEqual(f(1), 6)
        with self.assertRaises(PreconditionError):
            f(1, y=0)

    def test_kwargs(self):
        @contract
        def f(x: Int > 0) -> int:
            return x

        self.assertEqual(f(x=3), 3)

    def test_no_constraints_returns_original(self):
        def f(x):
            return x

        self.assertIs(contract(f), f)


class TestContractReturn(unittest.TestCase):
    def test_return_passes(self):
        @contract
        def f(x: Int) -> Int > 0:
            return x

        self.assertEqual(f(1), 1)

    def test_return_fails(self):
        @contract
        def f(x: Int) -> Int > 0:
            return -x

        with self.assertRaises(PostconditionError) as ctx:
            f(1)
        self.assertIn("return value", str(ctx.exception))


class TestContractIntrospection(unittest.TestCase):
    def test_metadata_attached(self):
        @contract
        def f(x: Int > 0, y: Str) -> Int:
            return x

        self.assertIn("x", f.__param_constraints__)
        self.assertIn("y", f.__param_constraints__)

    def test_functools_wraps(self):
        @contract
        def my_function(x: Int > 0) -> int:
            """Docstring."""
            return x

        self.assertEqual(my_function.__name__, "my_function")
        self.assertEqual(my_function.__doc__, "Docstring.")


class TestInvariant(unittest.TestCase):
    def _make_account(self):
        @invariant
        class BankAccount:
            balance: Float >= 0
            owner: Str.non_empty()

            def __init__(self, owner: str, balance: float) -> None:
                self.owner = owner
                self.balance = balance

            def deposit(self, amount: float) -> None:
                self.balance += amount

            def withdraw(self, amount: float) -> None:
                self.balance -= amount

        return BankAccount

    def test_valid_init(self):
        BankAccount = self._make_account()
        acc = BankAccount("Alice", 100.0)
        self.assertEqual(acc.balance, 100.0)

    def test_invalid_init_balance(self):
        BankAccount = self._make_account()
        with self.assertRaises(InvariantError) as ctx:
            BankAccount("Alice", -10.0)
        self.assertIn("balance", str(ctx.exception))

    def test_valid_method(self):
        BankAccount = self._make_account()
        acc = BankAccount("Alice", 100.0)
        acc.deposit(50.0)
        self.assertEqual(acc.balance, 150.0)

    def test_method_violates_invariant(self):
        BankAccount = self._make_account()
        acc = BankAccount("Alice", 100.0)
        with self.assertRaises(InvariantError) as ctx:
            acc.withdraw(200.0)
        self.assertIn("balance", str(ctx.exception))

    def test_empty_owner_violates(self):
        BankAccount = self._make_account()
        with self.assertRaises(InvariantError) as ctx:
            BankAccount("", 100.0)
        self.assertIn("owner", str(ctx.exception))

    def test_introspection(self):
        BankAccount = self._make_account()
        self.assertIn("balance", BankAccount.__invariant_constraints__)
        self.assertIn("owner", BankAccount.__invariant_constraints__)


class TestConfig(unittest.TestCase):
    def setUp(self):
        cfg.enable()

    def tearDown(self):
        cfg.enable()

    def test_disable_skips_contract(self):
        @contract
        def f(x: Int > 0) -> int:
            return x

        cfg.disable()
        self.assertEqual(f(-999), -999)

    def test_disable_skips_invariant(self):
        @invariant
        class C:
            x: Int > 0

            def __init__(self, v: int) -> None:
                self.x = v

        cfg.disable()
        c = C(-1)
        self.assertEqual(c.x, -1)

    def test_re_enable(self):
        @contract
        def f(x: Int > 0) -> int:
            return x

        cfg.disable()
        cfg.enable()
        with self.assertRaises(PreconditionError):
            f(-1)

    def test_top_level_shortcuts(self):
        contractual.disable()
        self.assertFalse(cfg.enabled)
        contractual.enable()
        self.assertTrue(cfg.enabled)


if __name__ == "__main__":
    unittest.main()
