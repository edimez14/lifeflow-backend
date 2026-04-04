#!/usr/bin/env python
"""Quick test script to verify backend endpoints without Thunder Client."""

import asyncio

import httpx


async def main() -> None:
    """Test the main backend endpoints."""

    base_url = "http://127.0.0.1:8000"

    async with httpx.AsyncClient() as client:
        print("Testing root endpoint...")
        response = await client.get(f"{base_url}/")
        print(f"GET / -> {response.status_code}: {response.json()}")

        print("\nTesting healthcheck endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"GET /health -> {response.status_code}: {response.json()}")

        print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
