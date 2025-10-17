"""Research Tools.

This module provides search and content processing utilities for the research agent,
including web search capabilities and content summarization tools.
"""
import os
from datetime import datetime
import uuid, base64

import httpx
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import InjectedToolArg, InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from markdownify import markdownify
from pydantic import BaseModel, Field
from tavily import TavilyClient
from typing_extensions import Annotated, Literal

from src.prompts import SUMMARIZE_WEB_SEARCH
from src.state import DeepAgentState
from langchain_qwq import ChatQwen
import asyncio
import langchain

if not hasattr(langchain, 'verbose'):
    langchain.verbose = False
if not hasattr(langchain, 'debug'):
    langchain.debug = False
if not hasattr(langchain, 'llm_cache'):
    langchain.llm_cache = False
# Summarization model 
summarization_model = ChatQwen(
        model="qwen-flash", 
        temperature=0.1
    )
tavily_client = TavilyClient()

class Summary(BaseModel):
    """Schema for webpage content summarization."""
    filename: str = Field(description="Name of the file to store.")
    summary: str = Field(description="Key learnings from the webpage.")

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %-d, %Y")

def run_tavily_search(
    search_query: str, 
    max_results: int = 1, 
    include_raw_content: bool = True, 
    topic: str = "general"
) -> dict:
    """Perform search using Tavily API for a single query.

    Args:
        search_query: Search query to execute
        max_results: Maximum number of results per query
        topic: Topic filter for search results
        include_raw_content: Whether to include raw webpage content

    Returns:
        Search results dictionary
    """
    result = tavily_client.search(
        search_query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic
    )

    return result

def summarize_webpage_content(webpage_content: str) -> Summary:
    """Summarize webpage content using the configured summarization model.

    Args:
        webpage_content: Raw webpage content to summarize

    Returns:
        Summary object with filename and summary
    """
    try:
        # Set up structured output model for summarization
        structured_model = summarization_model.with_structured_output(Summary)

        # Generate summary
        summary_and_filename = structured_model.invoke([
            HumanMessage(content=SUMMARIZE_WEB_SEARCH.format(
                webpage_content=webpage_content, 
                date=get_today_str()
            ))
        ])

        return summary_and_filename

    except Exception:
        # Return a basic summary object on failure
        return Summary(
            filename="search_result.md",
            summary=webpage_content[:1000] + "..." if len(webpage_content) > 1000 else webpage_content
        )

def process_search_results(results: dict) -> list[dict]:
    """Process search results by summarizing content where available.

    Args:
        results: Tavily search results dictionary

    Returns:
        List of processed results with summaries
    """
    processed_results = []

    # Create a client for HTTP requests
    HTTPX_CLIENT = httpx.Client()

    for result in results.get('results', []):

        # Get url 
        url = result['url']

        # Read url
        response = HTTPX_CLIENT.get(url)

        if response.status_code == 200:
            # Convert HTML to markdown
            raw_content = markdownify(response.text)
            summary_obj = summarize_webpage_content(raw_content)
        else:
            # Use Tavily's generated summary
            raw_content = result.get('raw_content', '')
            summary_obj = Summary(
                filename="URL_error.md",
                summary=result.get('content', 'Error reading URL; try another search.')
            )

        # uniquify file names
        uid = base64.urlsafe_b64encode(uuid.uuid4().bytes).rstrip(b"=").decode("ascii")[:8]
        name, ext = os.path.splitext(summary_obj.filename)
        summary_obj.filename = f"{name}_{uid}{ext}"

        processed_results.append({
            'url': result['url'],
            'title': result['title'],
            'summary': summary_obj.summary,
            'filename': summary_obj.filename,
            'raw_content': raw_content,
        })

    return processed_results

