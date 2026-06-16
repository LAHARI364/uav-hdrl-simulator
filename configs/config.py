# ─── Temporal Weather Evolution (Phase 6) ─────────────────────────────────────
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
NUM_UAVS = 10 #CAN CHANGE THI
MAX_BATTERY = 100.0 #100% FLOAT SO WE CAN GET IN POINTS


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



MAX_SPEED = 20.0            # m/s
UAV_COST = 1.0              # cost factor

#Task Settings
WORKLOAD_TO_LAMBDA = {
    "LOW": 2,
    "MEDIUM": 5,
    "HIGH": 10
}

TASK_ARRIVAL_RATE = {
    region: WORKLOAD_TO_LAMBDA[state]
    for region, state in REGION_WORKLOAD.items()
}    
PRIORITY_DISTRIBUTION = {"low": 0.5, "medium": 0.3, "high": 0.2}
NUM_EMERGENCY_EVENTS = 3    

#Charging Stations
NUM_CHARGING_STATIONS = 4
CHARGING_STATION_REGIONS = [0, 1, 2, 3]  
CHARGING_RATE = 10.0        # % per second

#Simulation Settings
TOTAL_SIM_TIME = 300        # seconds
TIMESTEP = 0.1 #TIME STEP IN SECONDS

VIZ_SPEED = 1.0             # 1.0 = realtime, 2.0 = 2x faster

# ─── Communication Engine (Phase 7) ───────────────────────────────────────────
BANDWIDTH_HZ       = 10e6      # 10 MHz channel bandwidth
TRANSMIT_POWER_W   = 0.1       # UAV transmit power in Watts
NOISE_POWER_W      = 1e-10     # Thermal noise power
PATH_LOSS_EXPONENT = 2.5       # Free-space path loss exponent
COMM_RANGE         = 2000.0    # Max communication range in meters

# ─── MEC Offloading (Phase 10) ────────────────────────────────────────────────
MEC_CPU_FREQUENCY  = 10e9      # MEC server CPU: 10 GHz
MEC_QUEUE_DELAY    = 0.05      # Fixed queue delay in seconds
DOWNLOAD_RATE_MBPS = 50.0      # Download rate from MEC to UAV in MB/s

# ─── Dynamic Priority Weights (Phase 9) ───────────────────────────────────────
W1_DEADLINE    = 0.35
W2_BATTERY     = 0.20
W3_WEATHER     = 0.15
W4_QUEUE       = 0.15
W5_IMPORTANCE  = 0.15

# ─── Congestion & Region Tracking (Stage 3) ───────────────────────────────────
CONGESTION_DECAY   = 0.99      # Congestion decays per timestep (exponential)
MAX_TASKS_PER_REGION = 20      # For normalisation
# ─── Non-Linear Battery Engine (Phase 5) ──────────────────────────────────────
BATTERY_CAPACITY_WH   = 60.0    # total battery energy capacity, Watt-hours
HOVER_BASE_POWER_W    = 150.0   # power just to stay airborne, no horizontal motion
DRAG_LINEAR_COEFF     = 1.5     # linear drag term coefficient
DRAG_CUBIC_COEFF      = 0.002   # cubic drag term coefficient (non-linear w.r.t. speed)
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