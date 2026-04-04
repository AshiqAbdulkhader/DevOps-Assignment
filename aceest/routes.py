from flask import Blueprint, redirect, render_template, request, session, url_for

from aceest.auth import login_required, safe_next_url
from aceest.db import get_db

bp = Blueprint("main", __name__)

_DASHBOARD = "main.dashboard"


@bp.get("/")
def index():
    if session.get("user"):
        return redirect(url_for(_DASHBOARD))
    return redirect(url_for("main.login"))


@bp.get("/health")
def health():
    return {"status": "healthy"}


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for(_DASHBOARD))

    error = None
    next_param = request.args.get("next") or ""

    if request.method == "POST":
        next_param = request.form.get("next") or next_param
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        db = get_db()
        row = db.execute(
            "SELECT role FROM users WHERE username=? AND password=?",
            (username, password),
        ).fetchone()
        if row:
            session["user"] = username
            session["role"] = row["role"]
            dest = safe_next_url(next_param) or url_for(_DASHBOARD)
            return redirect(dest)
        error = "Invalid credentials"

    return render_template("login.html", error=error, next=next_param or None)


@bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


@bp.get("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        user=session["user"],
        role=session.get("role", ""),
    )