@tool(parse_docstring=True)
def tavily_search(
    query: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_results: Annotated[int, InjectedToolArg] = 1,
    topic: Annotated[str, InjectedToolArg] = "general"
) -> Command:
    """Search web and save detailed results to files while returning minimal context.

    Performs web search and saves full content to files for context offloading.
    Returns only essential information to help the agent decide on next steps.

    Args:
        query: Search query to execute
        state: Injected agent state for file storage
        tool_call_id: Injected tool call identifier
        max_results: Maximum number of results to return (default: 1)
        topic: Topic filter - 'general', 'news', or 'finance' (default: 'general')

    Returns:
        Command that saves full results to files and provides minimal summary
    """
    # Execute search
    search_results = run_tavily_search(
        query,
        max_results=max_results,
        topic="general",
        include_raw_content=True,
    ) 

    # Process and summarize results
    processed_results = process_search_results(search_results)

    # Save each result to a file and prepare summary
    files = state.get("files", {})
    saved_files = []
    summaries = []

    for i, result in enumerate(processed_results):
        # Use the AI-generated filename from summarization
        filename = result['filename']

        # Create file content with full details
        file_content = f"""# Search Result: {result['title']}

**URL:** {result['url']}
**Query:** {query}
**Date:** {get_today_str()}

## Summary
{result['summary']}

## Raw Content
{result['raw_content'] if result['raw_content'] else 'No raw content available'}
"""

        files[filename] = file_content
        saved_files.append(filename)
        summaries.append(f"- {filename}: {result['summary']}...")

    # Create minimal summary for tool message - focus on what was collected
    summary_text = f"""🔍 Found {len(processed_results)} result(s) for '{query}':

{chr(10).join(summaries)}

Files: {', '.join(saved_files)}
💡 Use read_file() to access full details when needed."""

    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(summary_text, tool_call_id=tool_call_id)
            ],
        }
    )


@tool(parse_docstring=True)
def parallel_tavily_search(
    queries: list[str],
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_results: Annotated[int, InjectedToolArg] = 1,
    include_raw_content: Annotated[bool, InjectedToolArg] = True,
) -> Command:
    """Run multiple Tavily searches in parallel and save consolidated results.

    Args:
        queries: A list of independent search queries to execute concurrently
        state: Injected agent state for file storage
        tool_call_id: Injected tool call identifier
        max_results: Maximum results per query (default 1)
        include_raw_content: Whether to fetch raw content (default True)

    Returns:
        Command updating files with per-query findings and a compact summary message
    """

    async def _run_one(q: str):
        # Wrap sync run_tavily_search in a thread to avoid blocking
        return await asyncio.to_thread(
            run_tavily_search,
            q,
            max_results,
            include_raw_content,
        )

    async def _run_all(qs: list[str]):
        tasks = [asyncio.create_task(_run_one(q)) for q in qs]
        return await asyncio.gather(*tasks, return_exceptions=False)

    # Execute all queries concurrently
    results_per_query = asyncio.run(_run_all(queries)) if queries else []

    files = state.get("files", {})
    saved_files_all: list[str] = []
    summaries_all: list[str] = []

    # Process each query's results independently
    for q, raw_results in zip(queries, results_per_query):
        processed = process_search_results(raw_results)
        for item in processed:
            filename = item['filename']
            file_content = f"""# Search Result: {item['title']}

**URL:** {item['url']}
**Query:** {q}
**Date:** {get_today_str()}

## Summary
{item['summary']}

## Raw Content
{item['raw_content'] if item['raw_content'] else 'No raw content available'}
"""
            files[filename] = file_content
            saved_files_all.append(filename)
            summaries_all.append(f"- [{q}] {filename}: {item['summary']}...")

    summary_text = f"""⚡ Parallel search completed for {len(queries)} queries.

{chr(10).join(summaries_all)}

Files: {', '.join(saved_files_all)}
💡 Use read_file() to inspect details when needed."""

    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(summary_text, tool_call_id=tool_call_id)
            ],
        }
    )


