# Import modules with version neutral

import sys

# unittest
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
