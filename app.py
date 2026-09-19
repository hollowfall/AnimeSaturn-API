import os
import sys
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.app import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting AnimeSaturn Machine API on http://{host}:{port}")
    uvicorn.run("server.app:app", host=host, port=port, reload=True)
