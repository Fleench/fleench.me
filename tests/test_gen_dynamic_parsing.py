from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import gen


class DynamicElementParsingTests(unittest.TestCase):
    @property
    def one_value(self) -> int | str:
        return 1 if gen.YAML is not None else "1"

    def test_parse_dynamic_args_supports_escaped_parens(self) -> None:
        parsed = gen._parse_dynamic_args(r"Inhale \(Exhale\),album,1")
        self.assertEqual(parsed, ["Inhale (Exhale)", "album", self.one_value])

    def test_parse_dynamic_args_supports_quoted_parens(self) -> None:
        parsed = gen._parse_dynamic_args('"Inhale (Exhale)",album,1')
        self.assertEqual(parsed, ["Inhale (Exhale)", "album", self.one_value])

    def test_parse_dynamic_args_supports_commas_inside_quotes(self) -> None:
        parsed = gen._parse_dynamic_args('"Inhale, Exhale (Live)",album,1')
        self.assertEqual(parsed, ["Inhale, Exhale (Live)", "album", self.one_value])

    def test_inject_elements_no_args_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            element_file = root / "echo.py"
            element_file.write_text("def render(args=None, **kwargs):\n    return repr(args)\n", encoding="utf-8")
            template_path = root / "template.md"
            template_path.write_text("", encoding="utf-8")

            rendered = gen.inject_elements(":{echo.py}:", template_path)
            self.assertEqual(rendered, "[]")

    def test_inject_elements_supports_escaped_and_quoted_parens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            element_file = root / "echo.py"
            element_file.write_text("def render(args=None, **kwargs):\n    return repr(args)\n", encoding="utf-8")
            template_path = root / "template.md"
            template_path.write_text("", encoding="utf-8")

            escaped_rendered = gen.inject_elements(
                r":{echo.py}:(Inhale \(Exhale\),album,1)",
                template_path,
            )
            quoted_rendered = gen.inject_elements(
                ':{echo.py}:("Inhale (Exhale)",album,1)',
                template_path,
            )
            simple_rendered = gen.inject_elements(":{echo.py}:(Ben Rector,artist,1)", template_path)

            self.assertEqual(escaped_rendered, f"['Inhale (Exhale)', 'album', {repr(self.one_value)}]")
            self.assertEqual(quoted_rendered, f"['Inhale (Exhale)', 'album', {repr(self.one_value)}]")
            self.assertEqual(simple_rendered, f"['Ben Rector', 'artist', {repr(self.one_value)}]")

    def test_inject_elements_leaves_unclosed_arg_list_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            template_path = root / "template.md"
            template_path.write_text("", encoding="utf-8")
            text = "prefix :{echo.py}:(a,(b) suffix"

            rendered = gen.inject_elements(text, template_path)
            self.assertEqual(rendered, text)

    def test_template_meta_extends_applies_block_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "src"
            out = root / "dist"
            src.mkdir(parents=True, exist_ok=True)

            (src / "page.html.temp").write_text(
                "<html>~{block content_block}~{{ content }}~{endblock}~</html>",
                encoding="utf-8",
            )
            (src / "child.html.temp").write_text(
                """<!-- meta start -->
<!--
extends: src/page.html.temp
-->
<!-- meta end -->
~{block content_block}~<article>{{ title }}</article>~{endblock}~
""",
                encoding="utf-8",
            )
            (src / "index.md").write_text(
                "---\n"
                "title: Hello\n"
                "template: src/child.html.temp\n"
                "---\n"
                "Body",
                encoding="utf-8",
            )

            config = {"src_dir": "src", "out_dir": "dist", "default_template": "src/page.html.temp", "site_url": "https://example.com", "plugins": []}
            built, _pages = gen.build_site(src, out, src / "page.html.temp", config)
            self.assertEqual(built, 1)

            output = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("<article>Hello</article>", output)
            self.assertNotIn("~{block", output)


if __name__ == "__main__":
    unittest.main()
