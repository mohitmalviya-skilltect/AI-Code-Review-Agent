from datetime import datetime, timedelta


def calculate_weekdays(start_date, end_date):
    current_date = start_date
    weekdays = 0

    while current_date <= end_date:
        if current_date.weekday() < 5:
            weekdays += 1

        current_date += timedelta(days=1)

    return weekdays


start = datetime(2026, 5, 8)
end = datetime(2026, 8, 31)

result = calculate_weekdays(start, end)
print(f"Working days: {result}")