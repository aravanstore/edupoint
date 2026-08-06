import os
import pathlib

base = pathlib.Path(__file__).parent
for line in (base / 'deploy.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ[k.strip()] = v.strip()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edupoint.settings')
from edupoint.wsgi import application
from waitress import serve

serve(
    application,
    host='127.0.0.1',
    port=8000,
    threads=8,
    trusted_proxy='127.0.0.1',
    trusted_proxy_headers={'x-forwarded-proto', 'x-forwarded-for'},
    clear_untrusted_proxy_headers=True,
)
