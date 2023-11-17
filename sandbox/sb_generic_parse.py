#%%
import copy
import os

from pathlib import Path
import json
from tqdm import tqdm
from datetime import datetime

from fdllm import GPTCaller, ClaudeCaller
from fdllm.llmtypes import LLMMessage
from tairet.services.chunks import get_text_chunks

HERE = Path(__file__).parent
logdir = HERE / "logs"
logdir.mkdir(exist_ok=True, parents=True)
logdir_pyr = HERE / "logs_pyr"
logdir_pyr.mkdir(exist_ok=True, parents=True)

CHUNK_PROPERTIES = ["summary", "key_words"]
TEMPERATURE = 0
# MAX_TOKENS = 2000

#%%
format = {
    "sections": [
        {
            "theme": "Subject Description",
            "content:: Raw text": None,
        },
        {
            "theme": "Rationale for Inclusion",
            "content:: Raw text": None,
        },
        {
            "theme": "Learning Outcomes",
            "content:: Raw text": None,
        },
        {
            "theme": "Content (Themes / Topics)",
            "content:: Raw text": None,
        },
        {
            "theme": "Structure of the Syllabus",
            # "content": {
            #     "SSS1": [
            #         {"Term1": [{"heading:: If applicable": None, "Full text": None}]},
            #         {"Term2": [{"heading:: If applicable": None, "Full text": None}]},
            #         {"Term3": [{"heading:: If applicable": None, "Full text": None}]},
            #     ],
            #     "SSS2": [
            #         {"Term1": [{"heading:: If applicable": None, "Full text": None}]},
            #         {"Term2": [{"heading:: If applicable": None, "Full text": None}]},
            #         {"Term3": [{"heading:: If applicable": None, "Full text": None}]},
            #     ],
            #     "SSS3": [
            #         {"Term1": [{"heading:: If applicable": None, "Full text": None}]},
            #         {"Term2": [{"heading:: If applicable": None, "Full text": None}]},
            #         {"Term3": [{"heading:: If applicable": None, "Full text": None}]},
            #     ],
            # },
            "content:: Raw text": None,
        },
        {
            "theme": "Teaching Syllabus",
            # "content": {
            #     "Topic/Theme/Unit": [],
            #     "Learning outcomes": [],
            #     "Teaching methods": [],
            #     "Resources": [],
            #     "Assessment of learning outcomes": [],
            # },
            "content:: Raw text": None,
        },
    ]
}


# headings = {
#     "text": {
#         "description": {"Full text": None},
#         "headings": [
#             "Subject Description",
#             "Rationale for Inclusion",
#             "Learning Outcomes",
#             "Content (Themes / Topics)",
#             ]
#     },
#     "table": {
#         "description": {
#             "headers": [],
#             "rows": [{"index": None, "Full text": None}]
#         },
#         "headings": [
#             "Structure of the Syllabus",
#             "Teaching Syllabus"
#         ]
#     },        
# }

# format = {
#         ctype: {
#             "sections": [
#                 {
#                     "heading": heading,
#                     f"content": cval["description"],
#                     "completed": False,
#                 }
#                 for heading in cval["headings"]
#             ]
#         }
#         for ctype, cval in headings.items()
# }

#%%
caller = GPTCaller("gpt-4")
# caller = ClaudeCaller("claude-v1-100k")

#%%
def gen_jsonin(next_chunk, i):
    full = {f"chunk_{i :03d}": next_chunk}
    return full

def gen_message(jsonin, jsonout):
    return LLMMessage(
        Role="system",
        Message=(
            "Given the values in JSON1, fill in the empty values in JSON2:"
            f"\n\nJSON1:\n{json.dumps(jsonin, indent=4)}"
            f"\n\nJSON2:\n{json.dumps(jsonout, indent=4)}"
            "\n\nExpand any lists where necessary. Only return the raw json."
        )
    )

def gen_message2(jsonin, jsonout):
    return LLMMessage(
        Role="system",
        Message=(
            "Given the partial document in JSON1, fill in the empty section headings in JSON2:"
            f"\n\nJSON1:\n{json.dumps(jsonin, indent=4)}"
            f"\n\nJSON2:\n{json.dumps(jsonout, indent=4)}"
            "\n\nExpand any lists where necessary. Only return the raw json."
        )
    )

