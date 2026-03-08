#!/usr/bin/env python3
"""
Spark Membership Skill - Higher-level interface for spark-mcp
Provides natural language class booking with auto-discovery and fuzzy dates.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

CONFIG_DIR = Path.home() / ".config" / "spark-skill"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
PROFILES_FILE = CONFIG_DIR / "profiles.json"


@dataclass
class Profile:
    name: str
    attendee_ids: List[int]
    age_range: str = ""
    typical_classes: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    preferred_time: str = ""

    @property
    def display_name(self) -> str:
        return self.name.title()


class SparkSkill:
    def __init__(self):
        self.config = self._load_config()
        self.profiles: Dict[str, Profile] = {}
        self._load_profiles()

    def _load_config(self) -> dict:
        """Load or create default config."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return yaml.safe_load(f) or {}
        return {
            "defaults": {"export_format": "pretty", "auto_confirm": False, "dry_run": False}
        }

    def _load_profiles(self):
        """Load discovered profiles from cache."""
        if PROFILES_FILE.exists():
            with open(PROFILES_FILE) as f:
                data = json.load(f)
                for name, info in data.get("profiles", {}).items():
                    self.profiles[name] = Profile(name=name, **info)

    def _save_profiles(self):
        """Save profiles to cache."""
        data = {
            "profiles": {
                name: {
                    "attendee_ids": p.attendee_ids,
                    "age_range": p.age_range,
                    "typical_classes": p.typical_classes,
                    "aliases": p.aliases,
                    "preferred_time": p.preferred_time,
                }
                for name, p in self.profiles.items()
            }
        }
        with open(PROFILES_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _mcporter_call(self, tool: str, **kwargs) -> dict:
        """Call spark-mcp via mcporter."""
        args_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
        cmd = ["mcporter", "call", f"spark.{tool}"]
        if args_str:
            cmd.append(args_str)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"output": result.stdout}

    def discover_profiles(self):
        """Discover family members from existing bookings."""
        print("🔍 Discovering profiles from your Spark account...")

        classes = self._mcporter_call("my_classes")
        if not classes:
            print("No existing bookings found. Profiles will be created after first booking.")
            return

        profiles_data: Dict[str, dict] = {}

        for cls in classes:
            attendee_id = cls.get("attendee_id")
            class_name = cls.get("class_roster_name", "")

            # Extract name from class context or use generic
            name = self._extract_name_from_class(cls) or f"attendee_{attendee_id}"
            name_key = name.lower().replace(" ", "_")

            # Infer age range from class name
            age_range = self._extract_age_range(class_name)

            if name_key not in profiles_data:
                profiles_data[name_key] = {
                    "name": name,
                    "attendee_ids": [],
                    "age_range": age_range,
                    "typical_classes": [],
                    "aliases": [name_key[:3]],  # Short alias
                    "preferred_time": "",
                }

            if attendee_id not in profiles_data[name_key]["attendee_ids"]:
                profiles_data[name_key]["attendee_ids"].append(attendee_id)

            # Track typical classes
            class_type = self._extract_class_type(class_name)
            if class_type and class_type not in profiles_data[name_key]["typical_classes"]:
                profiles_data[name_key]["typical_classes"].append(class_type)

        # Convert to Profile objects
        self.profiles = {k: Profile(name=v["name"], **{ik: iv for ik, iv in v.items() if ik != "name"}) for k, v in profiles_data.items()}
        self._save_profiles()

        print(f"✅ Discovered {len(self.profiles)} profile(s):")
        for name, profile in self.profiles.items():
            classes_str = ", ".join(profile.typical_classes[:2]) if profile.typical_classes else "various"
            print(f"   • {profile.display_name} — {profile.age_range or 'unknown age'} — {classes_str}")

    def _extract_name_from_class(self, cls: dict) -> Optional[str]:
        """Try to extract attendee name from class data."""
        # This is a heuristic - Spark API doesn't always expose names clearly
        # In practice, users may need to manually map attendee IDs to names
        return None

    def _extract_age_range(self, class_name: str) -> str:
        """Extract age range from class name like 'Ninjas (ages 4-6)'."""
        match = re.search(r'ages?\s+(\d+)(?:-(\d+))?', class_name, re.IGNORECASE)
        if match:
            if match.group(2):
                return f"{match.group(1)}-{match.group(2)}"
            return f"{match.group(1)}+"
        return ""

    def _extract_class_type(self, class_name: str) -> str:
        """Extract class type from full name."""
        # Extract base class name before parenthetical
        match = re.match(r'^([^([]+)', class_name)
        if match:
            return match.group(1).strip()
        return class_name

    def _parse_date(self, date_str: str) -> str:
        """Parse fuzzy date to YYYY-MM-DD."""
        date_str = date_str.lower().strip()
        today = datetime.now()

        # Direct date formats
        for fmt in ["%Y-%m-%d", "%m-%d", "%m/%d", "%B %d", "%b %d"]:
            try:
                parsed = datetime.strptime(date_str, fmt)
                if parsed.year == 1900:  # Year not specified
                    parsed = parsed.replace(year=today.year)
                    if parsed < today:  # If in past, assume next year
                        parsed = parsed.replace(year=today.year + 1)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Relative dates
        if date_str == "today":
            return today.strftime("%Y-%m-%d")
        if date_str == "tomorrow":
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")

        # Day of week
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if date_str in days:
            target_day = days.index(date_str)
            days_ahead = target_day - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            target = today + timedelta(days=days_ahead)
            return target.strftime("%Y-%m-%d")

        if date_str.startswith("next "):
            day_name = date_str[5:]
            if day_name in days:
                target_day = days.index(day_name)
                days_ahead = target_day - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                days_ahead += 7  # Add another week for "next"
                target = today + timedelta(days=days_ahead)
                return target.strftime("%Y-%m-%d")

        raise ValueError(f"Could not parse date: {date_str}")

    def _find_profile(self, name: str) -> Optional[Profile]:
        """Find profile by name or alias."""
        name = name.lower()

        # Direct match
        if name in self.profiles:
            return self.profiles[name]

        # Check aliases
        for profile in self.profiles.values():
            if name in [a.lower() for a in profile.aliases]:
                return profile

        # Partial match
        for profile_name, profile in self.profiles.items():
            if name in profile_name.lower() or profile_name.lower() in name:
                return profile

        return None

    def cmd_who(self):
        """List discovered profiles."""
        if not self.profiles:
            print("No profiles discovered yet. Run 'spark discover' or make a booking first.")
            return

        print("👥 Discovered profiles:")
        for name, profile in sorted(self.profiles.items()):
            aliases = f" (aliases: {', '.join(profile.aliases)})" if profile.aliases else ""
            classes = f" — typically: {', '.join(profile.typical_classes[:2])}" if profile.typical_classes else ""
            print(f"   • {profile.display_name}{aliases}{classes}")

    def cmd_list(self, date_str: str = "", age_filter: str = ""):
        """List available classes."""
        if date_str:
            date = self._parse_date(date_str)
        else:
            date = datetime.now().strftime("%Y-%m-%d")

        print(f"📅 Classes for {date}:")
        classes = self._mcporter_call("list_classes", selected_date=date)

        if not classes:
            print("   No classes found.")
            return

        for cls in classes:
            class_name = cls.get("class_roster_name", "Unknown")
            spots = cls.get("spots_left", "?")
            full = "🔴 FULL" if cls.get("class_full") else f"🟢 {spots} spots"
            time = cls.get("class_time", "")
            print(f"   • {class_name} ({time}) — {full}")

    def cmd_book(self, who: str, when: str, dry_run: bool = False):
        """Book a class for someone."""
        profile = self._find_profile(who)
        if not profile:
            print(f"❌ Profile '{who}' not found. Run 'spark who' to see available profiles.")
            sys.exit(1)

        date = self._parse_date(when)

        # Get available classes for that date
        classes = self._mcporter_call("list_classes", selected_date=date)

        # Filter by age-appropriateness
        age_appropriate = []
        for cls in classes:
            class_age = self._extract_age_range(cls.get("class_roster_name", ""))
            if self._age_match(profile.age_range, class_age):
                age_appropriate.append(cls)

        if not age_appropriate:
            print(f"❌ No age-appropriate classes found for {profile.display_name} on {date}")
            return

        # Pick best match (first available or preferred time)
        selected = age_appropriate[0]

        class_name = selected.get("class_roster_name", "Unknown")
        roster_id = selected.get("class_roster_id")

        if dry_run:
            print(f"📝 [DRY RUN] Would book {profile.display_name} for {class_name} on {date}")
            return

        print(f"📌 Booking {profile.display_name} for {class_name} on {date}...")

        result = self._mcporter_call("book_class", class_roster_id=roster_id, class_date=date)

        if result is None or result.get("result") is None:
            print(f"✅ Booked! Attendee ID: {profile.attendee_ids[0]}")
        else:
            print(f"❌ Booking failed: {result}")

    def _age_match(self, profile_age: str, class_age: str) -> bool:
        """Check if profile age range matches class age range."""
        if not profile_age or not class_age:
            return True  # Allow if unknown

        # Parse ranges like "4-6" or "7+"
        def parse_range(age_str: str) -> Tuple[int, int]:
            age_str = age_str.replace("+", "-99")
            if "-" in age_str:
                parts = age_str.split("-")
                return int(parts[0]), int(parts[1])
            return int(age_str), int(age_str)

        try:
            p_min, p_max = parse_range(profile_age)
            c_min, c_max = parse_range(class_age)

            # Check if ranges overlap
            return p_min <= c_max and c_min <= p_max
        except (ValueError, IndexError):
            return True

    def cmd_my_classes(self):
        """Show current bookings."""
        classes = self._mcporter_call("my_classes")

        if not classes:
            print("📭 No upcoming classes booked.")
            return

        print("📚 Your bookings:")
        for cls in classes:
            name = cls.get("class_roster_name", "Unknown")
            date = cls.get("days", "")
            time = cls.get("time_start", "")
            attendee_id = cls.get("attendee_id", "")
            print(f"   • {name} — {date} at {time} (ID: {attendee_id})")

    def cmd_next(self):
        """Show next upcoming class."""
        classes = self._mcporter_call("my_classes")

        if not classes:
            print("📭 No upcoming classes.")
            return

        # Sort by date and take first
        next_class = classes[0]
        name = next_class.get("class_roster_name", "Unknown")
        date = next_class.get("days", "")
        time = next_class.get("time_start", "")

        print(f"⏭️  Next class: {name}")
        print(f"   📅 {date} at {time}")


