# Docker

## Development

Pro vývoj používáme **docker-compose.dev.yml**:
```bash
docker-compose -f docker-compose.dev.yml up
```

## Production

Pro produkci používáme **docker-compose.yml** a **Dockerfile** v jednotlivých složkách (backend/Dockerfile, frontend/Dockerfile)