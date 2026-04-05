import urllib.request
import urllib.parse
import re
import webbrowser
import json
import threading
from plugins.base_plugin import PluginBase, SearchResult


def strip_html(text):
    return re.sub(r'<[^>]+>', '', text).strip()


class WebSearchPlugin(PluginBase):
    id = "web_search"
    name = "Live Web Search"

    def __init__(self):
        # Cache: stores (query_text -> list[SearchResult]) for the last successful fetch
        self._cache = {}
        self._pending_query = None
        self._lock = threading.Lock()

    def query(self, text: str):
        text = text.strip()
        if not text:
            return []

        text_lower = text.lower()
        is_web_prefix = text_lower.startswith("web ") or text_lower.startswith("search ") or text_lower.startswith("g ")
        
        if text_lower.startswith("search "):
            text = text[7:].strip()
        elif text_lower.startswith("web "):
            text = text[4:].strip()
        elif text_lower.startswith("g "):
            text = text[2:].strip()
            
        if not text:
            return []

        results = []

        # 1. Immediately return cached real results if available for this query
        if text in self._cache:
            for item in self._cache[text]:
                if is_web_prefix:
                    item.score = max(item.score, 200) # Boost cached items natively
            results.extend(self._cache[text])

        # Start background fetch for real results if not cached
        if text not in self._cache:
            self._fetch_async(text, is_web_prefix)

        # 2. Always add quick Google Suggestions synchronously (very fast, ~100ms)
        suggestions = self._fetch_suggestions(text)
        suggestion_score_base = 88

        for idx, s in enumerate(suggestions[:3]):
            if s.lower() == text.lower():
                continue
            results.append(SearchResult(
                title=s,
                subtitle="Google Suggestion",
                score=suggestion_score_base - idx + (100 if is_web_prefix else 0),
                action=lambda q=s: webbrowser.open(
                    f"https://www.google.com/search?q={urllib.parse.quote(q)}"
                )
            ))

        # 3. Generic fallback at the very bottom
        results.append(SearchResult(
            title=f"Search Google for '{text}'",
            subtitle="Web Search",
            score=80 + (100 if is_web_prefix else 0),
            action=lambda q=text: webbrowser.open(
                f"https://www.google.com/search?q={urllib.parse.quote(q)}"
            )
        ))

        return results

    def _fetch_suggestions(self, text):
        try:
            url = f"http://suggestqueries.google.com/complete/search?client=chrome&q={urllib.parse.quote(text)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=0.5) as res:
                return json.loads(res.read().decode('utf-8'))[1]
        except Exception:
            return []

    def _fetch_async(self, text, is_web_prefix=False):
        """Fire-and-forget background thread to fetch DDG results and populate cache."""
        def _worker():
            try:
                data = urllib.parse.urlencode({'q': text}).encode()
                req = urllib.request.Request(
                    'https://lite.duckduckgo.com/lite/',
                    data=data,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                )
                html = urllib.request.urlopen(req, timeout=3.0).read().decode('utf-8')
                pairs = re.findall(r'<a rel="nofollow" href="([^"]*)"[^>]*>(.*?)</a>', html)

                real_results = []
                for idx, (url, title_raw) in enumerate(pairs[:5]):
                    clean_title = strip_html(title_raw)
                    if not clean_title:
                        continue
                    domain_match = re.match(r'https?://([^/]+)', url)
                    domain = domain_match.group(1).replace('www.', '') if domain_match else ''

                    real_results.append(SearchResult(
                        title=clean_title,
                        subtitle=domain,
                        score=110 - idx + (150 if is_web_prefix else 0),
                        action=lambda u=url: webbrowser.open(u),
                        context_actions=[
                            {"name": "Copy URL", "action": lambda u=url: self._copy_url(u)}
                        ]
                    ))

                if real_results:
                    with self._lock:
                        self._cache[text] = real_results
                    # Limit cache size
                    if len(self._cache) > 30:
                        oldest = next(iter(self._cache))
                        del self._cache[oldest]
            except Exception:
                pass

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _copy_url(self, url):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.clipboard().setText(url)