def clean_keys(d):
    if not isinstance(d, dict):
        return d
    out = d.copy()
    for key in d:
        usekey = key.split("::")[0]
        useval = out.pop(key)
        if isinstance(useval, dict):
            out[usekey] = clean_keys(useval)
        elif isinstance(useval, list):
            out[usekey] = [clean_keys(uv) for uv in useval]
        else:
            out[usekey] = useval
    return out

def deepmerge(d1, d2):
    out = d1.copy()
    for key, val2 in d2.items():
        if key in out:
            val1 = d1[key]
            if isinstance(val1, dict) and isinstance(val2, dict):
                out[key] = deepmerge(val1, val2)
            elif isinstance(val1, list) and isinstance(val2, list):
                out[key] = [*val1, *val2]
            else:
                out[key] = val2
        else:
            out[key] = val2
    return out
        
def trim_nonjson(text):
    pre, *post = text.split("{")
    text = "{".join(["", *post])
    *pre, post = text.split("}")
    text = "}".join([*pre, ""])
    return text

def chunkgen(text, chunksize, nsubchunks):
    chunks = get_text_chunks(text, chunksize//nsubchunks)
    chunkidx = list(range(0, len(chunks)-1, nsubchunks-1))
    for i, sidx in enumerate(tqdm(chunkidx)):
        eidx = min(sidx+nsubchunks, len(chunks)-1)
        chunk = "\n".join(chunks[sidx:eidx])
        yield chunk, i

def process_chunk(next_chunk, current_structure, caller, i):
    jsonin = gen_jsonin(next_chunk, i)
    jsonout = current_structure
    message = gen_message(jsonin, jsonout)
    ntok = len(caller.tokenize([message]))
    maxtok = caller.Token_Window - (ntok + 10)
    print(maxtok)
    if maxtok < 200:
        return None
    else:
        print(message.Message)
        out = caller.call(message, max_tokens=maxtok, temperature=TEMPERATURE)
        print(len(caller.tokenize([out])))
        return out

def process_document(text, caller, format=format, chunksize=200):
    logfile = HERE / "testlog.txt"
    current_structure = format
    
    # nsec = len(clean_keys(current_structure)["sections"])
    # nsubchunks = 7
    # out_structure = {"sections": []}
    # got = []
    # for chunk, i in chunkgen(text, chunksize, nsubchunks):
    #     # old_response = clean_keys(current_structure)
    #     response = process_chunk(chunk, current_structure, caller, i)
    #     if response is None:
    #         return {}
    #     logfile.write_text(response.Message)
    #     respjson = json.loads(trim_nonjson(response.Message))
    #     respjson_clean = clean_keys(respjson)
    #     print(respjson_clean)
    #     completed = len(respjson_clean["sections"]) - 2
    #     for j, sec in enumerate(respjson_clean["sections"]):
    #         if sec["heading"] is None:
    #             completed = j - 2
    #     current_structure["sections"] = [
    #         sec for j, sec in enumerate(respjson["sections"])
    #         if j > completed
    #     ]
    #     out_structure["sections"].extend(respjson_clean["sections"][:completed])
    # out_structure["sections"].extend(respjson_clean["sections"][-1])
    # return out_structure
    response = process_chunk(text, current_structure, caller, 0)
    if response is None:
        return {}
    logfile.write_text(response.Message)
    respjson = clean_keys(json.loads(trim_nonjson(response.Message)))
    current_structure = respjson
    return current_structure
        
#%%
chunksize = 1000
used = 7
files = HERE.parents[1] / "sssc_files.json"
with open(files) as f:
    data = json.load(f)
testtext = data[used]["text"]
data[used]["filename"]

#%%
current_structure = process_document(testtext, caller, format, chunksize),

#%%
# current_structure = process_document(testtext, caller, format["text"])
current_structure = {}
for fmt in format["sections"]:
    current_structure = deepmerge(
        current_structure,
        process_document(
            testtext, caller, {"sections": [fmt]}, chunksize
        ),
    )

#%%


# logfile = (
#     f'log{datetime.utcnow().strftime(r"%Y%m%d%H%M%S")}'
#     f"_chunksize{chunksize :05d}"
#     ".txt"
# )
# logfile = (
#     f'summary_{datetime.utcnow().strftime(r"%Y%m%d%H%M%S")}'
#     f"_chunksize{chunksize :05d}"
#     ".json"
# )
# with open((logdir / logfile), "w") as f:
#     json.dump(
#         {**total_summary, **{"chunk_summaries": chunk_summaries}},
#         f,
#     indent=4
#     )