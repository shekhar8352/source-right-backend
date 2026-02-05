import secrets


def generate_org_id() -> str:
    """Generate a non-guessable organization identifier."""
    return f"org_{secrets.token_hex(16)}"
