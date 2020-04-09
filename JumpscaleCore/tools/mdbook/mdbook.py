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

    def generate_summaries(self):
        """ Generate summaries for all packages """
        packages = j.tools.threebot_packages.find()
        for package in packages:
            pkg_wiki_path = package.path + 'wiki/'
            if j.sal.fs.exists(path=pkg_wiki_path):
                self.generate_pkg_summary(name=package.name)
    
    def generate_pkg_summary(self, name):

        #TODO: check failed links to readme files (readme-> index in mdbook build)
        #TODO: index.html in wiki (error)

        self.summary = ""
        pkg_path = ""
        if not j.tools.threebot_packages.find(name=name):
            raise ValueError(f"Package {name} does not exist")
        else:
            pkg_path = j.tools.threebot_packages.find(name=name)[0].path

        # Remove old summary and create README if not exists
        if j.sal.fs.exists(path=f"{pkg_path}/wiki/SUMMARY.md"):
            j.sal.fs.remove(path=f"{pkg_path}/wiki/SUMMARY.md")
        if not j.sal.fs.exists(path=f"{pkg_path}/wiki/README.md"):
            j.sal.fs.writeFile(filename=pkg_path+'wiki/README.md', contents=name)
        
        # Recursive generation of summary from md files
        def dir_summary(path, indent):
            """
            @param path: path of the dir
            @param indent: lvl of indentation of the current dir in the summary file
            """
            md_files = j.sal.fs.listFilesInDir(path=path, filter="*.md", depth=0)
            for file in md_files:
                rel_path = file.replace(pkg_path+'wiki/','') # remove pkg/wiki/
                filename = j.sal.fs.getBaseName(file)   # file.md
                if filename == 'README.md':
                    if rel_path == 'README.md': # readme in wiki dir
                        link_name = j.sal.fs.getDirName(path, levelsUp=0)
                    else:
                        link_name = j.sal.fs.getDirName(file, levelsUp=0)
                    self.summary += f"- [{link_name}]({rel_path})\n"
                else:
                    self.summary += f"{indent}- [{filename.rsplit('.', 1)[0]}]({rel_path})\n"
            
            dirs = j.sal.fs.listDirsInDir(path=path)
            for dir in dirs:
                dir_summary(dir, indent + '  ')

        dir_summary(path=pkg_path+'wiki', indent='')
        
        j.sal.fs.writeFile(filename=pkg_path+'wiki/SUMMARY.md', contents=self.summary)