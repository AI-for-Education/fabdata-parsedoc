from pathlib import Path

def flattener(pages, allflatpages=[]):
    flatpages = []
    for p in pages:
        if isinstance(p, list):
            flatpages.extend(flattener(p, allflatpages=flatpages))
        else:
            if p not in flatpages and p not in allflatpages:
                flatpages.append(p)
    return flatpages

def filesgen(path, exts):
    for fl in Path(path).rglob("*"):
        if fl.suffix in exts:
            yield fl