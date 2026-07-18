# UAV-HDRL Simulator — Single UAV Demo

This is a scaled-down, single-drone version of the `uav-hdrl-simulator` project
(https://github.com/LAHARI364/uav-hdrl-simulator), meant as a standalone
demonstration of the rule-based simulator's core mechanics before the HDRL
stage is layered on top.

It reuses the exact same module layout, class names, and physics formulas as
the full project (`configs`, `environment`, `uavs`, `power`, `tasks`,
`communication`, `offloading`, `weatherr`, `visualization`, `main.py`) so you
can drop these files straight into your existing repo — either alongside the
full-scale files (rename `main_single_uav.py` → `main.py` if you want it to
be the default entry point, or keep both and run whichever you need) or as a
`demo/` subfolder that imports from the shared `configs`, `power`, etc.
packages once you merge the two configs.

## What's scaled down, and why

| Setting | Full sim (20 UAVs) | This demo (1 UAV) | Why |
|---|---|---|---|
| `NUM_UAVS` | 20 | 1 | The whole point of the demo |
| `MAP_WIDTH` / `MAP_HEIGHT` | 10,000 m | 4,000 m | A single drone can't meaningfully patrol 100 km² in a short demo run; 16 km² keeps travel times watchable |
| `GRID_DIVISIONS` | 4 (→16 regions) | 2 (→4 regions) | Fewer regions for a single drone to plausibly cover |
| `WORKLOAD_TO_LAMBDA` | 0.05 / 0.1 / 0.2 / 0.3 | 0.01 / 0.02 / 0.04 / 0.06 | Cut to ~1/5 so task arrivals don't outpace one drone's throughput. 20 UAVs across 16 regions ≈ 1.25 UAVs/region of service capacity; 1 UAV across 4 regions ≈ 0.25 UAVs/region — roughly a 5x drop, so arrival rate is cut by the same factor |
| `NUM_CHARGING_STATIONS` | 4 (corners) | 1 | One drone only needs one charging point to demonstrate the FSM (FULL→NORMAL→WARNING→CRITICAL→EMERGENCY) and the return-to-charge behavior |
| `NUM_EMERGENCY_EVENTS` | 3 | 1 | Enough to show the emergency-task path without swamping a single drone |
| `COMM_RANGE` | 5,000 m | 2,500 m | On a 4 km map, a 5,000 m range would always be in range (diagonal ≈ 5,657 m), making the LOCAL-vs-MEC offloading trade-off trivial. 2,500 m keeps genuine in-range/out-of-range moments |

Everything else — battery physics (`HOVER_BASE_POWER_W`, drag coefficients,
CPU/comm power draw, voltage sag), the FSM thresholds, the priority-scoring
weights, the SNR/Shannon-capacity comms model, and the MEC offload decision
logic — is untouched. Those describe *one drone's* hardware and *one
scheduling decision's* logic, not fleet scale, so scaling them down would
have made the physics unrealistic rather than just smaller.

## Running it

```bash
pip install -r requirements.txt
python main_single_uav.py
```

A Pygame window opens showing the 4-region map, the single UAV, its target
task, the one charging station (cyan square, "C"), and the one MEC server
(purple circle, "M"). The side panel shows sim time, the UAV's battery %,
FSM state, flight mode, and running task counts (pending/assigned/done/
emergency).

If `data/historical_storm.csv` isn't present, `weatherr/weather_engine.py`
automatically falls back to a synthetic bell-curve storm profile (same shape
as the real one), so the demo runs standalone without needing the original
Hurricane Idalia dataset.

## Folding this back into the full project

Since `configs/config.py` here only differs from the full-sim config in the
values listed in the table above (no new fields), the cleanest way to merge
this back in is:

1. Add a `SINGLE_UAV_DEMO = True/False` flag (or a second config file,
   `config_demo.py`) to your existing `configs/config.py`.
2. Have `main.py` pick `NUM_UAVS`, `GRID_DIVISIONS`, `MAP_WIDTH/HEIGHT`,
   `WORKLOAD_TO_LAMBDA`, `NUM_CHARGING_STATIONS`, `CHARGING_STATION_REGIONS`,
   `NUM_EMERGENCY_EVENTS`, and `COMM_RANGE` from whichever config is active.
3. Everything in `environment/`, `uavs/`, `power/`, `tasks/`,
   `communication/`, `offloading/`, `weatherr/`, and `visualization/` here is
   compatible with both scales as-is — none of it hardcodes "20" or "16"
   anywhere; it all reads from `config`.

## Notes on behavior you'll see

- **Offloading tends toward LOCAL** for most normal tasks: with only one MEC
  server (co-located with the one charging station), the UAV is often far
  enough from it that upload latency outweighs the 10 GHz server's faster
  compute — the same "MEC always LOCAL" dynamic your project notes list as a
  known tuning issue for the full sim. Emergency tasks (larger `cpu_cycles`)
  are more likely to tip the decision toward MEC when the UAV happens to be
  near the station.
- **Charging cycles are infrequent** in a short 200s run at light task load,
  since `HOVER_BASE_POWER_W=30W` against a 60 Wh battery gives roughly two
  hours of pure hover endurance — battery pressure comes mainly from
  sustained high-speed cruising, not idle time. Lower `TOTAL_SIM_TIME` or
  raise `WORKLOAD_TO_LAMBDA` if you want to force more charging trips into a
  short demo.
