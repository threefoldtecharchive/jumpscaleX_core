from Jumpscale import j


class Packgesdocs2mdbook(j.baseclasses.object):
    __jslocation__ = "j.tools.packgesdocs2mdbook"

    def generate_summaries(self):
        """ Generate summaries for all packages """
        packages = j.tools.threebot_packages.find()
        for package in packages:
            pkg_wiki_path = package.path + "wiki/"
            if j.sal.fs.exists(path=pkg_wiki_path):
                self.generate_pkg_summary(name=package.name)

    def generate_pkg_summary(self, name):

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
            j.sal.fs.writeFile(filename=pkg_path + "wiki/README.md", contents=name)

        def dir_summary(path, indent):
            """
            Recursive generation of summary from md files
            @param path: path of the dir
            @param indent: lvl of indentation of the current dir in the summary file
            """
            md_files = j.sal.fs.listFilesInDir(path=path, filter="*.md", depth=0)
            for file in md_files:
                rel_path = file.replace(pkg_path + "wiki/", "")  # remove pkg/wiki/
                filename = j.sal.fs.getBaseName(file)  # file.md
                if filename == "README.md":
                    if rel_path == "README.md":  # readme in wiki dir
                        link_name = j.sal.fs.getDirName(path, levelsUp=0)
                    else:
                        link_name = j.sal.fs.getDirName(file, levelsUp=0)
                    self.summary += f"- [{link_name}]({rel_path})\n"
                else:
                    self.summary += f"{indent}- [{filename.rsplit('.', 1)[0]}]({rel_path})\n"

            dirs = j.sal.fs.listDirsInDir(path=path)
            for dir in dirs:
                dir_summary(dir, indent + "  ")

        dir_summary(path=pkg_path + "wiki", indent="")

        j.sal.fs.writeFile(filename=pkg_path + "wiki/SUMMARY.md", contents=self.summary)

    def generate_index_book(self):
        """ Generate index for all packages books """

        index_content = "# Index\n"

        # Create dir to copy package books into
        pkgs_books_path = j.sal.fs.joinPaths(j.dirs.TMPDIR, "pkgs_books")
        j.sal.fs.createDir(pkgs_books_path)

        packages = j.tools.threebot_packages.find()
        for package in packages:
            pkg_wiki_path = package.path + "wiki/"
            if j.sal.fs.exists(path=pkg_wiki_path):
                # Create dir with package name and copy the book into it
                dest_path = j.sal.fs.joinPaths(pkgs_books_path, package.name)
                j.sal.fs.createDir(dest_path)
                j.sal.fs.copyDirTree(src=pkg_wiki_path, dst=dest_path)

                if not j.sal.fs.exists(path=dest_path + "/SUMMARY.md"):
                    raise ValueError(package.name + " has no SUMMARY.md")

                pkg_summary = j.sal.fs.readFile(filename=dest_path + "/SUMMARY.md")
                # Indent pkg summary in index
                pkg_summary = "  ".join(("\n" + pkg_summary.lstrip()).splitlines(True))
                # Add package name to files pathes
                # TODO: may result in naming errors if file name contains ']('
                #       should find a better way
                pkg_summary = pkg_summary.replace("](", f"]({package.name}/")

                # Add a link to the package summary in the index
                index_content += "- [" + package.name + "](" + package.name + "/README.md)\n"
                index_content += pkg_summary

        # Generate index dir
        j.sal.fs.writeFile(filename=pkgs_books_path + "/SUMMARY.md", contents=index_content)
        indexbook_path = j.sal.fs.joinPaths(j.dirs.TMPDIR, "indexbook")
        j.sal.fs.createDir(indexbook_path)

        # Create new empty book
        toml_path = j.sal.fs.joinPaths(j.sal.fs.getDirName(__file__), "indexbook.toml")

        for directory in j.sal.fs.listDirsInDir(f"{indexbook_path}"):
            j.sal.fs.remove(directory)

        j.sal.fs.createDir(f"{indexbook_path}/book")
        j.sal.fs.createDir(f"{indexbook_path}/src")
        j.sal.fs.copyDirTree(f"{toml_path}", f"{indexbook_path}")

        # Copy packages books into the index book src dir
        for dir in j.sal.fs.listDirsInDir(f"{pkgs_books_path}"):
            j.sal.fs.moveDir(dir, f"{indexbook_path}/src/")
        for dir in j.sal.fs.listFilesInDir(f"{pkgs_books_path}"):
            j.sal.fs.moveFile(dir, f"{indexbook_path}/src/")

        # Build the mdbook
        j.sal.process.execute(f"cd {indexbook_path} && mdbook build")

        # Copy rendered book to mdbooks dir
        rendered_index_path = j.sal.fs.joinPaths(j.dirs.VARDIR, "mdbooks", "index")
        j.sal.fs.createDir(rendered_index_path)
        j.sal.fs.copyDirTree(src=indexbook_path + "/book", dst=rendered_index_path)
