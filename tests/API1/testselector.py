"""
Unit test for object selector parameters.

Originally implemented as doctests in Topographica in the file
testEnumerationParameter.txt
"""

import param
from . import API1TestCase
from.utils import check_defaults
from collections import OrderedDict


opts=dict(A=[1,2],B=[3,4],C=dict(a=1,b=2))


class TestSelectorParameters(API1TestCase):

    def setUp(self):
        super(TestSelectorParameters, self).setUp()
        class P(param.Parameterized):
            e = param.Selector([5,6,7])
            f = param.Selector(default=10)
            h = param.Selector(default=None)
            g = param.Selector([7,8])
            i = param.Selector([9],default=7, check_on_set=False)
            s = param.Selector(OrderedDict(one=1,two=2,three=3), default=3)
            p = param.Selector(dict(one=1,two=2,three=3), default=3)
            d = param.Selector(opts, default=opts['B'])

        self.P = P

    def _check_defaults(self, p):
        assert p.default is None
        assert p.allow_None is None
        assert p.objects == []
        assert p.compute_default_fn is None
        assert p.check_on_set is False
        assert p.names is None

    def test_defaults_class(self):
        class P(param.Parameterized):
            s = param.Selector()

        check_defaults(P.param.s, label='S')
        self._check_defaults(P.param.s)

    def test_defaults_inst(self):
        class P(param.Parameterized):
            s = param.Selector()

        p = P()

        check_defaults(p.param.s, label='S')
        self._check_defaults(p.param.s)

    def test_defaults_unbound(self):
        s = param.Selector()

        check_defaults(s, label=None)
        self._check_defaults(s)

    def test_unbound_default_inferred(self):
        s = param.Selector(objects=[0, 1, 2])

        assert s.default == 0

    def test_unbound_default_explicit(self):
        s = param.Selector(default=1, objects=[0, 1, 2])

        assert s.default == 1

    def test_unbound_default_check_on_set_inferred(self):
        s1 = param.Selector(objects=[0, 1, 2])
        s2 = param.Selector(objects=[])
        s3 = param.Selector(objects={})
        s4 = param.Selector()

        assert s1.check_on_set is True
        assert s2.check_on_set is False
        assert s3.check_on_set is False
        assert s4.check_on_set is False

    def test_unbound_default_check_on_set_explicit(self):
        s1 = param.Selector(check_on_set=True)
        s2 = param.Selector(check_on_set=False)

        assert s1.check_on_set is True
        assert s2.check_on_set is False

    def test_set_object_constructor(self):
        p = self.P(e=6)
        self.assertEqual(p.e, 6)

    def test_allow_None_is_None(self):
        p = self.P()
        assert p.param.e.allow_None is None
        assert p.param.f.allow_None is None
        assert p.param.g.allow_None is None
        assert p.param.h.allow_None is None
        assert p.param.i.allow_None is None
        assert p.param.s.allow_None is None
        assert p.param.d.allow_None is None

    def test_autodefault(self):
        class P(param.Parameterized):
            o1 = param.Selector([6, 7])
            o2 = param.Selector({'a': 1, 'b': 2})

        assert P.o1 == 6
        assert P.o2 == 1

        p = P()

        assert p.o1 == 6
        assert p.o2 == 1

    def test_get_range_list(self):
        r = self.P.param.params("g").get_range()
        self.assertEqual(r['7'],7)
        self.assertEqual(r['8'],8)

    def test_get_range_ordereddict(self):
        r = self.P.param.params("s").get_range()
        self.assertEqual(r['one'],1)
        self.assertEqual(r['two'],2)

    def test_get_range_dict(self):
        r = self.P.param.params("p").get_range()
        self.assertEqual(r['one'],1)
        self.assertEqual(r['two'],2)

    def test_get_range_mutable(self):
        r = self.P.param.params("d").get_range()
        self.assertEqual(r['A'],opts['A'])
        self.assertEqual(r['C'],opts['C'])
        self.d=opts['A']
        self.d=opts['C']
        self.d=opts['B']

    def test_set_object_outside_bounds(self):
        p = self.P(e=6)
        try:
            p.e = 9
        except ValueError:
            pass
        else:
            raise AssertionError("Object set outside range.")

    def test_set_object_setattr(self):
        p = self.P(e=6)
        p.f = 9
        self.assertEqual(p.f, 9)
        p.g = 7
        self.assertEqual(p.g, 7)
        p.i = 12
        self.assertEqual(p.i, 12)


    def test_set_object_not_None(self):
        p = self.P(e=6)
        p.g = 7
        try:
            p.g = None
        except ValueError:
            pass
        else:
            raise AssertionError("Object set outside range.")

    def test_set_object_setattr_post_error(self):
        p = self.P(e=6)
        p.f = 9
        self.assertEqual(p.f, 9)
        p.g = 7
        try:
            p.g = None
        except ValueError:
            pass
        else:
            raise AssertionError("Object set outside range.")

        self.assertEqual(p.g, 7)
        p.i = 12
        self.assertEqual(p.i, 12)

    def test_initialization_out_of_bounds(self):
        try:
            class Q(param.Parameterized):
                q = param.Selector([4], 5)
        except ValueError:
            pass
        else:
            raise AssertionError("Selector created outside range.")


    def test_initialization_no_bounds(self):
        try:
            class Q(param.Parameterized):
                q = param.Selector(10, default=5)
        except TypeError:
            pass
        else:
            raise AssertionError("Selector created without range.")

    def test_check_on_set_defined(self):
        class P(param.Parameterized):
            o1 = param.Selector(check_on_set=True)
            o2 = param.Selector(check_on_set=False)

        assert P.param.o1.check_on_set is True
        assert P.param.o2.check_on_set is False

        p = P()

        assert p.param.o1.check_on_set is True
        assert p.param.o2.check_on_set is False

    def test_check_on_set_empty_objects(self):
        class P(param.Parameterized):
            o = param.Selector()

        assert P.param.o.check_on_set is False

        p = P()

        assert p.param.o.check_on_set is False

    def test_check_on_set_else(self):
        class P(param.Parameterized):
            o = param.Selector(objects=[0, 1])

        assert P.param.o.check_on_set is True

        p = P()

        assert p.param.o.check_on_set is True

    def test_inheritance_behavior1(self):
        class A(param.Parameterized):
            p = param.Selector()

        class B(A):
            p = param.Selector()

        assert B.param.p.default is None
        assert B.param.p.objects == []
        assert B.param.p.check_on_set is False

        b = B()

        assert b.param.p.default is None
        assert b.param.p.objects == []
        assert b.param.p.check_on_set is False

    def test_inheritance_behavior2(self):
        class A(param.Parameterized):
            p = param.Selector([0, 1])

        class B(A):
            p = param.Selector()

        # B does not inherit objects from A but the default gets anyway auto-set
        # to 0 and check_on_set is False
        assert B.param.p.objects == []
        assert B.param.p.default == 0
        assert B.param.p.check_on_set is False

        b = B()

        assert b.param.p.objects == []
        assert b.param.p.default == 0
        assert b.param.p.check_on_set is False

    def test_inheritance_behavior3(self):
        class A(param.Parameterized):
            p = param.Selector(default=1, objects=[0, 1])

        class B(A):
            p = param.Selector()

        # B does not inherit objects from A but the default gets anyway set to 1
        # and check_on_set is False
        assert B.param.p.objects == []
        assert B.param.p.default == 1
        assert B.param.p.check_on_set is False

        b = B()

        assert b.param.p.objects == []
        assert b.param.p.default == 1
        assert b.param.p.check_on_set is False

    def test_inheritance_behavior4(self):
        class A(param.Parameterized):
            p = param.Selector([0, 1], check_on_set=False)

        class B(A):
            p = param.Selector()

        assert B.param.p.objects == []
        assert B.param.p.default == 0
        assert B.param.p.check_on_set is False

        b = B()

        assert b.param.p.objects == []
        assert b.param.p.default == 0
        assert b.param.p.check_on_set is False

    def test_inheritance_behavior5(self):
        class A(param.Parameterized):
            p = param.Selector([0, 1], check_on_set=True)

        class B(A):
            p = param.Selector()

        assert B.param.p.objects == []
        assert B.param.p.default == 0
        assert B.param.p.check_on_set is False

        b = B()

        assert b.param.p.objects == []
        assert b.param.p.default == 0
        assert b.param.p.check_on_set is False

    def test_inheritance_behavior6(self):
        class A(param.Parameterized):
            p = param.Selector(default=0, objects=[0, 1])

        class B(A):
            p = param.Selector(default=1)

        assert B.param.p.objects == []
        assert B.param.p.default == 1
        assert B.param.p.check_on_set is False

        b = B()

        assert b.param.p.objects == []
        assert b.param.p.default == 1
        assert b.param.p.check_on_set is False
