import uuid

from fdllm import get_caller

from .constants import EXTS, CHUNK_SIZE, N_SUB_CHUNKS
from .utils import extract_text, chunkgen, clean_text


class DocText:
    def __init__(self, file=None, exts=EXTS, suffix=None):
        if file is not None:
            self.name, self.pages, self.suffix = extract_text(file, exts, suffix=suffix)
        else:
            self.name = None
            self.pages = []
            self.suffix = None
        self._gen_pageidx()
        self.id = str(uuid.uuid4())
        self._contents = None
        self._cleaned = False

    @classmethod
    def from_dict(cls, docdict):
        out = cls()
        for attr, val in docdict.items():
            setattr(out, attr, val)
        return out

    def to_dict(self):
        save_attrs = ["name", "pages", "suffix", "id", "_contents", "_cleaned"]
        return {attr: getattr(self, attr) for attr in save_attrs}

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            outl = self.pages[idx]
        elif isinstance(idx, int):
            outl = [self.pages[idx]]
        else:
            raise NotImplementedError("idx must be int or slice")
        return "\n".join(outl)

    @property
    def text(self):
        return "\n".join(self.pages[:])

    @classmethod
    def from_file(cls, file, exts=EXTS, suffix=None):
        return cls(file, exts, suffix=suffix)

    @property
    def sorted_contents(self):
        if self._contents is not None:
            return sorted(self._contents, key=lambda x: x["page"])

    def chunks(self, chunksize=CHUNK_SIZE, nsubchunks=N_SUB_CHUNKS):
        return chunkgen(self.text, chunksize, nsubchunks, self.page_idx)

    def clean(self, idx=None):
        if not self._cleaned:
            if idx is None:
                idx = slice(0, len(self.pages))
            self.pages[idx] = [clean_text(page.strip()) for page in self.pages[idx]]
            self._cleaned = True

    def populate_contents(self, caller=None):
        from .utils.doc import extract_contents
        
        if isinstance(caller, str):
            caller = get_caller(caller)

        self._contents = extract_contents(self, caller=caller)

    def contents(self, idx=None):
        if idx is None:
            return self._contents
        for i, ct in enumerate(self.sorted_contents):
            if isinstance(idx, int):
                if ct["page"] == idx:
                    return ct["heading"]
            elif isinstance(idx, str):
                if ct["heading"] == idx:
                    return (ct["page"], self.sorted_contents[i + 1]["page"])

    def extract_section(self, heading):
        pass

    def _gen_pageidx(self):
        pgidx = {}
        idx = 0
        for i, pg in enumerate(self.pages):
            idx += len(pg) + 1
            pgidx[i] = idx
        self.page_idx = pgidx

    def fix_page_encoding(self):
        for i in range(len(self.pages)):
            self.pages[i] = (
                self.pages[i].encode("utf-8", errors="replace").decode("utf-8")
            )
