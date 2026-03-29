import unittest
from crawler import Crawler
from search import make_snippet, clean_text

class TestIndiasearchUtils(unittest.TestCase):
    
    def test_crawler_valid_link(self):
        # Valid HTML links
        self.assertTrue(Crawler.valid_link("https://example.com/page.html"))
        self.assertTrue(Crawler.valid_link("https://example.com/about/team"))
        
        # Invalid Media and File Links
        self.assertFalse(Crawler.valid_link("https://example.com/image.jpg"))
        self.assertFalse(Crawler.valid_link("https://example.com/report.pdf"))
        self.assertFalse(Crawler.valid_link("https://example.com/song.mp3"))
        
        # Auth Routes
        self.assertFalse(Crawler.valid_link("https://example.com/login"))
        self.assertFalse(Crawler.valid_link("https://example.com/signup"))

    def test_clean_text(self):
        dirty_text = "  This   is \n some dirty   text. \t  "
        cleaned = clean_text(dirty_text)
        self.assertEqual(cleaned, "This is some dirty text.")
        
    def test_search_snippet_generator(self):
        content = "The quick brown fox jumps over the lazy dog. The Python programming language is incredibly versatile and powerful."
        
        # Standard query snippet extraction
        snippet_python = make_snippet(content, "python")
        self.assertIn("...", snippet_python)
        self.assertIn("Python", snippet_python)
        
        # Fallback if text not found exactly
        snippet_ruby = make_snippet(content, "ruby")
        self.assertIn("The quick brown fox", snippet_ruby)
        self.assertTrue(snippet_ruby.endswith("..."))

if __name__ == "__main__":
    unittest.main()
