#%%
from pathlib import Path
import json

from fdparsedoc.parsedoctypes import DocText
from fdparsedoc.utils import general_query
from fdllm import GPTCaller, ClaudeCaller

#%%
jsonin = {
    "inputs:: These are 2 numbers to add": [2, 4]
}

jsonout = {
    "result:: The result of adding the 2 numbers": None
}

#%%
caller = GPTCaller("gpt-4-0314")
response = general_query(jsonin, jsonout, caller=caller)

print(response.to_dict())

#%%
jsonin = {
    "chunks": [
        {"chunk_000": "Some text"},
        {"chunk_001": "Some more text"},
    ]
}

jsonout = {
    "summary:: Summary of all of the chunks": None
}

#%%
caller = GPTCaller("gpt-4-0314")
response = general_query(jsonin, jsonout, caller=caller)

print(response.to_dict())

#%%
datapath = Path(r"D:\Fab_data\web_data\Global-Proficiency-Framework-Reading.pdf")
doc = DocText.from_file(datapath)



def check_sent1(words, sentences):
    cnt = 0
    idx = [None, None]
    for sent in sentences:
        notin = False
        sentwords = sent.split()
        for word in words:
            if word in sentwords:
                idx[0] = idx[-1]
                idx[-1] = sentwords.index(word)
                if idx[0] is not None and idx[0] + 1 != idx[-1]:
                    notin = True
                    break
            else:
                notin = True
                break
        if not notin:
            cnt += 1
    return cnt
                
def check_sent2(word, sentences):
    cnt = 0
    for sent in sentences:
        usesent = (
            " ".join(sent.split())
            .replace(".", "")
            .replace(")", "")
            .replace("(", "")
        )
        cnt += word in usesent
    return cnt
                
    final = [all([w in x for w in word]) for x in sentences]
    return sum(final)

def check_sent2(word, sentences):
    final = [word in x for x in sentences]
    return sum(final)

