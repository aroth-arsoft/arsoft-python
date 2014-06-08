#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

class syncrepl(object):
    def __init__(self, line=None):
        self._data = {}
        self._org_line = None
        self.parse(line)

    @staticmethod
    def _parse_key_value_line(line):
        ret = {}
        key_value_pairs = line.split(' ')
        keyno = 0
        while keyno < len(key_value_pairs):
            key_value_pair = key_value_pairs[keyno]
            if '=' in key_value_pair:
                #print(key_value_pair)
                equidx = key_value_pair.find('=', 0)
                key = key_value_pair[0:equidx]
                value = key_value_pair[equidx+1:]
                value_len = len(value)
                if value[0] == '"':
                    if value[value_len - 1] == '"':
                        ret[key] = value[1:value_len - 1]
                    else:
                        # continue value
                        value = value[1:]
                        #print('continue value of ' + key + ' value=' + value)
                        while keyno + 1 < len(key_value_pairs):
                            next_value = key_value_pairs[keyno + 1]
                            next_value_len = len(next_value)
                            if next_value[next_value_len - 1] == '"':
                                value = value + ' ' + next_value[0:next_value_len - 1]
                                break
                            else:
                                value = value + ' ' + next_value
                            keyno = keyno + 1
                        #print('got full value of ' + key + ' value=' + value)
                        ret[key] = value
                else:
                    ret[key] = value
            keyno = keyno + 1
        return ret

    @staticmethod
    def _copy_value(target, dict, keyname, default_value=None):
        if keyname in dict:
            target[keyname] = dict[keyname]
        else:
            target[keyname] = default_value

    @staticmethod
    def _contains_any(str, set):
        """Check whether 'str' contains ANY of the chars in 'set'"""
        return 1 in [c in str for c in set]

    @staticmethod
    def _need_quotes(value):
        if isinstance(value, str):
            return syncrepl._contains_any(value, ' ,=')
        else:
            return False
            
    def has_credentials(self):
        if self._data['binddn'] is not None:
            if self._data['bindmethod'] is None or self._data['bindmethod'] == 'simple':
                ret = True if self._data['credentials'] is not None else False
            elif self._data['bindmethod'] == 'gssapi':
                # assume that the keys are already available (krb5 ccache)
                ret = True
            else:
                # TODO add additional checks for more bind methods
                ret = False
        else:
            ret = False
        return ret

    def parse(self, line):
        if line is not None:
            key_value_dict = syncrepl._parse_key_value_line(line)
            self._org_line = line
        else:
            key_value_dict = {}
            self._org_line = None

        syncrepl._copy_value(self._data, key_value_dict, 'rid')
        syncrepl._copy_value(self._data, key_value_dict, 'provider')
        syncrepl._copy_value(self._data, key_value_dict, 'binddn')
        syncrepl._copy_value(self._data, key_value_dict, 'bindmethod')
        syncrepl._copy_value(self._data, key_value_dict, 'credentials')
        syncrepl._copy_value(self._data, key_value_dict, 'searchbase')
        syncrepl._copy_value(self._data, key_value_dict, 'filter', '(objectclass=*)')
        syncrepl._copy_value(self._data, key_value_dict, 'attrs', '*,+')
        syncrepl._copy_value(self._data, key_value_dict, 'scope', 'sub')
        syncrepl._copy_value(self._data, key_value_dict, 'type', 'refreshAndPersist')
        syncrepl._copy_value(self._data, key_value_dict, 'retry')
        syncrepl._copy_value(self._data, key_value_dict, 'timeout')
        syncrepl._copy_value(self._data, key_value_dict, 'schemachecking', 'off')
        
    def to_string(self):
        elems = []
        for (key, value) in self._data.items():
            if value is not None:
                if syncrepl._need_quotes(value):
                    key_value_pair = key + '="' + str(value) + '"'
                else:
                    key_value_pair = key + '=' + str(value)
                elems.append(key_value_pair)
        return ' '.join(elems)
    
    def original_string(self):
        return self._org_line

    def __str__(self):
        return self.to_string()

    def __getattr__(self, attr):
        if attr == '_data':
            self.__dict__['_data']
        else:
            return self.__dict__['_data'][attr]

    def __setattr__(self, attr, value):
        if attr == '_data':
            self.__dict__['_data'] = value
        else:
            #print(self.__dict__['_data'])
            self.__dict__['_data'][attr] = value


if __name__ == "__main__":
    line = '''rid=001 provider=ldaps://kdc01.example.com binddn="cn=dbroot,cn=config" bindmethod=simple credentials=QN1P5FYSPJdjssmAOlTqnlW6e searchbase="cn=config" type=refreshAndPersist retry="5 +" timeout=1'''
    s = syncrepl(line)
    print(s)


