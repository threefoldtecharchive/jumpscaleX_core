from Jumpscale import j


class MdBook(j.baseclasses.object):
    """
    load markdown with mdbook
    """

    __jslocation__ = "j.tools.mdbook"

    def _init(self):
        self.template_path = j.sal.fs.joinPaths(j.sal.fs.getDirName(__file__), "book.toml")
        self.output_path = j.sal.fs.joinPaths(j.dirs.VARDIR, "mdbooks")
        j.sal.fs.createDir(self.output_path)

    def save_config(self, name, source_path):
        dest_path = j.sal.fs.joinPaths(self.output_path, name)
        j.sal.fs.createDir(dest_path)

        toml_dest_path = j.sal.fs.joinPaths(source_path, "book.toml")
        j.tools.jinja2.template_render(path=self.template_path, dest=toml_dest_path, name=name, dest_path=dest_path)

    def load(self, name, source_path):
        self.save_config(name, source_path)
        j.sal.process.execute(f"cd {source_path} && mdbook build")

    def list_books(self):
        return j.sal.fs.listDirsInDir(self.output_path, dirNameOnly=True)

    def get_book_path(self, name):
        return j.sal.fs.joinPaths(self.output_path, name)
