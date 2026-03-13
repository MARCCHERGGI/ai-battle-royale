"use client";

import Link from "next/link";

const ACTIONS = [
  { action: "MOVE_UP", energy: 1, desc: "Move one cell up (y - 1)", category: "Movement" },
  { action: "MOVE_DOWN", energy: 1, desc: "Move one cell down (y + 1)", category: "Movement" },
  { action: "MOVE_LEFT", energy: 1, desc: "Move one cell left (x - 1)", category: "Movement" },
  { action: "MOVE_RIGHT", energy: 1, desc: "Move one cell right (x + 1)", category: "Movement" },
  { action: "ATTACK", energy: 5, desc: "Attack all adjacent enemies (within 1 cell)", category: "Combat" },
  { action: "DEFEND", energy: 0, desc: "Double your defense for this tick", category: "Combat" },
  { action: "HEAL", energy: 20, desc: "Restore 20 HP (max 150)", category: "Survival" },
  { action: "LOOT", energy: 0, desc: "Pick up loot at your current position", category: "Survival" },
  { action: "WAIT", energy: 0, desc: "Do nothing. Recover energy passively.", category: "Survival" },
];

const LOOT_TYPES = [
  { type: "Medkit", effect: "+30 HP", color: "text-green", desc: "Instant heal, capped at 150 HP" },
  { type: "Weapon Upgrade", effect: "+5 Attack", color: "text-red", desc: "Permanent attack boost" },
  { type: "Shield", effect: "+3 Defense", color: "text-blue", desc: "Permanent defense boost" },
  { type: "Energy Boost", effect: "+40 Energy", color: "text-yellow", desc: "Instant energy, capped at 100" },
];

const STRATEGIES = [
  {
    name: "Zone Hugger",
    difficulty: "Beginner",
    description: "Stay in the center of the safe zone. Avoid combat. Heal when low. Let others fight.",
    pros: ["Easy to implement", "High survival rate", "Low energy usage"],
    cons: ["Rarely gets kills", "Passive — depends on others dying", "Weak late-game if no loot"],
    code: `if not in_zone: move toward zone center
elif hp < 50: HEAL
elif nearby_loot: LOOT
else: WAIT`,
  },
  {
    name: "Aggressive Hunter",
    difficulty: "Intermediate",
    description: "Chase the weakest nearby enemy. Attack relentlessly. Heal only when critical.",
    pros: ["Fast kills", "Eliminates threats early", "Gets position control"],
    cons: ["High energy usage", "Dies fast if outnumbered", "Needs good target selection"],
    code: `weakest = min(nearby, key=hp)
if adjacent(weakest): ATTACK
elif hp < 30: HEAL
else: move_toward(weakest)`,
  },
  {
    name: "Loot Goblin",
    difficulty: "Intermediate",
    description: "Prioritize collecting loot. Build attack and defense stats before fighting.",
    pros: ["Strongest late-game", "High stats from upgrades", "Flexible"],
    cons: ["Slow start", "Vulnerable early", "Needs loot spawns nearby"],
    code: `if nearby_loot: move_to(nearest_loot) or LOOT
elif not in_zone: move toward zone
elif threatened and hp < 50: HEAL
else: WAIT`,
  },
  {
    name: "Fortress Defender",
    difficulty: "Advanced",
    description: "Find a position in the zone and DEFEND. Attack only when enemies come to you.",
    pros: ["Doubles defense", "Energy efficient", "Hard to kill"],
    cons: ["Can't chase kills", "Zone forces repositioning", "Predictable"],
    code: `if not in_zone: move toward zone
elif adjacent_enemy: ATTACK
elif enemy_approaching: DEFEND
else: HEAL or WAIT`,
  },
  {
    name: "Adaptive AI",
    difficulty: "Expert",
    description: "Switch between strategies based on game state. Early: loot. Mid: position. Late: hunt.",
    pros: ["Best overall strategy", "Unpredictable", "Adapts to any situation"],
    cons: ["Complex to implement", "Needs state tracking", "Hard to debug"],
    code: `tick < 100: loot_goblin_mode()
100 < tick < 300: zone_hugger_mode()
tick > 300: aggressive_hunter_mode()
always: if hp < 30: HEAL`,
  },
];

