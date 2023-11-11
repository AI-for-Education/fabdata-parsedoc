#%%
from pathlib import Path
import json
from tqdm import tqdm
from datetime import datetime

from fdllm import GPTCaller, ClaudeCaller
from fdllm.llmtypes import LLMMessage
from fdparsedoc import chunkgen, get_text_chunks
from fdparsedoc.llmtypes import ADict

HERE = Path(__file__).parent
logdir = HERE / "logs"
logdir.mkdir(exist_ok=True, parents=True)
logdir_pyr = HERE / "logs_pyr"
logdir_pyr.mkdir(exist_ok=True, parents=True)

CHUNK_PROPERTIES = ["summary", "key_words"]
TEMPERATURE = 0
NWORDS = 150

#%%
# used = -11
used = 0
files = HERE.parent / "parse_code/mbsseKP_files.json"
with open(files) as f:
    data = json.load(f)
data = [dat for dat in data if len(dat["text"].split()) > 5000]
testtext = data[used]["text"]
print(len(testtext.split()))
data[used]["filename"]
#%%
# caller = GPTCaller("gpt-4")
caller = GPTCaller("gpt-4-0314")
# caller = ClaudeCaller("claude-v1")
# caller = GPTCaller("gpt-3.5-turbo")
# caller = ClaudeCaller("claude-2")
sys_msg_template = (
    "The following json contains the following information about an incomplete document:"
    "\n   - current_summary:"
    "\n       - text: this is a summary of the incomplete document up to this point"
    "\n       - coverage: this is the percentage of the full document that is covered by this summary"
    "\n   - next_chunk:"
    "\n       - text: this is the next part that follows in the same document"
    "\n       - position: this is the position of the chunk in the document relative to the total number of chunks."
    " There is some overlap between chunks, so the beginning of this chunk was also"
    " present at the end of the incomplete document."
    "\n\nIf current_summary text is empty then next_chunk is the start of the document."
    "\n\nSynthesise a new summary text of the document, incorporating both the current"
    " partial summary along with new content from the next chunk in the document."
    " The new summary should be approximately {nwords} words long. "
    " Only return the raw summary, nothing else."
    "\n\n{chunkjson}"
)


#%%
def gen_jsonin(chunk_summaries, next_chunk=None, i=None):
    summ = {
        (
            "summaries::"
            "A list of summaries of previous text chunks"
            " from the same document as the current chunk"
        ): {
            key: {
                "number_of_words": len(chunksum["text"].split()),
                "text": chunksum["text"],
            }
            for key, chunksum in chunk_summaries.items()
        }
    }
    if next_chunk is not None:
        full = {
            (
                "full_text::"
                "Full text of the current chunk in the document"
            ): {
                f"chunk_{i :03d}": {
                    "number_of_words": len(next_chunk.split()),
                    "text": next_chunk,
                }
            }
        }
    else:
        full = {}
    return ADict({**summ, **full})

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

def process_chunk2(next_chunk, chunk_summaries, caller, i, nwords=NWORDS):
    jsonin = gen_jsonin(chunk_summaries, next_chunk, i)
    chunkname = f"chunk_{i :03d}"
    jsonout = ADict({
        (
            "summaries::"
            "A list of summaries to produce."
            " Use previous chunk summaries to"
            " interpret the current chunk in context."
        ): {
            chunkname: {
                (
                    "text::"
                    "Summary of the chunk."
                    f" Aim for around {nwords} words."
                ): None
            }
        },
    })
    message = gen_message(jsonin, jsonout)
    usechsm = chunk_summaries.copy()
    while len(caller.tokenize([message])) >= caller.Token_Window-4000:
        usechsm = {
            key: val for i, (key, val) in enumerate(usechsm.items())
            if i > 0
        }
        jsonin = gen_jsonin(usechsm, next_chunk, i)
        message = gen_message(jsonin, jsonout)
    print(message.Message)
    return caller.call(message, max_tokens=4000, temperature=TEMPERATURE)

