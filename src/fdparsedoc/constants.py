EXTS = [".docx", ".pdf", ".doc", ".zip", ".rtf", ".txt"]

CHUNK_SIZE = 1000  # The target size of each text chunk in tokens
N_SUB_CHUNKS = 10
MIN_CHUNK_SIZE_CHARS = 350  # The minimum size of each text chunk in characters
MIN_CHUNK_LENGTH_TO_EMBED = 0  # Discard chunks shorter than this
EMBEDDINGS_BATCH_SIZE = 128  # The number of embeddings to request at a time
MAX_NUM_CHUNKS = 10000  # The maximum number of chunks to generate from a text