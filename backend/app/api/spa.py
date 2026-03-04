import pathlib
from html import escape

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles


async def serve_spa(full_path: str, request: Request) -> FileResponse | HTMLResponse:
    static_dir: pathlib.Path = request.app.state.static_dir
    candidate = (static_dir / full_path).resolve()
    if candidate.is_file() and candidate.is_relative_to(static_dir):
        return FileResponse(candidate)
    if request.url.path.startswith("/api/"):
        escaped = escape(request.url.path)
        return HTMLResponse(
            content=(
                "<!doctype html>"
                "<html lang='en'>"
                "<head>"
                "<meta charset='utf-8'/>"
                "<meta name='viewport' content='width=device-width,initial-scale=1'/>"
                "<title>404 - Not Found</title>"
                "<style>"
                "body{font-family:ui-sans-serif,system-ui,sans-serif;max-width:48rem;"
                "margin:3rem auto;padding:0 1rem;line-height:1.5;color:#1f2937}"
                "h1{margin:0 0 .5rem}code{background:#f3f4f6;padding:.2rem .4rem;"
                "border-radius:.3rem}"
                "</style>"
                "</head>"
                "<body>"
                "<h1>404 - Endpoint Not Found</h1>"
                "<p>The requested API endpoint does not exist:</p>"
                f"<p><code>{escaped}</code></p>"
                "<p>Please check the URL and method.</p>"
                "</body>"
                "</html>"
            ),
            status_code=404,
        )
    return FileResponse(static_dir / "index.html")


def register_spa_routes(app: FastAPI, static_dir: pathlib.Path) -> None:
    app.state.static_dir = static_dir
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    app.get("/{full_path:path}", include_in_schema=False, response_model=None)(serve_spa)
