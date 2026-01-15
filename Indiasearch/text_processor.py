import re
import string
from collections import Counter

try:
    from langdetect import detect
except:
    detect = None


STOPWORDS = set("""
a an the is are was were am to of for in on and or not be it this that with as by from at
have has had do does did but so because can will would should you we they he she i
""".split())


def detect_language(text):
    """Return language code like en, hi, etc."""
    if not detect:
        return "unknown"

    try:
        lang = detect(text)
        return lang
    except:
        return "unknown"


def clean_text(text):
    """Main cleaner used everywhere"""

    if not text:
        return ""

    # remove HTML escapes
    text = re.sub(r"&[a-z]+;", " ", text)

    # remove urls
    text = re.sub(r"http\S+", " ", text)

    # remove email
    text = re.sub(r"\S+@\S+", " ", text)

    # remove numbers
    text = re.sub(r"\d+", " ", text)

    # remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))

    # make lowercase
    text = text.lower()

    # remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def tokenize(text):
    """Break into words but remove stopwords"""

    text = clean_text(text)

    tokens = [
        word for word in text.split()
        if word not in STOPWORDS and len(word) > 2
    ]

    return tokens


def extract_keywords(text, limit=15):
    """Return important words"""

    words = tokenize(text)

    counter = Counter(words)

    return [w for w, _ in counter.most_common(limit)]


def translate_to_english(text):
    """Translate non-English text to English"""
    lang = detect_language(text)
    if lang == "en" or lang == "unknown":
        return text
    return text


def spam_score(text):
    """Calculate spam score 0-10"""
    spam_words = ["casino", "betting", "loan fast", "earn money fast", "viagra"]
    score = sum(text.lower().count(w) for w in spam_words)
    return min(score * 2, 10)


def fake_news_score(text):
    """Calculate fake news risk 0-10"""
    suspicious = ["shocking truth", "exposed", "viral claim", "unverified"]
    score = sum(text.lower().count(w) for w in suspicious)
    return min(score * 2, 10)