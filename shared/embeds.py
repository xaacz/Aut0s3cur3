from config import get_bot_config

def get_config():
    return get_bot_config()["embeds"]

def auth_embed(auth_type: str, **kwargs) -> dict:
    embeds = get_config()["auth"]
    config = embeds[auth_type]
    title = config["title"]
    description = config["description"]

    for key, value in kwargs.items():
        title = title.replace("{" + key + "}", str(value))
        description = description.replace("{" + key + "}", str(value))

    return {
        "title": title,
        "description": description,
        "color": config["color"],
    }

def bauth_embed() -> dict | None:
    embeds = get_config()["before_auth"]
    config = embeds["default"]
    if not config["title"]:
        return None
    return {
        "title": config["title"],
        "description": config["description"],
        "color": config["color"]
    }

def verify_embed() -> dict:
    embeds = get_config()
    config = embeds["after_verify"]["default"]
    return {
        "title": config["title"],
        "description": config["description"],
        "color": config["color"]
    }
