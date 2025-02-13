"""
Unit test for Parameterized.
"""

import param
import numbergen

from . import API1TestCase
from .utils import MockLoggingHandler

# CEBALERT: not anything like a complete test of Parameterized!

import pytest

import random

from param.parameterized import ParamOverrides, shared_parameters
from param.parameterized import default_label_formatter, no_instance_params

class _SomeRandomNumbers(object):
    def __call__(self):
        return random.random()

class TestPO(param.Parameterized):
    __test__ = False

    inst = param.Parameter(default=[1,2,3],instantiate=True)
    notinst = param.Parameter(default=[1,2,3],instantiate=False, per_instance=False)
    const = param.Parameter(default=1,constant=True)
    ro = param.Parameter(default="Hello",readonly=True)
    ro2 = param.Parameter(default=object(),readonly=True,instantiate=True)
    ro_label = param.Parameter(default=object(), label='Ro Label')
    ro_format = param.Parameter(default=object())

    dyn = param.Dynamic(default=1)

class TestPOValidation(param.Parameterized):
    __test__ = False

    value = param.Number(default=2, bounds=(0, 4))

@no_instance_params
class TestPONoInstance(TestPO):
    __test__ = False
    pass

class AnotherTestPO(param.Parameterized):
    instPO = param.Parameter(default=TestPO(),instantiate=True)
    notinstPO = param.Parameter(default=TestPO(),instantiate=False)

class TestAbstractPO(param.Parameterized):
    __test__ = False

    __abstract = True

class _AnotherAbstractPO(param.Parameterized):
    __abstract = True

class TestParamInstantiation(AnotherTestPO):
    __test__ = False

    instPO = param.Parameter(default=AnotherTestPO(),instantiate=False)