@tool(parse_docstring=True)
def parallel_unsw_programs(
    queries: list[str],
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_results: Annotated[int, InjectedToolArg] = 1,
) -> Command:
    """Search multiple UNSW program/course queries in parallel.

    Args:
        queries: List of independent program-related queries (e.g., ["Master of IT UNSW", "COMP9020 UNSW"]).
        state: Injected agent state for file storage.
        tool_call_id: Injected tool call identifier.
        max_results: Max results per query (default 1).
    """

    async def _run_one(q: str):
        return q, await asyncio.to_thread(run_tavily_search, q, max_results, True)

    async def _run_all(qs: list[str]):
        tasks = [asyncio.create_task(_run_one(q)) for q in qs]
        return await asyncio.gather(*tasks, return_exceptions=False)

    results = asyncio.run(_run_all(queries)) if queries else []

    files = state.get("files", {})
    saved_files: list[str] = []
    summaries: list[str] = []

    for q, raw in results:
        processed = process_search_results(raw)
        for item in processed:
            filename = item['filename']
            content = f"""# Search Result: {item['title']}

**Query:** {q}
**Date:** {get_today_str()}

## Summary
{item['summary']}

## Raw Content
{item['raw_content'] if item['raw_content'] else 'No raw content available'}
"""
            files[filename] = content
            saved_files.append(filename)
            summaries.append(f"- [{q}] {filename}: {item['summary']}...")

    summary_text = f"""⚡ Parallel UNSW program searches completed for {len(queries)} queries.

{chr(10).join(summaries)}

Files: {', '.join(saved_files)}
💡 Use read_file() to inspect details when needed."""

    return Command(update={"files": files, "messages": [ToolMessage(summary_text, tool_call_id=tool_call_id)]})


@tool(parse_docstring=True)
def parallel_career_opportunities(
    topics: list[str],
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_results: Annotated[int, InjectedToolArg] = 1,
) -> Command:
    """Search multiple career opportunity topics in parallel (Australia/UNSW context).

    Args:
        topics: List of topics/roles/fields (e.g., ["data engineer", "ml engineer"]).
        state: Injected agent state for file storage.
        tool_call_id: Injected tool call identifier.
        max_results: Max results per topic (default 1).
    """

    def build_query(t: str) -> str:
        return f"{t} career opportunities jobs Australia UNSW"

    async def _run_one(t: str):
        q = build_query(t)
        return t, await asyncio.to_thread(run_tavily_search, q, max_results, True)

    async def _run_all(ts: list[str]):
        tasks = [asyncio.create_task(_run_one(t)) for t in ts]
        return await asyncio.gather(*tasks, return_exceptions=False)

    results = asyncio.run(_run_all(topics)) if topics else []

    files = state.get("files", {})
    saved_files: list[str] = []
    summaries: list[str] = []

    for topic, raw in results:
        processed = process_search_results(raw)
        for item in processed:
            filename = item['filename']
            content = f"""# Career Search Result: {item['title']}

**Topic:** {topic}
**Query:** {build_query(topic)}
**Date:** {get_today_str()}

## Summary
{item['summary']}

## Raw Content
{item['raw_content'] if item['raw_content'] else 'No raw content available'}
"""
            files[filename] = content
            saved_files.append(filename)
            summaries.append(f"- [{topic}] {filename}: {item['summary']}...")

    summary_text = f"""⚡ Parallel career searches completed for {len(topics)} topic(s).

{chr(10).join(summaries)}

Files: {', '.join(saved_files)}
💡 Use read_file() to inspect details when needed."""

    return Command(update={"files": files, "messages": [ToolMessage(summary_text, tool_call_id=tool_call_id)]})


