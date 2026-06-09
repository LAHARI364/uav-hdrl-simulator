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

# configs/config.py



# Workload per region 
REGION_WORKLOAD = {
    0:  "LOW",
    1:  "HIGH",
    2:  "MEDIUM",
    3:  "CRITICAL",
    4:  "LOW",
    5:  "MEDIUM",
    6:  "HIGH",
    7:  "LOW",
    8:  "CRITICAL",
    9:  "MEDIUM",
    10: "HIGH",
    11: "LOW",
    12: "MEDIUM",
    13: "HIGH",
    14: "CRITICAL",
    15: "LOW"
}



MAX_SPEED = 20.0            # m/s
UAV_COST = 1.0              # cost factor

#Task Settings
TASK_ARRIVAL_RATE = 5       # lambda for Poisson (tasks per second)
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

