"""MCP server for Spark Membership platform class scheduling."""

from __future__ import annotations

import json
import os

from mcp.server.fastmcp import FastMCP

from .client import SparkClient

mcp = FastMCP("spark", instructions="Class scheduling and studio management via Spark Membership API")
_client = SparkClient()


def _env_credentials() -> tuple[str, str, int] | None:
    email = os.environ.get("SPARK_EMAIL")
    password = os.environ.get("SPARK_PASSWORD")
    location_id = os.environ.get("SPARK_LOCATION_ID")
    if email and password and location_id:
        return email, password, int(location_id)
    return None


async def _ensure_auth() -> None:
    """Auto-login using env vars if not already authenticated."""
    if _client.is_authenticated:
        return
    creds = _env_credentials()
    if creds:
        await _client.login(*creds)


@mcp.tool()
async def login(email: str, password: str, location_id: int) -> str:
    """Authenticate with the Spark Membership API.

    Args:
        email: Account email address
        password: Account password
        location_id: Studio location ID
    """
    result = await _client.login(email, password, location_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_classes(selected_date: str = "") -> str:
    """List available classes for scheduling.

    Args:
        selected_date: Date in YYYY-MM-DD format. Empty string for today.
    """
    await _ensure_auth()
    classes = await _client.list_available_classes(selected_date)
    return json.dumps([c.model_dump() for c in classes], indent=2)


@mcp.tool()
async def my_classes() -> str:
    """List classes I'm currently enrolled in."""
    await _ensure_auth()
    classes = await _client.list_my_classes()
    return json.dumps([c.model_dump() for c in classes], indent=2)


@mcp.tool()
async def book_class(class_roster_id: int, class_date: str) -> str:
    """Book/schedule a class by its roster ID.

    Args:
        class_roster_id: The classRosterID from list_classes results.
        class_date: The date to book in YYYY-MM-DD format.
    """
    await _ensure_auth()
    result = await _client.book_class(class_roster_id, class_date)
    return json.dumps(result, indent=2)


@mcp.tool()
async def cancel_booking(attendee_id: int) -> str:
    """Cancel a class booking.

    Args:
        attendee_id: The attendee/booking ID to cancel.
    """
    await _ensure_auth()
    result = await _client.cancel_booking(attendee_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def join_waitlist(class_roster_id: int) -> str:
    """Join the waitlist for a full class.

    Args:
        class_roster_id: The classRosterID of the full class.
    """
    await _ensure_auth()
    result = await _client.join_waitlist(class_roster_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_waitlist() -> str:
    """Get classes I'm on the waitlist for."""
    await _ensure_auth()
    result = await _client.get_waitlist()
    return json.dumps(result, indent=2)


@mcp.tool()
async def checkin(class_roster_id: int) -> str:
    """Check in to a class.

    Args:
        class_roster_id: The classRosterID to check in to.
    """
    await _ensure_auth()
    result = await _client.checkin(class_roster_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def dashboard() -> str:
    """Get the dashboard overview."""
    await _ensure_auth()
    result = await _client.get_dashboard()
    return json.dumps(result, indent=2)


@mcp.tool()
async def attendance(page: int = 1, page_size: int = 20) -> str:
    """Get attendance history.

    Args:
        page: Page number (default 1).
        page_size: Results per page (default 20).
    """
    await _ensure_auth()
    result = await _client.get_attendance(page, page_size)
    return json.dumps(result, indent=2)


@mcp.tool()
async def announcements() -> str:
    """Get studio announcements."""
    await _ensure_auth()
    result = await _client.get_announcements()
    return json.dumps(result, indent=2)


@mcp.tool()
async def memberships() -> str:
    """Get membership status."""
    await _ensure_auth()
    result = await _client.get_memberships()
    return json.dumps(result, indent=2)
