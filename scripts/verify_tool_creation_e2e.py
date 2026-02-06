# scripts/verify_tool_creation_e2e.py
import sys
import os
import time

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, ToolMessage
from agent_core.tool_loader import load_dynamic_tools
from agent_core.basic_tools import BASIC_TOOLS
from agent_core.brain import AgentBrain
from agent_core.planner import AgentPlanner

def test_e2e_creation():
    print("--- Teste End-to-End de Self-Build ---")
    
    # Setup
    tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools_library")
    target_tool_path = os.path.join(tools_dir, "timestamp_tool.py")
    
    # Cleanup before test
    if os.path.exists(target_tool_path):
        os.remove(target_tool_path)
        
    brain = AgentBrain()
    
    # Combine tools (Initially just basic tools + existing dynamic ones)
    dynamic_tools = load_dynamic_tools(tools_dir)
    all_tools = BASIC_TOOLS + dynamic_tools
    
    # The Prompt
    user_input = """
    Create a new python tool in tools_library called 'timestamp_tool.py'.
    The content should range:
    1. Import datetime
    2. Define TOOL_DESC = "Returns current timestamp"
    3. Define run(input_str) that returns str(datetime.datetime.now())
    Use the write_file tool to create it.
    """
    
    print(f"Goal: {user_input}")
    
    chat_history = [HumanMessage(content=user_input)]
    
    print("Thinking...")
    # Force the execution loop (simplified version of main.py)
    # We expect the agent to Call write_file
    
    found_write_call = False
    
    for i in range(3): # Max 3 steps to create the file
        response = brain.think(user_input, chat_history, tools=all_tools)
        chat_history.append(response)
        
        if response.tool_calls:
            for tool_call in response.tool_calls:
                name = tool_call["name"]
                args = tool_call["args"]
                print(f"  🛠️ Agent called: {name}({args})")
                
                if name == "write_file":
                    # Execute it
                    tool = next(t for t in all_tools if t.name == "write_file")
                    result = tool.invoke(args)
                    print(f"  ✅ Result: {result}")
                    
                    chat_history.append(ToolMessage(tool_call_id=tool_call["id"], content=str(result), name=name))
                    found_write_call = True
        else:
            print(f"  🤖 Agent says: {response.content}")
            if found_write_call:
                break
                
    # Validation
    if os.path.exists(target_tool_path):
        print("✅ SUCCESS: File 'timestamp_tool.py' was created!")
    else:
        print("❌ FAILURE: File was NOT created.")
        return

    # Phase 2: Verify if we can load and use it
    print("\nPhase 2: Verifying new tool usage...")
    new_dynamic_tools = load_dynamic_tools(tools_dir)
    new_tool = next((t for t in new_dynamic_tools if t.name == "timestamp_tool"), None)
    
    if new_tool:
        print("✅ SUCCESS: New tool loaded dynamically.")
        res = new_tool.run("")
        print(f"   Execution Result: {res}")
    else:
        print("❌ FAILURE: Could not load the new tool.")

if __name__ == "__main__":
    test_e2e_creation()
