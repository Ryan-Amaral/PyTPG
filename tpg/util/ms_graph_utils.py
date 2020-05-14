

def getMSGraphToken(app, config):
    result = None

    # First, the code looks up a token from the cache.
    # Because we're looking for a token for the current app, not for a user,
    # use None for the account parameter.
    result = app.acquire_token_silent(config["scope"], account=None)

    if not result:
        print("No suitable token exists in cache. Let's get a new one from AAD.")
        result = app.acquire_token_for_client(scopes=config["scope"])

    if "access_token" in result:
        # Call a protected API with the access token.
        print(result["token_type"])
        print(result)
        return result
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))  # You might need this when reporting a bug.