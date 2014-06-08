#!/usr/bin/python

import ldif
from io import StringIO
from ldap.cidict import cidict

class LDAPSearchResult:
    """A class to model LDAP results.
    """

    dn = ''

    def __init__(self, entry_tuple):
        """Create a new LDAPSearchResult object."""
        (dn, attrs) = entry_tuple
        if dn:
            self.dn = dn
        else:
            return

        self.attrs = cidict(attrs)

    def get_attributes(self):
        """Get a dictionary of all attributes.
        get_attributes()->{'name1':['value1','value2',...], 
                                'name2: [value1...]}
        """
        return self.attrs

    def set_attributes(self, attr_dict):
        """Set the list of attributes for this record.

        The format of the dictionary should be string key, list of
        string alues. e.g. {'cn': ['M Butcher','Matt Butcher']}

        set_attributes(attr_dictionary)
        """

        self.attrs = cidict(attr_dict)

    def has_attribute(self, attr_name):
        """Returns true if there is an attribute by this name in the
        record.

        has_attribute(string attr_name)->boolean
        """
        return attr_name in self.attrs

    def get_attr_values(self, key):
        """Get a list of attribute values.
        get_attr_values(string key)->['value1','value2']
        """
        if key in self.attrs:
            return self.attrs[key]
        else:
            return []
    
    def get_attr_value(self, key, default=None):
        """Get the first attribute value.
        """
        if key in self.attrs:
            if type(self.attrs[key]) == type([]):
                return self.attrs[key][0]
            else:
                return self.attrs[key]
        else:
            return default

    def get_attr_names(self):
        """Get a list of attribute names.
        get_attr_names()->['name1','name2',...]
        """
        return list(self.attrs.keys())

    def get_dn(self):
        """Get the DN string for the record.
        get_dn()->string dn
        """
        return self.dn

                         
    def pretty_print(self):
        """Create a nice string representation of this object.

        pretty_print()->string
        """
        str = "DN: " + self.dn + "\n"
        for a, v_list in self.attrs.items():
            str = str + "Name: " + a + "\n"
            for v in v_list:
                str = str + "  Value: " + v + "\n"
        str = str + "========"
        return str

    def to_ldif(self):
        """Get an LDIF representation of this record.

        to_ldif()->string
        """
        out = StringIO()
        ldif_out = ldif.LDIFWriter(out)
        ldif_out.unparse(self.dn, self.attrs)
        return out.getvalue()
