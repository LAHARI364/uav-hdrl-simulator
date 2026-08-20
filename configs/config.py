#Temporal Weather Evolution 
WEATHER_DECAY_FACTOR    = 0.95    # per-second intensity decay for storm cells
WEATHER_SIGMA           = 3000.0  # spatial decay constant, meters (radial gradient)
WEATHER_MAX_INTENSITY   = 1.0
WEATHER_NOISE_SCALE     = 0.0008  # spatial frequency of ambient Perlin noise
WEATHER_TIME_SCALE      = 0.05    # how fast ambient noise drifts over time
STORM_SPAWN_PROBABILITY = 0.02    # chance per tick that a new storm forms
MAX_STORM_CELLS         = 5
MAP_WIDTH = 10000       # meters
MAP_HEIGHT = 10000      # meters
GRID_DIVISIONS = 4 #16 SUBREGIONS
NUM_UAVS = 20 #CAN CHANGE THIS
MAX_BATTERY = 100.0 #100% FLOAT SO WE CAN GET IN POINTS
UAV_CPU_GHZ = 0.5  # 500 MHz — realistic for a small drone

#BATTER THRESHOLD
BATTERY_FULL = 95
BATTERY_NORMAL = 50
BATTERY_WARNING = 20
BATTERY_CRITICAL = 10
BATTERY_EMERGENCY = 5


# Workload per region 
REGION_WORKLOAD = {
    0:  "LOW",
    1:  "HIGH",
    2:  "MEDIUM",
    3:  "HIGH",
    4:  "LOW",
    5:  "MEDIUM",
    6:  "HIGH",
    7:  "LOW",
    8:  "HIGH",
    9:  "MEDIUM",
    10: "HIGH",
    11: "LOW",
    12: "MEDIUM",
    13: "HIGH",
    14: "HIGH",
    15: "LOW"
}



MAX_SPEED = 100.0            # m/s
UAV_COST = 1.0              # cost factor

#Task Settings
WORKLOAD_TO_LAMBDA = {
    "LOW": 0.05,
    "MEDIUM": 0.1,
    "HIGH": 0.2,
    "CRITICAL": 0.3
}

TASK_ARRIVAL_RATE = {
    region: WORKLOAD_TO_LAMBDA[state]
    for region, state in REGION_WORKLOAD.items()
}    
PRIORITY_DISTRIBUTION = {"low": 0.5, "medium": 0.3, "high": 0.2}
NUM_EMERGENCY_EVENTS = 3    

#Charging Stations
NUM_CHARGING_STATIONS = 4
CHARGING_STATION_REGIONS = [0, 6, 10, 15]  
CHARGING_RATE = 4.0        # % per second
# Charging load-balancing — max UAVs allowed en-route/charging at one
# station before others get redirected to the next-closest free station
CHARGING_STATION_CAPACITY = 4

#Simulation Settings
TOTAL_SIM_TIME = 500        # seconds
# Weather playback speed — compress the full historical storm timeline
# (95 hrs / 342000s in historical_storm.csv) into the simulation window
STORM_DURATION_S = 342000.0        # last timestamp in historical_storm.csv
WEATHER_SPEEDUP = STORM_DURATION_S / TOTAL_SIM_TIME   # ≈ 1140×
TIMESTEP = 0.1 #TIME STEP IN SECONDS

VIZ_SPEED = 1.0             # 1.0 = realtime, 2.0 = 2x faster

# Communication Engine 
BANDWIDTH_HZ       = 10e6      # 10 MHz channel bandwidth
TRANSMIT_POWER_W   = 0.1       # UAV transmit power in Watts
NOISE_POWER_W      = 1e-10     # Thermal noise power
PATH_LOSS_EXPONENT = 2.5       # Free-space path loss exponent
COMM_RANGE         = 5000.0    # Max communication range in meters

# MEC Offloading 
MEC_CPU_FREQUENCY  = 10e9      # MEC server CPU: 10 GHz
MEC_QUEUE_DELAY    = 0.05      # Fixed queue delay in seconds
DOWNLOAD_RATE_MBPS = 50.0      # Download rate from MEC to UAV in MB/s

#Dynamic Priority Weights 
W1_DEADLINE    = 0.35
W2_BATTERY     = 0.20
W3_WEATHER     = 0.15
W4_QUEUE       = 0.15
W5_IMPORTANCE  = 0.15

