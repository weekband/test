from logging_manager import logger
from fastapi import FastAPI



# 로깅 설정 초기화


app = FastAPI()



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    logger.debug("who name is %s", name)
    return {"message": f"Hello {name}"}
