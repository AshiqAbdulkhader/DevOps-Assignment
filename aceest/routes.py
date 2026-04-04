from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from aceest.auth import client_required, login_required, safe_next_url
from aceest.db import get_db

bp = Blueprint("main", __name__)

_DASHBOARD = "main.dashboard"
_CLIENTS = "main.clients"


def _clients_post_clear():
    session.pop("current_client", None)
    flash("Cleared current client.", "success")
    return redirect(url_for(_CLIENTS))


def _clients_post_select(db):
    name = request.form.get("name", "").strip()
    if not name:
        flash("Client name is required.", "error")
        return redirect(url_for(_CLIENTS))
    exists = db.execute(
        "SELECT 1 FROM clients WHERE name = ?",
        (name,),
    ).fetchone()
    if not exists:
        flash("Unknown client.", "error")
    else:
        session["current_client"] = name
        flash(f"Current client: {name}", "success")
    return redirect(url_for(_CLIENTS))


def _clients_post_add(db):
    name = request.form.get("name", "").strip()
    if not name:
        flash("Client name is required.", "error")
        return redirect(url_for(_CLIENTS))
    cur = db.execute(
        "INSERT OR IGNORE INTO clients (name, membership_status) VALUES (?, ?)",
        (name, "Active"),
    )
    db.commit()
    if cur.rowcount:
        flash(f"Client {name} saved.", "success")
    else:
        flash(f'A client named "{name}" already exists.', "error")
    return redirect(url_for(_CLIENTS))


def _handle_clients_post(db):
    action = request.form.get("_action", "add")
    if action == "clear":
        return _clients_post_clear()
    if action == "select":
        return _clients_post_select(db)
    return _clients_post_add(db)


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


@bp.route("/clients", methods=["GET", "POST"])
@login_required
def clients():
    db = get_db()
    if request.method == "POST":
        return _handle_clients_post(db)

    rows = db.execute(
        "SELECT name, membership_status FROM clients ORDER BY name"
    ).fetchall()
    return render_template(
        "clients.html",
        clients=rows,
        current_client=session.get("current_client"),
    )


@bp.get("/client/summary")
@login_required
@client_required
def client_summary():
    db = get_db()
    name = session["current_client"]
    row = db.execute("SELECT * FROM clients WHERE name = ?", (name,)).fetchone()
    if row is None:
        session.pop("current_client", None)
        flash("That client no longer exists.", "error")
        return redirect(url_for(_CLIENTS))

    return render_template(
        "client_summary.html",
        name=row["name"],
        program=row["program"],
        calories=row["calories"],
        membership=row["membership_status"],
        membership_end=row["membership_end"],
    )
