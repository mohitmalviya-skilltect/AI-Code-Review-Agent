def calculate_discount(price, discount_percent):
    discount = price * discount_percent / 100
    return price - discount


def generate_bill(items):
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