#!/usr/bin/env python2
"""
Tests for eups.product
"""

import pdb                              # we may want to say pdb.set_trace()
import os
import sys
import unittest
import time
import testCommon
from testCommon import testEupsStack

from eups.Product import Product, TableFileNotFound
from eups.table import Table, BadTableContent
from eups.Eups import Eups

class TableTestCase1(unittest.TestCase):
    """test the Table class"""

    def setUp(self):
        os.environ["EUPS_PATH"] = testEupsStack
        self.tablefile = os.path.join(testEupsStack, "mwi.table")
        self.table = Table(self.tablefile)

    def testInit(self):
        self.assertEquals(self.table.file, self.tablefile)
        # Note: we add one to account for the default product
        self.assertEquals(len(self.table.actions("Darwin")), 14)
        self.assertEquals(len(self.table.actions("Linux")), 13)
        self.assertEquals(len(self.table.actions("Linux+2.1.2")), 14)
        self.assertEquals(len(self.table.actions("DarwinX86")), 14)

class TableTestCase2(unittest.TestCase):
    """test the Table class"""

    def setUp(self):
        self.environ0 = os.environ.copy()
        os.environ["EUPS_PATH"] = testEupsStack
        self.tablefile = os.path.join(testEupsStack, "tablesyntax.table")
        self.table = Table(self.tablefile)
        self.eups = Eups(flavor="Linux")
        for k in ["EIGEN_DIR",]:        # we're going to assert that it isn't set
            try:
                del os.environ[k]
            except KeyError:
                pass

    def tearDown(self):
        os.environ = self.environ0

    def testNoSetup(self):
        actions = self.table.actions("Linux")
        for action in actions:
            action.execute(self.eups, 1, True, True)
        self.assert_(os.environ.has_key("GOOBPATH"))
        self.assertEquals(os.environ["GOOBPATH"], 
                          "/home/user/goob:/usr/goob:/usr/local/goob")
        self.assert_(not os.environ.has_key("FOO"))
        self.assert_(not os.environ.has_key("BAR"))
        self.assert_(self.eups.aliases.has_key("longls"))
        self.assertEquals(self.eups.aliases["longls"], "ls -l")

        # undo
        for action in actions:
            action.execute(self.eups, 1, False, True)
        self.assert_(not os.environ.has_key("FOO"))
        self.assert_(not os.environ.has_key("BAR"))
        self.assert_(os.environ.has_key("GOOBPATH"))
        self.assertEquals(os.environ["GOOBPATH"], '')

    def testIfFlavor(self):
        actions = self.table.actions("DarwinX86")
        for action in actions:
            action.execute(self.eups, 1, True, True)
        self.assert_(os.environ.has_key("GOOBPATH"))
        self.assert_(os.environ.has_key("FOO"))
        self.assertEquals(os.environ["FOO"], "1")
        self.assert_(not os.environ.has_key("BAR"))

        # undo
        for action in actions:
            action.execute(self.eups, 1, False, True)
        self.assert_(not os.environ.has_key("FOO"))
        self.assert_(not os.environ.has_key("BAR"))
        self.assert_(os.environ.has_key("GOOBPATH"))
        self.assertEquals(os.environ["GOOBPATH"], '')
        

    def testIfType(self):
        actions = self.table.actions("DarwinX86", "build")
        for action in actions:
            action.execute(self.eups, 1, True, True)
        self.assert_(os.environ.has_key("GOOBPATH"))
        self.assert_(os.environ.has_key("FOO"))
        self.assertEquals(os.environ["FOO"], "1")
        self.assert_(os.environ.has_key("BAR"))

        # undo
        for action in actions:
            action.execute(self.eups, 1, False, True)
        self.assert_(not os.environ.has_key("FOO"))
        self.assert_(os.environ.has_key("GOOBPATH"))
        self.assert_(os.environ.has_key("BAR"))
        self.assertEquals(os.environ["GOOBPATH"], '')
        self.assertEquals(os.environ["BAR"], '')

    def testSetup(self):
        actions = self.table.actions("Linux")
        for action in actions:
            action.execute(self.eups, 1, True)
        self.assert_(os.environ.has_key("GOOBPATH"))
        self.assert_(os.environ.has_key("SETUP_PYTHON"))
        self.assert_(os.environ.has_key("PYTHON_DIR"))
        self.assert_(os.environ.has_key("CFITSIO_DIR"))
        self.assert_(not os.environ.has_key("EIGEN_DIR"))

    def testEmptyBlock(self):
        actions = self.table.actions("Linux64")
        for action in actions:
            action.execute(self.eups, 1, True)
        self.assert_(os.environ.has_key("GOOBPATH"))
        self.assert_(not os.environ.has_key("FOO"))
        self.assert_(not os.environ.has_key("BAR"))

    def testEnvSetWithForce(self):
        """ensure use of force does not cause failure"""
        actions = self.table.actions("Linux")
        self.eups.force = True

        # the following will fail if bug referred to in [11454] exists
        for action in actions:
            action.execute(self.eups, 1, True)


class EmptyTableTestCase(unittest.TestCase):
    """
    test out an (effectively) empty table file
    """
    def setUp(self):
        os.environ["EUPS_PATH"] = testEupsStack
        self.tablefile = os.path.join(testEupsStack, "empty.table")
        self.table = Table(self.tablefile)
        self.eups = Eups()

    def testEmptyBlock(self):
        actions = self.table.actions("Linux64")
        for action in actions:
            action.execute(self.eups, 1, True)

class IfElseTestCase(unittest.TestCase):
    """
    Check that if ... else if ... else blocks work
    """
    def setUp(self):
        os.environ["EUPS_PATH"] = testEupsStack
        self.tablefile = os.path.join(testEupsStack, "ifElse.table")
        self.table = Table(self.tablefile)
        self.eups = Eups()

    def testEmptyBlock(self):
        for t in ("sdss", "sst", ""):
            actions = self.table.actions(None, t)
            for action in actions:
                action.execute(self.eups, 1, True)

            if not t:
                t = "other"

            self.assertEqual(os.environ["FOO"].lower(), t)
                

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def suite(makeSuite=True):
    """Return a test suite"""

    return testCommon.makeSuite([
        EmptyTableTestCase,
        TableTestCase1,
        TableTestCase2,
        IfElseTestCase,
        ], makeSuite)

def run(shouldExit=False):
    """Run the tests"""
    testCommon.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)
