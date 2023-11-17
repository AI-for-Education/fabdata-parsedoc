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
doc.populate_contents()

#%%
start_page, end_page = doc.contents("TABLE 2: STRUCTURE OF THE GPF")