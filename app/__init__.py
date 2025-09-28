from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging, os

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.debug = True

# --- Startup diagnostics: confirm CLAUDE_API_KEY is present (masked) ---
logging.getLogger().setLevel(logging.INFO)
try:
    k = os.environ.get("CLAUDE_API_KEY") or getattr(Config, "CLAUDE_API_KEY", "")
    masked = (k[:6] + "..." + k[-4:]) if k and len(k) > 12 else ("<missing>" if not k else "<short>")
    print(f"[Startup] CLAUDE_API_KEY: {masked}")
except Exception:
    print("[Startup] CLAUDE_API_KEY: <error masking key>")

from app import routes, models, controller
