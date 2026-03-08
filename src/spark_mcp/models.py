from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str = ""
    access_token_expiration: str = ""
    refresh_token: str = ""


class ClassSchedule(BaseModel):
    class_roster_id: int = 0
    class_roster_name: str = ""
    rank_system_name: str = ""
    class_type: str = ""
    class_size_limit: int = 0
    class_roster_description: str = ""
    allow_app_schedule: bool = False
    enabled: bool = True
    instructor: str = ""
    instructor2: str = ""
    instructor3: str = ""
    is_virtual_class: bool = False
    spots_left: int = 0
    class_full: bool = False
    utc_start_time: str = ""
    utc_end_time: str = ""
    full_dates: list[str] = []
    allow_to_reserve_roster_before_x_minutes: int = 0

    @classmethod
    def from_api(cls, data: dict) -> ClassSchedule:
        return cls(
            class_roster_id=data.get("classRosterID") or 0,
            class_roster_name=data.get("classRosterName") or "",
            rank_system_name=data.get("rankSystemName") or "",
            class_type=data.get("classType") or "",
            class_size_limit=data.get("classSizeLimit") or 0,
            class_roster_description=data.get("classRosterDescription") or "",
            allow_app_schedule=data.get("allowAppSchedule") or False,
            enabled=data.get("enabled", True),
            instructor=data.get("instructor") or "",
            instructor2=data.get("instructor2") or "",
            instructor3=data.get("instructor3") or "",
            is_virtual_class=data.get("isVirtualClass") or False,
            spots_left=data.get("spotsLeft") or 0,
            class_full=data.get("classFull") or False,
            utc_start_time=data.get("utcStartTime") or "",
            utc_end_time=data.get("utcEndTime") or "",
            full_dates=data.get("fullDates") or [],
            allow_to_reserve_roster_before_x_minutes=data.get(
                "allowToReserveRosterBeforeXMinutes"
            ) or 0,
        )


class UserInfo(BaseModel):
    contact_id: int = 0
    name: str = ""
    location_id: str = ""
    profile_image: str = ""
