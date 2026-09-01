def process_user_data(data):
    result = []

    for item in data:
        if item.get("active") == True:
            if item.get("age") >= 18:
                if item.get("email") is not None:
                    result.append({
                        "Name": item.get("name"),
                        "Email": item.get("email"),
                        "Status": "eligible"
                    })

    return result