class TestParameterized(API1TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestParameterized, cls).setUpClass()
        log = param.parameterized.get_logger()
        cls.log_handler = MockLoggingHandler(level='DEBUG')
        log.addHandler(cls.log_handler)

    def test_parameter_name_fixed(self):
        testpo = TestPO()

        with pytest.raises(AttributeError):
            testpo.param.const.name = 'notconst'

    def test_constant_parameter(self):
        """Test that you can't set a constant parameter after construction."""
        testpo = TestPO(const=17)
        self.assertEqual(testpo.const,17)
        self.assertRaises(TypeError,setattr,testpo,'const',10)

        # check you can set on class
        TestPO.const=9
        testpo = TestPO()
        self.assertEqual(testpo.const,9)


    def test_readonly_parameter(self):
        """Test that you can't set a read-only parameter on construction or as an attribute."""
        testpo = TestPO()
        self.assertEqual(testpo.ro,"Hello")

        with self.assertRaises(TypeError):
            t = TestPO(ro=20)

        t=TestPO()
        self.assertRaises(TypeError,setattr,t,'ro',10)

        # check you cannot set on class
        self.assertRaises(TypeError,setattr,TestPO,'ro',5)

        self.assertEqual(testpo.param.params()['ro'].constant,True)

        # check that instantiate was ignored for readonly
        self.assertEqual(testpo.param.params()['ro2'].instantiate,False)


    def test_basic_instantiation(self):
        """Check that instantiated parameters are copied into objects."""

        testpo = TestPO()

        self.assertEqual(testpo.inst,TestPO.inst)
        self.assertEqual(testpo.notinst,TestPO.notinst)

        TestPO.inst[1]=7
        TestPO.notinst[1]=7

        self.assertEqual(testpo.notinst,[1,7,3])
        self.assertEqual(testpo.inst,[1,2,3])


    def test_more_instantiation(self):
        """Show that objects in instantiated Parameters can still share data."""
        anothertestpo = AnotherTestPO()

        ### CB: AnotherTestPO.instPO is instantiated, but
        ### TestPO.notinst is not instantiated - so notinst is still
        ### shared, even by instantiated parameters of AnotherTestPO.
        ### Seems like this behavior of Parameterized could be
        ### confusing, so maybe mention it in documentation somewhere.
        TestPO.notinst[1]=7
        # (if you thought your instPO was completely an independent object, you
        # might be expecting [1,2,3] here)
        self.assertEqual(anothertestpo.instPO.notinst,[1,7,3])


    def test_instantiation_inheritance(self):
        """Check that instantiate=True is always inherited (SF.net #2483932)."""
        t = TestParamInstantiation()
        assert t.param.params('instPO').instantiate is True
        assert isinstance(t.instPO,AnotherTestPO)


    def test_abstract_class(self):
        """Check that a class declared abstract actually shows up as abstract."""
        self.assertEqual(TestAbstractPO.abstract,True)
        self.assertEqual(_AnotherAbstractPO.abstract,True)
        self.assertEqual(TestPO.abstract,False)


    def test_override_class_param_validation(self):
        test = TestPOValidation()
        test.param.value.bounds = (0, 3)
        with self.assertRaises(ValueError):
            test.value = 4
        TestPOValidation.value = 4


    def test_remove_class_param_validation(self):
        test = TestPOValidation()
        test.param.value.bounds = None
        test.value = 20
        with self.assertRaises(ValueError):
            TestPOValidation.value = 10


    def test_params(self):
        """Basic tests of params() method."""

        # CB: test not so good because it requires changes if params
        # of PO are changed
        assert 'name' in param.Parameterized.param.params()
        assert len(param.Parameterized.param.params()) in [1,2]

        ## check for bug where subclass Parameters were not showing up
        ## if params() already called on a super class.
        assert 'inst' in TestPO.param.params()
        assert 'notinst' in TestPO.param.params()

        ## check caching
        assert param.Parameterized.param.params() is param.Parameterized().param.params(), "Results of params() should be cached." # just for performance reasons


    def test_param_iterator(self):
        self.assertEqual(set(TestPO.param), {'name', 'inst', 'notinst', 'const', 'dyn',
                                             'ro', 'ro2', 'ro_label', 'ro_format'})


    def test_param_contains(self):
        for p in ['name', 'inst', 'notinst', 'const', 'dyn', 'ro', 'ro2']:
            self.assertIn(p, TestPO.param)


    def test_class_param_objects(self):
        objects = TestPO.param.objects()

        self.assertEqual(set(objects),
                         {'name', 'inst', 'notinst', 'const', 'dyn',
                          'ro', 'ro2', 'ro_label', 'ro_format'})

        # Check caching
        assert TestPO.param.objects() is objects


    def test_instance_param_objects(self):
        inst = TestPO()
        objects = inst.param.objects()

        for p, obj in objects.items():
            if p == 'notinst':
                assert obj is TestPO.param[p]
            else:
                assert obj is not TestPO.param[p]


    def test_instance_param_objects_set_to_false(self):
        inst = TestPO()
        objects = inst.param.objects(instance=False)

        for p, obj in objects.items():
            assert obj is TestPO.param[p]


    def test_instance_param_objects_set_to_current(self):
        inst = TestPO()
        inst_param = inst.param.inst
        objects = inst.param.objects(instance='existing')

        for p, obj in objects.items():
            if p == 'inst':
                assert obj is inst_param
            else:
                assert obj is TestPO.param[p]


    def test_instance_param_objects_warn_on_params(self):
        inst = TestPO()
        inst.param['inst']

        inst.param.params()
        if param.parameterized.Parameters._disable_stubs is None:
            self.log_handler.assertContains(
                'WARNING', 'The Parameterized instance has instance parameters')


    def test_instance_param_getitem(self):
        test = TestPO()
        assert test.param['inst'] is not TestPO.param['inst']


    def test_instance_param_getitem_not_per_instance(self):
        test = TestPO()
        assert test.param['notinst'] is TestPO.param['notinst']


    def test_instance_param_getitem_no_instance_params(self):
        test = TestPONoInstance()
        assert test.param['inst'] is TestPO.param['inst']


    def test_instance_param_getattr(self):
        test = TestPO()
        assert test.param.inst is not TestPO.param.inst

        # Assert no deep copy
        assert test.param.inst.default is TestPO.param.inst.default


    def test_pprint_instance_params(self):
        # Ensure pprint does not make instance parameter copies
        test = TestPO()
        test.pprint()
        for p, obj in TestPO.param.objects('current').items():
            assert obj is TestPO.param[p]


    def test_update_instance_params(self):
        # Ensure update does not make instance parameter copies
        test = TestPO()
        test.param.update(inst=3)
        for p, obj in TestPO.param.objects('current').items():
            assert obj is TestPO.param[p]


    def test_values_instance_params(self):
        # Ensure values does not make instance parameter copies
        test = TestPO()
        test.param.values()
        for p, obj in TestPO.param.objects('current').items():
            assert obj is TestPO.param[p]


    def test_defaults_instance_params(self):
        # Ensure defaults does not make instance parameter copies
        test = TestPO()
        test.param.defaults()
        for p, obj in TestPO.param.objects('current').items():
            assert obj is TestPO.param[p]


    def test_state_saving(self):
        t = TestPO(dyn=_SomeRandomNumbers())
        g = t.param.get_value_generator('dyn')
        g._Dynamic_time_fn=None
        assert t.dyn!=t.dyn
        orig = t.dyn
        t.state_push()
        t.dyn
        assert t.param.inspect_value('dyn')!=orig
        t.state_pop()
        assert t.param.inspect_value('dyn')==orig


    def test_label(self):
        t = TestPO()
        assert t.param.params('ro_label').label == 'Ro Label'

    def test_label_set(self):
        t = TestPO()
        assert t.param.params('ro_label').label == 'Ro Label'
        t.param.params('ro_label').label = 'Ro relabeled'
        assert t.param.params('ro_label').label == 'Ro relabeled'

    def test_label_default_format(self):
        t = TestPO()
        assert t.param.params('ro_format').label == 'Ro format'


    def test_label_custom_format(self):
        param.parameterized.label_formatter = default_label_formatter.instance(capitalize=False)
        t = TestPO()
        assert t.param.params('ro_format').label == 'ro format'
        param.parameterized.label_formatter = default_label_formatter

    def test_label_constant_format(self):
        param.parameterized.label_formatter = lambda x: 'Foo'
        t = TestPO()
        assert t.param.params('ro_format').label == 'Foo'
        param.parameterized.label_formatter = default_label_formatter


