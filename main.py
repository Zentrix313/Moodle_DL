import os
import glob
import json
import subprocess
import shutil
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

class RunRequest(BaseModel):
    test_mode: bool = False   # erzeugt Dummy-Dateien
    full_mode: bool = False   # überspringt das Leeren des Download-Ordners

@app.get("/")
def health_check():
    return {"message": "Moodle-DL Service is running!"}

@app.post("/run")
def run_moodle_dl(req: RunRequest):
    # 1) Download-Ordner festlegen und anlegen
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_PATH", "/tmp/moodle")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # 2) Konfigurationsdatei schreiben
    config = {
        "moodle_domain": os.getenv("MOODLE_DOMAIN"),
        "moodle_path": os.getenv("MOODLE_PATH"),
        "token": os.getenv("MOODLE_TOKEN"),
        "path": DOWNLOAD_DIR,
        "verbose": os.getenv("VERBOSE", "false").lower() == "true"
    }
    with open("config.json", "w") as f:
        json.dump(config, f)

    # 3) Ordner leeren, außer im Full-Modus
    if not req.full_mode and not req.test_mode:
        for fname in os.listdir(DOWNLOAD_DIR):
            full = os.path.join(DOWNLOAD_DIR, fname)
            try:
                if os.path.isdir(full):
                    shutil.rmtree(full)
                else:
                    os.remove(full)
            except Exception:
                print(f"Could not delete {full}")

    # 3.1) Stale Lock entfernen
    lock_path = os.path.join(os.getcwd(), 'running.lock')
    if os.path.exists(lock_path):
        try:
            os.remove(lock_path)
            print(f"Removed stale lock: {lock_path}")
        except Exception as e:
            print(f"Failed to remove lock {lock_path}: {e}")

    # 4) Test-Modus: Dummy-Dateien
    if req.test_mode:
        for i in range(3):
            test_file = os.path.join(DOWNLOAD_DIR, f"testfile_{i}.txt")
            with open(test_file, "w") as f:
                f.write(f"This is test file {i}.\n")
        print("Running in TEST MODE: Dummy files created.")
    else:
        # 5) moodle-dl ausführen
        cmd = ["moodle-dl"]
        if config["verbose"]:
            cmd.append("--verbose")
        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 6) Log-Ausgabe & Verzeichnisinhalt
        print("=== MOODLE-DL STDOUT ===")
        print(result.stdout)
        print("=== MOODLE-DL STDERR ===")
        print(result.stderr)
        print("=== CONTENT OF DOWNLOAD_DIR ===")
        for root, dirs, files in os.walk(DOWNLOAD_DIR):
            for name in files:
                print(os.path.join(root, name))

        if result.returncode != 0:
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

    # 7) ZIP bauen (beinhaltet nun alle Dateien, je nach full_mode)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    zip_name = f"moodle_{timestamp}"
    shutil.make_archive(zip_name, 'zip', DOWNLOAD_DIR)

    # 8) Rückgabe mit ZIP-Name
    return {
        "returncode": 0,
        "zip_file": f"{zip_name}.zip"
    }

@app.get("/download")
def download_zip():
    zips = sorted(glob.glob("moodle_*.zip"))
    if not zips:
        return {"error": "Keine ZIP-Datei gefunden"}, 404
    latest = zips[-1]
    return FileResponse(
        path=latest,
        media_type="application/zip",
        filename=latest
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
