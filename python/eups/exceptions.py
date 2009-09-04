"""
exceptions raised by EUPS.  This includes EupsException, the base exception 
for EUPS related failures.  
"""
import sys, traceback

class EupsException(Exception):
    """
    an exception indicating a failure during an EUPS operation.
    """

    def __init__(self, message):
        """
        create the exception
        @param message  the message describing the failure.  
        """
        self.msg = message

    def __str__(self):
        """
        return the exception message
        """
        return self.getMessage()

    def getMessage(self):
        """
        return the exception message
        """
        return self.msg


class ProductNotFound(EupsException):
    """
    an exception indicating that the requested product was not found in 
    a stack database.

    An instance has the following public attributes:
        name     the product name
        version  the version.  A None value (default) means no product of 
                     any version was found.
        flavors  the platform flavors of interest.  A None value (default)
                     means that the flavor is unknown, though typically can
                     be assumed to mean any of the supportable platforms.
        stack    the path to the EUPS-managed software stack or to the 
                     database directory (ups_db).  A None value (default)
                     means that the flavor is unknown, though typically can
                     be assumed to mean any of the stacks in scope.
    """

    def __init__(self, name, version=None, flavors=None, stack=None, msg=None):
        """
        create the exception
        @param name     the product name
        @param version  the version.  Use None (default) if no product of 
                            any version was found.
        @param flavors   the platform flavors of interest.  default: None
        @param stack    the path to the EUPS-managed software stack or to the 
                           database directory (ups_db)
        @param msg      the descriptive message.  A default will be generated
                           from the product name.
        """
        message = msg
        if message is None:
            message = "Product " + name
            if version is not None:
                message += " %s" % version
            if flavors:
                message += " for %s" % str(flavors)
            message += " not found"
            if stack is not None:
                message += " in %s" % stack
        EupsException.__init__(self, message)
        self.name = name
        self.version = version
        if not isinstance(flavors, list):
            flavors = [flavors]
        self.flavors = flavors
        self.stack = stack

class UnderSpecifiedProduct(EupsException):
    """
    An exception indicating that not enough information about a product
    was provided to carry out a requested operation.  

    This exception includes the following public parameters, any of which 
    may be None (because they were either not provided by the user or not 
    relevent):
       name     the product name
       version  the version name
       flavor   the platform flavor
    """
    def __init__(self, productName=None, version=None, flavor=None, msg=None):
        """
        @param productName     the product name
        @param version  the version.  
        @param flavor   the platform flavor of interest.  
        @param msg      the descriptive message.  If None, A default will be 
                       generated from the product name
        """
        message = msg
        if message is None:
            message = "Under-specified product: " + str(productName)
            if version is not None:
                message += " ver: %s" % str(version)
            if flavor is not None:
                message += " flavor: %s" % str(flavor)

        EupsException.__init__(self, message)

        self.name = productName
        self.version = version
        self.flavor = flavor
        
class TablefileNotFound(EupsException):
    """
    This exception includes the following public parameters, any of which 
    may be None:
       tablefile  the path to the missing tablefile
       name       the product name
       version    the version name
       flavor     the platform flavor
    """

    def __init__(self, tablefile=None, productName=None, version=None, 
                 flavor=None, msg=None):
        """
        @param productName  the product name
        @param version      the version.  
        @param flavor       the platform flavor of interest.  
        @param msg          the descriptive message.  If None, A default will 
                               be generated.
        """
        message = msg
        if message is None:
            message = "Table file not found"
            if productName is not None:
                message += " for %s" % str(productName)
            if version is not None:
                message += " %s" % str(version)
            if flavor is not None:
                message += " (%s)" % str(flavor)
            if tablefile is not None:
                message += ": %s" % str(tablefile)

        EupsException.__init__(self, message)

        self.tablefile = tablefile
        self.name = productName
        self.version = version
        self.flavor = flavor
