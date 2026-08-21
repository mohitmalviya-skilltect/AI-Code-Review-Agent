def calculate_average(numbers):
    if not numbers:
        return 0
    total = sum(numbers)
    average = total / len(numbers)
    return average