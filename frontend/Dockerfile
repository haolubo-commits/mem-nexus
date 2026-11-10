# Multi-stage Dockerfile for MemNexus React 18 Frontend
FROM node:20-alpine as builder

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

# Nginx production server
FROM nginx:alpine as runner

COPY --from=builder /app/dist /usr/share/nginx/html

# Custom Nginx reverse proxy configuration
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass http://backend:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
