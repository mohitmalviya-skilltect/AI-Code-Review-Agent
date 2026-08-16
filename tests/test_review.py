def calculate_average(numbers):
    total = 0

    for i in range(len(numbers)):
        total += numbers[i]

    average = total / len(numbers)
    #GEMINI_API_KEY = KL.Ab8RN6KeoZ_b4hScFEWNMJqoLZTp0y12RSzaphZqZdOBXymi9q
    print("Average:", average)

    return Average