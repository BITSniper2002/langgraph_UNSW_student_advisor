# UNSW Student Advisor - Intelligent Course Advisory System

## 📋 Project Overview

UNSW Student Advisor is an intelligent course advisory system based on deep agent architecture, specifically designed to provide personalized academic planning and course selection advice for UNSW (University of New South Wales) students. The system integrates advanced AI technologies with multi-agent collaboration, task management, and file systems to deliver comprehensive, professional academic consulting services.

## 🏗️ Chatbot Design Philosophy and Overall Architecture

### Design Philosophy
- **Specialization-Oriented**: Focused exclusively on UNSW courses and programs, providing precise academic advice
- **Multi-Agent Collaboration**: Professional services through sub-agent division of labor
- **Task-Driven**: Based on TODO management system, ensuring systematic solutions to complex problems
- **Context Management**: Managing conversation history and important information through virtual file system

### Overall Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    UNSW Student Advisor                     │
├─────────────────────────────────────────────────────────────┤
│  Main Agent (React Agent)                                  │
│  ├── Course Planner Subagent (Course Planning Expert)      │
│  ├── Career Advisor Subagent (Career Development Advisor)  │
│  └── International Student Advisor (International Student  │
│      Support Specialist)                                    │
├─────────────────────────────────────────────────────────────┤
│  Core Tools & Services                                     │
│  ├── Search Tools (UNSW Program Search, Course Details,    │
│  │   Career Opportunities)                                 │
│  ├── Web Search (Tavily API Real-time Web Search)          │
│  ├── TODO Management (Task Planning & Progress Tracking)   │
│  ├── File System (Virtual File System Management)          │
│  └── Task Delegation (Intelligent Task Assignment)         │
├─────────────────────────────────────────────────────────────┤
│  AI Models & APIs                                          │
│  ├── Qwen Flash (Tongyi Qianwen Language Model)            │
│  ├── Tavily Search API (Web Search Service)                │
│  └── LangGraph (Agent Workflow Management)                 │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Technologies Used and Implementation Methods

### Core Technology Stack
- **Language Model**: Qwen Flash (Tongyi Qianwen) - Provides high-quality Chinese dialogue capabilities
- **Agent Framework**: LangGraph - Builds complex multi-agent workflows
- **Search Service**: Tavily API - Real-time web search and information retrieval
- **State Management**: DeepAgentState - Manages conversation state, TODO lists, and file system
- **Tool Integration**: LangChain Tools - Unified tool calling interface

### Implementation Methods
1. **Modular Design**: Split functionality into independent tool modules for easy maintenance and expansion
2. **Agent Collaboration**: Professional sub-agents handle specific domain problems through task delegation
3. **Context Isolation**: Each sub-agent has independent context to avoid information pollution
4. **Progressive Processing**: Decompose complex problems into manageable steps through TODO system
5. **File System Management**: Virtual file system stores search results and important information, supporting context persistence

### Key Technical Features
- **Recursive Control**: Prevents infinite loops, ensures system stability
- **Error Handling Mechanism**: Comprehensive exception handling and user-friendly error prompts
- **Output Optimization**: Intelligent filtering of file operation outputs, providing clean user interface
- **Multi-language Support**: Supports mixed Chinese-English conversations, adapting to international needs

## 🚀 Implemented Features and Workflow Introduction

### Core Functional Modules

#### 1. Course Planning Services
- **UNSW Course Search**: Search for various UNSW courses and program information
- **Course Detail Queries**: Obtain detailed information, prerequisites, and requirements for specific courses
- **Learning Path Planning**: Develop personalized learning plans based on student background and goals
- **Degree Structure Analysis**: Help students understand degree requirements and course arrangements

#### 2. Career Development Guidance
- **Career Opportunity Search**: Search for career opportunities related to UNSW graduates
- **Industry Trend Analysis**: Provide employment market insights for fields like data science
- **Skill Development Advice**: Skill enhancement recommendations based on target careers
- **Internship Recommendations**: Recommend relevant internship and work experience opportunities

#### 3. International Student Support
- **Visa Requirement Consultation**: Provide information about Australian student visa requirements
- **Language Requirement Guidance**: Explain IELTS/TOEFL and other language requirements
- **Cultural Adaptation Support**: Help international students adapt to Australian learning environment
- **Support Service Introduction**: Introduce various support services UNSW provides for international students

#### 4. Intelligent Task Management
- **TODO List Creation**: Automatically decompose complex problems into manageable tasks
- **Progress Tracking**: Real-time tracking of task completion status
- **Priority Management**: Intelligent task priority arrangement
- **Result Integration**: Integrate multiple task results into complete answers

### Workflow

#### Standard Consultation Process
```
User Input → Problem Analysis → TODO Planning → Task Assignment → Sub-agent Processing → Result Integration → Professional Response
```

#### Complex Problem Processing Workflow
```
1. Receive user question
2. Create TODO task list
3. Delegate to appropriate sub-agent based on question type
4. Sub-agent performs professional search and analysis
5. Integrate results from multiple sub-agents
6. Generate comprehensive professional advice
7. Provide follow-up support recommendations
```

### Special Features

#### 1. Professional Redirection
- When users ask about other universities, intelligently redirect to UNSW-related programs
- Maintain professionalism and consistency, avoid information confusion

#### 2. Multi-Modal Information Processing
- Web search + local knowledge base combination
- Real-time information retrieval with historical information management
- File system support for information persistence

#### 3. Intelligent Output Optimization
- Automatically hide technical details in file operations
- Provide clean, professional user interface
- Structured display of complex information

#### 4. Error Recovery Mechanism
- Automatic retry for failed searches
- Graceful handling of API limitations and errors
- Provide alternative solutions

## 📁 Project Structure

```
UNSW_student_advisor/
├── src/                          # Core source code
│   ├── search_tools.py          # UNSW search tools
│   ├── tavilys.py               # Web search service
│   ├── prompts.py               # Prompt templates
│   ├── state.py                 # State management
│   ├── task_tool.py             # Task delegation tool
│   ├── todo_tools.py            # TODO management tool
│   ├── file_tools.py            # File system tool
│   ├── utils.py                 # Utility functions
│   └── research_tools.py        # Research tools
├── unsw_deepagents_advisor.py   # Main program entry
├── requirements.txt             # Dependency package list
├── env_example.txt              # Environment variable example
└── README.md                    # Project documentation
```

## 🚀 Quick Start

### Environment Requirements
- Python 3.11+
- Required API keys (DASHSCOPE_API_KEY, TAVILY_API_KEY)

### Installation Steps
1. Clone the project and enter the directory
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables (refer to env_example.txt)
4. Run the program: `python unsw_deepagents_advisor.py`

### Usage Example
```
🔍 Your Question: I am a student from Beijing Institute of Technology with a GPA of 3.2/4.0 and IELTS 7/6, and I want to pursue a master's degree in data science. Please provide me with some advice.

The system will automatically:
1. Create TODO task list
2. Search UNSW data science program information
3. Analyze your background compatibility
4. Provide detailed application advice
5. Recommend related career development paths
```

## 🎯 Project Advantages

- **Specialization**: Focused on UNSW, providing precise academic advice
- **Intelligence**: Multi-agent collaboration, handling complex problems
- **User-Friendly**: Clean interface, intuitive interaction
- **Extensible**: Modular design, easy feature expansion
- **Stability**: Comprehensive error handling and state management

*UNSW Student Advisor - Let AI be your exclusive academic advisor* 🎓✨
