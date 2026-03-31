from backend.main import app  # type: ignore # pyright: ignore
import uvicorn  # type: ignore # pyright: ignore
from backend.config import HOST, PORT  # type: ignore # pyright: ignore

# The most compatible name for the FastAPI object
app = app 

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
