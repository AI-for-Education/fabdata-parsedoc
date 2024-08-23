from ..parsedoctypes import DocText
from ..querystrings.contents import JSONIN, JSONOUT
from ..utils import general_query

def extract_contents(doc: DocText, caller=None):
    max_page = 6
    contents = []
    for i, (chunk, page) in enumerate(doc.chunks(chunksize=500, nsubchunks=7)):
        jsonin = {
            JSONIN["CHUNK"].format(i=i): chunk,
            JSONIN["CONTENTS"]: contents,
        }
        jsonout = {
            JSONOUT["CONTENTS"]: [{"heading": None, "page:: int or numeral": None}],
        }
        response = general_query(jsonin, jsonout, caller=caller)
        prev_contents = contents
        contents = contents + [
            item for item in response.to_dict()["contents"] if item not in contents
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
            newct.append(ct)
        except:
            pass
            
    contents = newct
    ##############
    start_page = page[0]
    check_heading = None
    check_page = None
    for ct in contents:
        if isinstance(ct["page"], int):
            check_heading = ct["heading"]
            check_page = ct["page"]
            break
    if not contents:
        return contents
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
        if response.to_dict()["isin"]:
            break
    page_offset = page - check_page
    for ct in contents:
        ct["page"] += page_offset
    return contents
