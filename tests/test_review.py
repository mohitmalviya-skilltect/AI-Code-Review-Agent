def calculate_discount(price, discount):
    total = price - discount
    tax = total * 0.18

    print("Price:", price)
    print("Discount:", discount)

    final_price = total + tax

    if final_price < 0:
        return 0

    return final_price


def get_user_name(user):
    return user["name"].upper()