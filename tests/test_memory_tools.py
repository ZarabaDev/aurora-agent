
import unittest
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.brain import AgentBrain
from agent_core.memory_tools import MemoryTools

class TestMemoryTools(unittest.TestCase):
    def setUp(self):
        # Initialize brain (requires OpenAI key in environment)
        self.brain = AgentBrain()
        self.memory_manager = MemoryTools(self.brain)

    def test_save_and_search(self):
        if not self.brain.vector_db:
            print("Skipping test: Vector DB not initialized (check API Key).")
            return

        # Unique test data
        import uuid
        secret_code = f"CODE-{uuid.uuid4()}"
        test_content = f"The secret verification code is {secret_code}."

        print(f"Saving: {test_content}")
        result_save = self.memory_manager.save_interaction(test_content)
        print(f"Save Result: {result_save}")
        self.assertIn("sucesso", result_save)

        print("Searching...")
        result_search = self.memory_manager.search_history(f"secret verification code")
        print(f"Search Result: {result_search}")
        
        self.assertIn(secret_code, result_search)

if __name__ == '__main__':
    unittest.main()
