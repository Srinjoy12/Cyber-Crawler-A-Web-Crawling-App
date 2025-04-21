import os
from datetime import datetime
import aiofiles

async def save_chat_history_md(chat_history):
    """Save chat history to markdown file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_history_{timestamp}.md"
    
    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        for msg in chat_history:
            await f.write(f"## {msg['role'].title()}\n{msg['content']}\n\n")

async def save_crawl_to_markdown(content: str, metadata: dict, url: str) -> str:
    """Save crawled content to a markdown file in the crawls directory."""
    # Create crawls directory if it doesn't exist
    crawls_dir = "crawls"
    if not os.path.exists(crawls_dir):
        os.makedirs(crawls_dir)
    
    # Create a safe filename from the URL
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_url = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('?', '_').replace('&', '_')
    filename = os.path.join(crawls_dir, f"{safe_url}_{timestamp}.md")
    
    # Create markdown content
    markdown_content = f"""# Crawled Content: {url}

## Metadata
- Crawled at: {datetime.now().isoformat()}
- URL: {url}
"""
    
    # Add any metadata if available
    if metadata:
        markdown_content += "\n### Additional Metadata\n"
        for key, value in metadata.items():
            markdown_content += f"- {key}: {value}\n"
    
    # Add the main content
    markdown_content += "\n## Content\n\n"
    markdown_content += content
    
    # Save to file
    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        await f.write(markdown_content)
    
    return filename
