import unittest
from adb_data_network.main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        # Basic test to ensure main can be called
        self.assertIsNone(main())

if __name__ == '__main__':
    unittest.main()
