from gen.html.elements import Element, Page, Text

def test():
    page = Page("html", {"lang": "en"})
    with page:
        title = Element("title")
    title.add(Text("The Void"))
    print(page.render())

test()
