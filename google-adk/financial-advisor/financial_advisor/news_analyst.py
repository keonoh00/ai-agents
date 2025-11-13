from google.adk.agents import Agent
from ollama import OllamaLLM
from tools import web_search_tool

MODEL = OllamaLLM(model="ollama/gpt-oss:latest").googleAdk()

news_analyst = Agent(
    name="NewsAnalyst",
    model=MODEL,
    description="Uses Web Search tools to search and scrape real web content from the web.",
    instruction="""
    You are a News Analyst Specialist who uses web tools to find current information. Your job:
    
    1. **Web Search**: Use web_search_tool() to find recent news about a company.
    3. **Summarize Findings**: Explain what you found and its relevance
    
    **Your Web Tools:**
    - **web_search_tool()**: Firecrawl web search for company news
    
    Use external APIs to search and scrape web content for current information.
    """,
    tools=[
        web_search_tool,
    ],
)
