
MAP_WIDTH = 4000          # meters (4km) -- scaled down from 10000 (10km)
MAP_HEIGHT = 4000         # meters (4km)
GRID_DIVISIONS = 2        # creates 2x2 = 4 subregions (scaled down from 4x4=16)
MAX_TASKS_PER_REGION = 6 


NUM_UAVS = 1               # scaled down from 20 -- this is the single-UAV demo
MAX_BATTERY = 100.0        # SOC starts at 100%
MAX_SPEED = 100.0          # m/s, maximum UAV speed
UAV_CPU_GHZ = 0.5          # UAV onboard CPU (500 MHz, small drone)

BATTERY_FULL = 95.0        # freshly charged
BATTERY_NORMAL = 50.0      # operating normally
BATTERY_WARNING = 20.0     # start going to charge
BATTERY_CRITICAL = 10.0    # drop task, rush to station
BATTERY_EMERGENCY = 5.0    # emergency descent


BATTERY_CAPACITY_WH = 60.0        # total energy in Watt-hours
HOVER_BASE_POWER_W = 30.0         # power just to stay airborne
DRAG_LINEAR_COEFF = 0.3           # linear drag with speed
DRAG_CUBIC_COEFF = 0.0002         # non-linear drag (faster = much more drain)
CPU_POWER_PER_GHZ_W = 5.0         # power per GHz of CPU used
COMM_BASE_POWER_W = 8.0           # power when transmitting
VOLTAGE_SAG_COEFF = 0.25          # discharge efficiency sag as SOC drops

# Flight-mode power/speed coefficients
FLIGHT_MODE_PROFILE = {
    "CRUISE":            {"speed": 100.0, "hover_coeff": 1.0, "cpu_coeff": 1.0, "comm_coeff": 1.0},
    "ECO":               {"speed": 50.0,  "hover_coeff": 0.7, "cpu_coeff": 0.8, "comm_coeff": 1.0},
    "HOVER":             {"speed": 0.0,   "hover_coeff": 1.2, "cpu_coeff": 1.0, "comm_coeff": 1.0},
    "HIGH_SPEED":        {"speed": 100.0, "hover_coeff": 1.3, "cpu_coeff": 1.0, "comm_coeff": 1.0},
    "EMERGENCY_DESCENT": {"speed": 30.0,  "hover_coeff": 0.5, "cpu_coeff": 0.5, "comm_coeff": 0.5},
}


# Scaled down to ~1/5 of the full-sim lambdas (see module docstring).
WORKLOAD_TO_LAMBDA = {
    "LOW": 0.01,
    "MEDIUM": 0.02,
    "HIGH": 0.04,
    "CRITICAL": 0.06,
}

WORKLOAD_WEIGHTS = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 4,
    "CRITICAL": 6,
}

PRIORITY_DISTRIBUTION = {
    "low": 0.5,
    "medium": 0.3,
    "high": 0.2,
}

NUM_EMERGENCY_EVENTS = 1   # scaled down from 3

# Priority engine weights (unchanged -- these describe scoring logic, not scale)
PRIORITY_WEIGHTS = {
    "deadline": 0.35,
    "battery": 0.20,
    "weather": 0.15,
    "queue": 0.15,
    "importance": 0.15,
}
IMPORTANCE_BASE = {
    "low": 0.2,
    "medium": 0.5,
    "high": 0.8,
    "emergency": 1.0,
}

# Task cpu_cycles / deadline / data_size ranges
NORMAL_CPU_CYCLES_RANGE = (1e7, 1e8)
EMERGENCY_CPU_CYCLES_RANGE = (1e8, 5e8)
NORMAL_DEADLINE_RANGE = (20.0, 60.0)     # seconds
EMERGENCY_DEADLINE_RANGE = (8.0, 20.0)   # seconds, shorter for emergencies
NORMAL_DATA_SIZE_RANGE = (0.5, 5.0)      # MB
EMERGENCY_DATA_SIZE_RANGE = (2.0, 10.0)  # MB

# Scaled down from 4 stations at [0, 6, 10, 15] (corners of a 4x4 grid)
# to 1 station at region 0 (a single corner of the 2x2 grid).
NUM_CHARGING_STATIONS = 1
CHARGING_STATION_REGIONS = [0]
CHARGING_RATE = 10.0        # % per second, unchanged (per-station hardware)
COMM_RANGE = 2500.0         # meters, trimmed from 5000m (see module docstring)
MEC_CPU_FREQUENCY = 10.0    # GHz, unchanged (server hardware doesn't scale down)
MEC_QUEUE_DELAY = 0.05      # seconds, base queueing delay at MEC server
DOWNLOAD_RATE_MBPS = 20.0   # MB/s, result download rate from MEC
BANDWIDTH_HZ = 10e6         # 10 MHz channel bandwidth
TX_POWER_W = 0.5            # UAV transmit power for SNR calc
NOISE_POWER_W = 1e-9        # channel noise floor for SNR calc


TOTAL_SIM_TIME = 200.0      # seconds -- slightly shorter demo run
TIMESTEP = 0.1              # seconds per tick
VIZ_SPEED = 1.0              # 1.0 = realtime, 2.0 = 2x faster

# Derived: auto-generate TASK_ARRIVAL_RATE per region_id from workload.
# Filled in by environment/map.py once regions are created (region_id -> lambda),
# but we pre-seed a flat mapping here keyed by workload label for convenience.
TASK_ARRIVAL_RATE = {}  # populated at runtime: {region_id: lambda_value}
