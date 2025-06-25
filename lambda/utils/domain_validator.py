import re

def is_valid_domain(domain):
    pattern = r"^(?!\-)(?:[a-zA-Z0-9\-]{1,63}\.)+[a-zA-Z]{2,}$"
    return re.match(pattern, domain) is not None
