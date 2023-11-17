#%%
from pathlib import Path
from tempfile import TemporaryDirectory, SpooledTemporaryFile, NamedTemporaryFile

from fdparsedoc.parsedoctypes import DocText

#%%
dropboxpath = Path.home()
datapath = dropboxpath / (
    r"Fab Inc Dropbox\Fab Inc Other"
    r"\_Organised bank\Resources\IEFG\Donors_Partners\firelightfoundation"
)
filepath = datapath / r"FINAL-Impact-Report-FY22.pdf"

#%%
with open(filepath, "rb") as f:
    bts = f.read()

#%%
doc = DocText.from_file(bts, suffix=".pdf")

#%%
doc = DocText.from_file(filepath)

#%%
f = NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False)
f.write(bts)
doc = DocText.from_file(f.name)
f.close()
Path(f.name).unlink()