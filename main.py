# main.py
import os
import subprocess
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class RunRequest(BaseModel):
    course_ids: list[int] = None  # Optional: später wenn du nur bestimmte Kurse laden willst

@app.get("/")
def read_root():
    return {"message": "Moodle-DL Service is running!"}

@app.post("/run")
def run_moodle_dl(req: RunRequest):
    config_content = {
        "url": f"https://{os.getenv('MOODLE_DOMAIN')}{os.getenv('MOODLE_PATH')}",
        "token": os.getenv("MOODLE_TOKEN"),
        "download_dir": os.getenv("DOWNLOAD_PATH"),
        "verbose": os.getenv("VERBOSE", "false") == "true"
    }

    # Schreibe config.json ins aktuelle Verzeichnis
    with open("config.json", "w") as f:
        import json
        json.dump(config_content, f)

    # moodle-dl ausführen
    process = subprocess.run(
        ["moodle-dl", "-c", "config.json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return {
        "returncode": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr
    }
