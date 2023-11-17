#%%
import re
from pathlib import Path

import nltk
from nltk.corpus import wordnet, stopwords
from fdparsedoc import DocText

from nltk.corpus.reader.wordnet import Synset
nltk.download('wordnet')

STOP_WORDS = set(stopwords.words('english'))

PUNC_PAT = r"[^\w\s]+"
PUNC_PAT_NOHYPH = r"[^\w\s[^-]]+"
RE_SPEC_PAT = r"[-[\]{}()*+?.,\\^$|#\s]"
SPLIT_PAT = r"(\s+)"

PUNC_REQ = re.compile(PUNC_PAT)
PUNC_REQ_NOHYPH = re.compile(PUNC_PAT_NOHYPH)
RE_SPEC_REQ = re.compile(RE_SPEC_PAT)

RE_SPEC_REPFUN = lambda x: "\\" + x.group(0)

#%%
def check_word_grammar(pos, item, combinations, stop_words=STOP_WORDS):
    item_clean = re.sub(r'[\n.,()]', '', item.lower())
    item_clean = item_clean.replace("’s", '')
    if item_clean not in stop_words:
        synsets = wordnet.synsets(item_clean)
        if synsets and len(item_clean) > 1:
            pass
        else:
            ## check if it does not contain numbers/digits
            pattern = r'\d'
            if not re.search(pattern, item_clean):
                complete = combinations[pos] + combinations[pos+1]
                synsets = wordnet.synsets(complete)
                if synsets:
                    combinations[pos] = complete
                    combinations.pop(pos+1)
                    print(complete, pos)
                else:
                    complete = combinations[pos-1] + combinations[pos]
                    synsets = wordnet.synsets(complete)
                    if synsets:
                        combinations[pos] = complete
                        combinations.pop(pos-1)
                        print(complete, pos)
        return item

#%%
datapath_folder = Path.home() / (
    r"Fab Inc Dropbox/Fab Inc Other/_Organised bank"
    r"/Resources/IEFG/Donors_Partners/firelightfoundation"
)
pdf_docs_path  = datapath_folder.glob('*.pdf')
pdf_docs = []
for doc in pdf_docs_path:
    pdf_docs.append(doc)
doc = DocText.from_file(pdf_docs[15])
doc = DocText.from_file(r"D:\Fab_data\web_data\Global-Proficiency-Framework-Reading.pdf")
chunks = list(doc.chunks(chunksize=4000))

print("loaded")

#%% test performance of synsets
# #! %%timeit
testword = "hello"
wordnet.synsets(testword)

#%% test performance of re.sub
# #! %%timeit
testword = "hel\t\t-o,,''"
re.sub(PUNC_PAT, "", testword)
req = re.compile(PUNC_PAT)

#%%
# # ! %%timeit
req = re.compile(PUNC_PAT)
#%%
# #! %%timeit
req.sub("", testword)

#%%
text = " ".join(doc.pages)
words = text.split()

#%%
def cleanword(word, req=PUNC_REQ):
    return req.sub("", word).lower()

def isword(
    word,
    req=PUNC_REQ,
    stop_words=STOP_WORDS,
    clean=True,
    exclude_abrev=False
):
    if clean:
        word = cleanword(word, req)
    sww = stop_word_words(stop_words)
    syns = wordnet.synsets(word)
    isword = word in sww or any(syns)
    isabrev = len(word) < 3 and word not in sww and any(
        word != ss.name().split(".")[0] for ss in syns
    )
    if exclude_abrev:
        isword = isword and not isabrev
    return isword

def stop_word_words(stop_words=STOP_WORDS):
    return [
        word for word in stop_words if (
            (len(word) > 1 or word in ["a", "i"])
            and word[-1] != "'"       
        )
    ]

def ispunc(word, req=PUNC_REQ, exclude_hyph=False):
    ret = req.match(word) is not None and len(cleanword(word)) == 0
    if exclude_hyph:
        ret = ret and word not in ["-"]
    return ret

req = re.compile(PUNC_PAT)

#%%
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
        # print(currword)
    elif "\n" in currspace:
        print(currword)
    if currword == "document.":
        print(currword)
    candwordl.append(currword)
    candspacel.append(currspace)
    candword = "".join(candwordl)
    if (
        not isword(currword, exclude_abrev=True)
        and isword(candword, req=PUNC_REQ_NOHYPH, exclude_abrev=True)
    ):
        complete += candword + candspacel[-1]
        candwordl = []
        candspacel = []
    elif isword("".join(candwordl[:-1])):
        complete += "".join(candwordl[:-1]) + candspacel[-2]
        candwordl = [candwordl[-1]]
        candspacel = [candspacel[-1]]
    elif (isword(currword) or ispunc(currword, exclude_hyph=True)) and len(candwordl) > 1:
        complete += "".join(cw+cs for cw, cs in zip(candwordl, candspacel))
        candwordl = []
        candspacel = []
        
#%%
wordsorig = set(text.split())
wordsnew = set(complete.split())
droppedwords = wordsorig - wordsnew
addedwords = wordsnew - wordsorig

for word in sorted(addedwords)[:10]:
    if not isword(word):
        continue
    specword = RE_SPEC_REQ.sub(RE_SPEC_REPFUN, word)
    print("------\n------")
    oldmatches = list(re.finditer(specword, text))
    newmatches = list(re.finditer(specword, complete))
    print(len(oldmatches))
    print(len(newmatches))
    # for omtch, nmtch in zip(oldmatches, newmatches):
    #     ospan = omtch.span(0)
    #     nspan = nmtch.span(0)
    #     ocontext = text[ospan[0]-15:ospan[1]+14]
    #     ncontext = complete[nspan[0]-15:nspan[1]+14]
    #     print(f"{word}:\n\t{ocontext}\n\t{ncontext}")
    specword = r"\s+" + specword + r"\s+"
    newmatches = list(re.finditer(specword, complete))
    print("------")
    for nmtch in newmatches:
        nspan = nmtch.span(0)
        ncontext = complete[nspan[0]-15:nspan[1]+14]
        print(f"{word}:{ncontext}")

# sentence 1 - sentence 2
# sentence 1-sentence 2
