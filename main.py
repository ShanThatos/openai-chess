import atexit
import os
import subprocess
from pathlib import Path
from subprocess import Popen
from typing import Optional

import psutil
import uvicorn
from dotenv import load_dotenv

load_dotenv()

def fully_kill_process(process: Optional[Popen]):
    if process is None:
        return
    for child_process in psutil.Process(process.pid).children(True):
        try:
            child_process.kill()
        except psutil.NoSuchProcess:
            pass
    process.kill()


def start_server():
    CF_PROCESS: Optional[Popen] = None
    if os.environ.get("RUN_CLOUDFLARED") == "yes":
        cf_domain = os.environ.get("CLOUDFLARED_DOMAIN")
        if not Path("./cf_creds.json").exists():
            print("Retrieving cloudflare credentials...")
            subprocess.run(
                f"cloudflared tunnel token --cred-file cf_creds.json {cf_domain}",
                shell=True,
            )
        CF_PROCESS = Popen(
            f"cloudflared tunnel run --cred-file cf_creds.json --url 0.0.0.0:8086 {cf_domain}",
            shell=True,
            start_new_session=True,
        )
    atexit.register(lambda: fully_kill_process(CF_PROCESS))

    hot_reload = os.environ.get("ENVIRONMENT", "prod") == "dev"
    uvicorn.run("chessapp.app:app", host="0.0.0.0", port=8086, reload=hot_reload)


if __name__ == "__main__":
    start_server()
