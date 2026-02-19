def map_login_response(response: dict):
    live_own, demo_own = [], []
    live_shared, demo_shared = [], []

    # Own accounts
    for acc in response.get("accounts", []):
        target = demo_own if acc.get("isDemo", False) else live_own
        target.append({
            "id": acc["accountId"],
            "number": acc["accountNumber"],
            "type": acc["accountTypeName"],
            "balance": acc["balance"]
        })

    # Shared accounts - group by owner
    for shared in response.get("sharedAccounts", []):
        owner = shared["accountOwner"]
        
        # Separate accounts by demo/live
        live_accounts = []
        demo_accounts = []
        
        for acc in shared["accounts"]:
            acc_data = {
                "id": acc["accountId"],
                "number": acc["accountNumber"],
                "type": acc["accountTypeName"],
                "balance": acc["balance"]
            }
            
            if acc.get("isDemo", False):
                demo_accounts.append(acc_data)
            else:
                live_accounts.append(acc_data)
        
        # Add owner block for live accounts if any
        if live_accounts:
            live_shared.append({
                "owner": owner["fullName"],
                "username": owner["username"],
                "email": owner.get("email", ""),  # Include email
                "userId": owner.get("userId"),
                "accounts": live_accounts
            })
        
        # Add owner block for demo accounts if any
        if demo_accounts:
            demo_shared.append({
                "owner": owner["fullName"],
                "username": owner["username"],
                "email": owner.get("email", ""),  # Include email
                "userId": owner.get("userId"),
                "accounts": demo_accounts
            })

    return live_own, demo_own, live_shared, demo_shared
