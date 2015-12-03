#!/usr/bin/env python2
"""
Tests for eups.utils
"""

import pdb                              # we may want to say pdb.set_trace()
import os
import sys
import unittest
import time
import cStringIO
from testCommon import testEupsStack

from eups import utils

class UtilsTestCase(unittest.TestCase):

    def testPass(self):
        pass

    def testConfigProperty(self):
        err = cStringIO.StringIO()
#        err = sys.stderr
        gen = utils.ConfigProperty("alpha beta gamma".split(), "gen", err)
        gen.beta = utils.ConfigProperty("delta epsilon".split(), "gen.beta",err)
        gen.alpha = 'a'
        gen.beta.delta = 'bd'
        gen.beta.epsilon = 'be'
        gen.gamma = 'c'
        gen.beta = 'b'   # should fail
        msg = "gen.beta: Cannot over-write property with sub-properties\n"
        self.assertEquals(err.getvalue(), msg)
        gen.beta.zeta = 'bz'  # should fail
        msg += "gen.beta.zeta: No such property name defined\n"
        self.assertEquals(err.getvalue(), msg)


__all__ = "UtilsTestCase".split()        

if __name__ == "__main__":
    unittest.main()

