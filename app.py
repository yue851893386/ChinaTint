# -*- coding: utf-8 -*-
"""
中国地级市可编辑地图 - Demo 后端
功能：注册 / 登录 / 项目管理（保存、加载、删除、覆盖）

运行：
    pip install flask
    python app.py
然后浏览器打开 http://localhost:5000

数据存储：SQLite（mapdata.db，自动生成），无需任何配置。
仅用于本地原型演示，生产环境请更换为正式数据库并启用 HTTPS。
"""
import hashlib
import json
import os
import secrets
import sqlite3
import time
from functools import wraps

from flask import Flask, g, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "mapdata.db")
SESSION_TTL = 7 * 24 * 3600  # 会话有效期 7 天

app = Flask(__name__, static_folder=None)


# ---------------- 数据库 ----------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL,
            pw_hash TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            colors TEXT NOT NULL DEFAULT "{}",
            updated_at REAL NOT NULL,
            UNIQUE(user_id, name)
        );
    """)
    conn.commit()
    conn.close()


# ---------------- 工具 ----------------
def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                               salt.encode("utf-8"), 100000).hex()


def create_session(user_id):
    token = secrets.token_hex(32)
    db = get_db()
    db.execute("INSERT INTO sessions(token, user_id, expires_at) VALUES (?,?,?)",
               (token, user_id, time.time() + SESSION_TTL))
    db.commit()
    return token


def current_user():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    row = get_db().execute(
        "SELECT u.id, u.username FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token = ? AND s.expires_at > ?", (token, time.time())).fetchone()
    return row


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"error": "未登录或会话已过期"}), 401
        g.user = user
        return fn(*args, **kwargs)
    return wrapper


# ---------------- 页面 ----------------
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


# ---------------- 健康检查 ----------------
@app.route("/api/ping")
def ping():
    return jsonify({"ok": True, "time": time.time()})


# ---------------- JSON 错误兜底（前端可读） ----------------
@app.errorhandler(404)
def err_404(e):
    return jsonify({"error": "接口不存在"}), 404


@app.errorhandler(500)
def err_500(e):
    return jsonify({"error": "服务器内部错误: " + str(e)}), 500


# ---------------- 认证 ----------------
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not (3 <= len(username) <= 32) or not (6 <= len(password) <= 64):
        return jsonify({"error": "用户名需 3-32 位，密码需 6-64 位"}), 400
    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        return jsonify({"error": "用户名已存在"}), 409
    salt = secrets.token_hex(16)
    cur = db.execute("INSERT INTO users(username, salt, pw_hash, created_at) VALUES (?,?,?,?)",
                     (username, salt, hash_password(password, salt), time.time()))
    db.commit()
    token = create_session(cur.lastrowid)
    return jsonify({"token": token, "username": username})


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    row = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not row or hash_password(password, row["salt"]) != row["pw_hash"]:
        return jsonify({"error": "用户名或密码错误"}), 401
    token = create_session(row["id"])
    return jsonify({"token": token, "username": username})


@app.route("/api/logout", methods=["POST"])
def logout():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        get_db().execute("DELETE FROM sessions WHERE token = ?", (auth[7:].strip(),))
        get_db().commit()
    return jsonify({"ok": True})


# ---------------- 项目管理 ----------------
@app.route("/api/projects", methods=["GET"])
@login_required
def list_projects():
    rows = get_db().execute(
        "SELECT id, name, updated_at FROM projects WHERE user_id = ? ORDER BY updated_at DESC",
        (g.user["id"],)).fetchall()
    return jsonify([{"id": r["id"], "name": r["name"],
                     "updated_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(r["updated_at"]))}
                    for r in rows])


@app.route("/api/projects", methods=["POST"])
@login_required
def save_project():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()[:64]
    colors = data.get("colors")
    if not name:
        return jsonify({"error": "请填写项目名称"}), 400
    if not isinstance(colors, dict):
        return jsonify({"error": "colors 格式错误"}), 400
    db = get_db()
    # 同名项目覆盖保存 -> 支持"重复编辑"
    db.execute("INSERT INTO projects(user_id, name, colors, updated_at) VALUES (?,?,?,?) "
               "ON CONFLICT(user_id, name) DO UPDATE SET colors = excluded.colors, "
               "updated_at = excluded.updated_at",
               (g.user["id"], name, json.dumps(colors, ensure_ascii=False), time.time()))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/projects/<int:pid>", methods=["GET"])
@login_required
def get_project(pid):
    row = get_db().execute("SELECT name, colors FROM projects WHERE id = ? AND user_id = ?",
                           (pid, g.user["id"])).fetchone()
    if not row:
        return jsonify({"error": "项目不存在"}), 404
    return jsonify({"name": row["name"], "colors": json.loads(row["colors"])})


@app.route("/api/projects/<int:pid>", methods=["DELETE"])
@login_required
def delete_project(pid):
    cur = get_db().execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (pid, g.user["id"]))
    get_db().commit()
    if cur.rowcount == 0:
        return jsonify({"error": "项目不存在"}), 404
    return jsonify({"ok": True})


def ensure_db():
    """部署平台（如 gunicorn）导入时也需要建表"""
    init_db()


ensure_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))   # HF Spaces=7860, Render=10000, 本地=5000
    try:
        from waitress import serve
        print(f"Starting with waitress on http://0.0.0.0:{port}")
        serve(app, host="0.0.0.0", port=port, threads=8)
    except ImportError:
        app.run(host="0.0.0.0", port=port, debug=False)
