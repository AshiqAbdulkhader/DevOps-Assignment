from functools import wraps
from typing import Optional

from flask import redirect, request, session, url_for


def safe_next_url(target: Optional[str]) -> Optional[str]:
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("main.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped
