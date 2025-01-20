#!/bin/bash

# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv postgresql nginx

# Create a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install PM2 for process management
sudo npm install -g pm2

# Build Next.js application
npm install
npm run build

# Create systemd service for FastAPI
sudo tee /etc/systemd/system/fastapi-image-search.service << EOF
[Unit]
Description=FastAPI Image Search Service
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
Environment="ENV=production"
Environment="DB_USER=your_db_user"
Environment="DB_PASSWORD=your_db_password"
Environment="DB_HOST=localhost"
Environment="DB_NAME=image_search"
Environment="CORS_ORIGINS=https://imagesearch.pablothiermann.com"
ExecStart=$(pwd)/venv/bin/uvicorn api.index:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/image-search << EOF
server {
    listen 80;
    listen [::]:80;
    server_name imagesearch.pablothiermann.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name imagesearch.pablothiermann.com;

    ssl_certificate /etc/letsencrypt/live/imagesearch.pablothiermann.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/imagesearch.pablothiermann.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options "nosniff";

    location / {
        proxy_pass http://localhost:3002;  # Different port from ActionVerbs
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    location /uploads {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable the Nginx site
sudo ln -s /etc/nginx/sites-available/image-search /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Set up SSL certificate
sudo certbot --nginx -d imagesearch.pablothiermann.com

# Start the services
sudo systemctl start fastapi-image-search
sudo systemctl enable fastapi-image-search
pm2 start npm --name "image-search-next" -- start -- -p 3002  # Different port from ActionVerbs 