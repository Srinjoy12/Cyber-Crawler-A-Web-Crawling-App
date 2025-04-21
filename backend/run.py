import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from server import asgi_app

async def main():
    config = Config()
    config.bind = ["localhost:8080"]
    config.use_reloader = True
    config.accesslog = "-"  # Log to stdout
    
    print(f"Server running at http://localhost:8080")
    await serve(asgi_app, config)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down server...") 