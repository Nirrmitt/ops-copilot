"""Render API startup: seed the ephemeral demo database and bind to Render's port."""
import os

import uvicorn

from app.seed import seed


def main() -> None:
    seed()
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "10000")),
    )


if __name__ == "__main__":
    main()
