---
name: spark
homepage: https://github.com/aserper/spark-mcp
description: Natural language interface for Spark Membership class booking — discover family members, book classes with fuzzy dates, bulk scheduling, and calendar export.
metadata:
  openclaw:
    emoji: 🥊
    requires:
      bins:
        - mcporter
      env:
        - SPARK_EMAIL
        - SPARK_PASSWORD
        - SPARK_LOCATION_ID
    install:
      - id: node
        kind: node
        package: mcporter
        bins:
          - mcporter
      - id: docker
        kind: docker
        image: ghcr.io/aserper/spark-mcp:latest
    tags:
      - fitness
      - scheduling
      - martial-arts
      - family
---

# Spark Membership Skill

A higher-level interface for the [spark-mcp](https://github.com/aserper/spark-mcp) server. Instead of working with raw roster IDs, book classes using natural language like "book Hailey for Thursday" or "sign Ily up for next Saturday."

## Prerequisites

You need the `spark-mcp` server configured first:

```bash
# Using mcporter
mcporter config add spark --docker ghcr.io/aserper/spark-mcp:latest
```

Or via Claude Code's `.mcp.json` — see the [main spark-mcp README](../README.md) for setup.

## Natural Language Usage (OpenClaw/Claude Code)

When using this skill with OpenClaw or Claude Code, you can speak naturally instead of typing commands:

| Natural language | Command equivalent |
|------------------|-------------------|
| "Book Hailey for Thursday" | `spark book hailey thursday` |
| "What classes do we have?" | `spark my-classes` |
| "List Saturday classes" | `spark list saturday` |
| "When's our next class?" | `spark next` |
| "Cancel Hailey's Thursday booking" | `spark cancel <id>` |
| "Who's enrolled?" | `spark who` |
| "Book Ily for next Saturday" | `spark book ily "next saturday"` |

The agent handles translating your natural language to the appropriate skill commands.

## Quick Start

```bash
# Discover who's on your account
spark who

# Book a class
spark book hailey thursday
spark book "ily next saturday"

# List your current bookings
spark my-classes

# Bulk book (e.g., all Saturdays for 6 weeks)
spark bulk "hailey saturdays 6 weeks"
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `spark who` | List discovered family members | `spark who` |
| `spark book <who> <when>` | Book a class | `spark book hailey march-12` |
| `spark bulk <pattern>` | Book multiple classes | `spark bulk "ily saturdays 4 weeks"` |
| `spark list [date]` | List available classes | `spark list saturday` |
| `spark my-classes` | Show current bookings | `spark my-classes` |
| `spark cancel <id>` | Cancel a booking | `spark cancel 35833762` |
| `spark next` | Show next upcoming class | `spark next` |
| `spark export` | Export to ICS calendar | `spark export --ics > classes.ics` |

## How It Works

### Auto-Discovery

On first run, the skill queries your Spark account and builds a profile map from existing bookings:

```json
{
  "profiles": {
    "hailey": {
      "attendee_ids": [35833762],
      "age_range": "4-6",
      "typical_classes": ["Ninjas"]
    },
    "ily": {
      "attendee_ids": [35832461],
      "age_range": "11-14",
      "typical_classes": ["JRs"]
    }
  }
}
```

No hardcoded names — it learns your family from the API.

### Fuzzy Date Parsing

- `thursday` → next Thursday
- `next saturday` → upcoming Saturday
- `march 12` → 2026-03-12
- `tomorrow` → tomorrow's date
- `in 3 days` → date math

### Age-Appropriate Filtering

When booking, the skill only shows classes matching the profile's age range:

- Hailey (age 4-6) → sees "Ninjas", "Little Dragons"
- Ily (age 11-14) → sees "JRs", "Teen", "Adult"

### Smart Defaults

```bash
# These are equivalent if Hailey's typical class is Ninjas at 5:30pm:
spark book hailey thursday
spark book hailey thursday 5:30
spark book hailey --class "Ninjas" thursday
```

## Bulk Booking Patterns

```bash
# Every Saturday for N weeks
spark bulk "hailey saturdays 6 weeks"

# All weekdays in a range
spark bulk "ily monday-friday march 10-14"

# Specific days of week
spark bulk "hailey tuesday,thursday 4 weeks"
```

## Configuration

The skill stores preferences in `~/.config/spark-skill/config.yaml`:

```yaml
# Auto-discovered profiles (don't edit manually)
profiles:
  hailey:
    attendee_ids: [35833762]
    aliases: ["h", "hay"]
    preferred_time: "17:30"
  ily:
    attendee_ids: [35832461]
    aliases: ["i"]
    preferred_time: "09:00"

# Default behavior
defaults:
  export_format: pretty  # pretty|json|ics
  auto_confirm: false    # prompt before booking
  dry_run: false         # show what would be booked without doing it
```

## Integration with Claude Code / OpenClaw

Once installed, you can ask naturally:

- "What classes are available this week?"
- "Book Hailey for the next 4 Saturdays"
- "When is Ily's next class?"
- "Cancel Hailey's Thursday booking"
- "Export this month's classes to my calendar"

## Troubleshooting

**"No profiles found"**
- Run `mcporter call spark.my_classes` to verify the MCP server is working
- Ensure you have existing bookings for the skill to discover profiles from

**"Class not found"**
- Check `spark list <date>` to see available classes
- The class may be full or outside the age range

**"Booking failed"**
- Run with `--dry-run` to see the roster ID being used
- Verify the date format (YYYY-MM-DD)

## License

Same as spark-mcp — MIT License.
