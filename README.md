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

---

> **IMPORTANT: Follow these setup steps carefully!**
> If you are unsure about any step, follow the detailed instructions below. If you already know what you are doing, you may proceed quickly.

1. **Clone the repository:**
    ```bash
    git clone https://github.com/primegen-git/file-sharing-management-api
    cd file-sharing-management-api
    ```

2. **Install and Configure PostgreSQL:**
   - Install PostgreSQL on your system or use Docker.
   - Log in as the root user and create a database named `file-share` (or use your own name but match in .env).
   - **Default connection info:**
     - User: `postgres`
     - Password: `your_password_here`
     - Port: `5432`
     - Host: `localhost` (or service name if using Docker)
     - Database: `file-share`
   - Use these same values in your `.env` file as shown in `.env.example`.

3. **Install and Run Redis:**
   - Install Redis on your system or run with Docker.
   - Start Redis with a password (recommended):
     ```bash
     redis-server --requirepass your_redis_password
     ```
   - Make sure the same `REDIS_PASSWORD` is set in your `.env` file (see `.env.example`).

4. **Set up AWS S3 Bucket & Credentials:**
   - Create an S3 bucket on AWS.
   - Create an IAM user with programmatic access and attach a policy allowing access to your bucket.
   - Note the following details and add them to your `.env` file:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - `AWS_DEFAULT_REGION`
     - `S3_BUCKET_NAME`
   - See `.env.example` for all needed variables.

5. **Set up environment variables:**
   - Copy the example env file:
     ```bash
     cp .env.example .env
     ```
   - **Edit `.env` and fill in all required secrets and settings.**

6. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

7. **Run the application (example with uvicorn):**
    ```bash
    uvicorn main:app --reload
    ```

8. **Run with Docker Compose (Recommended for Ease & Consistency):**

   The project comes with a pre-configured `docker-compose.yml` that sets up three essential services:

   - **file-fastapi**: The FastAPI application server
   - **file-pg**: PostgreSQL database
   - **file-redis**: Redis cache server

   **Important steps before running:**
   1. **Copy and configure your environment file:**
      - Copy `.env.example` to `.env` in the project root:
        ```bash
        cp .env.example .env
        ```
      - Edit `.env` and fill in all secrets (Postgres password, Redis password, AWS credentials, etc.).
      - The `POSTGRES_PASSWORD` and `REDIS_PASSWORD` you set in `.env` **must** match the values in `docker-compose.yml`.

   2. **Verify Docker and Docker Compose are installed.**
      - For most systems, you can check with:
        ```bash
        docker --version
        docker-compose --version
        ```

   3. **Start all services:**
      - From the project root (with `.env` present), run:
        ```bash
        docker-compose up
        ```
      - This will launch:
        - `file-fastapi`: your API backend
        - `file-pg`: PostgreSQL Database
        - `file-redis`: Redis Server

   4. **Access the API:**
      - By default, the FastAPI server is available at [http://localhost:8000](http://localhost:8000).
      - You can adjust ports and settings in `docker-compose.yml` as needed.

   5. **Stop services:**
      - Use `Ctrl+C` in your terminal to stop, or run:
        ```bash
        docker-compose down
        ```

   > **Note:**
   > - All sensitive credentials should be managed in your `.env` file.
   > - The `.env` file **must** exist in the project root before starting Docker Compose.
   > - The structure of `.env` is provided in `.env.example`.
   > - For production, review your Docker and environment settings for security best practices.

---
```

## API Endpoints Overview

- `POST /auth/register` — Register a new user
- `POST /auth/login` — Login and receive JWT token in cookie
- `POST /auth/logout` — Logout and clear session
- `POST /user/upload` — Upload one or more files
- `GET /user/files` — List/search user files (with Redis caching)
- `DELETE /user/files` — Delete all user files
- `DELETE /user/` — Delete user account and all associated files

