"""Lifespan composition for job-hunting-hub.

Exports composed lifespans for FastMCP server initialization.
"""

from collections.abc import AsyncGenerator

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan

from hub.infra.neon import close_pool, create_pool


@lifespan
async def db_lifespan(server: FastMCP) -> AsyncGenerator[dict[str, object], None]:
    """Database lifespan managing asyncpg connection pool.
    
    Yields a dict with 'pool' key containing the asyncpg.Pool instance.
    Ensures pool is closed on teardown even if startup fails.
    """
    pool = await create_pool()
    try:
        yield {"pool": pool}
    finally:
        await close_pool()