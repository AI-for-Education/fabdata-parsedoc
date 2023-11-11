# %%
from pathlib import Path
import json

from fdparsedoc.parsedoctypes import DocText
from fdparsedoc.utils import general_query
from fdllm import GPTCaller, ClaudeCaller

# %%
datapath = Path(r"D:\Fab_data\web_data\Global-Proficiency-Framework-Reading.pdf")
# datapath = Path(
#     r"D:/Fab_data/web_data"
#     r"/mbsseknowledgeplatform.gov.sl"
#     r"/wp-content/uploads/2021/12"
#     r"/lesson-plans-for-jss-1-language-arts-term-1.pdf"
# )
doc = DocText.from_file(datapath)

# %%
max_page = 6
chunks = doc.chunks(chunksize=500, nsubchunks=7)
caller = GPTCaller("gpt-4")
# caller = GPTCaller("gpt-3.5-turbo")
# caller = ClaudeCaller("claude-v1")
contents = []
for i, (chunk, page) in enumerate(chunks):
    jsonin = {
        (
            f"chunk_{i :03d}:: "
            "A small chunk of an incomplete document"
            " which may or may not contain a full or partial"
            " table of contents."
        ): chunk,
        (
            "contents:: "
            "Incomplete table of contents extracted prior to this chunk"
        ): contents,
    }
    jsonout = {
        (
            "contents:: "
            # "table of contents updated to include this chunk."
            "table of contents for this chunk."
            " This will usually start with the heading 'contents'"
            " or something similar."
            # " Remove anything that you no longer consider to be"
            # " a part of the table of contents."
            " Only include new contents that weren't already found in previous chunks."
            " If there are no new contents then set to empty list."
        ): [{"heading": None,"page:: int or numeral": None}],
        # (
        #     "completed:: "
        #     "Set to true if the table of contents in JSON2 is "
        #     "the same as the table of contents in JSON1."
        # ): None,
    }
    response = general_query(jsonin, jsonout, caller=caller)
    print(json.dumps(response.to_dict(), indent=4))
    prev_contents = contents
    contents = contents + [
        item for item in response.to_dict()["contents"]
        if item not in contents
    ]
    
    if prev_contents:
        if contents == prev_contents:
            break
    elif page[0] > max_page:
        break

newct = []
for ct in contents:
    try:
        ct["page"] = int(ct["page"])
    except:
        pass
    finally:
        newct.append(ct)
contents = newct

#%%
start_page = page[0]
check_heading = None
check_page = None
for ct in contents:
    if isinstance(ct["page"], int):
        check_heading = ct["heading"]
        check_page = ct["page"]
        break
chunks = doc.chunks(chunksize=500, nsubchunks=7)
for page in range(start_page, len(doc.pages)):
    jsonin = {
        (
            f"page_{page :03d}:: "
            "A page of a document"
        ): doc.pages[page],
        (
            "heading:: "
            "A heading within this document"
        ): check_heading,
    }
    jsonout = {
        (
            "isin:: true if section given by heading is in this page"
        ): None
    }
    response = general_query(jsonin, jsonout, caller=caller)
    print(json.dumps(response.to_dict(), indent=4))
    if response.to_dict()["isin"]:
        break

page_offset = page - check_page
for ct in contents:
    ct["page"] += page_offset