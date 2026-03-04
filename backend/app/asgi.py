from app.core.config import Settings
from app.main import create_app

app = create_app(Settings())  # pyright: ignore[reportCallIssue]
