# main.py
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

# Environment variables for moodle-dl (configured in Render)
MOODLE_URL = os.getenv('MOODLE_URL')
MOODLE_DOMAIN = os.getenv('MOODLE_DOMAIN')
MOODLE_PATH = os.getenv('MOODLE_PATH')
MOODLE_TOKEN = os.getenv('MOODLE_TOKEN')
DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', '/tmp/moodle')
VERBOSE = os.getenv('VERBOSE', 'false').lower() == 'true'

@app.route('/run', methods=['POST'])
def run_moodle_dl():
    # Build config.json dynamically
    config = {
        "moodle_domain": MOODLE_DOMAIN,
        "moodle_path": MOODLE_PATH,
        "token": MOODLE_TOKEN,
        "path": DOWNLOAD_PATH,
        "verbose": VERBOSE
    }
    with open('config.json', 'w') as f:
        import json
        json.dump(config, f)

    # Execute moodle-dl
    cmd = ['moodle-dl']
    if VERBOSE:
        cmd.append('--verbose')

    result = subprocess.run(cmd, capture_output=True, text=True)
    return jsonify({
        'stdout': result.stdout,
        'stderr': result.stderr,
        'returncode': result.returncode
    }), 200

@app.route('/', methods=['GET'])
def index():
    return 'Moodle-DL Service is running!', 200

if __name__ == '__main__':
    # Bind to port from environment or default 8000
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

# requirements.txt
# flask
# moodle-dl