#Congestion & Region Tracking 
CONGESTION_DECAY   = 0.99      # Congestion decays per timestep (exponential)
MAX_TASKS_PER_REGION = 20      # For normalisation
# Non-Linear Battery Engine 
BATTERY_CAPACITY_WH   = 60.0    # total battery energy capacity, Watt-hours
HOVER_BASE_POWER_W    = 50.0   # power just to stay airborne, no horizontal motion
DRAG_LINEAR_COEFF     = 0.5     # linear drag term coefficient
DRAG_CUBIC_COEFF      = 0.0005   # cubic drag term coefficient (non-linear w.r.t. speed)
CPU_POWER_PER_GHZ_W   = 5.0     # watts consumed per GHz of CPU utilised
COMM_BASE_POWER_W     = 8.0     # watts consumed while actively transmitting
VOLTAGE_SAG_COEFF     = 0.25    # how much efficiency drops as SOC nears 0

# Power level profile per flight mode — multiplies each power component
FLIGHT_MODE_POWER_PROFILE = {
    "CRUISE":            {"power_level": "MEDIUM",   "hover_coeff": 1.0, "movement_coeff": 1.0, "cpu_coeff": 1.0, "comm_coeff": 1.0},
    "HOVER":             {"power_level": "LOW",      "hover_coeff": 1.0, "movement_coeff": 0.0, "cpu_coeff": 0.8, "comm_coeff": 1.0},
    "HIGH_SPEED":        {"power_level": "HIGH",     "hover_coeff": 1.1, "movement_coeff": 2.0, "cpu_coeff": 1.2, "comm_coeff": 1.0},
    "ECO":               {"power_level": "VERY_LOW", "hover_coeff": 0.6, "movement_coeff": 0.6, "cpu_coeff": 0.5, "comm_coeff": 0.7},
    "EMERGENCY_DESCENT": {"power_level": "HIGH",     "hover_coeff": 1.2, "movement_coeff": 1.5, "cpu_coeff": 1.0, "comm_coeff": 1.0},
}
# =============================================================================
# APPEND THIS BLOCK to the END of configs/config.py (single-uav-simulator
# branch). Same fixes as main — collision/load-balancer constants are
# omitted since those two systems aren't ported here (see uav_EDITS.py /
# guide for why).
# =============================================================================

# --- Priority scoring (Phase 9, revised) — identical rationale to main branch
PRIORITY_WEIGHTS = {
    "deadline":   0.4375,
    "weather":    0.1875,
    "queue":      0.1875,
    "importance": 0.1875,
}

# --- Assignment cost function (Phase 8, Slide 8) — battery lives here now
ASSIGNMENT_WEIGHTS = {
    "distance":   0.25,
    "delay":      0.15,
    "energy":     0.25,
    "weather":    0.15,
    "congestion": 0.10,
    "priority":   0.30,
}
MAX_ASSIGN_DISTANCE = 1.4142 * MAP_WIDTH

# --- Battery FSM: DEAD state -------------------------------------------------
BATTERY_DEAD = 0.0

# --- Charging release threshold fix (80%, matches spec) ---------------------
CHARGING_RELEASE_SOC = 80.0

# --- Collision avoidance (Stage 7 / Phase 11) --------------------------------
COLLISION_SAFE_DISTANCE = 150.0
COLLISION_REPULSION_GAIN = 40.0

# --- Swarm load balancing (Stage 7 / Phase 12) -------------------------------
CONGESTION_HOTSPOT_THRESHOLD = 0.6
LOAD_BALANCE_PATROL_MODE = "ECO"

# --- Failure management (Stage 7 / Phase 13) --------------------------------
SAFE_ZONE_MIN_UAV_SEPARATION = 100.0
# --- Static obstacles (Stage 7 / Phase 14) -----------------------------------
# Circular keep-out zones for physical obstacles (towers, buildings, terrain).
# UAVs are softly repelled, same style as UAV-UAV collision avoidance.
STATIC_OBSTACLES = [
    {"id": "OBS-1", "center": (3000.0, 8000.0), "radius": 400.0},
    {"id": "OBS-2", "center": (7500.0, 1500.0), "radius": 500.0},
    {"id": "OBS-3", "center": (4000.0, 4000.0), "radius": 350.0},
]
OBSTACLE_SAFE_DISTANCE  = 250.0    # extra clearance beyond the obstacle's own radius
OBSTACLE_REPULSION_GAIN = 60.0     # stronger than UAV-UAV gain, since obstacles never move

# --- No-fly zones (Stage 7 / Phase 14) ---------------------------------------
# Regulatory/hard-exclusion airspace — UAVs must never remain inside, unlike
# obstacles which only need soft avoidance.
NO_FLY_ZONES = [
    {"id": "NFZ-1", "center": (2000.0, 5500.0), "radius": 700.0},
    {"id": "NFZ-2", "center": (8000.0, 5000.0), "radius": 600.0},
]
NO_FLY_ZONE_MARGIN = 50.0          # extra buffer added on top of the stated radius