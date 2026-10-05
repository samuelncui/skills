"""Original teaching examples. Refactor for clarity, not branch-count targets."""


def deliver_nested(open_channel, ready, send):
    with open_channel() as channel:
        if ready():
            send(channel)
            return "sent"
        else:
            return "idle"


def deliver_guarded(open_channel, ready, send):
    with open_channel() as channel:
        if not ready():
            return "idle"
        send(channel)
        return "sent"


def classify_branch(value, at_least):
    if at_least(value, 10):
        return "high"
    elif at_least(value, 0):
        return "ordinary"
    return "negative"


def classify_rules(value, at_least):
    # Only useful when an extensible rule list is actually needed.
    rules = (
        (lambda: at_least(value, 10), lambda: "high"),
        (lambda: at_least(value, 0), lambda: "ordinary"),
    )
    for matches, handle in rules:
        if matches():
            return handle()
    return "negative"


def route_branch(kind, text_handler, binary_handler, fallback):
    # Contract: kind is a string; handlers take no arguments.
    if kind == "text":
        return text_handler()
    elif kind == "binary":
        return binary_handler()
    return fallback()


def route_map(kind, text_handler, binary_handler, fallback):
    handlers = {"text": text_handler, "binary": binary_handler}
    return handlers.get(kind, fallback)()


def should_retry(transient, attempts_left):
    # A readable local conjunction is worth keeping.
    if transient and attempts_left > 0:
        return True
    return False
