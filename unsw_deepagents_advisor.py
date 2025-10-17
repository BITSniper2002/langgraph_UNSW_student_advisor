#!/usr/bin/env python3
"""
UNSW课程选择顾问 - 基于官方deep-agents的深度智能体实现
使用官方deep-agents库，支持子智能体、TODO管理、文件系统等功能
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
from src.task_tool import _create_task_tool
from src.todo_tools import write_todos, read_todos
from src.file_tools import ls, read_file, write_file
from src.utils import format_messages
# 导入deep-agents

# Load environment variables
load_dotenv()

# ==================== 初始化 ====================

def create_llm():
    """创建通义千问LLM"""
    from langchain_qwq import ChatQwen
    import langchain
    
    # 设置环境变量
    os.environ["DASHSCOPE_API_KEY"] = os.environ["DASHSCOPE_API_KEY"]
    
    # 修复 langchain.verbose 和 langchain.debug 属性错误
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


# ========== 子智能体定义 ====================

def get_today_str() -> str:
    """获取当前日期的可读格式"""
    return datetime.now().strftime("%a %b %-d, %Y")

# 课程规划子智能体
course_planner_subagent = {
    "name": "course-planner",
    "description": "委托课程规划任务给课程规划专家。专注于课程选择、先修条件、学习路径规划。",
    "prompt": course_planner_subagent_prompt,
    "tools": ["search_course_details", "search_unsw_programs", "think_tool"],
}

# 职业顾问子智能体
career_advisor_subagent = {
    "name": "career-advisor", 
    "description": "委托职业咨询任务给职业发展顾问。专注于职业前景、就业机会、技能要求分析。",
    "prompt": career_advisor_subagent_prompt,
    "tools": ["search_career_opportunities", "think_tool"],
}

# 国际学生顾问子智能体
international_advisor_subagent = {
    "name": "international-advisor",
    "description": "委托国际学生咨询任务给国际学生顾问。专注于签证要求、支持服务、文化适应。",
    "prompt": international_advisor_subagent_prompt,
    "tools": ["search_international_student_info", "think_tool"],
}

# ==================== 创建深度智能体 ====================

def create_unsw_deep_agent():
    """创建基于deep-agents的UNSW课程顾问"""
    
    # 初始化LLM
    llm = create_llm()
    
    # 定义子智能体
    subagents = [
        course_planner_subagent,
        career_advisor_subagent,
        international_advisor_subagent
    ]
    
    sub_agent_tools = [search_unsw_programs, search_course_details, search_career_opportunities, search_international_student_info,think_tool]
    # 创建任务工具
    task_tool = _create_task_tool(
        sub_agent_tools, subagents, llm, DeepAgentState
    )
    
    # 定义基础工具
    basic_tools = [
        search_unsw_programs,
        search_course_details, 
        search_career_opportunities,
        search_international_student_info,
        think_tool,
        write_todos,
        read_todos,
        ls,
        read_file,
        write_file,
        task_tool
    ]
    
    # 创建简单的React智能体
    agent = create_react_agent(
        llm, basic_tools+[task_tool], prompt=INSTRUCTIONS, state_schema=DeepAgentState
    )
    
    return agent

# ==================== 主程序 ====================

def main():
    """主程序"""
    print("🎓 UNSW Deep-Agents Course Advisor")
    print("=" * 80)
    print("基于官方deep-agents的深度智能课程顾问")
    print("功能: 子智能体 | TODO管理 | 文件系统 | 工具集成")
    print("=" * 80)
    
    # 检查API密钥
    if not os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("DASHSCOPE_API_KEY") == "your_dashscope_api_key_here":
        print("⚠️  请在 .env 文件中设置您的 DASHSCOPE_API_KEY")
        return
    
    if not os.environ.get("TAVILY_API_KEY") or os.environ.get("TAVILY_API_KEY") == "your_tavily_api_key_here":
        print("⚠️  请在 .env 文件中设置您的 TAVILY_API_KEY")
        return
    
    try:
        # 创建深度智能体
        advisor = create_unsw_deep_agent()
        print("✅ Deep-Agents课程顾问初始化成功！")
        
        # 显示工作流图
        # try:
        #     print("📊 正在生成工作流图...")
            
        #     # 生成Mermaid格式的流程图
        #     mermaid_diagram = advisor.get_graph().draw_mermaid()
        #     with open("unsw_deepagents_workflow.mmd", "w", encoding="utf-8") as f:
        #         f.write(mermaid_diagram)
        #     print("✅ Mermaid工作流图已保存为: unsw_deepagents_workflow.mmd")
            
        #     # 生成PNG格式的流程图
        #     try:
        #         workflow_image = advisor.get_graph().draw_mermaid_png()
        #         with open("unsw_deepagents_workflow.png", "wb") as f:
        #             f.write(workflow_image)
        #         print("✅ PNG工作流图已保存为: unsw_deepagents_workflow.png")

                    
        #     except Exception as png_error:
        #         print(f"⚠️ PNG生成失败: {png_error}")
        #         print("💡 可以使用 https://mermaid.live/ 将 .mmd 文件转换为PNG")
                
        # except Exception as e:
        #     print(f"⚠️ 保存工作流图失败: {e}")
        
        # 交互循环
        while True:
            user_input = input("\n🔍 您的问题 (输入 'quit','exit', '退出' 退出程序): ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            if not user_input:
                continue
            
            try:
                print("\n🧠 Deep-Agents分析中...")
                
                # 调用深度智能体
                result = advisor.invoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    config={"recursion_limit": 100}
                )
                format_messages(result["messages"])
                    
            except Exception as e:
                print(f"❌ 错误: {e}")
                
    except Exception as e:
        print(f"❌ 初始化错误: {e}")

if __name__ == "__main__":
    main()