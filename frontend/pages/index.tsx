import React, { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import useWebSocket, { ReadyState, useEventSource } from 'react-use-websocket';
import { WebSocketMessage } from '../types/WebSocketMessage';



const HomePage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [messageHistory, setMessageHistory] = useState<MessageEvent<any>[]>([]);

  // WebSocket URL should match your backend WebSocket endpoint
  const socketUrl = 'ws://localhost:8000/ws/';

  // Connect to WebSocket based on taskId
  const { sendMessage, lastMessage, lastJsonMessage, readyState } = useWebSocket<WebSocketMessage>(
    taskId ? `${socketUrl}${taskId}` : null,
  );

  useEffect(() => {
    // Handle incoming WebSocket messages
    console.log("receive websocket json message", lastJsonMessage)
    if (lastJsonMessage) {
      const { progress: newProgress, videoUrl: newVideoUrl } = lastJsonMessage;
      setProgress(newProgress);
      setVideoUrl(newVideoUrl);
    }
  }, [lastJsonMessage]);

  useEffect(() => {
    // Handle incoming WebSocket messages
    console.log("receive websocket message", lastMessage)
    if (lastMessage) {
      setMessageHistory((prev) => prev.concat(lastMessage));
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

    try {
      const response = await axios.post('http://localhost:8000/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setProgress(0);
      console.log("set taskId", response.data.taskId);
      setTaskId(response.data.taskId);
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const handleClickSendMessage = useCallback(() => sendMessage('Hello'), []);

  const connectionStatus = {
    [ReadyState.CONNECTING]: 'Connecting',
    [ReadyState.OPEN]: 'Open',
    [ReadyState.CLOSING]: 'Closing',
    [ReadyState.CLOSED]: 'Closed',
    [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
  }[readyState];

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}
        disabled={progress !== null && progress !== 100}
      >
        Upload
      </button>
      <br></br>
      <button
        onClick={handleClickSendMessage}
        disabled={readyState !== ReadyState.OPEN}
      >
        Click Me to send 'Hello'
      </button>
      <span>The WebSocket is currently {connectionStatus}</span>
      {progress !== null && <p>Progress: {progress}%</p>}
      {videoUrl && (
        <video controls>
          <source src={videoUrl} type="video/mp4" />
        </video>
      )}
      {/* {lastMessage ? <span>Last message: {lastMessage}</span> : null} */}
      <ul>
        {messageHistory.map((message, idx) => (
          <ul key={idx}>{message ? message.data : null}</ul>
        ))}
      </ul>
      <br></br>

    </div>
  );
};

export default HomePage;
