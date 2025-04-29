# main.py

import logging
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the master router from router.py
from router.router import api_router

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(
    title='EurekAnno',
    description="API for EurekAnno",
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)
app.include_router(api_router, prefix='/api/v1')

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return "FASTAPI TEMPLATE FOR EUREKAI LAB"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
