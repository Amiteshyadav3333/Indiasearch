from duckduckgo_search import DDGS
import json

def test():
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            # Try with a specific region
            results = list(ddgs.images("India", max_results=5, region="in-en", safe_search="off"))
            print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
