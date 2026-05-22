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
    special_mobile_templates = {
        "src/templates/school-year-review.html.temp",
    }
    #print(nout_dir)
    for page in files:
        
        #print(f"{str(page.md_file)} has {str((src_dir / "notes"))} in it is { str((src_dir / "notes")) in str(page.md_file)}")
        template = config["API"]["parse_frontmatter"](page.md_file.read_text(encoding="utf-8")).metadata.get("template","")
        if (
            str((src_dir / "notes")) in str(page.md_file)
            or str((src_dir / "blogs")) in str(page.md_file)
            or str((src_dir / "about")) in str(page.md_file)
            or template in special_mobile_templates
        ):
            page.out_dir = nout_dir
            templates_dir = src_dir / "templates"
            td_path = templates_dir / "mobile.html.temp"
            other_temps = {
                "src/templates/note-full.html.temp": templates_dir / "mobile" / "mobile-note-full.html.temp",
                "src/templates/note.html.temp": templates_dir / "mobile" / "mobile-note.html.temp",
                "src/templates/blogs-full.html.temp": templates_dir / "mobile" / "mobile-blog-full.html.temp",
                "src/templates/blog.html.temp": templates_dir / "mobile" / "mobile-blog.html.temp",
                "src/templates/school-year-review.html.temp": templates_dir / "mobile" / "mobile-school-year-review.html.temp",
            }
            t_path = other_temps.get(template,td_path)
            page.template_path = t_path
            page.default_template = t_path
            if "mobile" not in str(template):
                #print(f"Using {t_path} on  {str(page.md_file)} as it's template {template} does not have mobile in it")
                page.custom_template_set = True
            page.render()
            #custom render flow
            """ 
            page.prep_template()
            #print(page.template_path)
            page.parse_content()
            page.derive_path()
            page.write()
            """
           
    skip_suffixes = {".md", ".element", ".py", ".temp", ".bak", ".html", ".pyc"}
    skip_names = {".env"}
    skip_dirs = {"__pycache__", "elements", ".elements", "templates"}
    for asset in src_dir.rglob("*"):
        if not asset.is_file():
            continue
        if asset.suffix.lower() in skip_suffixes or asset.name in skip_names:
            continue
        if any(part in skip_dirs for part in asset.relative_to(src_dir).parts[:-1]):
            continue
        dist_path = out_dir / asset.relative_to(src_dir)
        #print(dist_path)
        destination = out_dir / "mobile" /asset.relative_to(src_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(destination):
            os.link(dist_path,destination)
