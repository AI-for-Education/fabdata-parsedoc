# %%
from fdparsedoc.llmtypes import QueryVar, QueryVarList, QueryVarDict, ChunkVar, QueryVarPart

# %%
qv = QueryVar(
    name="chunk_000",
    value="test",
    description=(
        "A small chunk of an incomplete document"
        " which may or may not contain a full or partial"
        " table of contents."
    ),
)

#%%
qvl = QueryVarList(
    name="contents",
    value=[ChunkVar("test", i, "test") for i in range(10)]
)

#%%
qvin = QueryVarPart([qvl])