"""
POST /restarter  ->  relaunches ComfyUI 
with the same interpreter, flags and args.
"""
import os
import sys
import time
import threading
import subprocess

from aiohttp import web
from server import PromptServer
from comfy_api.latest import ComfyExtension, IO

from typing_extensions import override

def _build_cmd():
    # Interpreter flags like -s (portable builds) aren't in sys.argv, so recover them.
    cmd = [sys.executable, *subprocess._args_from_interpreter_flags(), *sys.argv]
    # Don't open a second browser tab; the existing tab reloads itself.
    if "--disable-auto-launch" not in cmd:
        cmd.append("--disable-auto-launch")
    return cmd


def _restart():
    time.sleep(0.75)  # let the HTTP response reach the browser first
    cmd = _build_cmd()
    print(f"[⏻ Restarter]: relaunching -> {' '.join(cmd)}", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    if os.name == "nt":
        # os.execv on Windows doesn't quote args with spaces; spawn properly, then exit.
        subprocess.Popen(cmd, cwd=os.getcwd())
        os._exit(0)
    else:
        os.execv(sys.executable, cmd)


@PromptServer.instance.routes.post("/restarter")
async def fg_restart(request):
    threading.Thread(target=_restart, daemon=True).start()
    return web.json_response({"status": "restarting"})


WEB_DIRECTORY = "./"
class Restarter(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[IO.ComfyNode]]:
        return []

async def comfy_entrypoint() -> Restarter:
    return Restarter()


