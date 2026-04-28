from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "bug_bounty.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-change-me"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_: Optional[BaseException]) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS targets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      scope TEXT NOT NULL,
      reward_min INTEGER NOT NULL,
      reward_max INTEGER NOT NULL,
      created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS findings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      target_id INTEGER NOT NULL,
      title TEXT NOT NULL,
      severity TEXT NOT NULL,
      status TEXT NOT NULL,
      submitted_at TEXT NOT NULL,
      notes TEXT,
      FOREIGN KEY (target_id) REFERENCES targets(id)
    );
    """
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.executescript(schema)
        conn.commit()


@app.route("/")
def dashboard():
    db = get_db()
    targets = db.execute("SELECT * FROM targets ORDER BY id DESC").fetchall()
    findings = db.execute(
        """
        SELECT findings.*, targets.name AS target_name
        FROM findings
        JOIN targets ON findings.target_id = targets.id
        ORDER BY findings.id DESC
        """
    ).fetchall()

    stats = {
        "total_targets": len(targets),
        "total_findings": len(findings),
        "critical_findings": sum(1 for f in findings if f["severity"] == "Critical"),
        "resolved_findings": sum(1 for f in findings if f["status"] == "Resolved"),
    }
    return render_template("dashboard.html", targets=targets, findings=findings, stats=stats)


@app.route("/targets/new", methods=["GET", "POST"])
def create_target():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        scope = request.form.get("scope", "").strip()
        reward_min = request.form.get("reward_min", "0").strip()
        reward_max = request.form.get("reward_max", "0").strip()

        if not name or not scope:
            flash("Name and scope are required.", "error")
            return redirect(url_for("create_target"))

        db = get_db()
        db.execute(
            """
            INSERT INTO targets (name, scope, reward_min, reward_max, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, scope, int(reward_min), int(reward_max), datetime.utcnow().isoformat()),
        )
        db.commit()
        flash("Target created.", "success")
        return redirect(url_for("dashboard"))

    return render_template("target_form.html")


@app.route("/findings/new", methods=["GET", "POST"])
def create_finding():
    db = get_db()
    targets = db.execute("SELECT id, name FROM targets ORDER BY name ASC").fetchall()

    if request.method == "POST":
        target_id = request.form.get("target_id", "").strip()
        title = request.form.get("title", "").strip()
        severity = request.form.get("severity", "Low")
        status = request.form.get("status", "Submitted")
        notes = request.form.get("notes", "").strip()

        if not target_id or not title:
            flash("Target and finding title are required.", "error")
            return redirect(url_for("create_finding"))

        db.execute(
            """
            INSERT INTO findings (target_id, title, severity, status, submitted_at, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (int(target_id), title, severity, status, datetime.utcnow().isoformat(), notes),
        )
        db.commit()
        flash("Finding submitted.", "success")
        return redirect(url_for("dashboard"))

    return render_template("finding_form.html", targets=targets)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
