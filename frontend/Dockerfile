# --- Build Stage ---
FROM node:20-alpine as build-stage

WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Install dependencies (use npm ci for reproducible builds)
RUN npm ci

# Copy source code
COPY . .

# Set up environment variables for build
ARG REACT_APP_API_URL=http://localhost:8001
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build the app
RUN npm run build

# --- Production Stage ---
FROM nginx:stable-alpine

# Set the working directory to Nginx's HTML content path
WORKDIR /usr/share/nginx/html

# Clean up default Nginx static files
RUN rm -rf ./*

# Copy the build artifacts from the build stage
COPY --from=build-stage /app/build .

# Create a custom Nginx configuration to support SPA routing (if needed)
# and listen on port 3000 (standard in the current project setup)
RUN echo 'server { \
    listen 3000; \
    location / { \
    root /usr/share/nginx/html; \
    index index.html index.htm; \
    try_files $uri $uri/ /index.html; \
    } \
    error_page 500 502 503 504 /50x.html; \
    location = /50x.html { \
    root /usr/share/nginx/html; \
    } \
    }' > /etc/nginx/conf.d/default.conf

# Expose port 3000
EXPOSE 3001

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
