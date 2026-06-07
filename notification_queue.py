_pending_notifications = []

def add_pending(title, text, ntype="achievement"):
    _pending_notifications.append({
        'title': title,
        'text': text,
        'type': ntype
    })

def get_pending():
    global _pending_notifications
    result = _pending_notifications.copy()
    _pending_notifications.clear()
    return result