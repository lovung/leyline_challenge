from fastapi import (
    FastAPI,
    UploadFile,
    File,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks,
)
from sqlalchemy import create_engine, Column, String, Integer, Enum as SQLAEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from enum import Enum as PyEnum
import time
import os
import uuid

app = FastAPI()

DATABASE_URL = "sqlite:///./test.db"
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

connected_clients = {}


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())
    image_path = f"images/{task_id}.jpg"
    os.makedirs("images", exist_ok=True)
    with open(image_path, "wb") as buffer:
        buffer.write(await file.read())

    db = SessionLocal()
    task = Task(id=task_id, image_path=image_path)
    db.add(task)
    db.commit()
    db.refresh(task)
    db.close()

    BackgroundTasks().add_task(process_image, task_id)
    return {"taskId": task_id}


@app.websocket("/ws/task_status/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    if task_id not in connected_clients:
        connected_clients[task_id] = []
    connected_clients[task_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        connected_clients[task_id].remove(websocket)


def process_image(task_id: str):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    task.status = TaskStatus.PROCESSING
    db.commit()

    for progress in range(0, 101, 10):
        time.sleep(3)
        task.progress = progress
        db.commit()
        notify_clients(task_id, task.progress, None)

    video_path = f"videos/{task_id}.mp4"
    os.makedirs("videos", exist_ok=True)
    with open(video_path, "wb") as f:
        f.write(os.urandom(1024))  # Simulate video generation

    task.status = TaskStatus.COMPLETED
    task.video_path = video_path
    db.commit()
    notify_clients(task_id, 100, video_path)
    db.close()


def notify_clients(task_id: str, progress: int, video_path: str):
    if task_id in connected_clients:
        for websocket in connected_clients[task_id]:
            data = {"progress": progress, "videoUrl": video_path}
            try:
                websocket.send_json(data)
            except:
                connected_clients[task_id].remove(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
