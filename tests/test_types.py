"""Tests for pycontract.types — Int, Float, Str, … singletons."""
import unittest
from pycontract.types import Any_, Bool, Dict, Float, Int, List, Str, Tuple


class TestInt(unittest.TestCase):
    def test_bare_accepts_int(self):    self.assertTrue(Int.check(1))
    def test_bare_rejects_str(self):    self.assertFalse(Int.check("1"))
    def test_gt_pass(self):             self.assertTrue((Int > 0).check(1))
    def test_gt_fail(self):             self.assertFalse((Int > 0).check(0))
    def test_ge_boundary(self):         self.assertTrue((Int >= 0).check(0))
    def test_lt(self):                  self.assertTrue((Int < 10).check(9))
    def test_le(self):                  self.assertTrue((Int <= 10).check(10))
    def test_eq(self):                  self.assertTrue((Int == 5).check(5))
    def test_ne(self):                  self.assertTrue((Int != 0).check(1))
    def test_between_in(self):          self.assertTrue(Int.between(1, 10).check(5))
    def test_between_boundary(self):    self.assertTrue(Int.between(1, 10).check(1))
    def test_between_exclusive(self):   self.assertFalse(Int.between(1, 10, inclusive=False).check(1))
    def test_rejects_float(self):       self.assertFalse((Int > 0).check(1.5))


class TestFloat(unittest.TestCase):
    def test_accepts_float(self):   self.assertTrue(Float.check(1.0))
    def test_accepts_int(self):     self.assertTrue(Float.check(1))   # int is valid for Float
    def test_rejects_str(self):     self.assertFalse(Float.check("x"))
    def test_gt(self):              self.assertTrue((Float > 0).check(0.1))
    def test_unit_in(self):
        c = Float.between(0, 1)
        for v in (0.0, 0.5, 1.0):
            self.assertTrue(c.check(v))
    def test_unit_out(self):
        c = Float.between(0, 1)
        for v in (-0.1, 1.1):
            self.assertFalse(c.check(v))


class TestStr(unittest.TestCase):
    def test_bare_pass(self):       self.assertTrue(Str.check("hi"))
    def test_bare_fail(self):       self.assertFalse(Str.check(1))
    def test_non_empty_pass(self):  self.assertTrue(Str.non_empty().check("x"))
    def test_non_empty_fail(self):  self.assertFalse(Str.non_empty().check(""))
    def test_min_len_pass(self):    self.assertTrue(Str.min_len(3).check("abc"))
    def test_min_len_fail(self):    self.assertFalse(Str.min_len(3).check("ab"))
    def test_max_len_pass(self):    self.assertTrue(Str.max_len(3).check("abc"))
    def test_max_len_fail(self):    self.assertFalse(Str.max_len(3).check("abcd"))
    def test_exact_len(self):       self.assertTrue(Str.len(3).check("abc"))
    def test_matches_pass(self):    self.assertTrue(Str.matches(r"[a-z]+").check("hello"))
    def test_matches_fail(self):    self.assertFalse(Str.matches(r"[a-z]+").check("Hello"))
    def test_matches_partial(self): self.assertFalse(Str.matches(r"[a-z]+").check("hello1"))


class TestList(unittest.TestCase):
    def test_bare_pass(self):       self.assertTrue(List.check([1, 2]))
    def test_bare_fail(self):       self.assertFalse(List.check((1, 2)))
    def test_non_empty_pass(self):  self.assertTrue(List.non_empty().check([1]))
    def test_non_empty_fail(self):  self.assertFalse(List.non_empty().check([]))
    def test_max_len_pass(self):    self.assertTrue(List.max_len(2).check([1, 2]))
    def test_max_len_fail(self):    self.assertFalse(List.max_len(2).check([1, 2, 3]))


class TestCombining(unittest.TestCase):
    def test_and_pass(self):
        c = (Int > 0) & (Int < 100)
        self.assertTrue(c.check(50))

    def test_and_fail_left(self):
        c = (Int > 0) & (Int < 100)
        self.assertFalse(c.check(0))

    def test_and_fail_right(self):
        c = (Int > 0) & (Int < 100)
        self.assertFalse(c.check(100))

    def test_or_left(self):
        c = (Int < 0) | (Int > 100)
        self.assertTrue(c.check(-1))

    def test_or_right(self):
        c = (Int < 0) | (Int > 100)
        self.assertTrue(c.check(101))

    def test_or_neither(self):
        c = (Int < 0) | (Int > 100)
        self.assertFalse(c.check(50))

    def test_not(self):
        c = ~(Int > 0)
        self.assertTrue(c.check(-1))
        self.assertFalse(c.check(1))


if __name__ == "__main__":
    unittest.main()