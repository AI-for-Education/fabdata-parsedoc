import re

import nltk
from nltk.corpus import wordnet, stopwords

nltk.download('wordnet', quiet=True)
nltk.download("stopwords", quiet=True)

STOP_WORDS = set(stopwords.words('english'))

PUNC_PAT = r"[^\w\s]+"
PUNC_PAT_NOHYPH = r"[^\w\s[^-]]+"
RE_SPEC_PAT = r"[-[\]{}()*+?.,\\^$|#\s]"
SPLIT_PAT = r"(\s+)"

PUNC_REQ = re.compile(PUNC_PAT)
PUNC_REQ_NOHYPH = re.compile(PUNC_PAT_NOHYPH)
RE_SPEC_REQ = re.compile(RE_SPEC_PAT)

RE_SPEC_REPFUN = lambda x: "\\" + x.group(0)


def clean_text(text):
    reqsplit = re.compile(SPLIT_PAT)
    splittext = reqsplit.split(text)
    candwordl = []
    candspacel = []
    complete = ""
    for i in range(0, len(splittext), 2):
        if len(splittext[i:i+2]) < 2:
            complete += splittext[i]
            continue
        currword, currspace = splittext[i:i+2]
        if "\n" in currspace and currword[-1] != ".":
            currspace = " "
        candwordl.append(currword)
        candspacel.append(currspace)
        candword = "".join(candwordl)
        if (
            not _isword(currword, exclude_abrev=True)
            and _isword(candword, req=PUNC_REQ_NOHYPH, exclude_abrev=True)
        ):
            complete += candword + candspacel[-1]
            candwordl = []
            candspacel = []
        elif _isword("".join(candwordl[:-1])):
            complete += "".join(candwordl[:-1]) + candspacel[-2]
            candwordl = [candwordl[-1]]
            candspacel = [candspacel[-1]]
        elif (_isword(currword) or _ispunc(currword, exclude_hyph=True)) and len(candwordl) > 1:
            complete += "".join(cw+cs for cw, cs in zip(candwordl, candspacel))
            candwordl = []
            candspacel = []
    return complete


def _cleanword(word, req=PUNC_REQ):
    return req.sub("", word).lower()

def _isword(
    word,
    req=PUNC_REQ,
    stop_words=STOP_WORDS,
    clean=True,
    exclude_abrev=False
):
    if clean:
        word = _cleanword(word, req)
    sww = _stop_word_words(stop_words)
    syns = wordnet.synsets(word)
    isword = word in sww or any(syns)
    isabrev = len(word) < 3 and word not in sww and any(
        word != ss.name().split(".")[0] for ss in syns
    )
    if exclude_abrev:
        isword = isword and not isabrev
    return isword

def _stop_word_words(stop_words=STOP_WORDS):
    return [
        word for word in stop_words if (
            (len(word) > 1 or word in ["a", "i"])
            and word[-1] != "'"       
        )
    ]

def _ispunc(word, req=PUNC_REQ, exclude_hyph=False):
    ret = req.match(word) is not None and len(_cleanword(word)) == 0
    if exclude_hyph:
        ret = ret and word not in ["-"]
    return ret