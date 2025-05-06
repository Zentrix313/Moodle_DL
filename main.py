# main.py
import os
import subprocess
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class RunRequest(BaseModel):
    # Optional parameters for future extensions (e.g., specific courses)
    course_ids: list[int] = None

@app.get("/")
def read_root():
    return {"message": "Moodle-DL Service is running!"}

@app.post("/run")
def run_moodle_dl(req: RunRequest):
    # Dynamically build config.json from environment variables
    config_content = {
        "moodle_domain": os.getenv("MOODLE_DOMAIN"),
        "moodle_path": os.getenv("MOODLE_PATH"),
        "token": os.getenv("MOODLE_TOKEN"),
        "path": os.getenv("DOWNLOAD_PATH", "/tmp/moodle"),
        "verbose": os.getenv("VERBOSE", "false").lower() == "true"
    }
    # Write config.json
    with open("config.json", "w") as f:
        import json
        json.dump(config_content, f)

    # Execute moodle-dl
    cmd = ["moodle-dl", "-c", "config.json"]
    if config_content["verbose"]:
        cmd.append("--verbose")

    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# requirements.txt
fastapi
uvicorn
moodle-dl

# render.yaml
services:
  - type: web
    name: moodle-dl-service
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: MOODLE_DOMAIN
        sync: true
      - key: MOODLE_PATH
        sync: true
      - key: MOODLE_TOKEN
        sync: true
      - key: DOWNLOAD_PATH
        sync: true
      - key: VERBOSE
        sync: true
