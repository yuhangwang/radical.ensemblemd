#!/usr/bin/env python

"""TODO: Docstring.
"""

__author__    = "Ole Weider <ole.weidner@rutgers.edu>"
__copyright__ = "Copyright 2014, http://radical.rutgers.edu"
__license__   = "MIT"

from radical.ensemblemd.execution_context import ExecutionContext


#-------------------------------------------------------------------------------
#
class StaticExecutionContext(ExecutionContext):
    """A static execution context provides a fixed set of computational 
       resources. 
    """

    def __init__(self):
        """Creates a new ExecutionContext instance.
        """