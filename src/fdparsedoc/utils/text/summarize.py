from pathlib import Path
import json
from tqdm import tqdm
from datetime import datetime

from fdllm import GPTCaller, ClaudeCaller
from fdllm.llmtypes import LLMMessage

from .chunking import chunkgen
from ...llmtypes import ADict
from ..llm import gen_message
from ...utils.llm import trim_nonjson

TEMPERATURE = 0
NWORDS = 150


def summarize_text(text, caller, chunksize=200, verbose=0):
    # logfile = HERE / "testlog.txt"
    chunk_summaries = {}
    nsubchunks = 10
    chunkiter = enumerate(chunkgen(text, chunksize, nsubchunks))
    if verbose > 0:
        print("Getting chunk summaries:")
        chunkiter = tqdm(list(chunkiter))
    for i, (chunk, _) in chunkiter:
        response = _process_chunk(chunk, chunk_summaries, caller, i, verbose=verbose)
        # logfile.write_text(response.Message)
        respjson = ADict(json.loads(trim_nonjson(response.Message)))
        chunk_summaries = ADict({**chunk_summaries, **respjson["summaries"]})
    for chunk in chunk_summaries.values():
        chunk["number_of_words"] = len(chunk["text"].split())
    # jsonin = gen_jsonin(chunk_summaries, None)

    ############
    jsonin = {"text": " ".join(chunk["text"] for chunk in chunk_summaries.values())}
    jsonout = {
        "summary": {
            "short_summary": None,
            "long_summary": None,
            "thematic_sections:: Based on all of the chunk summaries"
            " break the document down into its main thematic sections."
            : [],
        },
        "keywords": [],
    }
    message = gen_message(jsonin, jsonout)
    if verbose > 1:
        print(message.Message)
    if verbose > 0:
        print("Getting thematic sections")
    response = caller.call(message, max_tokens=4000, temperature=TEMPERATURE)
    total_summary = ADict(json.loads(trim_nonjson(response.Message)))
    # logfile.write_text(response.Message)
    ############
    jsonin = {key: chunk["text"] for key, chunk in chunk_summaries.items()}
    jsonout = ADict(
        {
            "thematic_sections": [
                {
                    "heading": sec,
                    ("content::" f" Aim for around {NWORDS} words."): None,
                    "related_chunks": [],
                }
                for sec in total_summary["summary"]["thematic_sections"]
            ]
        }
    )
    message = gen_message(jsonin, jsonout)
    if verbose > 1:
        print(message.Message)
    if verbose > 0:
        print("Getting final summary")
    response = caller.call(message, max_tokens=4000, temperature=TEMPERATURE)
    sections = ADict(json.loads(trim_nonjson(response.Message)))
    total_summary["summary"]["thematic_sections"] = sections["thematic_sections"]
    # logfile.write_text(response.Message)
    return chunk_summaries.to_dict(), total_summary.to_dict()


def _gen_jsonin(chunk_summaries, next_chunk=None, i=None):
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
            ("full_text::" "Full text of the current chunk in the document"): {
                f"chunk_{i :03d}": {
                    "number_of_words": len(next_chunk.split()),
                    "text": next_chunk,
                }
            }
        }
    else:
        full = {}
    return ADict({**summ, **full})


def _process_chunk(next_chunk, chunk_summaries, caller, i, nwords=NWORDS, verbose=0):
    jsonin = _gen_jsonin(chunk_summaries, next_chunk, i)
    chunkname = f"chunk_{i :03d}"
    jsonout = ADict(
        {
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
                        " Start with: 'This chunk'"
                    ): None
                }
            },
        }
    )
    message = gen_message(jsonin, jsonout)
    usechsm = chunk_summaries.copy()
    while len(caller.tokenize([message])) >= caller.Token_Window - 4000:
        usechsm = {key: val for i, (key, val) in enumerate(usechsm.items()) if i > 0}
        jsonin = _gen_jsonin(usechsm, next_chunk, i)
        message = gen_message(jsonin, jsonout)
    if verbose > 1:
        print(message.Message)
    return caller.call(message, max_tokens=4000, temperature=TEMPERATURE)
