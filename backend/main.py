from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.crawler import run_crawl
from backend.llm import ask_llm
from backend.utils import save_chat_history_md, save_crawl_to_markdown

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_history = []

class CrawlRequest(BaseModel):
    url: str
    max_depth: Optional[int] = 1

class ChatRequest(BaseModel):
    question: str
    context: List[str]

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/crawl")
async def crawl(request: CrawlRequest) -> Dict[str, Any]:
    # Run the crawler with specified depth
    result = await run_crawl(request.url, max_depth=request.max_depth)
    if result["status"] == "success":
        # Save content to markdown file
        filename = await save_crawl_to_markdown(result["content"], result.get("metadata", {}), request.url)
        result["saved_to"] = filename
    return result

@app.post("/ask")
async def ask(request: ChatRequest):
    return await ask_llm(request.question, request.context)

@app.get("/save-chat")
async def save_chat():
    await save_chat_history_md(chat_history)
    return {"status": "saved"}
