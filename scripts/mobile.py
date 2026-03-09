import os
def main(src_dir, out_dir, config, files):
    """
    print("---")
    print("Welcome to mobile buildier")
    print("---")
    print("This plugin is not implimented. But it will be making a mobile freindly site hardlinking any files except .element, .html, .html.temp, or .md files to dist/mobile. It will then be taking all notes and blogs and bulding them to be mobile friendly by removing everything but the content and author information.")
    print("All config will be in config.yml under mobile")
    print("---")
    """
    # should build mobile site we see
    print("Building Mobile Site")
    nout_dir = out_dir / "mobile"
    #print(nout_dir)
    for page in files:
        page.out_dir = nout_dir
        t_path = src_dir / "mobile.html.temp"
        page.template_path = t_path
        page.default_template = t_path
        page.custom_template_set = True
        print(page.template_path)
        #print(f"{str(page.md_file)} has {str((src_dir / "notes"))} in it is { str((src_dir / "notes")) in str(page.md_file)}")
        if str((src_dir / "notes")) in str(page.md_file) or str((src_dir / "blogs")) in str(page.md_file):
            page.render()
    for asset in src_dir.rglob("*"):
        skip = [".md", ".element", ".py", ".temp", ".bak", ".html"]
        if not asset.is_file() or asset.suffix.lower() in skip:
            continue
        dist_path = out_dir / asset.relative_to(src_dir)
        #print(dist_path)
        destination = out_dir / "mobile" /asset.relative_to(src_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(destination):
            os.link(dist_path,destination)