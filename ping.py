import requests
import json
from pathlib import Path

with open('config.json') as f:
    CONFIG = json.load(f)

SITE_URL = CONFIG['site_url']

def ping_google():
    sitemap_url = f"{SITE_URL}/sitemap.xml"
    ping_url = f"https://www.google.com/ping?sitemap={sitemap_url}"

    try:
        r = requests.get(ping_url, timeout=10)
        print(f"Google ping status: {r.status_code}")
    except Exception as e:
        print(f"Ping failed (non-critical): {e}")

def ping_bing():
    sitemap_url = f"{SITE_URL}/sitemap.xml"
    ping_url = f"https://www.bing.com/ping?sitemap={sitemap_url}"
    try:
        r = requests.get(ping_url, timeout=10)
        print(f"Bing ping status: {r.status_code}")
    except Exception as e:
        print(f"Bing ping failed: {e}")

if __name__ == '__main__':
    ping_google()
    ping_bing()
