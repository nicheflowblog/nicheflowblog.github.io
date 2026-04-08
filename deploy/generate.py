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
Target word count: 1,400–1,600 words

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
            f'class="affiliate-btn">Check price on Amazon ↗</a>'
        )

    return re.sub(pattern, replace_slot, html_content)


def wrap_in_template(article_html, keyword, slug):
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', article_html)
    title = title_match.group(1) if title_match else keyword.title()

    desc_match = re.search(r'<p class="intro">(.*?)</p>', article_html, re.DOTALL)
    desc = desc_match.group(1)[:155] if desc_match else f"Best {keyword} reviewed and ranked."
    desc = re.sub(r'<[^>]+>', '', desc).strip()

    site = CONFIG['site_name']
    site_url = CONFIG['site_url']
    date = datetime.now().strftime('%Y-%m-%d')

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
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:760px;margin:0 auto;padding:20px 16px;line-height:1.7;color:#1a1a1a}}
h1{{font-size:1.8em;line-height:1.3;margin-bottom:.5em}}
h2{{font-size:1.3em;margin-top:2em;padding-bottom:.3em;border-bottom:1px solid #eee}}
h3{{font-size:1.1em;margin-top:1.5em}}
.product-rec{{background:#f8f9fa;border-left:3px solid #0066cc;padding:16px;margin:20px 0;border-radius:0 8px 8px 0}}
.affiliate-btn{{display:inline-block;background:#ff9900;color:#111;padding:8px 16px;border-radius:6px;text-decoration:none;font-weight:600;font-size:.9em;margin-top:8px}}
.affiliate-btn:hover{{background:#e88800}}
.disclaimer{{font-size:.8em;color:#666;border-top:1px solid #eee;padding-top:1em;margin-top:2em}}
nav{{background:#0066cc;padding:12px 16px;margin:-20px -16px 30px;color:white}}
nav a{{color:white;text-decoration:none;font-weight:600}}
.date{{color:#666;font-size:.85em;margin-bottom:1em}}
</style>
</head>
<body>
<nav><a href="/">{site}</a> — Smart buying guides</nav>
<p class="date">Published {date}</p>
{article_html}
<p style="margin-top:2em"><a href="/">← Back to all guides</a></p>
</body>
</html>"""


def save_article(html, slug):
    posts_dir = Path(CONFIG['output_dir']) / 'posts'
    posts_dir.mkdir(parents=True, exist_ok=True)
    filepath = posts_dir / f"{slug}.html"
    filepath.write_text(html, encoding='utf-8')
    return filepath


def update_index(keyword, slug, title):
    index_path = Path(CONFIG['output_dir']) / 'index.html'
    entry = f'<li><a href="posts/{slug}.html">{title}</a></li>\n'

    if index_path.exists():
        content = index_path.read_text()
        content = content.replace('<!-- POSTS -->', f'{entry}<!-- POSTS -->')
    else:
        content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{CONFIG['site_name']} — Best product guides</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{{font-family:system-ui,sans-serif;max-width:760px;margin:0 auto;padding:20px 16px}}ul{{list-style:none;padding:0}}li{{margin:10px 0}}a{{color:#0066cc;text-decoration:none;font-size:1.05em}}a:hover{{text-decoration:underline}}</style>
</head>
<body>
<h1>{CONFIG['site_name']}</h1>
<p>Honest product reviews and buying guides.</p>
<ul>
{entry}<!-- POSTS -->
</ul>
</body>
</html>"""

    index_path.write_text(content, encoding='utf-8')


def mark_used(keyword):
    used_file = Path('logs/used_keywords.txt')
    used_file.parent.mkdir(exist_ok=True)
    with open(used_file, 'a') as f:
        f.write(keyword + '\n')


def main():
    log.info("=== NicheFlow generation run started ===")

    available, used = load_keywords()
    row = pick_keyword(available)
    keyword = row['keyword']
    slug = slugify(keyword)

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
        print(f"Generated: {filepath}")

    except Exception as e:
        log.error(f"Generation failed for '{keyword}': {e}")
        raise


if __name__ == '__main__':
    main()
