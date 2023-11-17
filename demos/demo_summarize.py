from pathlib import Path
import json
from argparse import ArgumentParser

from fdllm import get_caller
from fdllm.sysutils import register_models
from fdparsedoc import DocText
from fdparsedoc.utils.text.summarize import summarize_text


def main(opt):
    register_models(opt.model_config)
    caller = get_caller(opt.model)
    input = Path(opt.file_or_folder)
    output_folder = Path(opt.output_folder)
    output_folder.mkdir(exist_ok=True, parents=True)
    if not input.exists():
        raise ValueError(f"{str(input)} doesn't exist")
    if input.is_dir():
        for file in input.glob("*.pdf"):
            process_file(file, output_folder, caller, opt.chunksize, opt.verbose)
    else:
        process_file(input, output_folder, caller, opt.chunksize, opt.verbose)


def process_file(file, output_folder, caller, chunksize, verbose):
    if file.suffix != ".pdf":
        raise ValueError("Input file must be a pdf")
    try:
        doc = DocText.from_file(file)
    except:
        raise ValueError("Input file doesn't seem to be a valid pdf")
    chunk_summaries, total_summary = summarize_text(
        doc.text,
        caller=caller,
        chunksize=chunksize,
        verbose=verbose,
    )
    chunksummfile = output_folder / f"{file.stem}_chunksumm.json"
    totsummfile = output_folder / f"{file.stem}_totsumm.json"
    with open(chunksummfile, "w") as f:
        json.dump(chunk_summaries, f, indent=4)
    with open(totsummfile, "w") as f:
        json.dump(total_summary, f, indent=4)
    


if __name__ == "__main__":
    ROOT = Path(__file__).parents[1]
    default_config = str(ROOT / "configs/custom_models.yaml")
    parser = ArgumentParser()
    parser.add_argument(
        "-f",
        "--file-or-folder",
        type=str,
        required=True,
        help="Path to pdf file or folder of pdf files to summarize",
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        type=str,
        required=True,
        help="Path to folder to save output(s)",
    )
    parser.add_argument("--model", type=str, default="fabdata-openai-eastus2-gpt4")
    parser.add_argument("--model-config", type=str, default=default_config)
    parser.add_argument("--chunksize", type=int, default=1000)
    parser.add_argument("--verbose", type=int, default=1)
    opt = parser.parse_args()
    
    main(opt)
