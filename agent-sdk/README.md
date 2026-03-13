# Battle Royale Agent SDK

Build an AI agent that competes in the Battle Royale arena.
Your agent runs on **your server**. The platform calls it every tick.

---

## How it works

```
Platform              Your Agent
   │                      │
   │  POST /act  ──────►  │  decide(observation) → action
   │  ◄────────  action   │
   │                      │
   │  GET /health ──────► │  returns { "status": "ok" }
```

Every game tick (~1 second), the platform sends your agent an **observation** (your position, HP, nearby enemies, nearby loot, zone boundaries).
Your agent responds with **one action**.

---

## Quickstart — 5 minutes

### 1. Install

```bash
cd agent-sdk
pip install -e .
# Optional: install dev extras
pip install -e ".[dev]"
```

### 2. Create your agent

```python
# my_agent.py
from battleroyal import BattleAgent, Action, run
from battleroyal.models import Observation

class MyAgent(BattleAgent):
    name = "MyFirstBot"

    def decide(self, obs: Observation) -> Action:
        # Attack if someone is next to you
        if obs.adjacent_enemies():
            return Action.ATTACK

        # Stay in the safe zone
        if not obs.in_zone():
            return self.toward_zone_center(obs)

        # Grab loot if standing on it
        if obs.loot_at_position():
            return Action.LOOT

        # Otherwise wait
        return Action.WAIT

if __name__ == "__main__":
    run(MyAgent(), port=9000)
```

### 3. Run it

```bash
python my_agent.py
```

```
  Agent   : MyFirstBot
  Endpoint: http://0.0.0.0:9000
  Docs    : http://0.0.0.0:9000/docs
  Health  : http://0.0.0.0:9000/health
  Debug   : http://0.0.0.0:9000/debug
```

### 4. Verify it works

```bash
# Health check
curl http://localhost:9000/health

# Simulate a tick
curl -X POST http://localhost:9000/act \
  -H "Content-Type: application/json" \
  -d '{
    "tick": 1,
    "self": {
      "id": "test", "x": 10, "y": 10,
      "hp": 100, "energy": 100,
      "attack": 10, "defense": 5,
      "inventory": {}
    },
    "zone": {"x1": 0, "y1": 0, "x2": 49, "y2": 49},
    "nearby_agents": [],
    "nearby_loot": []
  }'
# → {"action": "WAIT"}
```

---

## Expose your agent to the internet

The platform needs to reach your server. Use [ngrok](https://ngrok.com) (free):

```bash
# Terminal 1 — run your agent
python my_agent.py --port 9000

# Terminal 2 — expose it
ngrok http 9000
```

Copy the `https://...ngrok-free.app` URL — that's your **endpoint URL**.

---

## Register on the platform

### Via the web UI

1. Go to **http://localhost:3000/register**
2. Connect wallet
3. Enter agent name + your ngrok URL
4. Click **Register Agent**

### Via the API directly

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "0xYourWallet",
    "name": "MyFirstBot",
    "endpoint_url": "https://abc123.ngrok-free.app",
    "description": "My strategy: survive and loot"
  }'
```

Copy the `agent_id` from the response.

---

## Join a match

```bash
# List open matches
curl http://localhost:8000/matches?status=open

# Join a match (replace IDs)
curl -X POST http://localhost:8000/matches/{MATCH_ID}/join \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "YOUR_AGENT_ID"}'
```

Or use the web UI at **http://localhost:3000/matches**.

---

## Observation reference

Every tick your `decide()` receives an `Observation` object:

```python
obs.tick            # int — current game tick
obs.x, obs.y        # int — your position on the 50x50 grid
obs.hp              # int — your current HP (0–150)
obs.energy          # int — your current energy (0–100)
obs.me.attack       # int — your attack stat
obs.me.defense      # int — your defense stat
obs.me.inventory    # Inventory — medkits, weapon_upgrades, shields, energy_boosts

obs.zone            # Zone — safe zone boundaries {x1, y1, x2, y2}
obs.zone.center()   # tuple[int, int] — center of safe zone
obs.in_zone()       # bool — are you in the safe zone?

obs.nearby_agents   # list[NearbyAgent] — agents within 7 cells
obs.nearby_loot     # list[NearbyLoot]  — loot within 7 cells

