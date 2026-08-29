def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate the price after applying a percentage discount.

    Args:
        price: The original price of the item.
        discount_percent: The percentage discount to apply.

    Returns:
        The discounted price as a float.
    """
    discount = price * discount_percent / 100
    return price - discount


def generate_bill(items: list[dict]) -> float:
    """Generate the total bill for a list of items, applying discounts where applicable.

    Args:
        items: A list of dictionaries, where each dictionary contains item details
               including 'price', 'quantity', and 'discount'.

    Returns:
        The calculated total bill amount.
    """
    total = 0

    for item in items:
        item_total = item["price"] * item["quantity"]

        if item["discount"] > 0:
            item_total = calculate_discount(
                item_total,
                item["discount"]
            )

        total += item_total

    return total


items = [
    {
        "name": "Laptop",
        "price": 60000,
        "quantity": 1,
        "discount": 10
    },
    {
        "name": "Mouse",
        "price": 1000,
        "quantity": 2,
        "discount": 5
    }
]

total_bill = generate_bill(items)

print("Total Bill:", total_bill)
