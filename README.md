# spark-mcp

MCP server for the [Spark Membership](https://sparkmembership.com/) platform — a CRM used by hundreds of martial arts studios. Manage class scheduling, bookings, attendance, and more through any MCP client (e.g. Claude Code).

Built by reverse-engineering the Spark Membership mobile app API.

## Quick Start (Docker)

Docker is the preferred way to run spark-mcp — no Python install needed.

**1. Pull the image:**

```bash
docker pull ghcr.io/aserper/spark-mcp:latest
```

**2. Add to your Claude Code config** (`.mcp.json` in your project root or `~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "spark": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "--rm", "-i",
        "-e", "SPARK_EMAIL", "-e", "SPARK_PASSWORD", "-e", "SPARK_LOCATION_ID",
        "ghcr.io/aserper/spark-mcp"],
      "env": {
        "SPARK_EMAIL": "your-email@example.com",
        "SPARK_PASSWORD": "your-password",
        "SPARK_LOCATION_ID": "1234"
      }
    }
  }
}
```

**3. Restart Claude Code** and start asking about your classes.

## Finding your Location ID

Every studio on Spark Membership has a numeric location ID. Use the included `find_location.py` script to look it up.

**Search by state code:**

```bash
# Docker
docker run --rm --entrypoint python ghcr.io/aserper/spark-mcp find_location.py MA

# Local
python find_location.py MA
```

**Search by studio name:**

```bash
# Docker
docker run --rm --entrypoint python ghcr.io/aserper/spark-mcp find_location.py "jiu jitsu"

# Local
python find_location.py natick
```

**Interactive mode** (lists countries, states, then locations):

```bash
# Docker
docker run --rm -it --entrypoint python ghcr.io/aserper/spark-mcp find_location.py

# Local
python find_location.py
```

Example output:

```
    ID  Name
    --  ----
  1588  Metrowest Academy of Jiu Jitsu (Natick)
  6218  Villaris Martial Arts of Natick (Natick)
```

Use the `ID` value as your `SPARK_LOCATION_ID`.

## Tools

| Tool | Description |
|------|-------------|
| `login` | Authenticate with email, password, and location ID |
| `list_classes` | List available classes for a given date |
| `my_classes` | List classes you're currently enrolled in |
| `book_class` | Book a class by roster ID and date |
| `cancel_booking` | Cancel a class reservation |
| `join_waitlist` | Join the waitlist for a full class |
| `get_waitlist` | List classes you're on the waitlist for |
| `checkin` | Check in to a class |
| `dashboard` | Get the studio dashboard overview |
| `attendance` | View attendance history |
| `announcements` | Get studio announcements |
| `memberships` | Get membership status |

## Usage Examples

Once configured, you can ask Claude things like:

- "What classes are available this Saturday?"
- "Book me into the 9am Ninjas class on March 21"
- "What am I signed up for?"
- "Cancel my Saturday booking"
- "Show my attendance history"
- "Any new announcements from the studio?"

## Alternative: Local Install

If you prefer not to use Docker:

```bash
git clone https://github.com/aserper/spark-mcp.git
cd spark-mcp
uv venv && source .venv/bin/activate
uv pip install -e .
```

Then configure Claude Code with:

```json
{
  "mcpServers": {
    "spark": {
      "type": "stdio",
      "command": "/path/to/spark-mcp/.venv/bin/python",
      "args": ["-m", "spark_mcp"],
      "env": {
        "SPARK_EMAIL": "your-email@example.com",
        "SPARK_PASSWORD": "your-password",
        "SPARK_LOCATION_ID": "1234"
      }
    }
  }
}
```

## Authentication

Credentials can be provided in three ways:

1. **Environment variables** (recommended) — set `SPARK_EMAIL`, `SPARK_PASSWORD`, and `SPARK_LOCATION_ID` in your MCP config. The server auto-authenticates on first tool call.
2. **`login` tool** — call it manually at runtime without any env vars.
3. **Mix** — set email/password in env vars and use `login` to switch locations.

Tokens are automatically refreshed when they expire.

## API Reference

All endpoints hit `https://mobileapi.sparkmembership.com/api/student/`. Auth uses Bearer tokens with automatic refresh. See [`api-discovery.md`](api-discovery.md) for the full endpoint reference.

## Requirements

- Docker (preferred), or Python 3.11+
- A Spark Membership account (through your studio's app)
