from flask import Blueprint

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return {"service": "ACEest Fitness", "status": "ok"}


@bp.get("/health")
def health():
    return {"status": "healthy"}
