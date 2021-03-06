#!/usr/bin/env python

import os
import sys
import pvl
import re

def find_keyword(obj, key, group=None):
    if group is not None:
        return find_keyword(obj[group], key)
    if key is None or obj is None:
        return None
    elif key in obj:
        return obj[key]
    for k, v in obj.items():
        if isinstance(v, dict):
            F_item = find_keyword(v, key)
            if F_item is not None:
                return F_item

def lower_keys(x):
    if isinstance(x, list):
        return [lower_keys(v) for v in x]
    elif isinstance(x, dict):
        return dict((k.lower(), lower_keys(v)) for k, v in x.items())
    else:
        return x

class UPCkeywords(object):

    label = None

    def __init__(self, input_pvl):
        if isinstance(input_pvl, str):
            try:
                self.label = lower_keys(pvl.load(input_pvl, strict=False))
            except:
                # Some labels are poorly formatted or include characters that
                #  cannot be parsed with the PVL library.  This finds those
                #  characters and replaces them so that we can properly parse
                #  the PVL.
                with open(input_pvl, 'r') as f:
                    filedata = f.read()

                filedata = filedata.replace(';', '-').replace('&', '-')
                filedata = re.sub(r'\-\s+', r'', filedata, flags=re.M)

                with open(input_pvl, 'w') as f:
                    f.write(filedata)

                self.label = lower_keys(pvl.load(input_pvl, strict=False))

        elif isinstance(input_pvl, pvl.PVLModule):
            self.label = lower_keys(input_pvl)


    def __str__(self):
        return(str(self.label))


    def getKeyword(self, keyword):
        Gkey = find_keyword(self.label, keyword.lower())
        return Gkey
