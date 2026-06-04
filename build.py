from gen.ssg.build import GenSSG


def main():
    GenSSG().run("src", "dist")


if __name__ == "__main__":
    main()
