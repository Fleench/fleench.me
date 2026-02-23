from pathlib import Path
import re
try:
    import html
except:
    print("YOU DUMBASS")
def main(**args):
    print("RUN")
    name = str(args["current_markdown"]).strip(".")[0]
    src = Path("./")
    md_lib = args["md"]
    try:
        for file in src.rglob("*.md"):
            print(name)
            if name in file.name and "left" in file.name:
                print(f"{file.name} had contents")
                if x:= file.read_text():
                    print("C")
                    return markdown_to_html(x,md_lib)
                else:
                    print("Z")
        # return "{{ left sidebar }}"
    except Exception as e:
        print(f"Error: {e}")
def markdown_to_html(markdown_text: str, md_lib) -> str:
    if md_lib is not None:
        return md_lib.markdown(markdown_text, extensions=["extra", "sane_lists"])

    chunks: list[str] = []
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1))
            chunks.append(f"<h{level}>{html.escape(heading.group(2))}</h{level}>")
        else:
            chunks.append(f"<p>{html.escape(stripped)}</p>")
    return "\n".join(chunks)