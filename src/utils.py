def isnumber(n: str) -> bool:
    """Detect if n is a number"""
    n_less = 0
    for c in n:
        if not (c.isdigit() or (c == "-" and n_less < 1)):
            return False
        if c == "-":
            n_less += 1
    return True
