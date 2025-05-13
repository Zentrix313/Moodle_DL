import os
import json
import subprocess
import shutil
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

# Verzeichnis, in dem moodle-dl seine Dateien legt
DOWNLOAD_DIR = os.getenv("DOWNLOAD_PATH", "/tmp/moodle")

class RunRequest(BaseModel):
    pass  # im Moment keine Parameter

@app.get("/")
def health_check():
    return {"message": "Moodle-DL Service is running!"}

@app.post("/run")
def run_and_zip(req: RunRequest):
    # 1) Konfigurationsdatei schreiben
    config = {
        "moodle_domain": os.getenv("MOODLE_DOMAIN"),
        "moodle_path": os.getenv("MOODLE_PATH"),
        "token": os.getenv("MOODLE_TOKEN"),
        "path": DOWNLOAD_DIR,
        "verbose": os.getenv("VERBOSE", "false").lower() == "true"
    }
    with open("config.json", "w") as f:
        json.dump(config, f)

    # 2) moodle-dl ausführen (lädt nur neue Dateien)
    cmd = ["moodle-dl"]
    if config["verbose"]:
        cmd.append("--verbose")
    # Setze Arbeitsverzeichnis, damit moodle-dl die config.json findet
    result = subprocess.run(cmd, cwd=os.getcwd(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)

    # Falls moodle-dl fehlschlägt, gib die Logs direkt zurück
    if result.returncode != 0:
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    # 3) ZIP-Archiv mit Timestamp im Projekt-Root erstellen
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    zip_basename = f"moodle_{timestamp}"
    shutil.make_archive(zip_basename, 'zip', DOWNLOAD_DIR)

    # 4) ZIP als FileResponse zurückliefern
    return FileResponse(f"{zip_basename}.zip",
                        media_type="application/zip",
                        filename=f"{zip_basename}.zip")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
