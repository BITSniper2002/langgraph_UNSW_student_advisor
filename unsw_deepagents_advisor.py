#!/usr/bin/env python3
"""
UNSW Course Advisor - Deep-agents based implementation
Supports sub-agents, TODO management, and a virtual file system.
"""

from operator import imod
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from datetime import datetime
from re import sub
from dotenv import load_dotenv
# TavilyClient is imported in tavily.py module
from IPython.display import Image, display
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command
from langgraph.prebuilt import InjectedState
from langchain_core.tools import InjectedToolCallId
from langgraph.prebuilt import create_react_agent
from src.search_tools import search_career_opportunities,search_course_details,search_international_student_info,search_unsw_programs
from src.prompts import international_advisor_subagent_prompt,course_planner_subagent_prompt,career_advisor_subagent_prompt,INSTRUCTIONS
from src.state import DeepAgentState
from src.tavilys import tavily_search,think_tool
from src.research_tools import (
    parallel_tavily_search,
    parallel_course_details,
    parallel_unsw_programs,
    parallel_career_opportunities,
    parallel_international_info,
)
from src.task_tool import _create_task_tool
from src.todo_tools import write_todos, read_todos, classify_task_complexity
from src.file_tools import ls, read_file, write_file
from src.utils import format_messages
# 导入deep-agents

# Load environment variables
load_dotenv()

# ==================== 初始化 ====================

def create_llm():
    """Create Qwen LLM"""
    from langchain_qwq import ChatQwen
    import langchain
    
    # Set environment variables
    os.environ["DASHSCOPE_API_KEY"] = os.environ["DASHSCOPE_API_KEY"]
    
    # Patch langchain verbose/debug attributes if missing
    if not hasattr(langchain, 'verbose'):
        langchain.verbose = False
    if not hasattr(langchain, 'debug'):
        langchain.debug = False
    if not hasattr(langchain, 'llm_cache'):
        langchain.llm_cache = False
    
    return ChatQwen(
        model="qwen-flash", 
        temperature=0.1
    )


# ========== Sub-agent definitions ====================

def get_today_str() -> str:
    """Get current date in a readable format"""
    return datetime.now().strftime("%a %b %-d, %Y")

# Course planner sub-agent
course_planner_subagent = {
    "name": "course-planner",
    "description": "Delegate course planning tasks to the course planner. Focus on course selection, prerequisites, and study pathways.",
    "prompt": course_planner_subagent_prompt,
    "tools": ["search_course_details", "search_unsw_programs", "think_tool"],
}

# Career advisor sub-agent
career_advisor_subagent = {
    "name": "career-advisor", 
    "description": "Delegate career consulting tasks to the career advisor. Focus on career outlook, job opportunities, and skill requirements.",
    "prompt": career_advisor_subagent_prompt,
    "tools": ["search_career_opportunities", "think_tool"],
}

# International advisor sub-agent
international_advisor_subagent = {
    "name": "international-advisor",
    "description": "Delegate international-student tasks to the international advisor. Focus on visa requirements, support services, and cultural adaptation.",
    "prompt": international_advisor_subagent_prompt,
    "tools": ["search_international_student_info", "think_tool"],
}

# ==================== 创建智能体 ====================

def create_unsw_deep_agent():
    """Create the deep-agents based UNSW course advisor"""
    
    # Initialize LLM
    llm = create_llm()
    
    # Define sub-agents
    subagents = [
        course_planner_subagent,
        career_advisor_subagent,
        international_advisor_subagent
    ]
    
    sub_agent_tools = [search_unsw_programs, search_course_details, search_career_opportunities, search_international_student_info, think_tool]
    # Create task tool
    task_tool = _create_task_tool(
        sub_agent_tools, subagents, llm, DeepAgentState
    )
    
    # Define base tools
    basic_tools = [
        search_unsw_programs,
        search_course_details, 
        search_career_opportunities,
        search_international_student_info,
        think_tool,
        parallel_tavily_search,
        parallel_course_details,
        parallel_unsw_programs,
        parallel_career_opportunities,
        parallel_international_info,
        classify_task_complexity,
        write_todos,
        read_todos,
        ls,
        read_file,
        write_file,
        task_tool
    ]
    
    # Create simple ReAct agent
    agent = create_react_agent(
        llm, basic_tools+[task_tool], prompt=INSTRUCTIONS, state_schema=DeepAgentState
    )
    
    return agent

# ==================== Main ====================

def main():
    """Main entrypoint"""
    print("🎓 UNSW Deep-Agents Course Advisor")
    print("=" * 80)
    print("Deep-agents based course advisor")
    print("Features: Sub-agents | TODO management | File system | Tool integration")
    print("=" * 80)
    
    # Check API keys
    if not os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("DASHSCOPE_API_KEY") == "your_dashscope_api_key_here":
        print("⚠️  Please set your DASHSCOPE_API_KEY in the .env file")
        return
    
    if not os.environ.get("TAVILY_API_KEY") or os.environ.get("TAVILY_API_KEY") == "your_tavily_api_key_here":
        print("⚠️  Please set your TAVILY_API_KEY in the .env file")
        return
    
    try:
        # Create advisor
        advisor = create_unsw_deep_agent()
        print("✅ Deep-Agents Student Advisor initialized successfully!")
        
        # Workflow graph (optional)
        # try:
        #     print("📊 Generating workflow diagram...")
            
        #     # Generate Mermaid diagram
        #     mermaid_diagram = advisor.get_graph().draw_mermaid()
        #     with open("unsw_deepagents_workflow.mmd", "w", encoding="utf-8") as f:
        #         f.write(mermaid_diagram)
        #     print("✅ Mermaid diagram saved: unsw_deepagents_workflow.mmd")
            
        #     # Generate PNG workflow diagram
        #     try:
        #         workflow_image = advisor.get_graph().draw_mermaid_png()
        #         with open("unsw_deepagents_workflow.png", "wb") as f:
        #             f.write(workflow_image)
        #         print("✅ PNG workflow saved: unsw_deepagents_workflow.png")

                    
        #     except Exception as png_error:
        #         print(f"⚠️ PNG generation failed: {png_error}")
        #         print("💡 Use https://mermaid.live/ to convert .mmd → PNG")
                
        # except Exception as e:
        #     print(f"⚠️ Saving workflow diagram failed: {e}")
        
        # REPL loop
        while True:
            user_input = input("\n🔍 Your question (enter 'quit','exit', 'quit' to exit the program): ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'quit']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            try:
                print("\n🧠 Deep-Agents analyzing...")
                
                # Pre-processing hint (agent decides complexity & budget)
                print("🎯 Calling complexity assessment tool to determine TODO complexity and tool budget...")
                
                # Invoke advisor
                result = advisor.invoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    config={"recursion_limit": 100}
                )
                format_messages(result["messages"])
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Initialization error: {e}")

if __name__ == "__main__":
    main()