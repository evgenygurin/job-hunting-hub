"""Neon database connection pool management."""

import os

import asyncpg  # type: ignore[import-untyped]

_pool: "asyncpg.Pool | None" = None


async def create_pool() -> "asyncpg.Pool":
    """Create and return a new asyncpg connection pool.
    
    Uses DATABASE_URL from environment. Raises RuntimeError if not set
    or if pool creation fails.
    """
    global _pool
    
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    
    try:
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=10,
        )
        return _pool
    except Exception as e:
        raise RuntimeError(f"Failed to create database pool: {e}") from e


async def close_pool() -> None:
    """Close the connection pool if it exists."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> "asyncpg.Pool":
    """Get the current connection pool.
    
    Returns the pool created by create_pool(). Should be called
    within a lifespan context where the pool is guaranteed to exist.
    """
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call create_pool() first.")
    return _pool