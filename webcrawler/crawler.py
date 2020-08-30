import re
from functools import reduce

from bs4 import BeautifulSoup

class Crawler:

    def clean_text(self, text):
        default_replace_strings = [
            ('`', '\''),
            ('“', '\"'),
            ('”', '\"'),
        ]

        default_clean_patterns = [
            r'^[A-z0-9\-\(\),\'"\. ]+: *',
            r'^\(.*',
            r'^\[.*',
            r'.*CQ-Roll Call.*',
            r'.*(C|c)ontent and (P|p)rogramming.*'
        ]

        if hasattr(self, 'replace_strings'):
            replace_strings = self.replace_strings + default_replace_strings
        else:
            replace_strings = default_replace_strings

        if hasattr(self, 'clean_patterns'):
            clean_patterns = self.clean_patterns + default_clean_patterns
        else:
            clean_patterns = default_clean_patterns

        out_text = ""

        # common broken html fixes
        text = re.sub(r'<p><Copy: .*</p>', '', text)
        text = re.sub(r'<br />', '</p><p>', text)
        text = re.sub(r'<br>', '</p><p>', text)

        soup = BeautifulSoup(text, 'html.parser')
        prev_line = None

        for graf in soup.select(self.transcript_graf_selector):
            graf_text = graf.getText().strip()
            
            cleaned_text = reduce(lambda txt, pair: txt.replace(pair[0], pair[1]), replace_strings, graf_text)
            cleaned_text = reduce(lambda txt, pattern: re.sub(pattern, '', txt), clean_patterns, cleaned_text)

            cleaned_text = cleaned_text.strip()

            if(cleaned_text):
                out_text = out_text + " " + cleaned_text
                prev_line = True
            else:
                if prev_line:
                    out_text = out_text + "\n"
                prev_line = False

        return out_text

    def get_cleaned_text(self):
        fetched = []
        while True:
            if not fetched:
                try:
                    fetched = self.fetch_post_batch()
                    if not fetched:
                        raise RuntimeError('No more posts to fetch')
                except Exception as e:
                    print(e)
                    break
            yield fetched.pop(0)