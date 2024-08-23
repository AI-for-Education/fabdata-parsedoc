#%%
from pathlib import Path

from fdparsedoc.parsedoctypes import DocText

# %%
datapath = Path(r"D:\Fab_data\web_data\Global-Proficiency-Framework-Reading.pdf")
doc = DocText.from_file(datapath)
# doc.populate_contents()

#%%
chunks = list(doc.chunks(chunksize=4000))

#%%
doc.populate_contents(caller="gpt-4o")

#%%
start_page, end_page = doc.contents("Grade 1")