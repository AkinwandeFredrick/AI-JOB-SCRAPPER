# Personal AI Job Application Assistant

A secure, human-in-the-loop, privacy-focused AI optimization assistant specifically configured to run locally on an Oracle Cloud Always Free ARM computing compute platform (`VM.Standard.A1.Flex`, maximum 2 OCPU / 12 GB RAM running safe standard Ubuntu Server kernels).

## Production Setup Procedures

### 1. Configure Local Ollama Environment
Log inside your running cloud server VM and provision the standalone runtime and target optimization model weights:
```bash
curl -fsSL https://ollama.com | sh
ollama pull qwen2.5:7b
```

### 2. Build Virtual Environment & Project Core Dependencies
Clone or place this repository on your architecture path located at `/home/ubuntu/job-ai`. Build the virtual environment mapping:
```bash
sudo apt-get update && sudo apt-get install -y python3-venv python3-pip

cd /home/ubuntu/job-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Provision low-level dynamic dependencies needed by the rendering platform
playwright install chromium
```

### 3. Establish Persistent Service Unit File
Map your background application web UI processing layer via systemd rules:
```bash
sudo nano /etc/systemd/system/job-dashboard.service
```

Insert the configuration specifications structure:
```ini
[Unit]
Description=Job AI Assistant Web Dashboard Production Daemon
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/job-ai
ExecStart=/home/ubuntu/job-ai/venv/bin/uvicorn app.dashboard:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Reload and initialize your new active app service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable job-dashboard.service
sudo systemctl start job-dashboard.service
```

### 4. Wire the Hourly Automated Worker Task via Crontab
To activate the automatic tracking engine safely once an hour without manual steps, register the sync profile row inside the hardware cron execution grid:
```bash
crontab -e
```

Append the timeline script trigger rule:
```text
0 * * * * cd /home/ubuntu/job-ai && /home/ubuntu/job-ai/venv/bin/python -m app.worker >> /home/ubuntu/job-ai/logs/cron.log 2>&1
```

### 5. Securely Connecting to the Management Control Board
Because all local network services are bound carefully to address `127.0.0.1` to maintain tight server posture, create an encrypted SSH tunnel mapping path from your local computer workstation to access your remote application view metrics securely:
```bash
ssh -L 8000:localhost:8000 ubuntu@YOUR_ORACLE_PUBLIC_IP
```
Navigate to target URL address `http://localhost:8000` via your everyday personal desktop browser window.

## Important Production Safety Considerations
* **Terms of Service Compliance**: Auto-extraction modules may violate host conditions on public sites. Replace mock execution code sequences inside `app/scraper/conservative.py` with custom hooks that observe targeted platforms' structural constraints.
* **Resume Veracity Constraints**: The prompting parameters explicitly restrict modification logic patterns to context mapping changes only. Do not attempt to let local engines fabricate employment benchmarks.
* **Human Action Validation Rule**: This application software never attempts to complete form-submitting tasks directly. Validation, assessment confirmation, and submission operations rely entirely on active human review.
