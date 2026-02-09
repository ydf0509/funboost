
import datetime

def is_time_in_range(run_only_on: str, current_dt: datetime.datetime = None) -> bool:
    """
    Parses strings like:
    - "Mon-Fri 09:00-18:00"
    - "23:00-02:00" (Crosses midnight)
    - "Sat-Sun"
    - "10:00-12:00"
    """
    if not current_dt:
        current_dt = datetime.datetime.now()
    
    parts = run_only_on.strip().split()
    
    time_part = None
    day_part = None
    
    for part in parts:
        if ':' in part:
            time_part = part
        elif '-' in part: # simple heuristic
            day_part = part
            
    # Check Day of Week
    if day_part:
        # Simple parser for Mon-Fri, etc.
        weekdays = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        try:
            start_day_str, end_day_str = day_part.lower().split('-')
            start_idx = -1
            end_idx = -1
            for i, d in enumerate(weekdays):
                if d in start_day_str: start_idx = i
                if d in end_day_str: end_idx = i
            
            current_weekday = current_dt.weekday() # 0=Mon, 6=Sun
            
            if start_idx != -1 and end_idx != -1:
                if start_idx <= end_idx:
                    if not (start_idx <= current_weekday <= end_idx):
                        return False
                else: # Crosses week boundary? e.g. Fri-Mon
                    if not (current_weekday >= start_idx or current_weekday <= end_idx):
                        return False
        except ValueError:
            pass # Parsing failed, maybe strictly ignore or log warning
            
    # Check Time Range
    if time_part:
        try:
            start_str, end_str = time_part.split('-')
            
            # Helper to parse HH:MM
            def parse_tm(s):
                h, m = map(int, s.split(':'))
                return datetime.time(h, m)

            start_time = parse_tm(start_str)
            end_time = parse_tm(end_str)
            now_time = current_dt.time()
            
            if start_time <= end_time:
                # Normal range: 09:00 - 18:00
                if not (start_time <= now_time <= end_time):
                    return False
            else:
                # Crossing midnight: 23:00 - 02:00
                # Run if >= 23:00 OR <= 02:00
                if not (now_time >= start_time or now_time <= end_time):
                    return False
                    
        except ValueError:
            pass
            
    return True

# Test cases
dt_mon_10am = datetime.datetime(2023, 10, 23, 10, 0, 0) # Monday
dt_fri_23pm = datetime.datetime(2023, 10, 27, 23, 30, 0) # Friday
dt_sat_10am = datetime.datetime(2023, 10, 28, 10, 0, 0) # Saturday
dt_sun_01am = datetime.datetime(2023, 10, 29, 1, 0, 0) # Sunday
dt_wed_01am = datetime.datetime(2023, 10, 25, 1, 0, 0) # Wednesday

print(f"Mon 10:00, Range 'Mon-Fri 09:00-18:00': {is_time_in_range('Mon-Fri 09:00-18:00', dt_mon_10am)}")
print(f"Sat 10:00, Range 'Mon-Fri 09:00-18:00': {is_time_in_range('Mon-Fri 09:00-18:00', dt_sat_10am)}")
print(f"Fri 23:30, Range '23:00-02:00': {is_time_in_range('23:00-02:00', dt_fri_23pm)}")
print(f"Wed 01:00, Range '23:00-02:00': {is_time_in_range('23:00-02:00', dt_wed_01am)}")
print(f"Mon 10:00, Range '23:00-02:00': {is_time_in_range('23:00-02:00', dt_mon_10am)}")
