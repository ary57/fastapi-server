### To Run

```bash
docker build -t fastapi-uv-app .
docker run -d -p 8000:8000 fastapi-uv-app
```

### To Stop: 
```bash
docker ps # Get the CONTAINER ID
docker stop <CONTAINER ID>
```