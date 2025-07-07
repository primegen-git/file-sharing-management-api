# File Backend Service

A robust, scalable backend service for secure file management, built with **FastAPI**, **PostgreSQL**, **Amazon S3**, **Redis**, and **Docker**. This project enables user authentication, file upload/download, metadata management, and efficient caching, making it suitable for modern cloud-native applications.

---

## Features

- **User Authentication:**
  Secure registration and login using JWT tokens stored in HTTP-only cookies.

- **File Upload & Storage:**
  Users can upload multiple files, which are stored in Amazon S3. Metadata is managed in a PostgreSQL database.

- **File Retrieval & Search:**
  Retrieve and search files by filename, extension, or content type. Generates presigned S3 URLs for secure file access.

- **File Deletion:**
  Users can delete individual files or all their files. Deletion is handled both in the database and in S3.

- **Caching with Redis:**
  File listing and search results are cached in Redis for fast repeated access and reduced database load.

- **Scalable Microservices:**
  All services are containerized with Docker for independent deployment and scalability.

---

## Tech Stack

- **Backend:** FastAPI
- **Database:** PostgreSQL (SQLAlchemy ORM)
- **Cloud Storage:** Amazon S3 (boto3)
- **Authentication:** JWT (PyJWT, passlib)
- **Caching:** Redis
- **Containerization:** Docker
- **Environment Management:** python-dotenv

---

## Project Structure

```
file_backend/
├── database.py         # Database connection and session management
├── dependecies.py      # Shared dependencies (auth, S3, etc.)
├── main.py             # FastAPI app entry point and router inclusion
├── models.py           # SQLAlchemy models for User and File
├── signals.py          # (Reserved for future signals/events)
└── routers/
    ├── auth.py         # User registration, login, logout endpoints
    └── user.py         # File upload, retrieval, search, and deletion endpoints
```

---

## How It Works

### Authentication

- Users register and log in via `/auth/register` and `/auth/login`.
- Passwords are securely hashed.
- JWT tokens are issued and stored in cookies for session management.

### File Operations

- **Upload:**
  Users upload files via `/user/upload`. Files are streamed to S3, and metadata is saved in PostgreSQL.
- **List/Search:**
  `/user/files` returns all files or filtered results. Results are cached in Redis for performance.
- **Delete:**
  `/user/files` deletes all user files (from both S3 and the database). Individual file deletion can be easily extended.
- **Presigned URLs:**
  Secure, time-limited S3 URLs are generated for file access.

### Caching

- Redis is used to cache file listings and search results, reducing database and S3 calls.

### Dockerization

- Each microservice (API, database, etc.) can be containerized and deployed independently for scalability and maintainability.

---

## Getting Started

1. **Clone the repository:**
    ```bash
    git clone https://github.com/primegen-git/file-sharing-management-api
    cd file-sharing-management-api
    ```

2. **Set up environment variables:**
   Create a `.env` file with your AWS, database, and Redis credentials.

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Run the application (example with uvicorn):**
    ```bash
    uvicorn main:app --reload
    ```

5. **(Optional) Run with Docker:**
   Create a `Dockerfile` and `docker-compose.yml` for full containerized deployment.

---

## API Endpoints Overview

- `POST /auth/register` — Register a new user
- `POST /auth/login` — Login and receive JWT token in cookie
- `POST /auth/logout` — Logout and clear session
- `POST /user/upload` — Upload one or more files
- `GET /user/files` — List/search user files (with Redis caching)
- `DELETE /user/files` — Delete all user files
- `DELETE /user/` — Delete user account and all associated files

