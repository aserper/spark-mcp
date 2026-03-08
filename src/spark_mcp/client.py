from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import httpx

from .models import ClassSchedule, Token, UserInfo

BASE_URL = "https://mobileapi.sparkmembership.com/api/student/"


class SparkClient:
    """HTTP client for the Spark Membership API."""

    def __init__(self) -> None:
        self._token: Token | None = None
        self._user: UserInfo | None = None
        self._location_id: str = ""
        self._device_id = str(uuid.uuid4())
        self._http = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "User-Agent": "okhttp/4.12.0",
            },
        )

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None and self._token.access_token != ""

    def _auth_headers(self) -> dict[str, str]:
        if not self._token:
            return {}
        return {
            "Authorization": f"Bearer {self._token.access_token}",
            "Content-Type": "application/json",
        }

    async def _maybe_refresh_token(self) -> None:
        """Refresh token if it's expired."""
        if not self._token or not self._token.access_token_expiration:
            return
        try:
            exp = datetime.fromisoformat(
                self._token.access_token_expiration.replace("Z", "+00:00")
            )
            if exp > datetime.now(timezone.utc):
                return
        except (ValueError, TypeError):
            return

        resp = await self._http.post(
            "auth/refresh",
            json={
                "accessToken": self._token.access_token,
                "refreshToken": self._token.refresh_token,
            },
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = Token(
            access_token=data.get("accessToken", ""),
            access_token_expiration=data.get("accessTokenExpiration", ""),
            refresh_token=data.get("refreshToken", ""),
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict | list:
        await self._maybe_refresh_token()
        resp = await self._http.request(
            method, path, json=json, params=params, headers=self._auth_headers()
        )
        resp.raise_for_status()
        data = resp.json()
        # API wraps responses in {"result": ...}
        if isinstance(data, dict) and "result" in data:
            data = data["result"]
        return data

    async def login(
        self, email: str, password: str, location_id: int
    ) -> dict:
        """Authenticate and store the session token."""
        payload = {
            "email": email,
            "password": password,
            "locationID": str(location_id),
            "pushID": str(uuid.uuid4()),
            "deviceID": self._device_id,
            "OSVersion": "Android",
            "firebaseSenderID": "000000000",
        }
        resp = await self._http.post(
            "auth/user/login",
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        # API wraps responses in {"result": ...}
        if isinstance(data, dict) and "result" in data:
            data = data["result"]

        token_data = data.get("token", {})
        self._token = Token(
            access_token=token_data.get("accessToken", ""),
            access_token_expiration=token_data.get("accessTokenExpiration", ""),
            refresh_token=token_data.get("refreshToken", ""),
        )
        self._location_id = str(data.get("locationID", location_id))
        # Extract user info from activeLocations[0].familyMember[0]
        name = ""
        contact_id = 0
        profile_image = ""
        locations = data.get("activeLocations", [])
        if locations:
            members = locations[0].get("familyMember", [])
            if members:
                member = members[0]
                name = member.get("name", "")
                contact_id = member.get("contactID", 0)
                profile_image = member.get("profileImage", "")
        self._user = UserInfo(
            contact_id=contact_id,
            name=name,
            location_id=self._location_id,
            profile_image=profile_image,
        )
        return {
            "contact_id": self._user.contact_id,
            "name": self._user.name,
            "location_id": self._location_id,
            "authenticated": True,
        }

    async def validate_email(self, email: str, location_id: int) -> dict:
        resp = await self._http.post(
            "auth/email/validate",
            json={"email": email, "locationID": str(location_id), "pushID": ""},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    async def list_available_classes(self, selected_date: str = "") -> list[ClassSchedule]:
        """Get available classes for scheduling. date format: YYYY-MM-DD or empty for today."""
        params = {}
        if selected_date:
            params["selectedDate"] = selected_date
        data = await self._request("GET", "classes/available", params=params)
        if isinstance(data, list):
            return [ClassSchedule.from_api(item) for item in data]
        return []

    async def list_my_classes(self) -> list[ClassSchedule]:
        """Get classes the user is enrolled in."""
        data = await self._request("GET", "classes")
        if isinstance(data, list):
            return [ClassSchedule.from_api(item) for item in data]
        return []

    async def book_class(self, class_roster_id: int, class_date: str, extra_params: dict | None = None) -> dict:
        """Schedule/reserve a class by roster ID."""
        body = {"classDate": class_date}
        if extra_params:
            body.update(extra_params)
        data = await self._request(
            "POST", f"classes/roster/{class_roster_id}/schedule", json=body
        )
        return data if isinstance(data, dict) else {"result": data}

    async def cancel_booking(
        self, attendee_id: int, single_day_item: dict | None = None
    ) -> dict:
        """Cancel a class reservation."""
        data = await self._request(
            "DELETE",
            f"classes/roster/attendee/{attendee_id}",
            json=single_day_item or {},
        )
        return data if isinstance(data, dict) else {"result": data}

    async def join_waitlist(self, class_roster_id: int, extra_params: dict | None = None) -> dict:
        body = extra_params or {}
        data = await self._request(
            "POST", f"classes/roster/{class_roster_id}/waitlist", json=body
        )
        return data if isinstance(data, dict) else {"result": data}

    async def get_waitlist(self) -> list:
        data = await self._request("GET", "classes/waitlist")
        return data if isinstance(data, list) else []

    async def checkin(self, class_roster_id: int) -> dict:
        data = await self._request("POST", f"classes/roster/{class_roster_id}/checkin")
        return data if isinstance(data, dict) else {"result": data}

    async def get_dashboard(self) -> dict:
        data = await self._request("GET", "dashboard")
        return data if isinstance(data, dict) else {"data": data}

    async def get_attendance(self, page_index: int = 1, page_size: int = 20) -> list:
        data = await self._request(
            "GET", "attendance", params={"pageIndex": page_index, "pageSize": page_size}
        )
        return data if isinstance(data, list) else []

    async def get_announcements(self) -> list:
        data = await self._request("GET", "announcement")
        return data if isinstance(data, list) else []

    async def get_memberships(self) -> dict:
        data = await self._request("GET", "user/memberships")
        return data if isinstance(data, dict) else {"data": data}

    async def close(self) -> None:
        await self._http.aclose()
