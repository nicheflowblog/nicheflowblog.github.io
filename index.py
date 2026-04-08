"""
Regenerates deploy/index.html from all posts in deploy/posts/.
Run from the ~/nicheflow directory: python3 index.py
"""

import re
from pathlib import Path
from datetime import datetime

POSTS_DIR = Path('deploy/posts')
OUT_PATH  = Path('deploy/index.html')

# ── Preserve Google site-verification tag if present ──────────────────────────
existing  = OUT_PATH.read_text() if OUT_PATH.exists() else ''
gsv_match = re.search(r'<meta name="google-site-verification"[^>]+/?>', existing)
gsv_tag   = gsv_match.group(0) + '\n' if gsv_match else ''

# ── Collect posts (newest mtime first) ────────────────────────────────────────
posts = sorted(POSTS_DIR.glob('*.html'), key=lambda p: p.stat().st_mtime, reverse=True)

entries = ''
for post in posts:
    content     = post.read_text(encoding='utf-8')
    title_match = re.search(r'<title>(.*?)\s*[|—]', content)
    title       = title_match.group(1).strip() if title_match else post.stem.replace('-', ' ').title()
    entries += f'''        <li class="guide-card">
          <a href="posts/{post.name}">
            <div class="card-inner">
              <span class="card-tag">Buyer&#39;s Guide</span>
              <h3>{title}</h3>
              <span class="card-cta">Read the guide &rarr;</span>
            </div>
          </a>
        </li>\n'''

year = datetime.now().year

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{gsv_tag}<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KitchenPickr &mdash; Expert Kitchen Reviews &amp; Buying Guides</title>
<meta name="description" content="Independent, honest kitchen product reviews and buying guides. We test the products so you don't have to.">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #ffffff;
  color: #1a1a1a;
  font-size: 16px;
  line-height: 1.6;
}}

/* ── Header ── */
header {{
  background: #1B4332;
  padding: 0 clamp(1rem, 5vw, 3rem);
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}}
.header-inner {{
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
}}
.site-logo {{
  font-size: 1.4rem;
  font-weight: 800;
  color: #ffffff;
  text-decoration: none;
  letter-spacing: -0.4px;
}}
.site-logo span {{ color: #86EFAC; }}
.site-tagline {{
  font-size: 0.82rem;
  color: rgba(255,255,255,0.55);
  font-style: italic;
}}

/* ── Hero ── */
.hero {{
  background: #1B4332;
  color: #ffffff;
  padding: clamp(2.5rem, 7vw, 5rem) clamp(1rem, 5vw, 3rem);
  text-align: center;
}}
.hero-inner {{ max-width: 640px; margin: 0 auto; }}
.hero-eyebrow {{
  display: inline-block;
  background: rgba(255,255,255,0.12);
  color: #86EFAC;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2px;
  padding: 5px 14px;
  border-radius: 20px;
  margin-bottom: 1.25rem;
}}
.hero h1 {{
  font-size: clamp(2rem, 5vw, 3.2rem);
  font-weight: 900;
  line-height: 1.15;
  letter-spacing: -1px;
  margin-bottom: 1rem;
  color: #ffffff;
}}
.hero h1 em {{ color: #86EFAC; font-style: normal; }}
.hero p {{
  font-size: 1.05rem;
  color: rgba(255,255,255,0.7);
  line-height: 1.7;
  max-width: 480px;
  margin: 0 auto;
}}

/* ── Trust bar ── */
.trust-bar {{
  background: #f9f9f9;
  border-bottom: 1px solid #e8e8e8;
  padding: 0.85rem 2rem;
}}
.trust-inner {{
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}}
.trust-item {{
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  color: #555;
  font-weight: 500;
}}
.trust-item .chk {{ color: #1B4332; font-weight: 700; }}

/* ── Guide grid ── */
.section-header {{
  max-width: 1200px;
  margin: 0 auto;
  padding: clamp(1.75rem, 4vw, 2.5rem) clamp(1rem, 3vw, 2rem) 1rem;
  display: flex;
  align-items: baseline;
  gap: 1rem;
}}
.section-header h2 {{
  font-size: 1.5rem;
  font-weight: 800;
  color: #1a1a1a;
}}
.section-header p {{
  font-size: 0.85rem;
  color: #777;
}}

.guides-grid {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 clamp(1rem, 3vw, 2rem) clamp(2rem, 5vw, 4rem);
}}
ul.guide-list {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
  list-style: none;
  padding: 0;
}}

.guide-card {{
  background: #ffffff;
  border: 1px solid #e4e4e4;
  border-radius: 10px;
  overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}}
.guide-card:hover {{
  transform: translateY(-3px);
  box-shadow: 0 10px 28px rgba(0,0,0,0.1);
}}
.guide-card a {{
  display: block;
  text-decoration: none;
  color: inherit;
  height: 100%;
}}
.card-inner {{
  padding: 1.4rem 1.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  height: 100%;
}}
.card-tag {{
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: #2D6A4F;
}}
.guide-card h3 {{
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.45;
  color: #1a1a1a;
  flex: 1;
}}
.card-cta {{
  font-size: 0.8rem;
  font-weight: 700;
  color: #2D6A4F;
}}
.guide-card:hover .card-cta {{ color: #1B4332; }}

/* ── Footer ── */
footer {{
  background: #111;
  color: rgba(255,255,255,0.45);
  text-align: center;
  padding: 2.5rem 2rem;
  font-size: 0.82rem;
  line-height: 2;
}}
footer a {{ color: rgba(255,255,255,0.65); text-decoration: none; }}
footer a:hover {{ color: #fff; }}

@media (max-width: 600px) {{
  ul.guide-list {{ grid-template-columns: 1fr; }}
  .trust-inner {{ gap: 1rem; }}
}}
</style>
</head>
<body>

<header>
  <div class="header-inner">
    <a class="site-logo" href="/">KitchenPickr<span>.</span></a>
    <span class="site-tagline">Honest reviews. No fluff.</span>
  </div>
</header>

<section class="hero">
  <div class="hero-inner">
    <span class="hero-eyebrow">Independent &middot; Unsponsored &middot; Honest</span>
    <h1>Kitchen Gear Worth <em>Your</em> Money</h1>
    <p>We research, compare, and rank the best kitchen products so you can buy with confidence &mdash; not guesswork.</p>
  </div>
</section>

<div class="trust-bar">
  <div class="trust-inner">
    <div class="trust-item"><span class="chk">&#10003;</span> Independent Reviews</div>
    <div class="trust-item"><span class="chk">&#10003;</span> No Paid Placements</div>
    <div class="trust-item"><span class="chk">&#10003;</span> Real-World Testing</div>
    <div class="trust-item"><span class="chk">&#10003;</span> Updated Regularly</div>
  </div>
</div>

<div class="section-header">
  <h2>All Buying Guides</h2>
  <p>Sorted by newest first</p>
</div>

<div class="guides-grid">
  <ul class="guide-list">
{entries}  </ul>
</div>

<footer>
  <p>&copy; {year} KitchenPickr &middot; All Rights Reserved</p>
  <p>As an Amazon Associate we earn from qualifying purchases. &middot; <a href="#">Privacy Policy</a> &middot; <a href="#">Affiliate Disclosure</a></p>
</footer>

</body>
</html>"""

OUT_PATH.write_text(html, encoding='utf-8')
print(f"Generated {OUT_PATH} with {len(posts)} posts.")
