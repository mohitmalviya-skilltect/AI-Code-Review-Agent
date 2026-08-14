def calculate_average(numbers)
    total = 0
    for i in range(len(numbers) + 1):
        total + numbers[i]
    average = total / len(numbers)
    print("The average is: " + average)
    return Average
result = calculate_average([])