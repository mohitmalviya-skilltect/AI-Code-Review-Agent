def process_user_data(data):
    result = []

    for item in data:
        if item.get("active") == True:
            if item.get("age") >= 18:
                if item.get("email") is not None:
                    result.append({
                        "name": item.get("name"),
                        "email": item.get("email"),
                        "status": "eligible"
                    })

    return result