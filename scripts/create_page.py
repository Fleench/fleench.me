import sys
from pathlib import Path

def create(name):
    # Create markdown file
    md_file = Path(f"src/{name}.md")
    md_file.write_text(f"---\ntitle: {name.replace('-', ' ').title()}\ndate: 2026-04-06\n---\n\nNew content here.", encoding="utf-8")
    
    # Create python file
    py_file = Path(f"src/{name}.py")
    py_file.write_text(f"def main():\n    print('Generated {name}')\n\nif __name__ == '__main__':\n    main()", encoding="utf-8")
    
    print(f"Created {md_file} and {py_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 create_page.py <name>")
        sys.exit(1)
    create(sys.argv[1])
