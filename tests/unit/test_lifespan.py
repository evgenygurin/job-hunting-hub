import os

from fastmcp import FastMCP

from hub.composition import db_lifespan


async def test_lifespan_yields_pool():
    # Ensure DATABASE_URL is set for the test
    os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    
    mcp = FastMCP("test", lifespan=db_lifespan)
    async with mcp.lifespan():
        pass