from param import parameterized

class some_fn(param.ParameterizedFunction):
    __test__ = False

    num_phase = param.Number(18)
    frequencies = param.List([99])
    scale = param.Number(0.3)

    def __call__(self,**params_to_override):
        params = parameterized.ParamOverrides(self,params_to_override)
        num_phase = params['num_phase']
        frequencies = params['frequencies']
        scale = params['scale']
        return scale,num_phase,frequencies

instance = some_fn.instance()

class TestParameterizedFunction(API1TestCase):

    def _basic_tests(self,fn):
        self.assertEqual(fn(),(0.3,18,[99]))
        self.assertEqual(fn(frequencies=[1,2,3]),(0.3,18,[1,2,3]))
        self.assertEqual(fn(),(0.3,18,[99]))

        fn.frequencies=[10,20,30]
        self.assertEqual(fn(frequencies=[1,2,3]),(0.3,18,[1,2,3]))
        self.assertEqual(fn(),(0.3,18,[10,20,30]))

    def test_parameterized_function(self):
        self._basic_tests(some_fn)

    def test_parameterized_function_instance(self):
        self._basic_tests(instance)

    def test_pickle_instance(self):
        import pickle
        s = pickle.dumps(instance)
        instance.scale=0.8
        i = pickle.loads(s)
        self.assertEqual(i(),(0.3,18,[10,20,30]))


class TestPO1(param.Parameterized):
    __test__ = False

    x = param.Number(default=numbergen.UniformRandom(lbound=-1,ubound=1,seed=1),bounds=(-1,1))
    y = param.Number(default=1,bounds=(-1,1))

class TestNumberParameter(API1TestCase):

    def test_outside_bounds(self):
        t1 = TestPO1()
        # Test bounds (non-dynamic number)
        try:
            t1.y = 10
        except ValueError:
            pass
        else:
            assert False, "Should raise ValueError."

    def test_outside_bounds_numbergen(self):
        t1 = TestPO1()
        # Test bounds (dynamic number)
        t1.x = numbergen.UniformRandom(lbound=2,ubound=3)  # bounds not checked on set
        try:
            t1.x
        except ValueError:
            pass
        else:
            assert False, "Should raise ValueError."


class TestStringParameter(API1TestCase):

    def setUp(self):
        super(TestStringParameter, self).setUp()

        class TestString(param.Parameterized):
            a = param.String()
            b = param.String(default='',allow_None=True)
            c = param.String(default=None)

        self._TestString = TestString

    def test_handling_of_None(self):
        t = self._TestString()

        with self.assertRaises(ValueError):
            t.a = None

        t.b = None

        assert t.c is None


