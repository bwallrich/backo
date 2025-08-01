"""
all imports
"""

import sys

sys.path.insert(1, "../stricto")

from .test_crud import TestCRUD
from .test_log import TestLog

# from .test_mongo import TestMongo
from .test_action import TestAction
from .test_routes import TestRoutes
from .test_reference import TestReferences

# from .test_view import TestViews
from .test_api_toolbox import TestApiToolbox
