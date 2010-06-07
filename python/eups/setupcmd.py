"""
functions for processing the eups setup requests.  

To run setup from Python, try:

To run an eups command from Python, try:

    import sys
    import eups.setupcmd

    setup = eups.setupcmd.EupsSetup()
    status = setup.run()

The output of run() is a status code appropriate for passing to sys.exit().
"""
import os, sys, glob, re
from cmd import EupsOptionParser
from exceptions import EupsException
import eups
import hooks

_errstrm = sys.stderr

class EupsSetup(object):
    """
    A class for executing the EUPS command-line setup tool.

    """

    usage = "%prog [-h|--help|-V|--version] [options] [product [version]]"

    # set this to True if the description is preformatted.  If false, it 
    # will be automatically reformatted to fit the screen
    noDescriptionFormatting = False

    description = \
"""(Un)Setup an EUPS-managed product.  This will "load" (or "unload") the 
product and all its dependencies into the environment so that it can be used.
"""

    def __init__(self, args=None, toolname=None):
        self._errstrm = _errstrm

        if not toolname and len(sys.argv) > 0:
            toolname = hooks.config.Eups.setupCmdName
        if not toolname:
            toolname = "setup"
        self.prog = toolname

        if args is None:
            args = sys.argv[1:]
        self.clargs = args[:]

        self.clo = EupsOptionParser(self._errstrm, self.usage, 
                                    self.description, 
                                    not self.noDescriptionFormatting,
                                    self.prog)
        self.clo.enable_interspersed_args()
        self.addOptions()
        (self.opts, self.args) = self.clo.parse_args(args)

        if self.opts.quiet:
            self.opts.verbose = 0

    def run(self):
        if self.opts.help:
            self.clo.print_help()
            return 0

        elif self.opts.version:
            if not self.opts.quiet:
                self.err("EUPS Version: " + eups.version())
            return 0

        elif self.opts.list:
            if not self.opts.quiet:
                self.err('option -l|--list is no longer supported; use "eups list"')
            return 2
        elif self.opts.current:
            if not self.opts.quiet:
                self.err('option -C|--current is no longer supported; use "--tag"')
            return 2

        return self.execute()

    def addOptions(self):

        self.clo.add_option("-C", "--current", dest="current", action="store_true", default=False,
                            help="deprecated (use --tag=current)")
        self.clo.add_option("-Z", "--database", dest="path", action="store",
                            help="The colon-separated list of product stacks (databases) to use. " +
                            "Default: $EUPS_PATH")
        self.clo.add_option("--debug", dest="debug", action="store", default="",
                            help="turn on specified debugging behaviors (allowed: raise)")
        self.clo.add_option("-e", "--exact", dest="exact_version", action="store_true", default=False,
                            help="Don't use exact matching even though an explicit version is specified")
        self.clo.add_option("-f", "--flavor", dest="flavor", action="store",
                            help="Assume this target platform flavor (e.g. 'Linux')")
        self.clo.add_option("-F", "--force", dest="force", action="store_true", default=False,
                            help="Force requested behaviour")
        self.clo.add_option("-h", "--help", dest="help", action="store_true",
                            help="show command-line help and exit")
        self.clo.add_option("-i", "--ignore-versions", dest="ignoreVer", action="store_true", default=False,
                            help="Ignore any explicit versions in table files")
        self.clo.add_option("-E", "--inexact", dest="inexact_version", action="store_true", default=False,
                            help="Don't use exact matching even though an explicit version is specified")
        self.clo.add_option("-j", "--just", dest="nodepend", action="store_true", default=False,
                            help="Just setup product, no dependencies (equivalent to --max-depth 0)")
        self.clo.add_option("-k", "--keep", dest="keep", action="store_true", default=False,
                            help="Keep any products already setup (regardless of their versions)")
        self.clo.add_option("-l", "--list", dest="list", action="store_true", default=False,
                            help="deprecated (use 'eups list')")
        self.clo.add_option("-m", "--table", dest="tablefile", action="store", default=None,
                            help="Use this table file")
        self.clo.add_option("-S", "--max-depth", dest="max_depth", action="store", type="int", default=-1,
                            help="Only show this many levels of dependencies (use with -v)")
        self.clo.add_option("-n", "--noaction", dest="noaction", action="store_true", default=False,
                            help="Don\'t actually do anything (for debugging purposes)")
        self.clo.add_option("-q", "--quiet", dest="quiet", action="store_true", default=False,
                            help="Suppress messages to user (overrides -v)")
        self.clo.add_option("-r", "--root", dest="productDir", action="store",
                            help="root directory of requested product")
        self.clo.add_option("-z", "--select-db", dest="dbz", action="store", metavar="DIR",
                            help="Select the product paths which contain this directory.  " +
                            "Default: all in path")
        self.clo.add_option("-t", "--tag", dest="tag", action="store",
                            help="assign TAG to the specified product")
        self.clo.add_option("-T", "--type", dest="setuptype", action="store",
                            help="the setup type to assume (ignored unless -d is specified)")
        self.clo.add_option("-u", "--unsetup", dest="unsetup", action="store_true", default=False,
                            help="Unsetup the specifed product")
        self.clo.add_option("-v", "--verbose", dest="verbose", action="count", default=0,
                            help="Print extra messages about progress (repeat for ever more chat)")
        self.clo.add_option("-V", "--version", dest="version", action="store_true", default=False,
                            help="Print eups version number")
        self.clo.add_option("--vro", dest="vro", action="store", metavar="LIST",
                            help="Set the Version Resolution Order")

    def execute(self):
        
        if self.opts.exact_version and self.opts.inexact_version:
            self.err("Specifying --exact --inexact confuses me, so I'll ignore both")
            self.opts.exact_version = False
            self.opts.inexact_version = False

        productName = versionName = None
        if len(self.args) > 0:
            productName = self.args[0]
        if len(self.args) > 1:
            versionName = self.args[1]

        if self.opts.tablefile:         # we're setting up a product based only on a tablefile
            if self.opts.unsetup:
                self.err("Ignoring --table as I'm unsetting up a product")
                self.opts.tablefile = None
            else:
                if not os.path.exists(self.opts.tablefile):
                    self.err("%s does not exist" % self.opts.tablefile)
                    print >> self._errstrm, self.clo.get_usage()
                    return 3
                    
                self.opts.tablefile = os.path.abspath(self.opts.tablefile)

                if not productName:
                    self.opts.productDir = os.path.dirname(self.opts.tablefile)
                    productName = os.path.splitext(os.path.basename(self.opts.tablefile))[0]

        if not self.opts.productDir and not productName:
            self.err("please specify at least a product name or use -r")
            print >> self._errstrm, self.clo.get_usage()
            return 3

        if not versionName:
            if self.opts.verbose > 1:
                if self.opts.inexact_version:
                    #self.err("--inexact has no effect unless you request a specific version")
                    pass

                if self.opts.tag:
                    self.err("Will look for version with tag="+self.opts.tag)
                else:
                    self.err("Will look for version with most preferred tag")

        if versionName and not self.opts.inexact_version:
            self.opts.exact_version = True # if they specify a version, that's what they want
            if self.opts.verbose:
                self.err("Assuming --exact as you specified a version by name (consider --inexact)")

        if self.opts.productDir:
            self.opts.productDir = os.path.abspath(self.opts.productDir)
            try:
                productName = eups.utils.guessProduct(os.path.join(self.opts.productDir, "ups"), productName)
            except EupsException, e:
                e.status = 4
                raise

        if not productName:
            self.err("Please specify a product")
            print >> self._errstrm, self.clo.get_usage()
            return 3

        if self.opts.nodepend:
            if self.opts.max_depth > 0:
                self.err("You may not specify both --just and --max_depth")
                return 3
            self.opts.max_depth = 0

        if not self.opts.vro:
            self.opts.vro = hooks.config.Eups.VRO
        #
        # Do the work
        #
        status = 0
        try:
            Eups = eups.Eups(flavor=self.opts.flavor, path=self.opts.path, 
                             dbz=self.opts.dbz, # root=self.opts.productDir, 
                             readCache=False, force=self.opts.force,
                             quiet=self.opts.quiet, verbose=self.opts.verbose, 
                             noaction=self.opts.noaction, keep=self.opts.keep, 
                             ignore_versions=self.opts.ignoreVer,
                             max_depth=self.opts.max_depth, vro=self.opts.vro,
                             exact_version=self.opts.exact_version)

            # Set the VRO.  Note that the order of these tests is significant
            if self.opts.tag:
                vroTag = self.opts.tag
            elif self.opts.productDir:
                vroTag = "path"
            elif versionName:
                vroTag = "commandLineVersion"
            else:
                vroTag = "default"

            Eups.setVRO(vroTag, self.opts.dbz)

            if self.opts.verbose > 1:
                self.err("Using VRO for \"%s\": %s" % (vroTag, Eups.getVRO()))

            if self.opts.unsetup:
                cmdName = "unsetup"
            else:
                cmdName = "setup"
            
            try:
                eups.commandCallbacks.apply(Eups, cmdName, self.opts, self.args)
            except eups.OperationForbidden, e:
                e.status = 255
                raise
            except Exception, e:
                e.status = 9
                raise
                                  
            cmds = eups.setup(productName, versionName, self.opts.tag,
                              self.opts.productDir, self.opts.setuptype, 
                              Eups, fwd=not self.opts.unsetup, tablefile=self.opts.tablefile)

        except EupsException, e:
            e.status = 1
            raise
        except Exception, e:
            e.status = -1
            raise

        if Eups.verbose > 2:
            self.err("\n\t".join(["Issuing commands:"] + cmds))

        print ";\n".join(cmds)

        return status

    def err(self, msg, volume=0):
        """
        print an error message to standard error.  The message will only 
        be printed if "-q" was not set and volume <= the number of "-v"
        arguments provided. 
        """
        if not self.opts.quiet and self.opts.verbose >= volume:
            print >> self._errstrm, "%s: %s" % (self.prog, msg)

