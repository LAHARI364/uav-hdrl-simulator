import os
from datetime import datetime
import pandas as pd
from meteostat import Hourly, Point

print("Fetching historical weather data...")

# 1. Define the geographic center of your simulation grid
# Let's anchor it to Miami, Florida (famous for severe tropical storms)
miami_coords = Point(25.7617, -80.1918)

# 2. Pick a historical time window where a major storm occurred
# Hurricane Idalia impacted Florida late August 2023
start_date = datetime(2023, 8, 28)
end_date = datetime(2023, 8, 31, 23, 59)

# 3. Request the hourly data series from Meteostat
data = Hourly(miami_coords, start_date, end_date)
df = data.fetch().reset_index()

# 4. Format the data to match your simulation needs
# Calculate a relative timestamp in seconds from the start of the data
df['timestamp'] = (df['time'] - df['time'].min()).dt.total_seconds()

# Select, rename, and clean up variables to map your weather engine requirements
# 'prcp' is precipitation in mm, 'wspd' is wind speed in km/h
df = df[['timestamp', 'prcp', 'wspd']]
df.columns = ['timestamp', 'precipitation', 'wind_speed']

# Safely swap any missing data gaps (NaNs) to 0.0
df = df.fillna(0.0)

# 5. Create the data directory and save it
os.makedirs('data', exist_ok=True)
df.to_csv('data/historical_storm.csv', index=False)

print(f"Success! Saved {len(df)} hourly storm intervals to data/historical_storm.csv")