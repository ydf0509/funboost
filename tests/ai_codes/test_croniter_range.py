
try:
    from croniter import croniter, CroniterBadCronError
except ImportError:
    print("Please install croniter using: pip install croniter")
    exit(1)

import datetime

def is_time_allowed_by_cron(cron_expression: str, current_dt: datetime.datetime = None) -> bool:
    """
    Checks if the current time (minute precision) matches the cron expression.
    This effectively uses Cron as a "Time Window" definition.
    If the cron expression allows execution at this minute, return True.
    """
    if not current_dt:
        current_dt = datetime.datetime.now()
        
    try:
        # croniter.match(cron_expr, dt) checks if the DT matches the cron schedule
        # It handles complex things like "1st of month", "Mon-Fri", "9-17"
        return croniter.match(cron_expression, current_dt)
    except CroniterBadCronError:
        print(f"Invalid cron expression: {cron_expression}")
        return False
    except Exception as e:
        print(f"Error checking cron: {e}")
        return False

# Test Cases
print("--- TEST RESULTS ---")

# 1. "Only run on the 1st of every month"
cron_1st_of_month = "* * 1 * *" 
dt_1st = datetime.datetime(2023, 11, 1, 10, 30, 0) # Nov 1st -> Should be True
dt_2nd = datetime.datetime(2023, 11, 2, 10, 30, 0) # Nov 2nd -> Should be False

print(f"Cron '{cron_1st_of_month}' (1st of Month):")
print(f"  {dt_1st}: {is_time_allowed_by_cron(cron_1st_of_month, dt_1st)} (Expected: True)")
print(f"  {dt_2nd}: {is_time_allowed_by_cron(cron_1st_of_month, dt_2nd)} (Expected: False)")

# 2. "Mon-Fri 09:00-18:00"
# Cron: * 9-17 * * 1-5 
# Note: 9-17 means hours 9,10...17. So 09:00:00 to 17:59:59.
cron_business_hours = "* 9-17 * * 1-5"

dt_mon_10am = datetime.datetime(2023, 10, 23, 10, 0, 0) # Mon 10:00 -> True
dt_sat_10am = datetime.datetime(2023, 10, 28, 10, 0, 0) # Sat 10:00 -> False
dt_mon_19pm = datetime.datetime(2023, 10, 23, 19, 0, 0) # Mon 19:00 -> False

print(f"\nCron '{cron_business_hours}' (Mon-Fri 09:00-17:59):")
print(f"  {dt_mon_10am}: {is_time_allowed_by_cron(cron_business_hours, dt_mon_10am)} (Expected: True)")
print(f"  {dt_sat_10am}: {is_time_allowed_by_cron(cron_business_hours, dt_sat_10am)} (Expected: False)")
print(f"  {dt_mon_19pm}: {is_time_allowed_by_cron(cron_business_hours, dt_mon_19pm)} (Expected: False)")

# 3. "Cross Midnight 23:00 - 03:00"
# Use comma for hours: 23,0,1,2 (23,0-2)
cron_night_shift = "* 23,0-2 * * *"

dt_night_2330 = datetime.datetime(2023, 10, 23, 23, 30) # 23:30 -> True
dt_night_0130 = datetime.datetime(2023, 10, 24, 1, 30)  # 01:30 -> True
dt_day_1200 = datetime.datetime(2023, 10, 24, 12, 00)   # 12:00 -> False

print(f"\nCron '{cron_night_shift}' (23:00-02:59):")
print(f"  {dt_night_2330}: {is_time_allowed_by_cron(cron_night_shift, dt_night_2330)} (Expected: True)")
print(f"  {dt_night_0130}: {is_time_allowed_by_cron(cron_night_shift, dt_night_0130)} (Expected: True)")
print(f"  {dt_day_1200}: {is_time_allowed_by_cron(cron_night_shift, dt_day_1200)} (Expected: False)")
