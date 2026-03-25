"""
test for CRUD()
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
from backo import Logger, Log_level


class TestLog(unittest.TestCase):
    """
    Log test
    """

    def test_log_error(self):
        """
        log an error
        """
        log_system = Logger()
        log1 = log_system.get_or_create_logger("test_1", Log_level.DEBUG)
        log2 = log_system.get_or_create_logger("test_2", Log_level.DEBUG)
        filehandler = log_system.set_filehandler("/dev/null")
        log_system.add_handler(filehandler, "test_1")
        # must do nothing
        log_system.add_handler(filehandler, "dontexists")

        self.assertEqual(log1.get_last_message(), None)
        self.assertEqual(log2.get_last_message(), None)
        memory_handler = log_system.set_memoryhandler(filehandler)
        log_system.add_handler(memory_handler, "test_1")
        self.assertEqual(log1.get_last_message(), None)
        self.assertEqual(log2.get_last_message(), None)
        log1.debug("hey baby")
        self.assertEqual(log1.get_last_message().message, "hey baby")
        self.assertEqual(log2.get_last_message(), None)
        log_system.setLevel(Log_level.INFO)
        log1.debug("hey baby 2")
        self.assertEqual(log1.get_last_message().message, "hey baby")