@tool(parse_docstring=True)
def parallel_international_info(
    aspects: list[str],
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_results: Annotated[int, InjectedToolArg] = 1,
) -> Command:
    """Search multiple international-student aspects in parallel (UNSW/Australia context).

    Args:
        aspects: List of aspects (e.g., ["visa requirements", "scholarships", "accommodation"]).
        state: Injected agent state for file storage.
        tool_call_id: Injected tool call identifier.
        max_results: Max results per aspect (default 1).
    """

    def build_query(a: str) -> str:
        return f"{a} international students visa requirements support UNSW"

    async def _run_one(a: str):
        q = build_query(a)
        return a, await asyncio.to_thread(run_tavily_search, q, max_results, True)

    async def _run_all(aspects_list: list[str]):
        tasks = [asyncio.create_task(_run_one(a)) for a in aspects_list]
        return await asyncio.gather(*tasks, return_exceptions=False)

    results = asyncio.run(_run_all(aspects)) if aspects else []

    files = state.get("files", {})
    saved_files: list[str] = []
    summaries: list[str] = []

    for aspect, raw in results:
        processed = process_search_results(raw)
        for item in processed:
            filename = item['filename']
            content = f"""# International Info Result: {item['title']}

**Aspect:** {aspect}
**Query:** {build_query(aspect)}
**Date:** {get_today_str()}

## Summary
{item['summary']}

## Raw Content
{item['raw_content'] if item['raw_content'] else 'No raw content available'}
"""
            files[filename] = content
            saved_files.append(filename)
            summaries.append(f"- [{aspect}] {filename}: {item['summary']}...")

    summary_text = f"""⚡ Parallel international info searches completed for {len(aspects)} aspect(s).

{chr(10).join(summaries)}

Files: {', '.join(saved_files)}
💡 Use read_file() to inspect details when needed."""

    return Command(update={"files": files, "messages": [ToolMessage(summary_text, tool_call_id=tool_call_id)]})


@tool(parse_docstring=True)
def parallel_course_details(
    course_codes: list[str],
    base_query: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_results: Annotated[int, InjectedToolArg] = 1,
) -> Command:
    """Fetch multiple course details in parallel using the same underlying search flow.

    Args:
        course_codes: List of course codes (e.g., ["COMP9020","COMP9021"]).
        base_query: A short query template to combine with each code (e.g., "course details UNSW").
        state: Injected agent state for file storage.
        tool_call_id: Injected tool call identifier.
        max_results: Max results per course (default 1).

    Returns:
        Command that saves per-course findings to files and returns a compact summary.
    """

    async def _run_one(code: str):
        q = f"{code} {base_query}"
        return code, await asyncio.to_thread(
            run_tavily_search,
            q,
            max_results,
            True,
        )

    async def _run_all(codes: list[str]):
        tasks = [asyncio.create_task(_run_one(c)) for c in codes]
        return await asyncio.gather(*tasks, return_exceptions=False)

    results = asyncio.run(_run_all(course_codes)) if course_codes else []

    files = state.get("files", {})
    saved_files_all: list[str] = []
    summaries_all: list[str] = []

    for code, raw_results in results:
        processed = process_search_results(raw_results)
        for item in processed:
            filename = item['filename']
            file_content = f"""# Search Result: {item['title']}

**Course Code:** {code}
**Query:** {code} {base_query}
**Date:** {get_today_str()}

## Summary
{item['summary']}

## Raw Content
{item['raw_content'] if item['raw_content'] else 'No raw content available'}
"""
            files[filename] = file_content
            saved_files_all.append(filename)
            summaries_all.append(f"- [{code}] {filename}: {item['summary']}...")

    summary_text = f"""⚡ Parallel course details fetched for {len(course_codes)} course(s).

{chr(10).join(summaries_all)}

Files: {', '.join(saved_files_all)}
💡 Use read_file() to inspect details when needed."""

    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(summary_text, tool_call_id=tool_call_id)
            ],
        }
    )

@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?
    - How complex is the question: Have I reached the number of search limits?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making. If parallel is suitable, add a note to the reflection and 
        use the parallel_tavily_search tool.
    """
    return f"Reflection recorded: {reflection}"
