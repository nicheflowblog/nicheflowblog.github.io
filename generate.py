import os
import json
import csv
import re
import random
import logging
from datetime import datetime
from pathlib import Path
import anthropic
 
logging.basicConfig(
    filename='logs/run.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
log = logging.getLogger(__name__)
 
with open('config.json') as f:
    CONFIG = json.load(f)
 
client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
 
 
def load_keywords():
    used = set()
    used_file = Path('logs/used_keywords.txt')
    if used_file.exists():
        used = set(used_file.read_text().splitlines())
 
    available = []
    with open('keywords.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['keyword'] not in used:
                available.append(row)
    return available, used
 
 
def pick_keyword(available):
    if not available:
        log.warning("All keywords used — resetting queue")
        Path('logs/used_keywords.txt').write_text('')
        with open('keywords.csv') as f:
            return list(csv.DictReader(f))[0]
    return random.choice(available)
 
 
def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
 
 
SYSTEM_PROMPTS = [
    """You are an expert product reviewer writing for a consumer advice website.
Write naturally, honestly, and helpfully. Include specific product recommendations
with pros/cons. Never use buzzwords like 'game-changer' or 'revolutionary'.
Write like a knowledgeable friend, not a marketer.""",
 
    """You are a home cook and kitchen enthusiast who tests products extensively.
Write detailed, practical reviews based on real-world use. Include specific use cases,
who each product is best for, and what to avoid. Be direct and opinionated.""",
 
    """You are a consumer advocate writer. Your goal is to help readers make smart
purchasing decisions by cutting through marketing hype. Focus on value, durability,
and real-world performance. Include clear recommendations for different budgets.""",
]
 
 
def generate_article(keyword_row):
    keyword = keyword_row['keyword']
    article_type = keyword_row['type']
 
    system_prompt = random.choice(SYSTEM_PROMPTS)
 
    user_prompt = f"""Write a comprehensive SEO article for the keyword: "{keyword}"
 
Article type: {article_type}
Target word count: 1,000–1,200 words
 
Required structure (use these exact HTML tags):
<h1>[Your compelling title — must include the keyword]</h1>
<p class="intro">[2-3 sentence hook that addresses the reader's problem]</p>
 
<h2>Quick Answer</h2>
[2-3 sentences with the direct answer/top recommendation for skimmers]
 
<h2>[First main section]</h2>
[Content with product recommendations. For each product you mention, format it like:]
<div class="product-rec">
<h3>[Product Name]</h3>
<p>[2-3 sentences on why it's recommended]</p>
<p><strong>Best for:</strong> [specific use case]</p>
<p><strong>Price range:</strong> [$XX–$XX]</p>
<span class="affiliate-slot" data-query="[exact amazon search query for this product]"></span>
</div>
 
[Continue with 3-5 products total]
 
<h2>What to Look For</h2>
[3-4 buying criteria explained practically]
 
<h2>Our Verdict</h2>
[Honest summary, who should buy what]
 
<p class="disclaimer">As an Amazon Associate we earn from qualifying purchases.</p>
 
Output only the HTML content between and including the h1 tag to the disclaimer. No markdown, no code fences, just clean HTML."""
 
    log.info(f"Generating article for: {keyword}")
 
    response = client.messages.create(
        model=CONFIG['claude_model'],
        max_tokens=CONFIG['max_tokens'],
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
 
    return response.content[0].text
 
 
def inject_affiliate_links(html_content):
    tag = CONFIG['affiliate']['amazon_tag']
 
    def make_affiliate_link(query):
        encoded = query.replace(' ', '+')
        return f"https://www.amazon.com/s?k={encoded}&tag={tag}"
 
    pattern = r'<span class="affiliate-slot" data-query="([^"]+)"></span>'
 
    def replace_slot(match):
        query = match.group(1)
        url = make_affiliate_link(query)
        return (
            f'<a href="{url}" rel="nofollow sponsored" target="_blank" '
            f'class="affiliate-btn">Check Price on Amazon ↗</a>'
        )
 
    return re.sub(pattern, replace_slot, html_content)
 
 
# ─────────────────────────────────────────────
#  ARTICLE PAGE TEMPLATE  (wrap_in_template)
# ─────────────────────────────────────────────
def wrap_in_template(article_html, keyword, slug, date_display=None, date_iso=None):
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', article_html)
    title = title_match.group(1) if title_match else keyword.title()

    desc_match = re.search(r'<p class="intro">(.*?)</p>', article_html, re.DOTALL)
    desc = desc_match.group(1)[:155] if desc_match else f"Best {keyword} reviewed and ranked."
    desc = re.sub(r'<[^>]+>', '', desc).strip()

    site = CONFIG['site_name']
    site_url = CONFIG['site_url']
    if date_display is None:
        date_display = datetime.now().strftime('%B %d, %Y')
    if date_iso is None:
        date_iso = datetime.now().strftime('%Y-%m-%d')

    # Strip h1 from article body — rendered separately above content
    article_body = re.sub(r'<h1[^>]*>.*?</h1>', '', article_html, count=1, flags=re.DOTALL).strip()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | {site}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<link rel="canonical" href="{site_url}/posts/{slug}.html">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #ffffff;
  color: #2d2d2d;
  line-height: 1.75;
  font-size: 1rem;
}}

/* ── HEADER ── */
header {{
  background: #1B4332;
  padding: 0 1.5rem;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}}
.header-inner {{
  max-width: 780px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
}}
.site-logo {{
  font-family: Georgia, serif;
  font-size: 1.35rem;
  font-weight: 700;
  color: #ffffff;
  text-decoration: none;
}}
.site-logo span {{ color: #86EFAC; }}
header nav a {{
  color: rgba(255,255,255,0.85);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
}}
header nav a:hover {{ color: #ffffff; text-decoration: underline; }}

/* ── CONTENT AREA ── */
.content {{
  max-width: 780px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem 4rem;
}}

/* ── META + TITLE ── */
.post-date {{
  display: block;
  font-size: 0.8rem;
  color: #888;
  margin-bottom: 0.6rem;
}}

h1 {{
  font-family: Georgia, serif;
  font-size: 2.2rem;
  font-weight: 700;
  color: #1a1a1a;
  line-height: 1.25;
  margin-bottom: 1rem;
}}

h2 {{
  font-family: Georgia, serif;
  font-size: 1.4rem;
  font-weight: 700;
  color: #1B4332;
  margin: 2.25rem 0 0.75rem;
  padding-bottom: 0.35rem;
  border-bottom: 2px solid #e8e8e8;
}}

h3 {{
  font-size: 1.05rem;
  font-weight: 700;
  color: #1a1a1a;
  margin: 1.25rem 0 0.4rem;
}}

p {{ margin-bottom: 1.1em; }}

/* ── INTRO BLOCK ── */
p.intro {{
  background: #f0f7f4;
  border-left: 4px solid #2D6A4F;
  color: #1a1a1a;
  font-style: italic;
  padding: 1.25rem 1.5rem;
  border-radius: 0 8px 8px 0;
  margin-bottom: 2rem;
  line-height: 1.8;
}}

/* ── PRODUCT CARDS ── */
.product-rec {{
  background: #ffffff;
  border: 1px solid #e4e4e4;
  border-radius: 10px;
  padding: 1.5rem;
  margin: 1.75rem 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}}
.product-rec h3 {{
  font-family: Georgia, serif;
  font-size: 1.1rem;
  font-weight: 700;
  color: #1a1a1a;
  margin-top: 0;
  margin-bottom: 0.6rem;
}}
.product-rec strong {{ color: #1B4332; }}

.affiliate-btn {{
  display: inline-block;
  background: #E8A020;
  color: #ffffff;
  padding: 10px 20px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 700;
  font-size: 0.9rem;
  margin-top: 0.75rem;
}}
.affiliate-btn:hover {{ background: #c98a18; }}

/* ── DISCLAIMER ── */
p.disclaimer {{
  font-size: 0.78rem;
  color: #888;
  background: #f8f8f8;
  border: 1px solid #e4e4e4;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin-top: 2.5rem;
}}

/* ── FOOTER ── */
footer {{
  background: #1a1a1a;
  color: rgba(255,255,255,0.5);
  text-align: center;
  padding: 2rem 1.5rem;
  font-size: 0.82rem;
  margin-top: 3rem;
}}
footer a {{ color: rgba(255,255,255,0.7); text-decoration: none; }}
footer a:hover {{ color: #ffffff; }}

@media (max-width: 600px) {{
  h1 {{ font-size: 1.7rem; }}
  .content {{ padding: 1.5rem 1rem 3rem; }}
  .product-rec {{ padding: 1.1rem; }}
}}
</style>
</head>
<body>

<header>
  <div class="header-inner">
    <a class="site-logo" href="/">{site}<span>.</span></a>
    <nav><a href="/">All Guides</a></nav>
  </div>
</header>

<div class="content">
  <time class="post-date" datetime="{date_iso}">Published {date_display}</time>
  <h1>{title}</h1>
  {article_body}
  <p style="margin-top:2.5rem"><a href="/" style="color:#2D6A4F;font-size:0.9rem;font-weight:600;text-decoration:none;">← Back to All Guides</a></p>
</div>

<footer>
  <p>© {datetime.now().year} {site} · Independent reviews, honest opinions · <a href="/">Home</a></p>
  <p style="margin-top:6px">As an Amazon Associate we earn from qualifying purchases.</p>
</footer>

</body>
</html>"""
 
 
# ─────────────────────────────────────────────
#  HOMEPAGE TEMPLATE  (update_index)
# ─────────────────────────────────────────────
def update_index(keyword, slug, title):
    index_path = Path(CONFIG['output_dir']) / 'index.html'
 
    entry = f'''        <li class="guide-card">
          <a href="posts/{slug}.html">
            <div class="card-inner">
              <span class="card-tag">Buyer's Guide</span>
              <h3>{title}</h3>
              <span class="card-cta">Read the guide →</span>
            </div>
          </a>
        </li>\n'''
 
    if index_path.exists():
        content = index_path.read_text()
        content = content.replace('<!-- POSTS -->', f'<!-- POSTS -->\n{entry}')
        index_path.write_text(content, encoding='utf-8')
        return
 
    site = CONFIG['site_name']
    year = datetime.now().year
 
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{site} — Expert Kitchen Reviews &amp; Buying Guides</title>
  <meta name="description" content="Independent, honest kitchen product reviews and buying guides. We test the products so you don't have to.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Lora:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
 
    :root {{
      --green:    #1B4332;
      --green-mid:#2D6A4F;
      --amber:    #B45309;
      --cream:    #FDFAF5;
      --ink:      #1C1917;
      --muted:    #78716C;
      --rule:     #E7E0D8;
      --white:    #FFFFFF;
    }}
 
    body {{
      font-family: 'DM Sans', sans-serif;
      background: var(--cream);
      color: var(--ink);
    }}
 
    /* ── HEADER ── */
    header {{
      background: var(--green);
      padding: 0 clamp(1rem, 5vw, 4rem);
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    }}
    .header-inner {{
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 64px;
    }}
    .site-logo {{
      font-family: 'Playfair Display', serif;
      font-size: 1.55rem;
      font-weight: 900;
      color: white;
      text-decoration: none;
      letter-spacing: -0.5px;
    }}
    .site-logo span {{ color: #86EFAC; }}
    header p {{
      font-size: 0.82rem;
      color: rgba(255,255,255,0.55);
      font-style: italic;
      font-family: 'Lora', serif;
    }}
 
    /* ── HERO ── */
    .hero {{
      background: var(--green);
      padding: clamp(3rem, 8vw, 6rem) clamp(1rem, 5vw, 4rem);
      text-align: center;
      position: relative;
      overflow: hidden;
    }}
    .hero::before {{
      content: '';
      position: absolute;
      inset: 0;
      background: radial-gradient(ellipse at 60% 50%, rgba(45,106,79,0.6) 0%, transparent 70%);
      pointer-events: none;
    }}
    .hero-inner {{ position: relative; max-width: 680px; margin: 0 auto; }}
    .hero-eyebrow {{
      display: inline-block;
      background: rgba(255,255,255,0.12);
      color: #86EFAC;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 2px;
      padding: 5px 16px;
      border-radius: 20px;
      margin-bottom: 1.5rem;
    }}
    .hero h1 {{
      font-family: 'Playfair Display', serif;
      font-size: clamp(2.2rem, 5vw, 3.5rem);
      font-weight: 900;
      color: white;
      line-height: 1.15;
      letter-spacing: -1px;
      margin-bottom: 1.25rem;
    }}
    .hero h1 em {{
      color: #86EFAC;
      font-style: normal;
    }}
    .hero p {{
      font-family: 'Lora', serif;
      font-size: 1.1rem;
      color: rgba(255,255,255,0.7);
      line-height: 1.7;
      max-width: 520px;
      margin: 0 auto;
    }}
 
    /* ── TRUST BAR ── */
    .trust-bar {{
      background: white;
      border-bottom: 1px solid var(--rule);
      padding: 1rem 2rem;
    }}
    .trust-inner {{
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 2.5rem;
      flex-wrap: wrap;
    }}
    .trust-item {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.82rem;
      color: var(--muted);
      font-weight: 500;
    }}
    .trust-item .icon {{ font-size: 1rem; }}
 
    /* ── GRID ── */
    .section-header {{
      max-width: 1200px;
      margin: 0 auto;
      padding: clamp(2rem, 4vw, 3rem) clamp(1rem, 3vw, 2rem) 1rem;
      display: flex;
      align-items: baseline;
      gap: 1rem;
    }}
    .section-header h2 {{
      font-family: 'Playfair Display', serif;
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--ink);
    }}
    .section-header p {{
      font-size: 0.875rem;
      color: var(--muted);
    }}
 
    .guides-grid {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 clamp(1rem, 3vw, 2rem) clamp(2rem, 5vw, 4rem);
    }}
    ul.guide-list {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
      gap: 20px;
      list-style: none;
      padding: 0;
    }}
 
    .guide-card {{
      background: white;
      border: 1px solid var(--rule);
      border-radius: 10px;
      overflow: hidden;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .guide-card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 12px 32px rgba(0,0,0,0.1);
    }}
    .guide-card a {{
      display: block;
      text-decoration: none;
      color: inherit;
      height: 100%;
    }}
    .card-inner {{
      padding: 1.5rem 1.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      height: 100%;
    }}
    .card-tag {{
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: var(--green-mid);
    }}
    .guide-card h3 {{
      font-family: 'Lora', serif;
      font-size: 1.05rem;
      font-weight: 600;
      line-height: 1.45;
      color: var(--ink);
      flex: 1;
    }}
    .card-cta {{
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--green-mid);
      margin-top: 0.25rem;
    }}
    .guide-card:hover .card-cta {{
      color: var(--green);
    }}
 
    /* ── FOOTER ── */
    footer {{
      background: var(--ink);
      color: rgba(255,255,255,0.45);
      text-align: center;
      padding: 2.5rem 2rem;
      font-size: 0.82rem;
      line-height: 2;
    }}
    footer a {{ color: rgba(255,255,255,0.65); text-decoration: none; }}
    footer a:hover {{ color: white; }}
 
    @media (max-width: 600px) {{
      ul.guide-list {{ grid-template-columns: 1fr; }}
      .trust-inner {{ gap: 1rem; }}
    }}
  </style>
</head>
<body>
 
<header>
  <div class="header-inner">
    <a class="site-logo" href="/">{site}<span>.</span></a>
    <p>Honest reviews. No fluff.</p>
  </div>
</header>
 
<section class="hero">
  <div class="hero-inner">
    <span class="hero-eyebrow">Independent · Unsponsored · Honest</span>
    <h1>Kitchen Gear Worth <em>Your</em> Money</h1>
    <p>We research, compare, and rank the best kitchen products so you can buy with confidence — not guesswork.</p>
  </div>
</section>
 
<div class="trust-bar">
  <div class="trust-inner">
    <div class="trust-item"><span class="icon">✓</span> Independent Reviews</div>
    <div class="trust-item"><span class="icon">✓</span> No Paid Placements</div>
    <div class="trust-item"><span class="icon">✓</span> Real-World Testing</div>
    <div class="trust-item"><span class="icon">✓</span> Updated Regularly</div>
  </div>
</div>
 
<div class="section-header">
  <h2>All Buying Guides</h2>
  <p>Sorted by newest first</p>
</div>
 
<div class="guides-grid">
  <ul class="guide-list">
<!-- POSTS -->
{entry}  </ul>
</div>
 
<footer>
  <p>© {year} {site} · All Rights Reserved</p>
  <p>As an Amazon Associate we earn from qualifying purchases. <a href="#">Privacy Policy</a> · <a href="#">Affiliate Disclosure</a></p>
</footer>
 
</body>
</html>"""
 
    index_path.write_text(content, encoding='utf-8')
 
 
def mark_used(keyword):
    used_file = Path('logs/used_keywords.txt')
    used_file.parent.mkdir(exist_ok=True)
    with open(used_file, 'a') as f:
        f.write(keyword + '\n')
 
 
def main():
    BATCH_SIZE = 5
 
    log.info(f"=== NicheFlow generation run started (Batch: {BATCH_SIZE}) ===")
 
    available, used = load_keywords()
 
    if not available:
        print("No more keywords left in keywords.csv!")
        return
 
    for i in range(min(BATCH_SIZE, len(available))):
        row = available[i]
        keyword = row['keyword']
        slug = slugify(keyword)
 
        print(f"[{i+1}/{BATCH_SIZE}] Generating: {keyword}...")
        log.info(f"Keyword selected: {keyword}")
 
        try:
            article_html = generate_article(row)
            article_html = inject_affiliate_links(article_html)
 
            title_match = re.search(r'<h1[^>]*>(.*?)</h1>', article_html)
            title = re.sub(r'<[^>]+>', '', title_match.group(1)) if title_match else keyword.title()
 
            full_html = wrap_in_template(article_html, keyword, slug)
            filepath = save_article(full_html, slug)
            update_index(keyword, slug, title)
            mark_used(keyword)
 
            log.info(f"Article saved: {filepath}")
            print(f"✅ Success: {filepath}")
 
        except Exception as e:
            log.error(f"Generation failed for '{keyword}': {e}")
            print(f"❌ Failed: {keyword}")
            continue
 
    print("\nBatch complete! Run 'python3 publish.py' to push changes to GitHub.")
 
 
def save_article(html, slug):
    posts_dir = Path(CONFIG['output_dir']) / 'posts'
    posts_dir.mkdir(parents=True, exist_ok=True)
    filepath = posts_dir / f"{slug}.html"
    filepath.write_text(html, encoding='utf-8')
    return filepath
 
 
if __name__ == '__main__':
    main()