# v4coppercoreagent

# systemd file
/etc/systemd/system/v4coppercoreagent-webapp.service
```
[Unit]
Description=V4 Copper Core agent Python App
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/projects/v4coppercoreagent
ExecStart=/home/ec2-user/projects/v4coppercoreagent/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8005
# If you need environment variables, you can set them as well:
# Environment="MYSQL_HOST=localhost" "MYSQL_USER=root" "MYSQL_PASS=secret"

# Ensure the process is automatically restarted if it crashes:
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

# start the app
```sudo systemctl start v4coppercoreagent-webapp.service```

# restart the app
```sudo systemctl restart v4coppercoreagent-webapp.service```

# check log 
```sudo journalctl -u v4coppercoreagent-webapp.service```
