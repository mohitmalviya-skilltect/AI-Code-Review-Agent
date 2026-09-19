user_name = "Alex"
user_age = "25"  # Bug 1: Age is stored as a string, not an integer.

def calculate_months(age)
    # Bug 2: Missing colon at the end of the function definition.
    return age * 12

if user_name == "John":
print("Hello, John!") 
# Bug 3: This print statement is missing indentation.

# Bug 4: The operator is wrong below. It divides instead of multiplying, causing an incorrect output.
total_months = calculate_months(user_age) / 1 

print("You are " + total_months + " months old.")