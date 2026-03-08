#!/usr/bin/env python3
"""Find your Spark Membership studio location ID."""

import asyncio
import sys

import httpx

BASE = "https://mobileapi.sparkmembership.com/api/student/"
HEADERS = {"Accept": "application/json"}


async def get_countries(client: httpx.AsyncClient) -> list[dict]:
    r = await client.get("auth/countries", headers=HEADERS)
    r.raise_for_status()
    return r.json().get("result", [])


async def get_states(client: httpx.AsyncClient, country_id: int) -> list[dict]:
    r = await client.get(f"auth/states/{country_id}", headers=HEADERS)
    r.raise_for_status()
    return r.json().get("result", [])


async def get_locations(client: httpx.AsyncClient, state_code: str) -> list[dict]:
    r = await client.get(f"auth/locations/{state_code}", headers=HEADERS)
    r.raise_for_status()
    return r.json().get("result", [])


async def search(query: str) -> None:
    query_lower = query.lower()
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as client:
        countries = await get_countries(client)

        # Try query as a state code first (e.g. "MA", "CA")
        if len(query) == 2 and query.isalpha():
            locations = await get_locations(client, query.upper())
            if locations:
                print_locations(locations)
                return

        # Search all US states for matching locations
        print(f"Searching for '{query}' across all states...\n")
        states = await get_states(client, 1)  # US
        found = []
        for state in states:
            code = state.get("locationState", "")
            if not code:
                continue
            locations = await get_locations(client, code)
            for loc in locations:
                name = loc.get("name", "")
                if query_lower in name.lower():
                    found.append(loc)

        if found:
            print_locations(found)
        else:
            print(f"No locations found matching '{query}'.")
            print("Try a state code (e.g. MA) or a broader search term.")


async def interactive() -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as client:
        countries = await get_countries(client)
        print("Countries:")
        for c in countries:
            print(f"  {c['id']:>4}  {c['name']}")

        country_id = int(input("\nEnter country ID (1 for US): ").strip() or "1")
        states = await get_states(client, country_id)

        print("\nStates:")
        for s in states:
            code = s.get("locationState", "")
            name = s.get("stateName", "")
            if code:
                print(f"  {code:>4}  {name}")

        state_code = input("\nEnter state code (e.g. MA): ").strip().upper()
        locations = await get_locations(client, state_code)
        print()
        print_locations(locations)


def print_locations(locations: list[dict]) -> None:
    if not locations:
        print("No locations found.")
        return
    print(f"{'ID':>6}  {'Name'}")
    print(f"{'--':>6}  {'----'}")
    for loc in sorted(locations, key=lambda x: x.get("name", "")):
        print(f"{loc['id']:>6}  {loc['name']}")


def main() -> None:
    args = sys.argv[1:]
    if args:
        asyncio.run(search(" ".join(args)))
    else:
        asyncio.run(interactive())


if __name__ == "__main__":
    main()
