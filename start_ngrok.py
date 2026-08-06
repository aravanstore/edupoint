# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import time
import threading

# Fix encoding for Windows terminal
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edupoint.settings')

try:
    from pyngrok import ngrok
except ImportError:
    print("Installing pyngrok...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyngrok"], check=True)
    from pyngrok import ngrok

PORT = 8000

def run_django():
    manage_py = os.path.join(os.path.dirname(__file__), 'manage.py')
    subprocess.run([sys.executable, manage_py, 'runserver', str(PORT)],
                   env={**os.environ, 'PYTHONUTF8': '1'})

print("=" * 50)
print("  Edu Point - Public Launch")
print("=" * 50)

django_thread = threading.Thread(target=run_django, daemon=True)
django_thread.start()
print(f"Django started on http://localhost:{PORT}")
time.sleep(3)

try:
    tunnel = ngrok.connect(PORT, "http")
    public_url = tunnel.public_url
    if public_url.startswith("http://"):
        public_url = public_url.replace("http://", "https://", 1)

    print("\n" + "=" * 50)
    print("  SITE IS LIVE! SHARE THIS LINK:")
    print(f"\n  >>> {public_url} <<<\n")
    print("  Anyone can open this link right now!")
    print("=" * 50)
    print("\n  Press Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        ngrok.disconnect(tunnel.public_url)
        ngrok.kill()

except Exception as e:
    print(f"\nngrok error: {e}")
    print("\nYou may need a free token from https://ngrok.com/signup")
    print("Then run: python -m pyngrok.ngrok authtoken YOUR_TOKEN")
    print(f"\nDjango is still running at http://localhost:{PORT}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