class TestParameterizedUtilities(API1TestCase):

    def setUp(self):
        super(TestParameterizedUtilities, self).setUp()


    def test_default_label_formatter(self):
        assert default_label_formatter('a_b_C') == 'A b C'


    def test_default_label_formatter_not_capitalized(self):
        assert default_label_formatter.instance(capitalize=False)('a_b_C') == 'a b C'


    def test_default_label_formatter_not_replace_underscores(self):
        assert default_label_formatter.instance(replace_underscores=False)('a_b_C') == 'A_b_C'
    def test_default_label_formatter_overrides(self):
        assert default_label_formatter.instance(overrides={'a': 'b'})('a') == 'b'

class TestParamOverrides(API1TestCase):

    def setUp(self):
        super(TestParamOverrides, self).setUp()
        self.po = param.Parameterized(name='A',print_level=0)

    def test_init_name(self):
        self.assertEqual(self.po.name, 'A')

    def test_simple_override(self):
        overrides = ParamOverrides(self.po,{'name':'B'})
        self.assertEqual(overrides['name'], 'B')
        self.assertEqual(overrides['print_level'], 0)

    # CEBALERT: missing test for allow_extra_keywords (e.g. getting a
    # warning on attempting to override non-existent parameter when
    # allow_extra_keywords is False)

    def test_missing_key(self):
        overrides = ParamOverrides(self.po,{'name':'B'})
        with self.assertRaises(AttributeError):
            overrides['doesnotexist']


class TestSharedParameters(API1TestCase):

    def setUp(self):
        super(TestSharedParameters, self).setUp()
        with shared_parameters():
            self.p1 = TestPO(name='A', print_level=0)
            self.p2 = TestPO(name='B', print_level=0)
            self.ap1 = AnotherTestPO(name='A', print_level=0)
            self.ap2 = AnotherTestPO(name='B', print_level=0)

    def test_shared_object(self):
        self.assertTrue(self.ap1.instPO is self.ap2.instPO)
        self.assertTrue(self.ap1.param.params('instPO').default is not self.ap2.instPO)

    def test_shared_list(self):
        self.assertTrue(self.p1.inst is self.p2.inst)
        self.assertTrue(self.p1.param.params('inst').default is not self.p2.inst)


def test_inheritance_None_is_not_special_cased_default():

    class A(param.Parameterized):
        p = param.String(default='test')

    class B(A):
        p = param.String(default=None)

    b = B()

    assert b.p == 'test'


@pytest.mark.parametrize('attribute', [
    'default',
    'doc',
    'precedence',
    'readonly',
    'pickle_default_value',
    'per_instance',
    # These 3 parameters of Parameter are handled dynamically, instantiating
    # Parameter with their value to None doesn't lead to the attribute value
    # on Parameter being None.
    # 'instantiate',
    # 'constant',
    # 'allow_None',
])
def test_inheritance_None_is_not_special_cased(attribute):
    """
    Somewhat strange test as it's setting attributes of Parameter to None
    while it's not necessarily an allowed value. It's to test that it's no
    longer considered as a sentinel allowing inheritance.
    """

    class A(param.Parameterized):
        p = param.Parameter(**{attribute: 'test'})

    class B(A):
        p = param.Parameter(**{attribute: None})

    b = B()

    assert getattr(b.param.p, attribute) == 'test'


def test_inheritance_no_default_declared_in_subclass():
    default = 5.0
    class A(param.Parameterized):
        p = param.Number(default=default)

    class B(A):
        p = param.Number()

    b = B()
    assert b.p == 0.0


def test_inheritance_attribute_from_non_subclass_not_inherited():
    class A(param.Parameterized):
        p = param.String(doc='1')

    class B(A):
        p = param.Number()

    b = B()

    assert b.param.p.doc == '1'


def test_inheritance_sub_attribute_is_used():
    class A(param.Parameterized):
        p = param.String(doc='1')

    class B(A):
        p = param.String(doc='2')

    b = B()

    assert b.param.p.doc == '2'


def test_inheritance_default_is_not_None_in_sub():
    class A(param.Parameterized):
        p = param.String(default='1')

    class B(A):
        p = param.Number()

    b = B()

    assert b.p == 0.0


def test_inheritance_default_is_None_in_sub():
    class A(param.Parameterized):
        p = param.String(default='1')

    class B(A):
        p = param.Action()

    b = B()

    assert b.p == '1'


