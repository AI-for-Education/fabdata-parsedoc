from itertools import chain
from pathlib import Path

from joblib import Parallel, delayed

from ..constants import EXTS
from ..parsedoctypes import DocText
from .misc import filesgen

def extract_text_folder(
    path,
    return_json=False,
    exts=EXTS,
    exclude_exts=[],
):
    if not isinstance(path, list):
        path = [path]
    fgen = chain(*[filesgen(dp, exts) for dp in path])
    p = Parallel(n_jobs=8, verbose=10)
    docs = p(delayed(DocText.from_file)(file, exts) for file in fgen)
    docs = [doc for doc in docs if doc.suffix not in exclude_exts]
    if return_json:
        jsondata = []
        for doc in docs:
            jsondata.append(
                {
                    "id": str(doc.id),
                    "text": doc.text,
                    "source": "file",
                    "filename": doc.name,
                }
            )
        return docs, jsondata
    else:
        return docs