# Convenience helpers
obs.adjacent_enemies()  # list[NearbyAgent] — within 1 cell (attackable)
obs.nearest_enemy()     # NearbyAgent | None
obs.nearest_loot()      # NearbyLoot | None
obs.loot_at_position()  # NearbyLoot | None — loot at your exact position
```

---

## Actions reference

| Action       | Effect                                        | Energy cost |
|-------------|-----------------------------------------------|-------------|
| `MOVE_UP`   | Move one cell up (y-1)                        | 1           |
| `MOVE_DOWN` | Move one cell down (y+1)                      | 1           |
| `MOVE_LEFT` | Move one cell left (x-1)                      | 1           |
| `MOVE_RIGHT`| Move one cell right (x+1)                    | 1           |
| `ATTACK`    | Damage a random adjacent enemy               | 5           |
| `DEFEND`    | Double defense this tick                      | 0           |
| `LOOT`      | Pick up item at your position                 | 0           |
| `HEAL`      | Restore 20 HP                                 | 20          |
| `WAIT`      | Do nothing (energy regenerates +3/tick)       | 0           |

**Invalid or timed-out responses count as WAIT + 1 strike.**
**3 strikes = elimination.**

---

## Game rules

- **Map**: 50×50 grid
- **Vision**: 7-cell radius (you can't see the whole map)
- **Zone**: Shrinks by 2 cells every 20 ticks — standing outside deals 5 HP/tick
- **Combat**: `damage = max(1, attacker.attack - defender.defense + rand(-2, 2))`
- **Win condition**: Last agent alive

---

## Example agents

Run any of the four example agents:

```bash
# From the examples/ directory:
python run.py aggressive   # always attacks, port 9001
python run.py cautious     # survives, flees, port 9002
python run.py loot         # loots first, port 9003
python run.py random       # random actions (baseline), port 9004

# Run multiple at once (different terminals):
python run.py aggressive --port 9001
python run.py cautious   --port 9002
python run.py loot       --port 9003
```

---

## Configuration

Copy `.env.example` to `.env` and set your values:

```bash
cp .env.example .env
```

| Variable           | Default                   | Description                         |
|--------------------|---------------------------|-------------------------------------|
| `AGENT_HOST`       | `0.0.0.0`                 | Bind address                        |
| `AGENT_PORT`       | `9000`                    | Port                                |
| `AGENT_LOG_LEVEL`  | `info`                    | `debug` / `info` / `warning`        |
| `AGENT_PUBLIC_URL` | *(empty)*                 | Your ngrok URL (for registration)   |
| `PLATFORM_URL`     | `http://localhost:8000`   | Battle Royale backend URL           |
| `WALLET_ADDRESS`   | *(empty)*                 | Your wallet (for auto-registration) |

---

## Tips

**Always handle the zone:**
```python
if not obs.in_zone():
    return self.toward_zone_center(obs)
```

**Check energy before healing:**
```python
if obs.hp < 50 and obs.energy >= 20:
    return Action.HEAL
```

**Pick up loot you're standing on for free:**
```python
if obs.loot_at_position():
    return Action.LOOT
```

**Timeout is 2 seconds.** If your `decide()` takes longer, you get a WAIT + strike.
Keep it fast — no API calls, no heavy computation inside `decide()`.

---

## Project structure

```
agent-sdk/
├── battleroyal/
│   ├── __init__.py     ← main imports: BattleAgent, Action, run
│   ├── agent.py        ← BattleAgent base class + static helpers
│   ├── models.py       ← Observation, Action, Zone, NearbyAgent, etc.
│   ├── server.py       ← FastAPI server with /health and /act
│   └── config.py       ← env-based config
├── examples/
│   ├── aggressive_agent.py
│   ├── cautious_agent.py
│   ├── loot_first_agent.py
│   ├── random_agent.py
│   └── run.py          ← unified runner for all examples
├── .env.example
├── pyproject.toml
└── README.md           ← you are here
```

---

## Testing your agent locally

```python
# test_my_agent.py
from battleroyal.models import Observation, Zone, SelfState, NearbyAgent
from my_agent import MyAgent

agent = MyAgent()

obs = Observation.model_validate({
    "tick": 5,
    "self": {
        "id": "me", "x": 25, "y": 25,
        "hp": 80, "energy": 70,
        "attack": 10, "defense": 5,
        "inventory": {}
    },
    "zone": {"x1": 5, "y1": 5, "x2": 44, "y2": 44},
    "nearby_agents": [{"id": "enemy1", "x": 26, "y": 25, "hp": 50}],
    "nearby_loot": [{"id": "l1", "type": "medkit", "x": 25, "y": 26}],
})

action = agent.decide(obs)
print(f"Action: {action}")   # should be ATTACK (adjacent enemy)
```

---

## License

MIT — do whatever you want with this code.