def process_document2(text, caller, chunksize=200):
    logfile = HERE / "testlog.txt"
    chunk_summaries = {}
    nsubchunks = 7
    for i, (chunk, _) in enumerate(chunkgen(text, chunksize, nsubchunks)):
        response = process_chunk2(chunk, chunk_summaries, caller, i)
        logfile.write_text(response.Message)
        respjson = ADict(json.loads(response.Message))
        chunk_summaries = ADict({**chunk_summaries, **respjson["summaries"]})
    for chunk in chunk_summaries.values():
        chunk["number_of_words"] = len(chunk["text"].split())
    # jsonin = gen_jsonin(chunk_summaries, None)
    
    ############
    jsonin = {
        "text": " ".join(chunk["text"] for chunk in chunk_summaries.values())
    }
    jsonout = {
        "summary": {
            "short_summary": None,
            "long_summary": None,
            "thematic_sections": []
        },
        "keywords": [],
    }
    message = gen_message(jsonin, jsonout)
    print(message.Message)
    response = caller.call(message, max_tokens=4000, temperature=TEMPERATURE)
    total_summary = ADict(json.loads(response.Message))
    logfile.write_text(response.Message)
    ############
    jsonin = {
        key: chunk["text"]
        for key, chunk in chunk_summaries.items()
    }
    jsonout = ADict({
        "thematic_sections": [
            {
                "heading": sec,
                (
                    "content::"
                    f" Aim for around {NWORDS} words."
                ): None,
                "related_chunks": []
            }
            for sec in total_summary["summary"]["thematic_sections"]
        ]
    })
    message = gen_message(jsonin, jsonout)
    print(message.Message)
    response = caller.call(message, max_tokens=4000, temperature=TEMPERATURE)
    sections = ADict(json.loads(response.Message))
    total_summary["summary"]["thematic_sections"] = sections["thematic_sections"]
    logfile.write_text(response.Message)
    return chunk_summaries.to_dict(), total_summary.to_dict()

def process_chunk(
    next_chunk, current_summary, sys_msg_template, caller, cov, i, n
):
    nwords = int((i/n)**0.75 * 1000)
    chunkjson = {
        "current_summary": {
            "text": current_summary,
            "coverage": f"{int(cov) :d}%"
        },
        "next_chunk": {
            "text": next_chunk,
            "position": f"{i :d} / {n :d}"
        }
    }
    message = LLMMessage(
        Role="system", Message=sys_msg_template.format(
            chunkjson=chunkjson, nwords=nwords
        )
    )
    print(message.Message)
    print(nwords)
    return caller.call(message, max_tokens=2000)
    
def process_document(text, sys_msg_template, caller, chunksize=200):
    logfile = HERE / "testlog.txt"
    nsubchunks = 3
    chunks = get_text_chunks(text, chunksize//nsubchunks)
    current_summary = ""
    chunkidx = list(range(0, len(chunks)-1, nsubchunks-1))
    for i, sidx in enumerate(tqdm(chunkidx)):
        cov = 100 * (sidx / len(chunks))
        eidx = min(sidx+nsubchunks, len(chunks)-1)
        chunk = "\n".join(chunks[sidx:eidx])
        print(i)
        response = process_chunk(
            chunk,
            current_summary,
            sys_msg_template,
            caller,
            cov,
            i+1,
            len(chunkidx),
        )
        current_summary = response.Message
        logfile.write_text(current_summary)
        print(len(current_summary.split()))
    return current_summary

def process_document_pyramid(text, sys_msg_template, caller, chunksize=200):
    ntok = len(caller.tokenize([LLMMessage(Role="system", Message=text)]))
    if ntok > chunksize:
        text1, text2 = text[:len(text)//2], text[len(text)//2:]
        summs = "\n".join(
            process_document_pyramid(t, sys_msg_template, caller, chunksize)
            for t in (text1, text2)
        )
        summsjson = {"text1": summs[0], "text2": summs[1]}
        message = LLMMessage(
            Role="system",
            Message=(
                "Combine the following two pieces of text in less than 1000 words:"
                f"\n\n{summsjson}"
            )
        )
        response = caller.call(message, max_tokens=2000, temperature=TEMPERATURE)
        return response.Message
    else:
        message = LLMMessage(
            Role="system",
            Message=f"Summarize the following text in less than 1000 words:\n\n{text}"
        )
        response = caller.call(message, max_tokens=2000)
        print(response.Message)
        return response.Message
        
#%%
chunksize = 1000
chunk_summaries, total_summary = process_document2(testtext, caller, chunksize)
# logfile = (
#     f'log{datetime.utcnow().strftime(r"%Y%m%d%H%M%S")}'
#     f"_chunksize{chunksize :05d}"
#     ".txt"
# )
logfile = (
    f'summary_{datetime.utcnow().strftime(r"%Y%m%d%H%M%S")}'
    f"_chunksize{chunksize :05d}"
    ".json"
)
with open((logdir / logfile), "w") as f:
    json.dump(
        {**total_summary, **{"chunk_summaries": chunk_summaries}},
        f,
    indent=4
    )
# (logdir / logfile).write_text(summary)
# print(len(summary.split()))
        
    
#%%
chunksize = 1000
summary = process_document(testtext, sys_msg_template, caller, chunksize)
logfile = (
    f'log{datetime.utcnow().strftime(r"%Y%m%d%H%M%S")}'
    f"_chunksize{chunksize :05d}"
    ".txt"
)
(logdir / logfile).write_text(summary)
print(len(summary.split()))

#%%
chunksize = 500
summary = process_document_pyramid(testtext, sys_msg_template, caller, chunksize)
logfile = (
    f'log{datetime.utcnow().strftime(r"%Y%m%d%H%M%S")}'
    f"_chunksize{chunksize :05d}"
    ".txt"
)
(logdir_pyr / logfile).write_text(summary)