#!/usr/bin/env python3
import os
import json
from datetime import datetime
from flask import Flask, render_template, abort
import requests

app = Flask(__name__)

API_KEY = os.environ.get("WORDNIK_API_KEY")
CACHE_PATH = "cache.json"
WORDNIK_BASE = "https://api.wordnik.com/v4"

def load_cache():
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_cache(data):
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def fetch_word_of_the_day(date_str):
    if not API_KEY:
        raise RuntimeError("WORDNIK_API_KEY not set")
    url = f"{WORDNIK_BASE}/words.json/wordOfTheDay"
    params = {"date": date_str, "api_key": API_KEY}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code == 200:
        return r.json()
    # If Wordnik doesn't have it for some reason, return None
    return None

def fetch_definitions(word):
    url = f"{WORDNIK_BASE}/word.json/{word}/definitions"
    params = {
        "limit": 5,
        "includeRelated": "false",
        "useCanonical": "false",
        "includeTags": "false",
        "api_key": API_KEY,
    }
    r = requests.get(url, params=params, timeout=10)
    if r.status_code == 200:
        return r.json()
    return []

def fetch_pronunciations(word):
    url = f"{WORDNIK_BASE}/word.json/{word}/pronunciations"
    params = {"useCanonical": "false", "limit": 50, "api_key": API_KEY}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code == 200:
        return r.json()
    return []

def fetch_example(word):
    url = f"{WORDNIK_BASE}/word.json/{word}/topExample"
    params = {"useCanonical": "false", "api_key": API_KEY}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code == 200:
        return r.json()
    return None

@app.route("/")
def index():
    today = datetime.utcnow().date().isoformat()
    cache = load_cache()

    # Use cache if we already fetched today's word
    if cache.get("date") == today and cache.get("word"):
        data = cache
    else:
        if not API_KEY:
            return render_template("error.html", message="WORDNIK_API_KEY is not set in environment.")
        # Try wordOfTheDay endpoint
        wotd = fetch_word_of_the_day(today)
        if wotd and wotd.get("word"):
            word = wotd.get("word")
            definitions = wotd.get("definitions") or fetch_definitions(word)
            pronunciations = wotd.get("pronunciations") or fetch_pronunciations(word)
            example = (wotd.get("examples") or [])
            example_text = example[0].get("text") if example else None
            note = wotd.get("note")
            data = {
                "date": today,
                "word": word,
                "definitions": definitions,
                "pronunciations": pronunciations,
                "example": example_text,
                "note": note,
                "source": "Wordnik wordOfTheDay",
            }
        else:
            # Fallback: choose a random word and fetch info
            rnd = requests.get(f"{WORDNIK_BASE}/words.json/randomWord", params={"api_key": API_KEY}, timeout=10)
            if rnd.status_code != 200:
                abort(502, description="Could not fetch word from Wordnik.")
            word = rnd.json().get("word")
            definitions = fetch_definitions(word)
            pronunciations = fetch_pronunciations(word)
            example_obj = fetch_example(word)
            example_text = example_obj.get("text") if example_obj else None
            data = {
                "date": today,
                "word": word,
                "definitions": definitions,
                "pronunciations": pronunciations,
                "example": example_text,
                "note": None,
                "source": "Wordnik randomWord (fallback)",
            }

        cache = data
        save_cache(cache)

    # Choose display-friendly pronunciation (first valid)
    pron = None
    for p in cache.get("pronunciations") or []:
        if p.get("raw"):
            pron = p.get("raw")
            break

    # Flatten definitions into simple list
    defs = []
    for d in cache.get("definitions") or []:
        text = d.get("text") or d.get("textRaw") or d.get("definition")
        part = d.get("partOfSpeech") or d.get("partOfSpeech")
        defs.append({"text": text, "partOfSpeech": part})

    return render_template(
        "index.html",
        date=cache.get("date"),
        word=cache.get("word"),
        pronunciations=cache.get("pronunciations"),
        pronunciation_display=pron,
        definitions=defs,
        example=cache.get("example"),
        note=cache.get("note"),
        source=cache.get("source"),
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))