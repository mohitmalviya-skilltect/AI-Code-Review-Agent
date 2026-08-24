def calculate_total(price, quantity):
    total = price * quantity
    return total

price = 100
quantity = "5"

result = calculate_total(price, quantity)
print("Total:", result)