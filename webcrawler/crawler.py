import re
import logging
from collections import OrderedDict
from functools import reduce

from bs4 import BeautifulSoup

class TranscriptCrawler:

    def __init__(self):
        self.logger = logging.getLogger('crawler')
        log_formatter = logging.Formatter("%(asctime)s %(name)s.%(funcName)s [%(levelname)s] %(message)s")

        handler = logging.FileHandler('crawler.log')
        handler.setFormatter(log_formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(level=logging.INFO)

    def clean_text(self, text):
        default_replace_strings = [
            ('`', '\''),
            ('“', '\"'),
            ('”', '\"'),
        ]

        default_clean_patterns = [
            r'^\(.*',
            r'^\[.*',
            r'.*CQ-Roll Call.*',
            r'.*(C|c)ontent and (P|p)rogramming.*'
        ]

        speaker_pattern = r'^([A-Z0-9\-\(\),\'"\. ]+: )*'

        if hasattr(self, 'replace_strings'):
            replace_strings = self.replace_strings + default_replace_strings
        else:
            replace_strings = default_replace_strings

        if hasattr(self, 'clean_patterns'):
            clean_patterns = self.clean_patterns + default_clean_patterns
        else:
            clean_patterns = default_clean_patterns

        out_text = []

        # common broken html fixes
        text = re.sub(r'<p><Copy: .*</p>', '', text)
        text = re.sub(r'<br />', '</p><p>', text)
        text = re.sub(r'<br>', '</p><p>', text)

        soup = BeautifulSoup(text, 'html.parser')

        line = ""
        current_speaker = None
        known_speakers = OrderedDict()
        speaker_count = 0
        self.logger.debug('*' * 10)
        for graf in soup.select(self.transcript_graf_selector):
            graf_text = graf.getText().strip()
            
            cleaned_text = reduce(lambda txt, pair: txt.replace(pair[0], pair[1]), replace_strings, graf_text)
            cleaned_text = reduce(lambda txt, pattern: re.sub(pattern, '', txt), clean_patterns, cleaned_text)
            cleaned_text = cleaned_text.strip()

            if(cleaned_text):
                speaker_searcher = re.search(speaker_pattern, cleaned_text)
                if speaker_searcher and speaker_searcher.group(1):
                    speaker = speaker_searcher.group(1).strip()

                    if speaker not in known_speakers.keys():
                        cleaned_short_name = re.sub(r'[A-Z]+\.', '', speaker).strip().replace(':', '').strip()

                        speaker_full = None
                        for n in reversed(known_speakers):
                            self.logger.debug("looking for `%s` in `%s`" % (cleaned_short_name, known_speakers[n]))
                            if cleaned_short_name in known_speakers[n]:
                                speaker_full = known_speakers[n]
                                self.logger.debug("matched")
                                break

                        if speaker_full:
                            self.logger.debug("added new match mapping: %s => %s" % (speaker, speaker_full))
                            known_speakers[speaker] = speaker_full
                            speaker = speaker_full
                        else:
                            self.logger.debug("no match, adding identity mapping: %s => %s" % (speaker, speaker))
                            known_speakers[speaker] = speaker
                    else:
                        self.logger.debug("found a known match: %s => %s" % (speaker, known_speakers[speaker]))
                        speaker = known_speakers[speaker]

                    if current_speaker:
                        out_text.append( (current_speaker, line) )
                        speaker_count = speaker_count + 1

                    current_speaker = speaker
                    cleaned_text = re.sub(speaker_pattern, '', cleaned_text).strip()
                    line = cleaned_text
                else:
                    line = line + " " + cleaned_text

        if line:
            out_text.append( (current_speaker, line) )
            speaker_count = speaker_count + 1

        self.logger.debug('-' * 10)
        for n in reversed(known_speakers):
            self.logger.debug("%s => %s" % (n, known_speakers[n]))
        self.logger.debug("%s speakers" % speaker_count)
        self.logger.debug('*' * 10)
        self.logger.debug('\n\n')

        return out_text

    def get_cleaned_text(self):
        fetched = []
        while True:
            if not fetched:
                try:
                    fetched = self.fetch_post_batch()
                    if not fetched:
                        raise RuntimeError('No more posts to fetch')
                except BaseException as e:
                    print(e)
                    break
            yield fetched.pop(0)