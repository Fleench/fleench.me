def main(src_dir, out_dir, config, files):
    for page in files:
        p = page.parsed.metadata
        #print(p)
        if not p.get("hidden",False):
            print(page.canonical.split("https://flench.me")[1].split("/")[1:-1])