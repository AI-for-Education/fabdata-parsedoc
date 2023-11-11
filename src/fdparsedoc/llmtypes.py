from __future__ import annotations

from typing import Optional, Union, List
from pydantic import BaseModel

from .utils.llm import ADict


class QueryVar(BaseModel):
    name: str
    value: Optional[Union[str, QueryVar]] = None
    description: Optional[str] = None

    @property
    def outname(self):
        out = self.name
        if self.description is not None:
            out += f":: {self.description}"
        return out

    @property
    def outvalue(self):
        if isinstance(self.value, QueryVar):
            return self.value.output()
        else:
            return self.value

    def output(self):
        return ADict({self.outname: self.outvalue})


class QueryVarDict(QueryVar):
    name: str
    value: List[QueryVar]
    description: Optional[str] = None

    @property
    def outvalue(self):
        return ADict(
                {
                val.outname: val.outvalue
                for val in self.value
            }
        )


class QueryVarList(QueryVar):
    name: str
    value: List[Optional[Union[str, QueryVar]]]
    description: Optional[str] = None

    @property
    def outvalue(self):
        return [
            val.output() if isinstance(val, QueryVar) else val for val in self.value
        ]


class QueryVarPart(QueryVarDict):
    def __init__(self, value):
        super().__init__(name="null", value=value)

    def output(self):
        return self.outvalue


class ChunkVar(QueryVar):
    def __init__(self, chunk, idx, description=None):
        super().__init__(name=f"chunk_{idx :03d}", value=chunk, description=description)
