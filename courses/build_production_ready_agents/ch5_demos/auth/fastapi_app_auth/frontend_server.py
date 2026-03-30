import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

load_dotenv()

app = FastAPI(title="Echo Service Frontend")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
API_URL = os.environ.get("API_URL", "http://localhost:8000")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "client_id": CLIENT_ID, "api_url": API_URL},
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="localhost", port=port)
