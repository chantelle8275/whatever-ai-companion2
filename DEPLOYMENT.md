# Deployment Support

This repository now includes a container-based deployment setup for local development and CI automation.

## Local deployment with Docker Compose

Use Docker Compose to start MongoDB, the backend, and the Expo frontend web server.

```bash
cd /app
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend web: http://localhost:19006
- MongoDB: mongodb://localhost:27017

### Backend configuration

The backend service reads configuration from environment variables:

- `MONGO_URL` (default in compose: `mongodb://mongo:27017`)
- `DB_NAME` (default in compose: `test_database`)
- `EMERGENT_LLM_KEY` (if using Emergent LLM integration)

If you need local secrets, add them to `backend/.env` and the `backend` container will load them when it starts.

## GitHub Actions CI

A CI workflow was added at `.github/workflows/ci.yml` with two jobs:

- `backend` — installs Python dependencies and runs `pytest backend/tests`
- `frontend` — installs Node dependencies and runs `yarn lint` in `frontend`

This provides a basic automated check for backend and frontend health on `push` and `pull_request`.

## What changed

- `backend/Dockerfile`
- `backend/.dockerignore`
- `frontend/Dockerfile`
- `frontend/.dockerignore`
- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `DEPLOYMENT.md`

## Notes

- The frontend container provides Expo web for local testing.
- The backend container runs `uvicorn server:app --host 0.0.0.0 --port 8000`.
- This setup is compatible with cloud platforms that support Docker and GitHub Actions.
