from pathlib import Path
import os
from zipfile import ZipFile
import warnings
from tempfile import TemporaryDirectory
from io import BytesIO

import fitz


from ..constants import EXTS
from .misc import filesgen

def extract_text(file, exts=EXTS, suffix=None):
    if isinstance(file, (str, os.PathLike)):
        file = Path(file)
        suffix = file.suffix
        name = file.name
    elif isinstance(file, bytes) and suffix is not None:
        file = BytesIO(file)
        name = None
    elif isinstance(file, BytesIO):
        if hasattr(file, "name"):
            name = file.name
            suffix = Path(file.name).suffix
        elif suffix is not None:
            name = None
        else:
            _file_error()
    else:
        _file_error()
    try:
        if suffix in [".pdf",".doc", ".docx", ".html"]: # ".rtf" is not supported
            text = _extract_text_doc(file)
        elif suffix in [".txt"]:
            text = _extract_text_plain(file)
        elif suffix == ".zip":
            with ZipFile(file, mode="r") as zf, TemporaryDirectory() as td:
                zf.extractall(td)
                return [extract_text(fl, exts) for fl in filesgen(td, exts)]
        else:
            warnings.warn(f"{file} not supported filetype")
        return name, text, suffix
    except Exception as err:
        return name, None, suffix


def _extract_text_doc(file):
    pdf = fitz.open(file)
    return [page.get_text() for page in pdf.pages()]


def _extract_text_plain(file):
    with open(file, "r") as f:
        text = f.read()
    return [text.strip().replace("\r", "")]

def _file_error():
    raise ValueError(
        "file must be either a path string, a Path object, bytes, or BytiesIO."
        " If bytes or BytesIO, suffix must be provided as an additional argument."
    )