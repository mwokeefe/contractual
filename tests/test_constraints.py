"""Tests for pycontract.constraints — the raw constraint nodes."""

import unittest
from pycontract.constraints import (
    _And,
    _Between,
    _Compare,
    _ExactLen,
    _IsInstance,
    _Matches,
    _MaxLen,
    _MinLen,
    _NonEmpty,
    _Not,
    _Or,
)


class TestCompare(unittest.TestCase):
    def test_gt(self):
        self.assertTrue(_Compare(">", 0).check(1))

    def test_gt_fail(self):
        self.assertFalse(_Compare(">", 0).check(0))

    def test_ge(self):
        self.assertTrue(_Compare(">=", 0).check(0))

    def test_lt(self):
        self.assertTrue(_Compare("<", 10).check(9))

    def test_le(self):
        self.assertTrue(_Compare("<=", 10).check(10))

    def test_eq(self):
        self.assertTrue(_Compare("==", 5).check(5))

    def test_ne(self):
        self.assertTrue(_Compare("!=", 5).check(4))

    def test_type_error_false(self):
        self.assertFalse(_Compare(">", 0).check("hello"))

    def test_describe(self):
        self.assertEqual(_Compare(">", 0).describe(), "value > 0")

    def test_cross_param_reference(self):
        c = _Compare(">", "lo")
        self.assertTrue(c.check(5, {"lo": 3}))
        self.assertFalse(c.check(2, {"lo": 3}))


class TestBetween(unittest.TestCase):
    def test_inclusive_in(self):
        c = _Between(0, 10)
        for v in (0, 5, 10):
            self.assertTrue(c.check(v))

    def test_inclusive_out(self):
        c = _Between(0, 10)
        for v in (-1, 11):
            self.assertFalse(c.check(v))

    def test_exclusive_boundary(self):
        c = _Between(0, 10, inclusive=False)
        self.assertFalse(c.check(0))
        self.assertFalse(c.check(10))
        self.assertTrue(c.check(5))

    def test_describe_brackets(self):
        self.assertIn("[", _Between(0, 10).describe())
        self.assertIn("(", _Between(0, 10, inclusive=False).describe())


class TestMatches(unittest.TestCase):
    def test_match(self):
        self.assertTrue(_Matches(r"\d+").check("123"))

    def test_no_match(self):
        self.assertFalse(_Matches(r"\d+").check("abc"))

    def test_partial_fails(self):
        self.assertFalse(_Matches(r"\d+").check("12abc"))


class TestLen(unittest.TestCase):
    def test_min_pass(self):
        self.assertTrue(_MinLen(3).check("abc"))

    def test_min_fail(self):
        self.assertFalse(_MinLen(3).check("ab"))

    def test_max_pass(self):
        self.assertTrue(_MaxLen(3).check("abc"))

    def test_max_fail(self):
        self.assertFalse(_MaxLen(3).check("abcd"))

    def test_exact_pass(self):
        self.assertTrue(_ExactLen(3).check("abc"))

    def test_exact_fail(self):
        self.assertFalse(_ExactLen(3).check("ab"))


class TestNonEmpty(unittest.TestCase):
    def test_list_truthy(self):
        self.assertTrue(_NonEmpty().check([1]))

    def test_list_empty(self):
        self.assertFalse(_NonEmpty().check([]))

    def test_str_truthy(self):
        self.assertTrue(_NonEmpty().check("x"))

    def test_str_empty(self):
        self.assertFalse(_NonEmpty().check(""))


class TestIsInstance(unittest.TestCase):
    def test_match(self):
        self.assertTrue(_IsInstance(int).check(1))

    def test_no_match(self):
        self.assertFalse(_IsInstance(int).check("x"))

    def test_multi(self):
        self.assertTrue(_IsInstance((int, float)).check(1.0))


class TestLogical(unittest.TestCase):
    def test_and_both_pass(self):
        self.assertTrue(_And(_Compare(">", 0), _Compare("<", 10)).check(5))

    def test_and_left_fail(self):
        self.assertFalse(_And(_Compare(">", 0), _Compare("<", 10)).check(-1))

    def test_and_right_fail(self):
        self.assertFalse(_And(_Compare(">", 0), _Compare("<", 10)).check(15))

    def test_or_left(self):
        self.assertTrue(_Or(_Compare("<", 0), _Compare(">", 10)).check(-1))

    def test_or_right(self):
        self.assertTrue(_Or(_Compare("<", 0), _Compare(">", 10)).check(11))

    def test_or_neither(self):
        self.assertFalse(_Or(_Compare("<", 0), _Compare(">", 10)).check(5))

    def test_not_true(self):
        self.assertTrue(_Not(_Compare(">", 0)).check(-1))

    def test_not_false(self):
        self.assertFalse(_Not(_Compare(">", 0)).check(1))

    def test_operator_and(self):
        c = _Compare(">", 0) & _Compare("<", 10)
        self.assertTrue(c.check(5))
        self.assertFalse(c.check(0))

    def test_operator_or(self):
        c = _Compare("<", 0) | _Compare(">", 10)
        self.assertTrue(c.check(-1))
        self.assertFalse(c.check(5))

    def test_operator_invert(self):
        c = ~_Compare(">", 0)
        self.assertTrue(c.check(-1))
        self.assertFalse(c.check(1))


if __name__ == "__main__":
    unittest.main()
