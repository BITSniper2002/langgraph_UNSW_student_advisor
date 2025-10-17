from tavily import TavilyClient
from langchain_core.tools import tool
import os
from langgraph.types import Command
from dotenv import load_dotenv
from src.tavilys import *

load_dotenv()

def generate_file_content(result, query):
    """Generate file content for a single search result."""
    return f"""# Search Result: {result['title']}

**URL:** {result['url']}
**Query:** {query}
**Date:** {get_today_str()}

## Summary
{result['summary']}

## Raw Content
{result['raw_content'] if result['raw_content'] else 'No raw content available'}
"""

def generate_search_summary(processed_results, query):
    """Generate summary text for search results."""
    summaries = []
    saved_files = []
    
    for result in processed_results:
        filename = result['filename']
        saved_files.append(filename)
        summaries.append(f"- {filename}: {result['summary']}...")
    
    summary_text = f"""🔍 Found {len(processed_results)} result(s) for '{query}':

{chr(10).join(summaries)}

Files: {', '.join(saved_files)}
💡 Use read_file() to access full details when needed."""
    
    return summary_text, saved_files

@tool
def search_unsw_programs(query: str,
 state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_results: Annotated[int, InjectedToolArg] = 1) -> Command:
    """Search UNSW programs and course information."""
    search_results = run_tavily_search(
        query,
        max_results=max_results,
        include_raw_content=True,
        topic="general"
    ) 

    # Process and summarize results
    processed_results = process_search_results(search_results)
    
    # Save each result to a file and prepare summary
    files = state.get("files", {})
    saved_files = []
    
    for i, result in enumerate(processed_results):
        # Use the AI-generated filename from summarization
        filename = result['filename']
        
        # Create file content using the common function
        file_content = generate_file_content(result, query)
        
        files[filename] = file_content
        saved_files.append(filename)
    
    # Generate summary text using the common function
    summary_text, _ = generate_search_summary(processed_results, query)

    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(summary_text, tool_call_id=tool_call_id)
            ],
        }
    )

@tool
def search_course_details(query: str, course_code: str,
 state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_results: Annotated[int, InjectedToolArg] = 1) -> Command:
    """Search a specific course's detailed information."""
    search_results = run_tavily_search(
        query,
        max_results=max_results,
        include_raw_content=True,
        topic="general"
    ) 

    # Process and summarize results
    processed_results = process_search_results(search_results)
    
    # Save each result to a file and prepare summary
    files = state.get("files", {})
    saved_files = []

    for i, result in enumerate(processed_results):
        # Use the AI-generated filename from summarization
        filename = result['filename']
        
        # Create file content using the common function
        file_content = generate_file_content(result, query)
        
        files[filename] = file_content
        saved_files.append(filename)
    
    # Generate summary text using the common function
    summary_text, _ = generate_search_summary(processed_results, query)

    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(summary_text, tool_call_id=tool_call_id)
            ],
        }
    )
    
@tool
def search_career_opportunities(query: str,
 state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_results: Annotated[int, InjectedToolArg] = 1,
    field: Annotated[str, InjectedToolArg] = "career") -> Command:
    """Search career opportunities information."""
    search_results = run_tavily_search(
        f"{query} {field} career opportunities jobs Australia",
        max_results=max_results,
        include_raw_content=True,
        topic="general"
    ) 
    
    processed_results = process_search_results(search_results)
    
    # Save each result to a file and prepare summary
    files = state.get("files", {})
    saved_files = []

    for i, result in enumerate(processed_results):
        # Use the AI-generated filename from summarization
        filename = result['filename']
    
        # Create file content using the common function
        file_content = generate_file_content(result, query)
        
        files[filename] = file_content
        saved_files.append(filename)
    
    # Generate summary text using the common function
    summary_text, _ = generate_search_summary(processed_results, query)

    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(summary_text, tool_call_id=tool_call_id)
            ],
        }
    )
@tool
def search_international_student_info(query: str,
 state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_results: Annotated[int, InjectedToolArg] = 1,
    ) -> Command:
    """Search international student related information."""
    search_results = run_tavily_search(
        f"{query} international students visa requirements support",
        max_results=max_results,
        include_raw_content=True,
        topic="general"
    ) 
    
    processed_results = process_search_results(search_results)
    
    # Save each result to a file and prepare summary
    files = state.get("files", {})
    saved_files = []

    for i, result in enumerate(processed_results):
        # Use the AI-generated filename from summarization
        filename = result['filename']
        
        # Create file content using the common function
        file_content = generate_file_content(result, query)
        
        files[filename] = file_content
        saved_files.append(filename)
    
    # Generate summary text using the common function
    summary_text, _ = generate_search_summary(processed_results, query)

    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(summary_text, tool_call_id=tool_call_id)
            ],
        }
    )
