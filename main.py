import os
import json
import subprocess
import shutil
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()
DOWNLOAD_DIR = os.getenv("DOWNLOAD_PATH", "/tmp/moodle")

class RunRequest(BaseModel):
    pass

@app.get("/")
def health_check():
    return {"message": "Moodle-DL Service is running!"}

@app.post("/run")
def run_moodle_dl(req: RunRequest):
    # Write config.json
    config = {
        "moodle_domain": os.getenv("MOODLE_DOMAIN"),
        "moodle_path": os.getenv("MOODLE_PATH"),
        "token": os.getenv("MOODLE_TOKEN"),
        "path": DOWNLOAD_DIR,
        "verbose": os.getenv("VERBOSE", "false").lower() == "true"
    }
    with open("config.json", "w") as f:
        json.dump(config, f)

    # Run moodle-dl
    cmd = ["moodle-dl"]
    if config["verbose"]:
        cmd.append("--verbose")
    result = subprocess.run(cmd, cwd=os.getcwd(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
    if result.returncode != 0:
        return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}

    # Build ZIP for download
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    zip_name = f"moodle_{timestamp}"
    shutil.make_archive(zip_name, 'zip', DOWNLOAD_DIR)
    return {"returncode": 0, "zip_file": f"{zip_name}.zip"}

@app.get("/download")
def download_zip():
    # Find latest ZIP in working directory
    zips = sorted([f for f in os.listdir('.') if f.startswith('moodle_') and f.endswith('.zip')])
    if not zips:
        return {"error": "no zip found"}
    latest = zips[-1]
    return FileResponse(latest, media_type="application/zip", filename=latest)
