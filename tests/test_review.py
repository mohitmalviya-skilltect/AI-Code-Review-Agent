<<<<<<< HEAD
def calculate_average(numbers):
    total = 0

    for i in range(len(numbers)):
        total += numbers[i]

    average = total / len(numbers)

    print("Average:", average)

    return average
=======
# 1. This script manages a simple user profile setup
def greet_user(username):
print("Welcome to the platform, " + username)

# 2. Ask user for age and convert to number
age_input = input("Enter your age: ")
user_age = int(age_input)

# 3. Check if user is old enough
if user_age >= 18:
    is_adult = True
else
    is_adult = False

# 4. Try to print status using un-matching quotes
if is_adult:
    print('Access granted")
else:
    print("Access denied')

# 5. Loop through a list of starting items
items = ["badge", "coins", "map"]
for item in items:
    print("Added item: " + items)

# 6. Try to add a bonus item to the list
items.add("sword")
>>>>>>> main
