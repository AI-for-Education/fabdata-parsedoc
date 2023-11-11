import json

from tqdm import tqdm

from fdllm import GPTCaller
from fdllm.llmtypes import LLMMessage

class ADict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, val in self.items():
            if isinstance(val, dict):
                self[key] = self.__class__(val)
            elif isinstance(val, list):
                self[key] = [
                    self.__class__(val_) if isinstance(val_, dict)
                    else val_
                    for val_ in val
                ]
    
    def __getitem__(self, key):
        for k, val in self.items():
            if key in [k.split("::")[0], k]:
                return val
        raise IndexError()
    
    def __setitem__(self, key, value):
        for k in self:
            if key in [k.split("::")[0], k]:
                super().__setitem__(k, value)
                return
        super().__setitem__(key, value)
    
    def to_dict(self):
        return clean_keys(dict(self))

def general_query(
    jsonin,
    jsonout,
    caller=None,
    temperature=0,
    max_input_tokens=None,
    min_new_token_window=500,
    reduce_callback=None,
):
    if caller is None:
        caller = GPTCaller("gpt-4")
    msg = gen_message(jsonin, jsonout)
    ntok = len(caller.tokenize([msg]))
    if max_input_tokens is not None and ntok > max_input_tokens:
        raise ValueError("Message is too long")
    max_tokens = caller.Token_Window - ntok
    if max_tokens < min_new_token_window:
        if reduce_callback is None:
            raise ValueError("Message is too long")
        else:
            while max_tokens < min_new_token_window:
                jsonin, jsonout = reduce_callback(jsonin, jsonout)
                msg = gen_message(jsonin, jsonout)
                ntok = len(caller.tokenize([msg]))
                max_tokens = caller.Token_Window - ntok
    out = caller.call(msg, max_tokens=max_tokens, temperature=temperature)
    
    try:
        return ADict(json.loads(trim_nonjson(out.Message)))
    except:
        raise ValueError("Invalid output")
    

def gen_message(jsonin, jsonout):
    return LLMMessage(
        Role="system",
        Message=(
            "Given the values in JSON1, fill in the empty values in JSON2:"
            f"\n\nJSON1:\n{json.dumps(jsonin, indent=4, ensure_ascii=False)}"
            f"\n\nJSON2:\n{json.dumps(jsonout, indent=4, ensure_ascii=False)}"
            "\n\nExpand any lists where necessary. Only return the raw json."
            " For any field names that contain '::', only reproduce the part of the"
            " name before the '::'."
        )
    )

def clean_keys(d):
    if not isinstance(d, dict):
        return d
    out = d.copy()
    for key in d:
        usekey = key.split("::")[0]
        useval = out.pop(key)
        if isinstance(useval, dict):
            out[usekey] = clean_keys(useval)
        elif isinstance(useval, list):
            out[usekey] = [clean_keys(uv) for uv in useval]
        else:
            out[usekey] = useval
    return out

def trim_nonjson(text):
    pre, *post = text.split("{")
    text = "{".join(["", *post])
    *pre, post = text.split("}")
    text = "}".join([*pre, ""])
    return text