def test_inheritance_diamond_not_supported():
    """
    In regular Python, the value of the class attribute p on D is resolved
    to 2:

        class A:
            p = 1

        class B(A):
            pass

        class C(A):
            p = 2

        class D(B, C):
            pass

        assert D.p == 2

    This is not supported by Param (https://github.com/holoviz/param/issues/715).
    """

    class A(param.Parameterized):
        p = param.Parameter(default=1, doc='11')

    class B(A):
        p = param.Parameter()

    class C(A):
        p = param.Parameter(default=2, doc='22')

    class D(B, C):
        p = param.Parameter()

    assert D.p != 2
    assert D.param.p.doc != '22'
    assert D.p == 1
    assert D.param.p.doc == '11'

    d = D()

    assert d.p != 2
    assert d.param.p.doc != '22'
    assert d.p == 1
    assert d.param.p.doc == '11'


def test_inheritance_from_multiple_params_class():
    class A(param.Parameterized):
        p = param.Parameter(doc='foo')

    class B(A):
        p = param.Parameter(default=2)

    class C(B):
        p = param.Parameter(instantiate=True)

    assert A.param.p.instantiate is False
    assert A.param.p.default is None
    assert A.param.p.doc == 'foo'

    assert B.param.p.instantiate is False
    assert B.param.p.default == 2
    assert B.param.p.doc == 'foo'

    assert C.param.p.instantiate is True
    assert C.param.p.default == 2
    assert C.param.p.doc == 'foo'


def test_inheritance_from_multiple_params_inst():
    # Picked Parameters whose default value is None
    class A(param.Parameterized):
        p = param.Parameter(doc='foo')

    class B(A):
        p = param.Action(default=2)

    class C(B):
        p = param.Date(instantiate=True)

    a = A()
    b = B()
    c = C()

    assert a.param.p.instantiate is False
    assert a.param.p.default is None
    assert a.param.p.doc == 'foo'

    assert b.param.p.instantiate is False
    assert b.param.p.default == 2
    assert b.param.p.doc == 'foo'

    assert c.param.p.instantiate is True
    assert c.param.p.default == 2
    assert c.param.p.doc == 'foo'


def test_inheritance_from_multiple_params_intermediate_setting():
    class A(param.Parameterized):
        p = param.Parameter(doc='foo')

    A.param.p.default = 1
    A.param.p.doc = 'bar'

    class B(A):
        p = param.Action(default=2)

    assert A.param.p.default == 1
    assert A.param.p.doc == 'bar'

    assert B.param.p.default == 2
    assert B.param.p.doc == 'bar'

    a = A()
    b = B()

    assert a.param.p.default == 1
    assert a.param.p.doc == 'bar'

    assert b.param.p.default == 2
    assert b.param.p.doc == 'bar'


def test_inheritance_instantiate_behavior():
    class A(param.Parameterized):
        p = param.Parameter(instantiate=True)

    class B(A):
        p = param.Parameter(readonly=True)


    # Normally, param.Parameter(readonly=True, instantiate=True) ends up with
    # instantiate being False.
    assert B.param.p.instantiate is True

    b = B()

    assert b.param.p.instantiate is True


def test_inheritance_constant_behavior():
    class A(param.Parameterized):
        p = param.Parameter(readonly=True)

    class B(A):
        p = param.Parameter()


    # Normally, param.Parameter(readonly=True) ends up with constant being
    # True.
    assert B.param.p.constant is False

    b = B()

    assert b.param.p.constant is False


def test_inheritance_allow_None_behavior():
    class A(param.Parameterized):
        p = param.Parameter(default=1)

    class B(A):
        p = param.Parameter()

    # A computes allow_None to False, B sets it to True.
    assert A.param.p.allow_None !=  B.param.p.allow_None
    assert B.param.p.allow_None is True

    a = A()
    b = B()

    assert a.param.p.allow_None !=  b.param.p.allow_None
    assert b.param.p.allow_None is True


def test_inheritance_allow_None_behavior2():
    class A(param.Parameterized):
        p = param.Parameter(allow_None=False)
        
    class B(A):
        p = param.Parameter(default=None)


    # A says None is not allowed, B sets the default to None and recomputes
    # allow_None.
    assert B.param.p.allow_None is True

    b = B()

    assert b.param.p.allow_None is True


def test_inheritance_class_attribute_behavior():
    class A(param.Parameterized):
        p = param.Parameter(1)
        
    class B(A):
        p = param.Parameter()

    assert B.p == 1

    A.p = 2

    # Should be 2?
    # https://github.com/holoviz/param/issues/718
    assert B.p == 1
