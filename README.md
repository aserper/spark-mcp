# spark-mcp

MCP server for the [Spark Membership](https://sparkmembership.com/) platform — a CRM used by martial arts studios. Lets you manage class scheduling, bookings, attendance, and more through any MCP client (e.g. Claude Code).

Built by reverse-engineering the Spark Membership mobile app API.

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

## Setup

### 1. Install

```bash
git clone https://github.com/yourusername/spark-mcp.git
cd spark-mcp
uv venv && source .venv/bin/activate
uv pip install -e .
```

### 2. Find your Location ID

Your studio has a numeric location ID on the Spark platform. To find it:

```bash
source .venv/bin/activate
python -c "
import asyncio, httpx
async def find():
    base = 'https://mobileapi.sparkmembership.com/api/student/'
    async with httpx.AsyncClient(base_url=base, timeout=30) as c:
        # List US states (use country ID 1 for US)
        states = (await c.get('auth/states/1', headers={'Accept':'application/json'})).json().get('result',[])
        state = input('Enter state code (e.g. MA): ').strip().upper()
        locs = (await c.get(f'auth/locations/{state}', headers={'Accept':'application/json'})).json().get('result',[])
        for loc in locs:
            print(f\"  {loc['id']:>6}  {loc['name']}\")
asyncio.run(find())
"
```

### 3. Configure Claude Code

Add to your project's `.mcp.json`:

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

Or use the `login` tool manually without env vars.

## Usage

Once configured, you can ask Claude things like:

- "What classes are available this Saturday?"
- "Book me into the 9am NINJAS class on March 21"
- "What am I signed up for?"
- "Show my attendance history"

## API

All endpoints hit `https://mobileapi.sparkmembership.com/api/student/`. Auth uses Bearer tokens with automatic refresh. See `api-discovery.md` for the full endpoint reference.

## Requirements

- Python 3.11+
- A Spark Membership account (through your studio's app)
