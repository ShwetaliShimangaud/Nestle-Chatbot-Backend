from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as chat_router


# from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()
# app.add_middleware(HTTPSRedirectMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=["https://react-frontend-821842650532.northamerica-northeast1.run.app","http://localhost:5173", "http://localhost:8080"],  # Restrict to your frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
