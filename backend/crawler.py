from typing import List, Dict, Any, Set, Optional
import asyncio
import json
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from utils import save_crawl_to_markdown
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

# Global browser instance management
_browser_lock = asyncio.Lock()
_browser: Optional[Browser] = None
_playwright: Optional[Playwright] = None

async def get_or_create_browser() -> Browser:
    """Get existing browser instance or create a new one."""
    global _browser, _playwright
    
    async with _browser_lock:
        if _browser is None or not _browser.is_connected():
            if _playwright is not None:
                try:
                    await _playwright.stop()
                except Exception:
                    pass
                _playwright = None
            
            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--window-size=1920,1080'
                ]
            )
        return _browser

async def cleanup_browser():
    """Clean up the global browser instance."""
    global _browser, _playwright
    
    async with _browser_lock:
        if _browser:
            try:
                await _browser.close()
            except Exception as e:
                print(f"Warning: Error closing browser: {str(e)}")
            _browser = None
        
        if _playwright:
            try:
                await _playwright.stop()
            except Exception as e:
                print(f"Warning: Error stopping playwright: {str(e)}")
            _playwright = None

async def extract_urls_from_text(text: str, base_url: str) -> List[str]:
    """Extract URLs from text content and normalize them."""
    # Basic URL regex pattern
    url_pattern = r'https?://[^\s()<>]+(?:\([\w\d]+\)|(?:[^,.;:!?)\]\s<>"]|\.[^,.;:!?)\]\s<>"]))'
    
    # Extract URLs
    found_urls = set(re.findall(url_pattern, text))
    
    # Normalize URLs
    normalized_urls = []
    base_domain = urlparse(base_url).netloc
    
    for url in found_urls:
        # Skip media files, PDFs, etc.
        if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.mp4', '.mp3', '.zip']):
            continue
            
        # Only include URLs from the same domain
        parsed_url = urlparse(url)
        if parsed_url.netloc == base_domain or not parsed_url.netloc:
            # Normalize the URL
            if not parsed_url.netloc:
                url = urljoin(base_url, url)
            normalized_urls.append(url)
    
    return normalized_urls

async def run_crawl(url: str, max_depth: int = 1, crawled_urls: Set[str] = None) -> Dict[str, Any]:
    """
    Crawl a URL and optionally follow links found in the content.
    
    Args:
        url: URL to crawl
        max_depth: Maximum link-following depth
        crawled_urls: Set of already crawled URLs
        
    Returns:
        Dict with crawl results
    """
    # Initialize the set of crawled URLs
    if crawled_urls is None:
        crawled_urls = set()
    
    # Skip if already crawled
    if url in crawled_urls:
        return {
            "status": "skipped",
            "message": "URL already crawled",
            "url": url
        }
    
    # Add to crawled URLs set
    crawled_urls.add(url)
    
    # Results container
    all_results = {
        "status": "success",
        "url": url,
        "content": "",
        "metadata": {},
        "saved_to": None,
        "linked_pages": []
    }
    
    context = None
    page = None
    
    try:
        # Get or create browser instance
        browser = await get_or_create_browser()
        
        # Create a new context with proper settings
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            ignore_https_errors=True
        )
        
        # Create a new page
        page = await context.new_page()
        
        try:
            # Navigate to URL and wait for load
            await page.goto(url, wait_until='networkidle')
            
            # Extract content
            content = await page.content()
            text = await page.evaluate('document.body.innerText')
            
            # Get metadata
            title = await page.title()
            metadata = {
                "title": title,
                "url": url
            }
            
            # Save content to markdown file
            saved_file = await save_crawl_to_markdown(
                content=text if text else "No content extracted",
                metadata=metadata,
                url=url
            )
            
            all_results["content"] = text if text else "No content extracted"
            all_results["metadata"] = metadata
            all_results["saved_to"] = saved_file
            
            # Extract URLs if depth allows
            if max_depth > 0:
                # Get all links on the page
                links = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.href)
                        .filter(href => href.startsWith('http'));
                }''')
                
                # Normalize URLs
                extracted_urls = await extract_urls_from_text('\n'.join(links), url)
                
                # Remove duplicates
                extracted_urls = list(set(extracted_urls))
                
                # Limit the number of URLs to crawl
                max_urls_to_crawl = 5
                extracted_urls = extracted_urls[:max_urls_to_crawl]
                
                # Recursively crawl extracted URLs
                for linked_url in extracted_urls:
                    if linked_url not in crawled_urls:
                        linked_result = await run_crawl(
                            url=linked_url,
                            max_depth=max_depth - 1,
                            crawled_urls=crawled_urls
                        )
                        all_results["linked_pages"].append({
                            "url": linked_url,
                            "saved_to": linked_result.get("saved_to")
                        })
                        
        except Exception as e:
            print(f"Error during page processing: {str(e)}")
            all_results["status"] = "error"
            all_results["message"] = str(e)
                
    except Exception as e:
        print(f"Error during browser setup: {str(e)}")
        all_results["status"] = "error"
        all_results["message"] = str(e)
        
    finally:
        # Clean up resources in reverse order
        if page:
            try:
                await page.close()
            except Exception as e:
                print(f"Warning: Error closing page: {str(e)}")
        
        if context:
            try:
                await context.close()
            except Exception as e:
                print(f"Warning: Error closing context: {str(e)}")
            
    return all_results

if __name__ == "__main__":
    async def main():
        try:
            await run_crawl("https://www.google.com")
        finally:
            await cleanup_browser()
    
    asyncio.run(main())
