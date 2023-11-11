#%%
from pathlib import Path

from fdparsedoc.parsedoctypes import DocText
from fdparsedoc.utils import general_query, ADict
from fdllm import GPTCaller
from fdllm.llmtypes import LLMMessage

#%%
datapath = Path(r"D:\Fab_data\web_data\Global-Proficiency-Framework-Reading.pdf")
doc = DocText.from_file(datapath)
# doc.populate_contents()

#%%
caller = GPTCaller("gpt-4-0314")

for chunk, pages in doc.chunks(chunksize=200):
    message = (
        "The following text contains some words with whitespace inside the word."
        " Return the text with whitespace removed from inside words."
        f" Text follows: \n{chunk}"
    )
    response = caller.call(
        LLMMessage(Role="user", Message=message)
    )
    print(chunk)
    print(response.Message)
    # jsonin = ADict(
    #     {
    #         (
    #             "text"
    #         ): chunk
    #     }
    #     )
    # jsonout = ADict(
    #     {
    #         (
    #             "markdown"
    #         ): None
    #     }
    # )
    
    # response = general_query(jsonin, jsonout, caller=caller)
    # print(chunk)
    # print(response["markdown"])
    