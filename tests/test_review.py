def process_user_data(data):
    """
    Processes a collection of user data dictionaries and filters for eligible users.

    An eligible user is defined as one who:
    - Has an active status ('active' == True)
    - Is 18 years of age or older ('age' >= 18)
    - Has a non-null email address

    Args:
        data (iterable): An iterable containing dictionaries with user details.
                         If data is None or not iterable, an empty list is returned.

    Returns:
        list: A list of formatted dictionaries for each eligible user,
              containing 'Name', 'Email', and 'Status'.
    """
    # Validate that 'data' is a valid iterable and not a string/bytes object
    if data is None or not hasattr(data, '__iter__') or isinstance(data, (str, bytes)):
        return []

    result = []

    for item in data:
        # Ensure that the item is a dictionary before using the .get() method
        # to prevent AttributeError for non-dict items.
        if not isinstance(item, dict):
            continue

        # Extract fields safely using .get()
        is_active = item.get("active")
        age = item.get("age")
        email = item.get("email")

        # Check eligibility criteria:
        # - Status must be active (active == True)
        # - Age must be a number and >= 18 (safeguards against TypeError)
        # - Email must not be None
        if (
            is_active == True
            and isinstance(age, (int, float))
            and age >= 18
            and email is not None
        ):
            result.append({
                "Name": item.get("name"),
                "Email": email,
                "Status": "eligible"
            })

    return result