from typing import Optional, List, Tuple, Iterator

import numpy as np
from tqdm import tqdm
import tiktoken

tokenizer = tiktoken.get_encoding("cl100k_base")

from ...constants import (
    CHUNK_SIZE,
    N_SUB_CHUNKS,
    MAX_NUM_CHUNKS,
    MIN_CHUNK_SIZE_CHARS,
    MIN_CHUNK_LENGTH_TO_EMBED,
)

def chunkgen(
    text: str,
    chunksize: int=CHUNK_SIZE,
    nsubchunks: Optional[int]=None,
    page_idx: Optional[dict]=None
) -> Iterator[Tuple[str, int]]:
    if nsubchunks is None:
        for chunk, page in zip(*get_text_chunks(text, chunksize, page_idx)):
            yield chunk, page
    else:
        chunks, pages = get_text_chunks(text, chunksize // nsubchunks, page_idx)
        for sidx in range(0, len(chunks), nsubchunks - 1):
            eidx = min(sidx + nsubchunks, len(chunks))
            chunk = "\n".join(chunks[sidx:eidx])
            allpage = np.array(pages[sidx:eidx]).ravel()
            page = (allpage.min(), allpage.max())
            yield chunk, page

def get_text_chunks(
    text: str, chunk_token_size: Optional[int], page_idx: Optional[dict]
) -> Tuple[List[str], List[Tuple]]:
    """
    Based on:
    https://github.com/openai/chatgpt-retrieval-plugin/blob/main/services/chunks.py
    Modified to return the page index corresponding to each chunk if the string indices for each
    page are given as input
    
    Split a text into chunks of ~CHUNK_SIZE tokens, based on punctuation and newline boundaries.

    Args:
        text: The text to split into chunks.
        chunk_token_size: The target size of each chunk in tokens, or None to use the default CHUNK_SIZE.

    Returns:
        A list of text chunks, each of which is a string of ~CHUNK_SIZE tokens.
    """
    # Return an empty list if the text is empty or whitespace
    if not text or text.isspace():
        return []

    # Tokenize the text
    tokens = tokenizer.encode(text, disallowed_special=())

    # Initialize an empty list of chunks
    chunks = []
    pages = []

    # Use the provided chunk token size or the default one
    chunk_size = chunk_token_size or CHUNK_SIZE

    # Initialize a counter for the number of chunks
    num_chunks = 0
    
    curr_idx = 0
    curr_pg = (0, 0)

    # Loop until all tokens are consumed
    while tokens and num_chunks < MAX_NUM_CHUNKS:
        # Take the first chunk_size tokens as a chunk
        chunk = tokens[:chunk_size]

        chunk_text = tokenizer.decode(chunk)

        # Skip the chunk if it is empty or whitespace
        if not chunk_text or chunk_text.isspace():
            curr_idx += len(chunk_text)
            # Remove the tokens corresponding to the chunk text from the remaining tokens
            tokens = tokens[len(chunk) :]
            # Continue to the next iteration of the loop
            continue

        # Find the last period or punctuation mark in the chunk
        last_punctuation = max(
            chunk_text.rfind("."),
            chunk_text.rfind("?"),
            chunk_text.rfind("!"),
            chunk_text.rfind("\n"),
        )

        # If there is a punctuation mark, and the last punctuation index is before MIN_CHUNK_SIZE_CHARS
        if last_punctuation != -1 and last_punctuation > MIN_CHUNK_SIZE_CHARS:
            # Truncate the chunk text at the punctuation mark
            chunk_text = chunk_text[: last_punctuation + 1]

        if page_idx is not None:
            curr_idx, curr_pg = _page_from_chunk_text(
                chunk_text, page_idx, curr_idx, curr_pg, text
            )

        # Remove any newline characters and strip any leading or trailing whitespace
        chunk_text_to_append = chunk_text.replace("\n", " ").strip()

        if len(chunk_text_to_append) > MIN_CHUNK_LENGTH_TO_EMBED:
            # Append the chunk text to the list of chunks
            chunks.append(chunk_text_to_append)
            pages.append(curr_pg)

        # Remove the tokens corresponding to the chunk text from the remaining tokens
        tokens = tokens[len(tokenizer.encode(chunk_text, disallowed_special=())) :]

        # Increment the number of chunks
        num_chunks += 1

    # Handle the remaining tokens
    if tokens:
        chunk_text = tokenizer.decode(chunk)
        if page_idx is not None:
            curr_idx, curr_pg = _page_from_chunk_text(
                chunk_text, page_idx, curr_idx, curr_pg, text
            )
        remaining_text = chunk_text.replace("\n", " ").strip()
        if len(remaining_text) > MIN_CHUNK_LENGTH_TO_EMBED:
            chunks.append(remaining_text)
            pages.append(curr_pg)

    return chunks, pages

def _page_from_chunk_text(chunk_text, page_idx, curr_idx, curr_pg, full_text):
    curr_pg = list(curr_pg)
    got_pg = [False, False]
    prev_idx = curr_idx
    curr_idx = full_text.find(chunk_text) + len(chunk_text)
    # determine page
    for key, val in page_idx.items():
        if not got_pg[0] and prev_idx < val:
            curr_pg[0] = key
            got_pg[0] = True
        if not got_pg[1] and curr_idx < val:
            curr_pg[1] = key
            got_pg[1] = True
    return curr_idx, tuple(curr_pg)
