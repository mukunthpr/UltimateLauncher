import urllib.request
import urllib.parse
import json
import webbrowser
import threading
from plugins.base_plugin import PluginBase, SearchResult


class DictionaryPlugin(PluginBase):
    id = "dictionary"
    name = "Dictionary"
    prefix_alias = "def"

    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()

    def query(self, text: str):
        text_lower = text.strip().lower()
        if not text_lower:
            return []
            
        is_def_prefix = text_lower.startswith("def ") or text_lower.startswith("define ")
        if text_lower.startswith("define "):
            text = text_lower[7:].strip()
        elif text_lower.startswith("def "):
            text = text_lower[4:].strip()

        words = text.split()
        if not text or len(words) > 3:
            return []

        # Return cached result immediately if available
        if text in self._cache:
            if self._cache[text]:
                # Boost cache score if explicit prefix used
                result = self._cache[text][0]
                result.score = 115 + (100 if is_def_prefix else 0)
                return [result]
            return []

        # Kick off background fetch
        self._fetch_async(text, is_def_prefix)
        return []

    def _fetch_async(self, text, is_def_prefix=False):
        def _worker():
            try:
                url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(text)}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 UltimateLauncher'})
                with urllib.request.urlopen(req, timeout=2.0) as res:
                    data = json.loads(res.read().decode('utf-8'))

                if not isinstance(data, list) or not data:
                    return

                entry = data[0]
                word = entry.get('word', text)
                meanings = entry.get('meanings', [])
                if not meanings:
                    return

                first_meaning = meanings[0]
                part_of_speech = first_meaning.get('partOfSpeech', '')
                definitions = first_meaning.get('definitions', [])
                if not definitions:
                    return

                definition = definitions[0].get('definition', '')
                if len(definition) > 90:
                    definition = definition[:90] + '...'

                result = [SearchResult(
                    title=f"{word.capitalize()} ({part_of_speech})",
                    subtitle=definition,
                    score=115 + (100 if is_def_prefix else 0),
                    action=lambda w=word: webbrowser.open(
                        f"https://www.google.com/search?q=define+{urllib.parse.quote(w)}"
                    )
                )]

                with self._lock:
                    self._cache[text] = result
                    if len(self._cache) > 50:
                        del self._cache[next(iter(self._cache))]

            except Exception:
                # Word not found or network error — cache empty list so we don't retry
                with self._lock:
                    self._cache[text] = []

        threading.Thread(target=_worker, daemon=True).start()
