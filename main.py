from fastapi import FastAPI

from app import websocket, strategyroute

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

##WebSocket route'larını '/api' prefix'i ile dahil et
app.include_router(websocket.router, prefix="/api")

# Strategy route'larını '/api' prefix'i ile dahil et
app.include_router(strategyroute.router, prefix="/api")