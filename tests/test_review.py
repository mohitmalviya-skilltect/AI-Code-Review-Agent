def calculate_total(price: float, quantity: int) -> float:
    """
    Calculate the total cost based on the price and quantity.
    """
    total = price * quantity
    return total

price = 100
quantity = 5

result = calculate_total(price, quantity)
print("Total:", result)