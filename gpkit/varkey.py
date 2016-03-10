"""Defines the VarKey class"""
from .small_classes import Strings, Quantity
from .small_classes import Counter
from .small_scripts import mag, unitstr


class VarKey(object):
    """An object to correspond to each 'variable name'.

    Arguments
    ---------
    name : str, VarKey, or Monomial
        Name of this Variable, or object to derive this Variable from.

    **kwargs :
        Any additional attributes, which become the descr attribute (a dict).

    Returns
    -------
    VarKey with the given name and descr.
    """
    new_unnamed_id = Counter()
    subscripts = ["models", "idx"]
    eq_ignores = frozenset(["units", "value"])
    # ignore value in ==. Also skip units, since pints is weird and the unitstr
    #    will be compared anyway

    def __init__(self, name=None, **kwargs):
        self.descr = kwargs
        # Python arg handling guarantees 'name' won't appear in kwargs
        if isinstance(name, VarKey):
            self.descr.update(name.descr)
        elif hasattr(name, "c") and hasattr(name, "exp"):
            if mag(name.c) == 1 and len(name.exp) == 1:
                var = list(name.exp)[0]
                self.descr.update(var.descr)
            else:
                raise TypeError("variables can only be formed from monomials"
                                " with a c of 1 and a single variable")
        else:
            if name is None:
                name = "\\fbox{%s}" % VarKey.new_unnamed_id()
            self.descr["name"] = str(name)

        from . import units as ureg  # update in case user has disabled units

        if "value" in self.descr:
            value = self.descr["value"]
            if isinstance(value, Quantity):
                self.descr["value"] = value.magnitude
                self.descr["units"] = value/value.magnitude
        if ureg and "units" in self.descr:
            units = self.descr["units"]
            if isinstance(units, Strings):
                units = units.replace("-", "dimensionless")
                self.descr["units"] = Quantity(1.0, units)
            elif isinstance(units, Quantity):
                self.descr["units"] = units/units.magnitude
            else:
                raise ValueError("units must be either a string"
                                 " or a Quantity from gpkit.units.")
        self._hashvalue = hash(self.str_without("model", "models"))  # HACK
        self.key = self
        self.descr["unitstr"] = self.make_unitstr()

    def __repr__(self):
        return self.str_without()

    def str_without(self, *excluded_fields):
        string = self.name
        for subscript in self.subscripts:
            if subscript in self.descr and subscript not in excluded_fields:
                substring = self.descr[subscript]
                if subscript == "models":
                    substring = ", ".join(substring)
                string += "_%s" % (substring,)
        if self.shape and not self.idx:
            string = "\\vec{%s}" % string  # add vector arrow for veckeys
        return string

    @property
    def allstrs(self):
        strings = set([str(self), self.name, self.latex()])
        strings.update(self.str_without(ss) for ss in self.subscripts)
        return strings

    def __getattr__(self, attr):
        return self.descr.get(attr, None)

    def make_unitstr(self):
        units = unitstr(self.units, r"~\mathrm{%s}", "L~")
        units_tf = units.replace("frac", "tfrac").replace(r"\cdot", r"\cdot ")
        return units_tf if units_tf != r"~\mathrm{-}" else ""

    def latex(self):
        string = self.name
        for subscript in self.subscripts:
            if subscript in self.descr:
                string = "{%s}_{%s}" % (string, self.descr[subscript])
                if subscript == "idx":
                    if len(self.descr["idx"]) == 1:
                        # drop the comma for 1-d vectors
                        string = string[:-3]+string[-2:]
        if self.shape and not self.idx:
            string = "\\vec{%s}" % string  # add vector arrow for veckeys
        return string

    def _repr_latex_(self):
        return "$$"+self.latex()+"$$"

    def __hash__(self):
        return self._hashvalue

    def __eq__(self, other):
        if not hasattr(other, "descr"):
            return False
        if self.descr["name"] != other.descr["name"]:
            return False
        keyset = set(self.descr.keys())
        keyset = keyset.symmetric_difference(other.descr.keys())
        if keyset - self.eq_ignores:
            return False
        for key in self.descr:
            if key not in self.eq_ignores:
                if self.descr[key] != other.descr[key]:
                    return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)
