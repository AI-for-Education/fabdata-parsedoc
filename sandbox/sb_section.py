# %%
from pathlib import Path
import json
import copy

from fdparsedoc.parsedoctypes import DocText
from fdparsedoc.utils import general_query, ADict
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
doc.populate_contents()

# %%
section = "TABLE 2: STRUCTURE OF THE GPF"
# section = "Table 16: General Features of Grade 2 -level Texts"
# section = "APPENDIX B: GPF TEXT COMPLEXITY CONTINUUM AND EXAMPLES"
# section = "Grade 3"
start_page, end_page = doc.contents(section)

max_page = 6
chunks = doc.chunks(chunksize=2000, nsubchunks=7)
# caller = GPTCaller("gpt-4")
caller = GPTCaller("gpt-4-0314")
# caller = ClaudeCaller("claude-v1")
content = []
buffer = ["", ""]
fullcontent = ""
for i, (chunk, page) in enumerate(chunks):
    if page[1] < start_page or page[0] > end_page:
        continue
    jsonin = {
        (
            f"chunk_{i :03d}:: "
            "A small chunk of an incomplete document"
        ): chunk,
        # (
        #     "contents:: "
        #     "Table of contents for the full document"
        # ): doc.contents(),
        (
            "headings:: "
            "A list of headings within this document"
            " that we want to extract the full text from."
        ): [section],
        (
            "content:: "
            "Full content extracted so far from previous chunks."
        ): content,
    }
    jsonout = {
        (
            "content:: "
            # "Content updated to include this chunk."
            "Full content for this chunk."
            " Only include new content that isn't already found in previous chunks."
            " If there is no new content return an empty string."
            " Try to format the text without losing any content from the section."
        ): [
            {
                "heading": section, 
                (
                    "markdown:: "
                    "use tables, lists, headings (#) where appropriate."
                ): None
            }
        ],
    }
    response = general_query(jsonin, jsonout)
    content = response.to_dict()["content"]
    buffer[0] = buffer[1]
    buffer[1] = content[0]["markdown"]
    if fullcontent:
        fullcontent += "\n" + buffer[1]
    else:
        fullcontent = buffer[1]
    print(json.dumps(response.to_dict(), indent=4))
    content[0]["markdown"] = "\n".join(b for b in buffer if b)
with open("tmp.md", "w") as f:
    f.write(fullcontent)
