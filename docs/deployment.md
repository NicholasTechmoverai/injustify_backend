# Production Deployment Guide

## 1. Local / Standard Execution
Run the server using Uvicorn:
```bash
python appp.py
```
Or via CLI:
```bash
uvicorn appp:app --host 127.0.0.1 --port 5000 --workers 4
```

---

## 2. Production Gunicorn + Uvicorn Workers
For high-concurrency production deployments:
```bash
gunicorn appp:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5000
```

---

## 3. Nginx Reverse Proxy Configuration
```nginx
server {
    listen 80;
    server_name admin.injustify.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
```
