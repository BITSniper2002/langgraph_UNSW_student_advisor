"""TODO management tools for task planning and progress tracking.

This module provides tools for creating and managing structured task lists
that enable agents to plan complex workflows and track progress through
multi-step operations.
"""

from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from src.prompts import WRITE_TODOS_DESCRIPTION
from src.state import DeepAgentState, Todo

# Qwen model for classification
from langchain_qwq import ChatQwen
from langchain_core.messages import HumanMessage


@tool(description=WRITE_TODOS_DESCRIPTION,parse_docstring=True)
def write_todos(
    todos: list[Todo], tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Create or update the agent's TODO list for task planning and tracking.

    Args:
        todos: List of Todo items with content and status
        tool_call_id: Tool call identifier for message response

    Returns:
        Command to update agent state with new TODO list
    """
    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(f"Updated todo list to {todos}", tool_call_id=tool_call_id)
            ],
        }
    )


@tool(parse_docstring=True)
def read_todos(
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    """Read the current TODO list from the agent state.

    This tool allows the agent to retrieve and review the current TODO list
    to stay focused on remaining tasks and track progress through complex workflows.

    Args:
        state: Injected agent state containing the current TODO list
        tool_call_id: Injected tool call identifier for message tracking

    Returns:
        Formatted string representation of the current TODO list
    """
    todos = state.get("todos", [])
    if not todos:
        return "No todos currently in the list."

    result = "Current TODO List:\n"
    for i, todo in enumerate(todos, 1):
        status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
        emoji = status_emoji.get(todo["status"], "❓")
        result += f"{i}. {emoji} {todo['content']} ({todo['status']})\n"

    return result.strip()


@tool(parse_docstring=True)
def classify_task_complexity(user_request: str) -> dict:
    """Classify the user request for TODO complexity and type.

    Args:
        user_request: The raw user query to analyze.

    Returns:
        dict: A JSON-compatible dict with exactly two keys:
            - task_type: Task type (e.g., Course Planning / Program Info / Career Advice / International Support / Comparison / General Inquiry)
            - difficulty: Difficulty level (Simple / Moderate / Difficult)

    Example:
        {
          "task_type": "Comparison",
          "difficulty": "Moderate"
        }
    """
    model = ChatQwen(model="qwen-flash", temperature=0.0)

    system_hint = (
        "You are a task classifier. Output valid JSON only, with no explanations. "
        "Fields: task_type (type), difficulty (Simple/Moderate/Difficult). "
        "Decide the most fitting task_type and difficulty from the user request."
    )

    format_constraint = (
        "Strictly output JSON with this shape, no extra text:\n"
        "{\n  \"task_type\": \"<type>\",\n  \"difficulty\": \"<Simple/Moderate/Difficult>\"\n}"
    )

    prompt = f"{system_hint}\n\nUser request:\n{user_request}\n\n{format_constraint}"

    resp = model.invoke([HumanMessage(content=prompt)])
    content = resp.content if isinstance(resp.content, str) else str(resp.content)

    # Best-effort parse; if parsing fails, return conservative default
    import json
    try:
        data = json.loads(content)
        # minimal validation
        if "task_type" in data and "difficulty" in data:
            return data
    except Exception:
        pass

    return {"task_type": "General Inquiry", "difficulty": "Moderate"}
