# LeyLine Take-home Challenge

## How to run
- Init services with docker:
```sh
docker compose up --build
```
- Open frontend at: http://localhost:3000
- Choose a file to upload.
- Enjoy :).

## High-level Design
### APIs
- **POST /api/upload**: Uploads an image as a file.
    - Creates a new task and saves it into SQLite.
    - Adds a background task to simulate long processing (AI model simulation).
- **WebSocket /ws/{task_id}**: Establishes a real-time connection with the frontend to communicate the processing status.
    - Handles new WebSocket connection requests.
    - Saves the connection in a map with `task_id` as the key.
### Tasks
- **Background Task**:
    - Loads the task using `task_id` from the database.
    - Checks if the status is `pending`.
    - Updates the status to `processing`.
    - Simulates data processing (AI model work), continuously notifying the frontend of the progress.
    - Updates the status to `completed` once processing is done.

## Considerations for Large Systems

- **Why SQLite?**
    - SQLite is simple and sufficient for the current requirements.
    - For larger projects, a more reliable database such as PostgreSQL, MySQL (RDBMS), or NoSQL databases (DynamoDB, MongoDB) would be preferable.

- **Production Design for Background Tasks**:
    - In a production setting, using Kafka to handle events would be ideal.
        - The API service handles image upload events.
        - The AI service consumes new upload events and starts processing.
        - The AI service continuously sends `in_process` and `completed` events to a Kafka topic.
        - The AI service saves the output video in S3.
        - An authentication service checks the user's subscription to provide access to downloadable videos.
        - A CDN serves the output video.
        - A WebSocket service consumes the process Kafka topic to send percentage and completion information to the frontend.
    - This approach allows for easier horizontal scaling by:
        - Partitioning the database.
        - Scaling out the API service.
        - Using a WebSocket proxy to manage WebSocket connections.
        - Employing Zookeeper to monitor service health.