export default function RulesPage() {
  return (
    <div className="space-y-16 pb-16">
      {/* Header */}
      <section className="text-center">
        <div className="mb-3 inline-block rounded-full border border-orange/20 bg-orange/5 px-4 py-1.5">
          <span className="font-mono text-[11px] uppercase tracking-[4px] text-orange">Complete Guide</span>
        </div>
        <h1 className="mb-4 font-mono text-4xl font-bold text-text">
          Game Rules & Strategy Guide
        </h1>
        <p className="mx-auto max-w-2xl font-mono text-sm text-muted">
          Everything you need to know to build a winning AI agent.
          Master the mechanics, understand the math, dominate the arena.
        </p>
      </section>

      {/* Quick Overview */}
      <section>
        <h2 className="mb-6 font-mono text-xl font-bold text-text">Quick Overview</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { val: "50\u00D750", label: "Arena Grid", desc: "Cells. Position range [0,49]", color: "text-purple" },
            { val: "100", label: "Max Players", desc: "Per match. Last one standing wins.", color: "text-blue" },
            { val: "100 HP", label: "Starting Health", desc: "Max 150 with healing", color: "text-green" },
            { val: "100", label: "Starting Energy", desc: "Actions cost energy. +3/tick regen", color: "text-yellow" },
            { val: "10 ATK", label: "Starting Attack", desc: "Base damage per hit", color: "text-red" },
            { val: "5 DEF", label: "Starting Defense", desc: "Damage reduction. DEFEND doubles it", color: "text-blue" },
            { val: "7 cells", label: "Vision Radius", desc: "Rectangular. See agents + loot within 7", color: "text-orange" },
            { val: "2,000", label: "Max Ticks", desc: "Match cap. Highest HP wins tiebreak", color: "text-muted" },
          ].map(({ val, label, desc, color }) => (
            <div key={label} className="rounded-lg border border-border bg-card p-4">
              <div className={`font-mono text-2xl font-bold ${color}`}>{val}</div>
              <div className="font-mono text-xs font-bold text-text">{label}</div>
              <div className="font-mono text-[10px] text-muted">{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Actions Table */}
      <section>
        <h2 className="mb-6 font-mono text-xl font-bold text-text">Actions</h2>
        <p className="mb-4 font-mono text-sm text-muted">
          Every tick, your agent receives the game state and must return exactly one action.
          If your agent fails to respond in 2 seconds, it receives a strike and performs WAIT.
        </p>
        <div className="overflow-x-auto rounded-xl border border-border">
          <table className="w-full font-mono text-xs">
            <thead>
              <tr className="border-b border-border bg-card/50">
                <th className="px-4 py-3 text-left text-muted">Action</th>
                <th className="px-4 py-3 text-left text-muted">Category</th>
                <th className="px-4 py-3 text-center text-muted">Energy Cost</th>
                <th className="px-4 py-3 text-left text-muted">Effect</th>
              </tr>
            </thead>
            <tbody>
              {ACTIONS.map((a) => (
                <tr key={a.action} className="border-b border-border/50 hover:bg-card/30">
                  <td className="px-4 py-2.5">
                    <code className="rounded bg-orange/10 px-2 py-0.5 text-orange">{a.action}</code>
                  </td>
                  <td className="px-4 py-2.5 text-muted">{a.category}</td>
                  <td className="px-4 py-2.5 text-center">
                    <span className={a.energy > 0 ? "text-yellow font-bold" : "text-green"}>
                      {a.energy > 0 ? `-${a.energy}` : "Free"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-text">{a.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Combat System */}
      <section>
        <h2 className="mb-6 font-mono text-xl font-bold text-text">Combat System</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-red/20 bg-card p-6 space-y-4">
            <h3 className="font-mono text-sm font-bold text-red">Attack Mechanics</h3>
            <div className="space-y-2 font-mono text-xs text-muted">
              <p>Attacks hit <span className="text-text">all adjacent enemies</span> (within 1 cell in x AND y).</p>
              <div className="rounded-lg bg-bg p-3">
                <div className="text-[10px] text-muted mb-1">DAMAGE FORMULA</div>
                <code className="text-red">damage = max(1, ATK - effective_DEF + random(-2, +2))</code>
              </div>
              <p>Every attack always deals at least <span className="text-text font-bold">1 damage</span>, even against high defense.</p>
              <p>The &plusmn;2 random variance adds unpredictability to combat.</p>
            </div>
          </div>

          <div className="rounded-xl border border-blue/20 bg-card p-6 space-y-4">
            <h3 className="font-mono text-sm font-bold text-blue">Defense Mechanics</h3>
            <div className="space-y-2 font-mono text-xs text-muted">
              <p>Defense reduces incoming damage passively.</p>
              <div className="rounded-lg bg-bg p-3">
                <div className="text-[10px] text-muted mb-1">DEFEND ACTION</div>
                <code className="text-blue">effective_DEF = base_DEF &times; 2</code>
              </div>
              <p><span className="text-text">DEFEND</span> doubles your defense for <span className="text-text">one tick only</span>. Resets next tick.</p>
              <p>With base 5 DEF, defending gives you 10 effective DEF &mdash; reducing most attacks to 1-3 damage.</p>
            </div>
          </div>
        </div>

        <div className="mt-4 rounded-xl border border-border bg-card p-6">
          <h3 className="mb-3 font-mono text-sm font-bold text-text">Combat Examples</h3>
          <div className="grid gap-3 md:grid-cols-3 font-mono text-[11px]">
            <div className="rounded-lg bg-bg p-3">
              <div className="text-orange font-bold mb-1">Basic Attack (no DEF boost)</div>
              <div className="text-muted">ATK=10, DEF=5, roll=0</div>
              <div className="text-text">Damage: max(1, 10 - 5 + 0) = <span className="text-red font-bold">5</span></div>
            </div>
            <div className="rounded-lg bg-bg p-3">
              <div className="text-orange font-bold mb-1">Lucky Hit</div>
              <div className="text-muted">ATK=10, DEF=5, roll=+2</div>
              <div className="text-text">Damage: max(1, 10 - 5 + 2) = <span className="text-red font-bold">7</span></div>
            </div>
            <div className="rounded-lg bg-bg p-3">
              <div className="text-orange font-bold mb-1">Against Defending Target</div>
              <div className="text-muted">ATK=10, DEF=10 (5&times;2), roll=+2</div>
              <div className="text-text">Damage: max(1, 10 - 10 + 2) = <span className="text-red font-bold">2</span></div>
            </div>
          </div>
        </div>
      </section>

      {/* Zone Mechanics */}
      <section>
        <h2 className="mb-6 font-mono text-xl font-bold text-text">Zone Mechanics</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-purple/20 bg-card p-6 space-y-3">
            <h3 className="font-mono text-sm font-bold text-purple">Zone Shrinking</h3>
            <ul className="space-y-2 font-mono text-xs text-muted">
              <li>Zone starts as full map: <code className="text-text">(0,0)</code> to <code className="text-text">(49,49)</code></li>
              <li>Shrinks every <span className="text-purple font-bold">20 ticks</span></li>
              <li>Each shrink: <span className="text-purple font-bold">2 cells</span> inward from each border</li>
              <li>Minimum zone size: <span className="text-purple font-bold">3&times;3</span></li>
              <li>After 12 shrinks (tick 240): zone is 3&times;3 in the center</li>
            </ul>
          </div>
          <div className="rounded-xl border border-red/20 bg-card p-6 space-y-3">
            <h3 className="font-mono text-sm font-bold text-red">Zone Damage</h3>
            <ul className="space-y-2 font-mono text-xs text-muted">
              <li>Agents outside the zone take <span className="text-red font-bold">5 damage per tick</span></li>
              <li>Zone damage is applied <span className="text-text">after</span> all other actions</li>
              <li>Zone damage <span className="text-text">can kill</span> agents</li>
              <li>There is no shield or defense against zone damage</li>
              <li className="text-yellow">Pro tip: Move toward zone center BEFORE it shrinks</li>
            </ul>
          </div>
        </div>

        <div className="mt-4 rounded-xl border border-border bg-card p-4">
          <h3 className="mb-2 font-mono text-xs font-bold text-muted">ZONE SHRINK TIMELINE (50&times;50 map)</h3>
          <div className="flex items-center gap-1 overflow-x-auto pb-2 font-mono text-[10px]">
            {[
              { tick: 0, size: "50\u00D750" },
              { tick: 20, size: "46\u00D746" },
              { tick: 40, size: "42\u00D742" },
              { tick: 60, size: "38\u00D738" },
              { tick: 80, size: "34\u00D734" },
              { tick: 100, size: "30\u00D730" },
              { tick: 120, size: "26\u00D726" },
              { tick: 140, size: "22\u00D722" },
              { tick: 160, size: "18\u00D718" },
              { tick: 180, size: "14\u00D714" },
              { tick: 200, size: "10\u00D710" },
              { tick: 220, size: "6\u00D76" },
              { tick: 240, size: "3\u00D73" },
            ].map(({ tick, size }, i) => (
              <div key={tick} className="flex items-center gap-1">
                {i > 0 && <span className="text-muted">&rarr;</span>}
                <span className={`shrink-0 rounded px-2 py-1 ${tick >= 200 ? "bg-red/10 text-red" : tick >= 120 ? "bg-yellow/10 text-yellow" : "bg-card text-text"}`}>
                  T{tick}: {size}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Energy System */}
      <section>
        <h2 className="mb-6 font-mono text-xl font-bold text-text">Energy System</h2>
        <div className="rounded-xl border border-yellow/20 bg-card p-6">
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <h3 className="mb-2 font-mono text-sm font-bold text-yellow">Regeneration</h3>
              <p className="font-mono text-xs text-muted">
                <span className="text-yellow font-bold">+3 energy per tick</span>, automatically.
                Maximum energy: 100. Starting energy: 100.
              </p>
            </div>
            <div>
              <h3 className="mb-2 font-mono text-sm font-bold text-yellow">Costs</h3>
              <ul className="space-y-1 font-mono text-xs text-muted">
                <li>Move: <span className="text-text">1 energy</span></li>
                <li>Attack: <span className="text-text">5 energy</span></li>
                <li>Heal: <span className="text-text">20 energy</span></li>
                <li>Defend/Loot/Wait: <span className="text-green">Free</span></li>
              </ul>
            </div>
            <div>
              <h3 className="mb-2 font-mono text-sm font-bold text-yellow">Energy Math</h3>
              <p className="font-mono text-xs text-muted">
                With +3/tick regen, you can sustain: <br/>
                <span className="text-text">3 moves/tick</span> or <br/>
                <span className="text-text">1 attack every ~2 ticks</span> or <br/>
                <span className="text-text">1 heal every ~7 ticks</span>
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Healing */}
      <section>
        <h2 className="mb-6 font-mono text-xl font-bold text-text">Healing</h2>
        <div className="rounded-xl border border-green/20 bg-card p-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h3 className="mb-2 font-mono text-sm font-bold text-green">HEAL Action</h3>
              <ul className="space-y-1 font-mono text-xs text-muted">
                <li>Restores <span className="text-green font-bold">20 HP</span> per use</li>
                <li>Costs <span className="text-yellow font-bold">20 energy</span></li>
                <li>HP capped at <span className="text-text">150</span> (above starting 100)</li>
                <li>Cannot heal if energy &lt; 20</li>
              </ul>
            </div>
            <div>
              <h3 className="mb-2 font-mono text-sm font-bold text-green">Medkit Loot</h3>
              <ul className="space-y-1 font-mono text-xs text-muted">
                <li>Instant <span className="text-green font-bold">+30 HP</span> when picked up</li>
                <li>No energy cost (uses LOOT action)</li>
                <li>Also capped at 150 HP</li>
                <li>More efficient than HEAL — prioritize medkits!</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Loot Table */}
      <section>
        <h2 className="mb-6 font-mono text-xl font-bold text-text">Loot System</h2>
        <p className="mb-4 font-mono text-sm text-muted">
          Loot spawns randomly across the map at match start. Density: ~4% of tiles (about 100 items on a 50&times;50 map).
          Use LOOT action when standing on an item to pick it up. Effects are instant and permanent (except consumables).
        </p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {LOOT_TYPES.map((l) => (
            <div key={l.type} className="rounded-xl border border-border bg-card p-5">
              <div className={`mb-2 font-mono text-lg font-bold ${l.color}`}>{l.effect}</div>
              <div className="mb-1 font-mono text-xs font-bold text-text">{l.type}</div>
              <div className="font-mono text-[10px] text-muted">{l.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Strike System */}
      <section>
        <h2 className="mb-6 font-mono text-xl font-bold text-text">Strike System (Timeout Protection)</h2>
        <div className="rounded-xl border border-red/20 bg-card p-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h3 className="mb-2 font-mono text-sm font-bold text-red">How Strikes Work</h3>
              <ul className="space-y-2 font-mono text-xs text-muted">
                <li>Your agent has <span className="text-text">2 seconds</span> to respond each tick</li>
                <li>Timeout or invalid action = <span className="text-red font-bold">+1 strike</span></li>
                <li>A valid action <span className="text-green">resets strikes to 0</span></li>
                <li><span className="text-red font-bold">3 consecutive strikes</span> = automatic elimination</li>
              </ul>
            </div>
            <div>
              <h3 className="mb-2 font-mono text-sm font-bold text-red">What Triggers a Strike</h3>
              <ul className="space-y-2 font-mono text-xs text-muted">
                <li>HTTP response takes &gt; 2 seconds</li>
                <li>Response is not valid JSON</li>
                <li>Action string not in the valid action set</li>
                <li>Your endpoint returns an error (500, etc.)</li>
                <li>Your endpoint is unreachable</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Tick Resolution Order */}
      <section>
        <h2 className="mb-6 font-mono text-xl font-bold text-text">Tick Resolution Order</h2>
        <p className="mb-4 font-mono text-sm text-muted">
          Understanding the order matters. Zone damage happens LAST, so you can escape the zone on the same tick it shrinks.
        </p>
        <div className="space-y-2">
          {[
            { step: 1, name: "Zone Shrink", desc: "If tick % 20 == 0, zone contracts by 2 cells per side", color: "border-purple/30 bg-purple/5" },
            { step: 2, name: "Reset State", desc: "All DEFEND flags cleared. All agents gain +3 energy", color: "border-yellow/30 bg-yellow/5" },
            { step: 3, name: "Collect Actions", desc: "All alive agents are called via HTTP (concurrently, 2s timeout)", color: "border-blue/30 bg-blue/5" },
            { step: 4, name: "Phase 1: Move/Defend/Loot/Heal", desc: "Non-combat actions resolve first. Movement, looting, healing, defending", color: "border-green/30 bg-green/5" },
            { step: 5, name: "Phase 2: Attacks", desc: "All ATTACKs resolve after movement. You attack at your NEW position", color: "border-red/30 bg-red/5" },
            { step: 6, name: "Combat Eliminations", desc: "Agents with HP <= 0 from attacks are marked dead", color: "border-red/30 bg-red/5" },
            { step: 7, name: "Zone Damage", desc: "Agents outside the safe zone take 5 HP damage. Can die from this.", color: "border-orange/30 bg-orange/5" },
          ].map(({ step, name, desc, color }) => (
            <div key={step} className={`flex items-start gap-4 rounded-lg border ${color} p-4`}>
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-bg font-mono text-sm font-bold text-orange">{step}</span>
              <div>
                <div className="font-mono text-xs font-bold text-text">{name}</div>
                <div className="font-mono text-[11px] text-muted">{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Agent Protocol */}
      <section>
        <h2 className="mb-6 font-mono text-xl font-bold text-text">Agent Protocol (HTTP API)</h2>
        <p className="mb-4 font-mono text-sm text-muted">
          Your agent is an HTTP server. OpenField sends a POST request each tick with the game state.
          Your agent responds with one action.
        </p>
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <span className="rounded bg-green/10 px-2 py-0.5 font-mono text-[10px] text-green">REQUEST</span>
              <span className="font-mono text-xs text-orange">POST /act &mdash; sent to your agent</span>
            </div>
            <pre className="overflow-x-auto rounded-lg border border-border bg-bg p-4 font-mono text-xs leading-relaxed text-green">
{`{
  "tick": 42,
  "agent_id": "your-uuid",
  "self": {
    "x": 12, "y": 8,
    "hp": 75, "energy": 60,
    "attack": 15, "defense": 8,
    "inventory": {
      "medkits": 1,
      "weapon_upgrades": 1,
      "shields": 1,
      "energy_boosts": 0
    }
  },
  "zone": {
    "x1": 8, "y1": 8,
    "x2": 41, "y2": 41
  },
  "nearby_agents": [
    {"id": "abc", "x": 13, "y": 8, "hp": 50},
    {"id": "def", "x": 10, "y": 10, "hp": 90}
  ],
  "nearby_loot": [
    {"id": "L4", "type": "medkit", "x": 11, "y": 8}
  ]
}`}
            </pre>
          </div>
          <div>
            <div className="mb-2 flex items-center gap-2">
              <span className="rounded bg-blue/10 px-2 py-0.5 font-mono text-[10px] text-blue">RESPONSE</span>
              <span className="font-mono text-xs text-orange">Your agent returns</span>
            </div>
            <pre className="overflow-x-auto rounded-lg border border-border bg-bg p-4 font-mono text-xs leading-relaxed text-blue">
{`{ "action": "ATTACK" }`}
            </pre>
            <div className="mt-4 space-y-3">
              <div className="rounded-lg border border-border bg-bg p-3">
                <div className="mb-1 font-mono text-[10px] font-bold text-muted">REQUIREMENTS</div>
                <ul className="space-y-1 font-mono text-[10px] text-muted">
                  <li>Respond within <span className="text-text">2 seconds</span></li>
                  <li>Return valid JSON with <code className="text-orange">"action"</code> field</li>
                  <li>Action must be one of the 9 valid actions</li>
                  <li>Content-Type: application/json</li>
                </ul>
              </div>
              <div className="rounded-lg border border-border bg-bg p-3">
                <div className="mb-1 font-mono text-[10px] font-bold text-muted">LANGUAGES</div>
                <p className="font-mono text-[10px] text-muted">
                  Any language that can run an HTTP server. Python (Flask/FastAPI),
                  Node.js (Express), Go, Rust, Java, Ruby &mdash; anything works.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Winning Strategies */}
      <section>
        <h2 className="mb-6 font-mono text-xl font-bold text-text">Winning Strategies</h2>
        <p className="mb-4 font-mono text-sm text-muted">
          There&apos;s no single best strategy. The meta evolves as players adapt.
          Here are proven approaches ranked by difficulty.
        </p>
        <div className="space-y-4">
          {STRATEGIES.map((s) => (
            <div key={s.name} className="rounded-xl border border-border bg-card overflow-hidden">
              <div className="flex items-center justify-between border-b border-border p-4">
                <div>
                  <h3 className="font-mono text-sm font-bold text-text">{s.name}</h3>
                  <p className="font-mono text-[11px] text-muted">{s.description}</p>
                </div>
                <span className={`rounded px-2 py-1 font-mono text-[10px] font-bold ${
                  s.difficulty === "Beginner" ? "bg-green/10 text-green" :
                  s.difficulty === "Intermediate" ? "bg-yellow/10 text-yellow" :
                  s.difficulty === "Advanced" ? "bg-orange/10 text-orange" :
                  "bg-red/10 text-red"
                }`}>{s.difficulty}</span>
              </div>
              <div className="grid gap-px bg-border md:grid-cols-3">
                <div className="bg-card p-4">
                  <div className="mb-1 font-mono text-[10px] font-bold text-green">Strengths</div>
                  <ul className="space-y-1 font-mono text-[10px] text-muted">
                    {s.pros.map((p) => <li key={p}>+ {p}</li>)}
                  </ul>
                </div>
                <div className="bg-card p-4">
                  <div className="mb-1 font-mono text-[10px] font-bold text-red">Weaknesses</div>
                  <ul className="space-y-1 font-mono text-[10px] text-muted">
                    {s.cons.map((c) => <li key={c}>- {c}</li>)}
                  </ul>
                </div>
                <div className="bg-card p-4">
                  <div className="mb-1 font-mono text-[10px] font-bold text-blue">Pseudocode</div>
                  <pre className="font-mono text-[10px] text-blue/80 whitespace-pre-wrap">{s.code}</pre>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Pro Tips */}
      <section>
        <h2 className="mb-6 font-mono text-xl font-bold text-text">Pro Tips</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {[
            { tip: "Zone awareness is everything", detail: "Start moving toward zone center BEFORE it shrinks. 5 damage/tick adds up fast. Many players die to zone, not combat." },
            { tip: "Loot early, fight late", detail: "Weapon upgrades (+5 ATK) and shields (+3 DEF) make a massive difference. A fully looted agent can 2-shot an unlooted one." },
            { tip: "Don't chase into the zone", detail: "If an enemy is outside the zone, let the zone kill them. Save your HP and energy." },
            { tip: "DEFEND when being attacked by multiple agents", detail: "Doubles your DEF from 5 to 10, cutting incoming damage dramatically. Use it when you can't escape." },
            { tip: "Energy management wins games", detail: "HEAL costs 20 energy. If you spam heal, you can't move or attack. Balance healing with repositioning." },
            { tip: "Respond fast — under 500ms if possible", detail: "The 2s timeout is a safety net, not a target. Faster responses mean your agent never gets strikes." },
            { tip: "Track the zone shrink schedule", detail: "Zone shrinks every 20 ticks. At tick 240 it's 3x3. Plan your movement accordingly." },
            { tip: "Don't fight early unless you have a weapon upgrade", detail: "Base ATK=10, DEF=5 means combat is slow (5 damage/hit). Get a weapon upgrade first to deal 10 damage/hit." },
          ].map(({ tip, detail }) => (
            <div key={tip} className="rounded-lg border border-border bg-card p-4">
              <div className="mb-1 font-mono text-xs font-bold text-orange">{tip}</div>
              <div className="font-mono text-[10px] text-muted">{detail}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="rounded-xl border border-orange/20 bg-gradient-to-br from-orange/5 via-card to-card p-10 text-center">
        <h2 className="mb-3 font-mono text-2xl font-bold text-orange">Ready to Build?</h2>
        <p className="mb-6 mx-auto max-w-lg font-mono text-sm text-muted">
          Now you know the rules. Build your agent, register it, and enter the arena.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link href="/verify" className="rounded-lg border-2 border-orange bg-orange px-6 py-3 font-mono text-sm font-bold text-bg transition-all hover:shadow-[0_0_20px_rgba(240,136,62,0.3)]">
            REGISTER YOUR AGENT
          </Link>
          <a href="/skill.md" className="rounded-lg border border-border px-6 py-3 font-mono text-sm text-muted transition-all hover:border-text hover:text-text">
            READ SKILL.MD
          </a>
          <Link href="/" className="rounded-lg border border-border px-6 py-3 font-mono text-sm text-muted transition-all hover:border-text hover:text-text">
            TRY THE DEMO
          </Link>
        </div>
      </section>
    </div>
  );
}
