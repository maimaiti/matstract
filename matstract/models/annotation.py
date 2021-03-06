import datetime
import nltk
from nltk.chunk.util import ChunkScore
from matstract.models.word_embeddings import EmbeddingEngine


class Annotation:
    def __init__(self, doi, user=None):
        self.doi = doi
        self.user = user
        self.date = datetime.datetime.now().isoformat()
        self.authenticated = False

    def authenticate(self, db):
        """Authenticate the user"""
        if self.user is not None and db.user_keys.find({"user_key": self.user}).count() > 0:
            self.authenticated = True
        return self.authenticated


class MacroAnnotation(Annotation):
    """
    Used to annotate
    relevant:   true or false
    type:       experiment, theory or both
    flag:       strange, incomplete abstracts
    """
    def __init__(self, doi, relevant, flag, abs_type, user=None):
        Annotation.__init__(self, doi, user)
        self.relevant = relevant
        self.flag = flag
        self.abs_type = abs_type


class TokenAnnotation(Annotation):
    """
    Used to annotate each token of the abstract for named entity recognition
    and information retrieval
    tokens: every word in the text is considered a token. It is a dictionary with
            an annotation label, start/end and content (the actual token text)
    labels: a list of token labels that was used for that annotation
    tags:   a list of tags for the whole abstract, if one wants to add any extra info
    """
    def __init__(self, doi=None, tokens=None, labels=None, tags=None, user=None, annotation=None):
        if annotation is not None:
            self.from_dict(annotation)
        else:
            Annotation.__init__(self, doi, user)
            self.tokens = tokens
            self.labels = labels
            self.tags = tags

    def from_dict(self, dictionary):
        """Builds a TokenAnnotation object from a dictionary"""
        Annotation.__init__(self, dictionary["doi"], dictionary["user"])
        self.tokens = dictionary["tokens"]
        self.labels = dictionary["labels"]
        self.tags = dictionary["tags"]

    def to_iob(self, phrases=False):
        """
        Converts the annotation object to CoNNL IOB annotation text string, with
        each row corresponding to a single token.
        :param phrases: if set to true, will run the phraser of the most recent word2vec model and convert tokens
        to phrases. Only useful if using these particular word embeddings as features
        :return: the string in CoNNL IOB annotation format
        """
        iob = []
        iob_str = []
        tokens = self.phrase_tokens() if phrases else self.tokens
        for row_idx, tokenRow in enumerate(tokens):
            iob.append([])
            for idx, token in enumerate(tokenRow):
                if token["annotation"] is None:
                    label = "O"
                elif idx == 0 or tokenRow[idx - 1]["annotation"] != token["annotation"]:
                    label = "B-" + token["annotation"]
                else:
                    label = "I-" + token["annotation"]
                iob[row_idx].append((token["text"], token["pos"], label))
                iob_str.append(token["text"] + " " + token["pos"] + " " + label + "\n")
            iob_str.append("\n")
        return iob, "".join(iob_str)

    def to_agr_list(self):
        """
        Returns a list of tuples to be used with nltk.metrics.agreement
        :return: list of tuples ("annotator", "tokenId", "label")
        """
        counter = 0
        aggr_list = []
        for tokenRow in self.tokens:
            for token in tokenRow:
                aggr_tuple = (self.user, counter, token["annotation"])
                aggr_list.append(aggr_tuple)
                counter += 1
        return aggr_list

    def to_ann_list(self):
        """
        An ordered list of annotation labels, that can be used for building a confusion matrix
        :return:
        """
        ann_list = []
        for tokenRow in self.tokens:
            for token in tokenRow:
                ann_list.append(str(token["annotation"]))
        return ann_list

    def compare(self, ann2, labels=None):
        """
        Estimates the accuracy of annotation/prediction assuming the current
        Annotation is the gold standard
        :return: NLTK ChinkScore Object
        """
        if labels is None:
            labels = tuple(value for value in self.labels if value in ann2.labels)
        self_nltk = nltk.chunk.conllstr2tree(self.to_iob()[1], chunk_types=labels)
        ann2_nltk = nltk.chunk.conllstr2tree(ann2.to_iob()[1], chunk_types=labels)

        chunk_score = ChunkScore()
        chunk_score.score(self_nltk, ann2_nltk)

        return chunk_score

    def group_and_process(self):
        def merge_tokens(toks):
            """
            Merges a list of tokens into one token if the annotations agree
            :param toks: a list of tokens
            :return: a new merged token
            """
            new_tok = dict()
            for key in toks[0].keys():
                new_tok[key] = toks[0][key]
            if type(new_tok["text"]) is not list:
                new_tok["text"] = [new_tok["text"]]
                new_tok["pos"] = [new_tok["pos"]]
                new_tok["id"] = [new_tok["id"]]
            for tok in toks[1:]:
                if tok["annotation"] != toks[0]["annotation"]:
                    raise ValueError('Tried to merge tokens with different annotations!')
                new_tok["end"] = max(tok["end"], new_tok["end"])
                new_tok["start"] = min(tok["start"], new_tok["start"])

                new_tok["text"] += [tok["text"]]
                new_tok["pos"] += [tok["pos"]]
                new_tok["id"] += [tok["id"]]
            return new_tok

        new_toks = []
        for row_idx, tokenRow in enumerate(self.tokens):
            new_toks.append([])
            for idx, token in enumerate(tokenRow):
                if len(new_toks[row_idx]) == 0:
                    new_toks[row_idx].append(token)
                elif token["annotation"] == new_toks[row_idx][-1]["annotation"]:
                    new_toks[row_idx][-1] = merge_tokens([new_toks[row_idx][-1], token])
                else:
                    new_toks[row_idx].append(token)
        return new_toks

    def phrase_tokens(self):
        def ungroup_tokens(toks):
            new_toks = []
            for t_r in toks:
                new_toks.append([])
                for t in t_r:
                    for ii, elem in enumerate(t["text"]):
                        new_toks[-1].append({"text": elem,
                                             "pos": t["pos"][ii],
                                             "annotation": t["annotation"]})
            return new_toks

        grouped_toks = self.group_and_process()
        ee = EmbeddingEngine()
        for row_idx, tokenRow in enumerate(grouped_toks):
            for idx, token in enumerate(tokenRow):
                grouped_toks[row_idx][idx]["text"] = ee.phraser[ee.dp.process_sentence(
                    token["text"] if type(token["text"]) is list else [token["text"]])]
                new_pos_tags = []
                for i, tok in enumerate(grouped_toks[row_idx][idx]["text"]):
                    p_l = len(new_pos_tags)
                    if "_" not in tok:
                        new_pos_tags.append(grouped_toks[row_idx][idx]["pos"][p_l])
                    else:
                        new_pos_tags.append("_".join([
                            grouped_toks[row_idx][idx]["pos"][k] for k in range(p_l, p_l+len(tok.split("_")))
                        ]))
                grouped_toks[row_idx][idx]["pos"] = new_pos_tags
        return ungroup_tokens(grouped_toks)