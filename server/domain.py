import os
import sys
import secrets
import subprocess
import threading
import time
import logging

logger = logging.getLogger("animesaturn.domain")

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
DOMAIN_FILE = os.path.join(SERVER_DIR, ".domain")

def get_or_create_subdomain() -> str:
    if os.path.exists(DOMAIN_FILE):
        try:
            with open(DOMAIN_FILE, "r", encoding="utf-8") as f:
                saved = f.read().strip()
                if saved:
                    return saved
        except Exception as e:
            logger.warning(f"Error reading {DOMAIN_FILE}: {e}")

    random_hex = secrets.token_hex(4)
    subdomain = f"saturn-api-{random_hex}"
    try:
        with open(DOMAIN_FILE, "w", encoding="utf-8") as f:
            f.write(subdomain)
    except Exception as e:
        logger.warning(f"Error writing {DOMAIN_FILE}: {e}")

    return subdomain

def get_public_url(provider: str = "serveo") -> str:
    subdomain = get_or_create_subdomain()
    custom_base = os.getenv("DOMAIN_BASE")
    if custom_base:
        return f"https://{subdomain}.{custom_base.lstrip('.')}"
    
    if provider == "localtunnel":
        return f"https://{subdomain}.loca.lt"
    elif provider == "pinggy":
        return f"https://{subdomain}.a.pinggy.link"
    else:
        return f"https://{subdomain}.serveo.net"

def start_tunnel_process(port: int = 8000, provider: str = "serveo"):
    subdomain = get_or_create_subdomain()

    def tunnel_worker():
        while True:
            try:
                if provider == "localtunnel":
                    cmd = ["npx", "localtunnel", "--port", str(port), "--subdomain", subdomain]
                elif provider == "pinggy":
                    cmd = ["ssh", "-p", "443", "-R0:localhost:" + str(port), "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=30", "a.pinggy.io"]
                else:
                    cmd = [
                        "ssh",
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "ServerAliveInterval=30",
                        "-o", "ServerAliveCountMax=3",
                        "-o", "ExitOnForwardFailure=yes",
                        "-R", f"{subdomain}:80:localhost:{port}",
                        "serveo.net"
                    ]

                logger.info(f"[Tunnel] Starting {provider} tunnel for persistent subdomain '{subdomain}'...")
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                for line in iter(proc.stdout.readline, ""):
                    if line.strip():
                        logger.info(f"[Tunnel] {line.strip()}")
                proc.wait()
            except Exception as e:
                logger.warning(f"[Tunnel] Tunnel error: {e}")
            
            logger.info("[Tunnel] Reconnecting in 5 seconds...")
            time.sleep(5)

    thread = threading.Thread(target=tunnel_worker, daemon=True, name="PersistentTunnelThread")
    thread.start()
    return thread
