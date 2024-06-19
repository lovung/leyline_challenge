from fastapi import (
    FastAPI,
    UploadFile,
    File,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks,
)
# from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles;
from sqlalchemy import create_engine, Column, String, Integer, Enum as SQLAEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from enum import Enum as PyEnum
from typing import Dict, List

import time
import os
import uuid
import asyncio
import logging

app = FastAPI()

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./data/task.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TaskStatus(PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"


class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, index=True)
    status = Column(SQLAEnum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)
    image_path = Column(String, nullable=True)
    video_path = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)

connected_clients: Dict[str, List[WebSocket]] = {}

# CORS (Cross-Origin Resource Sharing) configuration
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.mount("/videos", StaticFiles(directory="./videos"), name="videos")

@app.post("/api/upload")
async def upload_image(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())
    image_path = f"images/{task_id}.jpg"
    os.makedirs("images", exist_ok=True)
    with open(image_path, "wb") as buffer:
        buffer.write(await file.read())

    db = SessionLocal()
    task = Task(id=task_id, image_path=image_path, status=TaskStatus.PENDING)
    db.add(task)
    db.commit()
    db.refresh(task)
    db.close()

    logger.info(f"Add to background tasks. Task ID: {task_id}")
    background_tasks.add_task(process_image, task_id)
    return {"taskId": task_id}


@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    logger.info(f"Client connected to WebSocket. Task ID: {task_id}")
    if task_id not in connected_clients:
        connected_clients[task_id] = []
    connected_clients[task_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo message was: {data}")
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from WebSocket. Task ID: {task_id}")
        connected_clients[task_id].remove(websocket)

async def process_image(task_id: str):
    logger.info(f"Start {task_id}...")
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    if task.status is not TaskStatus.PENDING:
        db.close()
        return
    
    task.status = TaskStatus.PROCESSING
    db.commit()
    logger.info(f"Query in DB. Task ID: {task.id}...")

    try:
        for progress in range(0, 101, 5):
            await asyncio.sleep(0.1) # set as 1.5 to simulate 30s of process
            logger.info(f"Processing {task.id}... {progress}%")
            task.progress = progress
            db.commit()
            # Await notify_clients here
            await notify_clients(task_id, progress, None)

        # Output of AI model return here
        video_path = f"http://localhost:8000/videos/template.mp4"
        # os.makedirs("videos", exist_ok=True)
        # Simulate video generation
        # with open(video_path, "wb") as f:
            # f.write(os.urandom(1024))

        task.status = TaskStatus.COMPLETED
        task.video_path = video_path
        db.commit()
        await notify_clients(task_id, 100, video_path)  
    finally:
        db.close()


async def notify_clients(task_id: str, progress: int, video_path: str):
    if task_id in connected_clients:
        message = {"progress": progress, "videoUrl": video_path}
        for websocket in connected_clients[task_id]:
            try:
                await websocket.send_json(message)
                logger.info(f"Notifying client {websocket} - Data: {message}")
            except Exception as e:
                logger.error(f"Error notifying client {websocket}: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
