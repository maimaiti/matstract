from chemdataextractor.doc import Paragraph
from chemdataextractor import Document
from matstract.utils import open_db_connection


class AnnotationBuilder:
    _db = None

    def __init__(self):
        self._db = open_db_connection(local=True)

    @staticmethod
    def get_tokens(paragraph):
        # getting initial annotation
        cde_cem_starts = [cem.start for cem in Document(paragraph).cems]

        # getting all tokens
        all_tokens = Paragraph(paragraph).tokens
        # building the array for annotation
        tokens = []
        for idx, sentence in enumerate(all_tokens):
            tokens.append([])
            for elem in sentence:
                tokens[idx].append({
                    "id": "token-" + str(elem.start) + "-" + str(elem.end),
                    "annotation": ('material' if elem.start in cde_cem_starts else None),
                    "text": elem.text,
                    "start": elem.start,
                    "end": elem.end
                })
        return tokens

    @staticmethod
    def prepare_annotation(doi, tokens, macro, username):
        annotation = {'doi': doi,
                      'tokens': tokens,
                      'tags': macro['tags'],
                      'type': macro['type'],
                      'category': macro['category'],
                      'user': username}
        return annotation

    def insert_annotation(self, annotation):
        self._db.annotations.insert_one(annotation)

    def update_tags(self, tags):
        current_tags = self._db.abstract_tags.find({})
        for tag in tags:
            if tags not in current_tags:
                try:
                    self._db.abstract_tags.insert_one(self.prepare_tag(tag))
                except Exception as e:
                    print(e)

    @staticmethod
    def prepare_tag(tag):
        return {"tag": tag}
