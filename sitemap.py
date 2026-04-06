import json
from pathlib import Path
from datetime import datetime

with open('config.json') as f:
    CONFIG = json.load(f)

SITE_URL = CONFIG['site_url']
OUTPUT_DIR = Path(CONFIG['output_dir'])


def build_sitemap():
    posts_dir = OUTPUT_DIR / 'posts'
    urls = [f"{SITE_URL}/\n"]

    if posts_dir.exists():
        for html_file in sorted(posts_dir.glob('*.html')):
            slug = html_file.stem
            modified = datetime.fromtimestamp(html_file.stat().st_mtime).strftime('%Y-%m-%d')
            urls.append(
                f"""  <url>
    <loc>{SITE_URL}/posts/{slug}.html</loc>
    <lastmod>{modified}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>"""
            )

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{"".join(urls)}
</urlset>"""

    sitemap_path = OUTPUT_DIR / 'sitemap.xml'
    sitemap_path.write_text(sitemap)
    print(f"Sitemap rebuilt: {len(urls)} URLs")


if __name__ == '__main__':
    build_sitemap()
