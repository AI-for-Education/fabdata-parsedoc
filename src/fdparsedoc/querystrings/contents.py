JSONIN = {
    "CHUNK": (
        "chunk_{i:03d}:: "
        "A small chunk of an incomplete document"
        " which may or may not contain a full or partial"
        " table of contents."
    ),
    "CONTENTS": (
        "contents:: "
        "Incomplete table of contents extracted prior to this chunk"
    )
}

JSONOUT = {
    "CONTENTS": (
        "contents:: "
        # "table of contents updated to include this chunk."
        "table of contents for this chunk."
        " This will usually start with the heading 'contents'"
        " or something similar."
        # " Remove anything that you no longer consider to be"
        # " a part of the table of contents."
        " Only include new contents that weren't already found in previous chunks."
        " If there are no new contents then set to empty list."
    )
}