def main():
    parser = argparse.ArgumentParser(description="Spark Membership Skill")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # who
    subparsers.add_parser("who", help="List discovered profiles")

    # discover
    subparsers.add_parser("discover", help="Discover profiles from Spark account")

    # list
    list_parser = subparsers.add_parser("list", help="List available classes")
    list_parser.add_argument("date", nargs="?", default="", help="Date (e.g., 'thursday', '2026-03-12')")

    # book
    book_parser = subparsers.add_parser("book", help="Book a class")
    book_parser.add_argument("who", help="Who to book for (profile name)")
    book_parser.add_argument("when", help="When to book (e.g., 'thursday', 'march 12')")
    book_parser.add_argument("--dry-run", action="store_true", help="Show what would be booked")

    # my-classes
    subparsers.add_parser("my-classes", help="Show current bookings")

    # next
    subparsers.add_parser("next", help="Show next upcoming class")

    # cancel
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a booking")
    cancel_parser.add_argument("attendee_id", help="Attendee/booking ID to cancel")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    skill = SparkSkill()

    if args.command == "discover":
        skill.discover_profiles()
    elif args.command == "who":
        skill.cmd_who()
    elif args.command == "list":
        skill.cmd_list(args.date)
    elif args.command == "book":
        skill.cmd_book(args.who, args.when, args.dry_run)
    elif args.command == "my-classes":
        skill.cmd_my_classes()
    elif args.command == "next":
        skill.cmd_next()
    elif args.command == "cancel":
        print(f"Use: mcporter call spark.cancel_booking attendee_id={args.attendee_id}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
