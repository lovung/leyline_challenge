// pages/index.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import useWebSocket from 'react-use-websocket';

const HomePage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  const { sendMessage, lastMessage } = useWebSocket(
    taskId ? `ws://localhost:8000/ws/task_status/${taskId}` : null,
    {
      onOpen: () => console.log('WebSocket connection established'),
      onClose: () => console.log('WebSocket connection closed'),
      onError: (event) => console.error('WebSocket error', event),
      shouldReconnect: () => true,
    }
  );

  useEffect(() => {
    if (lastMessage !== null) {
      const data = JSON.parse(lastMessage.data);
      setProgress(data.progress);
      setVideoUrl(data.videoUrl);
    }
  }, [lastMessage]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append('file', selectedFile);

    const response = await axios.post('http://localhost:8000/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    setTaskId(response.data.taskId);
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      {progress > 0 && <p>Progress: {progress}%</p>}
      {videoUrl && (
        <video controls>
          <source src={videoUrl} type="video/mp4" />
        </video>
      )}
    </div>
  );
};

export default HomePage;
