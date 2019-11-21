import os
import random
import hashlib
import unittest
import time
from datetime import datetime
from pwd import getpwuid
from subprocess import run, PIPE
from string import punctuation

from Jumpscale import j
from parameterized import parameterized
from checksumdir import dirhash
import pickle

from .base_test import BaseTest, Testadd


class FS(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_dir = cls.random_string()
        cls.temp_path = os.path.join("/tmp", cls.temp_dir)
        j.sal.fs.createDir(cls.temp_path)

    @classmethod
    def tearDownClass(cls):
        j.sal.fs.remove(cls.temp_path)
        super().tearDownClass()

    def create_tree(self, symlinks=True):
        """Create a tree with many sub directories and files.
        """
        base_dir = os.path.join(self.temp_path, self.random_string())
        for _ in range(3):
            parent_name = self.random_string()
            parent_path = os.path.join(base_dir, parent_name)
            j.sal.fs.createDir(parent_path)

            types = ["logs", "txts", "pys", "mds", "symlinks"]
            for t in types:
                if not symlinks and t == "symlinks":
                    continue
                child_path = os.path.join(parent_path, t)
                j.sal.fs.createDir(child_path)

                for _ in range(3):
                    file_name = "{name}.{ext}".format(name=self.random_string(), ext=t[:-1])
                    file_path = os.path.join(child_path, file_name)
                    if t == "symlinks":
                        src = os.path.join(parent_path, "pys")
                        os.symlink(src, file_path, target_is_directory=True)
                        content = os.readlink(file_path)
                    elif t == "mds":
                        content = "{name}: " + self.random_string()
                        j.sal.fs.writeFile(file_path, content)
                    else:
                        content = self.random_string()
                        j.sal.fs.writeFile(file_path, content)

        files_ext = [".py", ".txt", ".log"]
        for ext in files_ext:
            file_name = self.random_string() + ext
            file_path = os.path.join(base_dir, file_name)
            j.sal.fs.createEmptyFile(file_path)

        link_name = self.random_string()
        link_path = os.path.join(base_dir, link_name)
        os.symlink(file_path, link_path)

        return base_dir

    def md5sum(self, file_or_dir):
        if not os.path.exists(file_or_dir):
            return False
        if os.path.isfile(file_or_dir):
            hash_md5 = hashlib.md5()
            with open(file_or_dir, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)

            return hash_md5.hexdigest()
        else:
            return dirhash(file_or_dir, hashfunc="md5")

    def list_files_dirs_in_dir(
        self, dir, files_list=True, dirs_list=True, followlinks=False, show_links=True, translate=True
    ):
        dirs_paths = []
        files_paths = []
        for root, dirs, files in os.walk(dir):
            for names in dirs:
                dir_path = os.path.join(root, names)
                if followlinks and os.path.islink(dir_path) and show_links:
                    list_dirs = self.list_files_dirs_in_dir(
                        os.readlink(dir_path),
                        files_list=files_list,
                        dirs_list=dirs_list,
                        followlinks=followlinks,
                        show_links=show_links,
                    )
                    for file_dir in list_dirs:
                        if os.path.isfile(file_dir):
                            files_paths.append(file_dir)
                        else:
                            dirs_paths.append(file_dir)

                if not show_links and os.path.islink(dir_path):
                    continue
                if show_links and os.path.islink(dir_path) and translate:
                    dir_path = os.readlink(dir_path)
                if not followlinks and show_links and not dirs_list and os.path.islink(dir_path):
                    files_paths.append(dir_path)

                dirs_paths.append(dir_path)

            if files_list:
                for names in files:
                    file_path = os.path.join(root, names)
                    if not show_links and os.path.islink(file_path):
                        continue
                    if show_links and os.path.islink(file_path) and translate:
                        file_path = os.readlink(file_path)
                    files_paths.append(file_path)

        if files_list and dirs_list:
            return dirs_paths + files_paths
        elif dirs_list and not files_list:
            return dirs_paths
        elif not dirs_list and files_list:
            return files_paths
        else:
            return []

    def test001_create_exist_move_rename_delete_dir(self):
        """TC340
        Test case for creating, moving, renaming and deleting directory.

        **Test scenario**
        #. Create a directory (D1) under /tmp.
        #. Check that (D1) is created.
        #. Move it to /tmp/(D2).
        #. Check that this directory is moved.
        #. Rename this directory to (D3).
        #. Check that (D3) is exists.
        #. Delete (D3) directory and check that it is not exists.
        """
        self.info("Create a directory (D1) under /tmp.")
        dir_name_1 = self.random_string()
        dir_path_1 = os.path.join(self.temp_path, dir_name_1)
        j.sal.fs.createDir(dir_path_1)

        self.info("Check that (D1) is created.")
        self.assertTrue(os.path.isdir(dir_path_1))
        self.assertTrue(j.sal.fs.isDir(dir_path_1))
        self.assertTrue(os.path.exists(dir_path_1))
        self.assertTrue(j.sal.fs.exists(dir_path_1))

        self.info("Move it to /tmp/(D2).")
        dir_name_2 = self.random_string()
        dir_path_2 = os.path.join(self.temp_path, dir_name_2)
        j.sal.fs.moveDir(dir_path_1, dir_path_2)

        self.info("Check that this directory is moved.")
        self.assertTrue(os.path.exists(dir_path_2))
        self.assertFalse(os.path.exists(dir_path_1))

        self.info("Rename this directory to (D3).")
        dir_name_3 = self.random_string()
        dir_path_3 = os.path.join(self.temp_path, dir_name_3)
        j.sal.fs.renameDir(dir_path_2, dir_path_3)

        self.info("Check that (D3) is exists.")
        self.assertTrue(os.path.exists(dir_path_3))
        self.assertFalse(os.path.exists(dir_path_2))

        self.info("Delete (D3) directory and check that it is not exists.")
        j.sal.fs.remove(dir_path_3)
        self.assertFalse(os.path.exists(dir_path_3))

    def test002_write_append_read_delete_file(self):
        """TC341
        Test case for writing, appending, reading and deleting file.

        **Test scenario**
        #. Write a file under /tmp.
        #. Check that the file is exists and check its content.
        #. Read this file using sal.fs and check that it has same content.
        #. Append content to this file.
        #. Check that file content, the new content should be found.
        #. Write to same file without appending.
        #. Check that the new content is only exists.
        #. Delete this file.
        """
        self.info("Write a file under /tmp.")
        file_name = self.random_string()
        file_content = self.random_string()
        file_path = os.path.join(self.temp_path, file_name)
        j.sal.fs.writeFile(filename=file_path, contents=file_content, append=False)

        self.info("Check that the file is exists and check its content.")
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(j.sal.fs.exists(file_path))
        self.assertTrue(os.path.isfile(file_path))
        self.assertTrue(j.sal.fs.isFile(file_path))
        with open(file_path, "r") as f:
            content_1 = f.read()
        self.assertEquals(content_1, file_content)

        self.info("Read this file using sal.fs and check that it has same content.")
        content_2 = j.sal.fs.readFile(file_path)
        self.assertEquals(content_2, file_content)

        self.info("Append content to this file.")
        append = self.random_string()
        j.sal.fs.writeFile(filename=file_path, contents=append, append=True)

        self.info("Check that file content, the new content should be found.")
        with open(file_path, "r") as f:
            new_content_1 = f.read()
        self.assertEquals(new_content_1, file_content + append)

        self.info("Write to same file without appending.")
        j.sal.fs.writeFile(filename=file_path, contents=append, append=False)

        self.info("Check that the new content is only exists.")
        with open(file_path, "r") as f:
            new_content_2 = f.read()
        self.assertEquals(new_content_2, append)

        self.info("Delete this file.")
        j.sal.fs.remove(file_path)
        self.assertFalse(os.path.exists(file_path))

    def test003_create_move_rename_copy_file(self):
        """TC342
        Test case for creating, moving, renaming and copying files.

        **Test scenario**
        #. Create an empty file.
        #. Check that the file is exists.
        #. Create a directory and move this file to this directory.
        #. Check that the file is moved.
        #. Rename this file and Check that the file is renamed.
        #. Copy this file to a non-existing directory, should fail.
        #. Copy this file to a non-existing directory with createDirIfNeeded=True, should success.
        #. Check that file is copied.
        #. Write a word to the copied file.
        #. Try to copy this file again to the same directory with overwriteFile=False.
        #. Check the content of the copied file, should not be changed.
        #. Try again to copy this file to the same directory with overwriteFile=True.
        #. Check the content of the copied file, should be changed.
        """
        self.info("Create an empty file.")
        file_name_1 = self.random_string()
        file_path_1 = os.path.join(self.temp_path, file_name_1)
        j.sal.fs.createEmptyFile(file_path_1)

        self.info("Check that the file is exists.")
        self.assertTrue(os.path.exists(file_path_1))

        self.info("Create a directory and move this file to this directory.")
        dir_name_1 = self.random_string()
        dir_path_1 = os.path.join(self.temp_path, dir_name_1)
        j.sal.fs.createDir(dir_path_1)
        j.sal.fs.moveFile(file_path_1, dir_path_1)

        self.info("Check that the file is moved.")
        file_path_2 = os.path.join(dir_path_1, file_name_1)
        self.assertTrue(os.path.exists(file_path_2))
        self.assertFalse(os.path.exists(file_path_1))

        self.info("Rename this file and Check that the file is renamed.")
        file_name_2 = self.random_string()
        file_path_3 = os.path.join(dir_path_1, file_name_2)
        j.sal.fs.renameFile(file_path_2, file_path_3)
        self.assertTrue(os.path.exists(file_path_3))
        self.assertFalse(os.path.exists(file_path_2))

        self.info("Copy this file to a non-existing directory, should fail.")
        dir_name_2 = self.random_string()
        dir_path_2 = os.path.join(self.temp_path, dir_name_2)
        file_path_4 = os.path.join(dir_path_2, file_name_2)
        with self.assertRaises(Exception):
            j.sal.fs.copyFile(file_path_3, file_path_4, createDirIfNeeded=False)

        self.info("Copy this file to a non-existing directory with createDirIfNeeded=True, should success.")
        j.sal.fs.copyFile(file_path_3, file_path_4, createDirIfNeeded=True)

        self.info("Check that file is copied.")
        self.assertTrue(os.path.exists(file_path_4))
        self.assertTrue(os.path.exists(file_path_3))

        self.info("Write a word (W) to the copied file.")
        file_content = self.random_string()
        j.sal.fs.writeFile(file_path_3, file_content)

        self.info("Try to copy this file again to the same directory with overwriteFile=False.")
        j.sal.fs.copyFile(file_path_4, file_path_3, overwriteFile=False)

        self.info("Check the content of the copied file, should not be changed.")
        content_1 = j.sal.fs.readFile(file_path_3)
        self.assertEquals(content_1, file_content)

        self.info("Try again to copy this file to the same directory with overwriteFile=True.")
        j.sal.fs.copyFile(file_path_4, file_path_3, overwriteFile=True)

        self.info("Check the content of the copied file, should be changed.")
        content_1 = j.sal.fs.readFile(file_path_3)
        self.assertNotEquals(content_1, file_content)

    @parameterized.expand([(True,), (False,)])
    def test004_copy_dir_tree_symlinks(self, keep_links):
        """TC343
        Test case for copying tree with keepsymlinks.

        **Test scenario**
        #. Create a tree with many sub directories, files and symlinks.
        #. Copy this tree with keepsymlinks=True.
        #. Compare copied tree with original one, should be the same.
        #. Copy this tree with keepsymlinks=False.
        #. Compare copied tree with the original one, should not be the same.
        """
        self.info("Create a tree with many sub directories, files and symlinks.")
        base_dir = self.create_tree()

        self.info(f"Copy this tree with keepsymlinks={keep_links}.")
        dir_name = self.random_string()
        dir_path = os.path.join(self.temp_path, dir_name)
        j.sal.fs.copyDirTree(base_dir, dir_path, keepsymlinks=keep_links)

        self.info("Compare copied tree with original one.")
        origial_md5 = self.md5sum(base_dir)
        copied_md5 = self.md5sum(dir_path)
        if keep_links:
            self.assertEquals(copied_md5, origial_md5)
        else:
            self.assertNotEquals(copied_md5, origial_md5)

    @parameterized.expand([(True,), (False,)])
    def test005_copy_dir_tree_delete_first(self, delete_first):
        """TC343
        Test case for copying tree with deleting the destination before copying.

        **Test scenario**
        #. Create a tree with many sub directories, files and symlinks.
        #. Copy this tree to another directory.
        #. Change the content of some files in the destination directory.
        #. Copy this tree with deletefirst=False and destination must be the copied tree.
        #. Compare the copied tree with original one, should not be the same.
        #. Copy this tree with deletefirst=True and destination must be the copied tree.
        #. Compare the copied tree with original one, should be the same.
        """
        self.info("Create a tree with many sub directories, files and symlinks.")
        base_dir = self.create_tree()

        self.info("Copy this tree to another directory.")
        dir_name = self.random_string()
        dir_path = os.path.join(self.temp_path, dir_name)
        j.sal.fs.copyDirTree(base_dir, dir_path, keepsymlinks=True)

        self.info("Change the content of some files in the destination directory.")
        content = self.random_string()
        files = [x for x in self.list_files_dirs_in_dir(base_dir) if ".md" in x]
        for path in files:
            j.sal.fs.writeFile(path, content)

        self.info(f"Copy this tree with deletefirst={delete_first} and destination must be the copied tree.")
        j.sal.fs.copyDirTree(
            base_dir,
            dir_path,
            keepsymlinks=True,
            deletefirst=delete_first,
            rsyncdelete=False,
            rsync=False,
            overwriteFiles=False,
        )

        self.info("Compare the copied tree with original one.")
        origial_md5 = self.md5sum(base_dir)
        copied_md5 = self.md5sum(dir_path)
        if delete_first:
            self.assertEquals(copied_md5, origial_md5)
        else:
            self.assertNotEquals(copied_md5, origial_md5)

    @parameterized.expand([(True,), (False,)])
    def test006_copy_dir_tree_overwrite(self, overwrite):
        """TC343
        Test case for copying tree with overwritting files.

        **Test scenario**
        #. Create a tree with many sub directories, files and symlinks.
        #. Copy this tree to another directory.
        #. Change the content of some files in the original directory.
        #. Copy the tree to the same destination directory with overwriteFiles=False.
        #. Check the changed files, should be the same.
        #. Copy the tree to the same destination directory with overwriteFiles=True.
        #. Check the changed files, should be changed to the original.
        """
        self.info("Create a tree with many sub directories, files and symlinks.")
        base_dir = self.create_tree()
        origial_md5 = self.md5sum(base_dir)

        self.info("Copy this tree to another directory.")
        dir_name = self.random_string()
        dir_path = os.path.join(self.temp_path, dir_name)
        j.sal.fs.copyDirTree(base_dir, dir_path, keepsymlinks=True)

        self.info("Change the content of some files in the original directory.")
        content = self.random_string()
        files = [os.path.join(base_dir, x) for x in os.listdir(base_dir) if ".txt" in x]
        for path in files:
            j.sal.fs.writeFile(path, content)

        self.info(f"Copy the tree to the same destination directory with overwriteFiles={overwrite}.")
        j.sal.fs.copyDirTree(base_dir, dir_path, keepsymlinks=True, overwriteFiles=overwrite)

        self.info("Check the changed files.")
        origial_md5_new = self.md5sum(base_dir)
        copied_md5 = self.md5sum(dir_path)
        if overwrite:
            self.assertEquals(copied_md5, origial_md5_new)
        else:
            self.assertNotEquals(copied_md5, origial_md5_new)
            self.assertEquals(copied_md5, origial_md5)

    def test007_copy_dir_tree_ignore_files_dirs(self):
        """TC343
        Test case for copying tree with ignoring files and directories.

        **Test scenario**
        #. Create a tree with many sub directories, files and symlinks.
        #. Copy this tree with ignoring list of files.
        #. Check that these files are not in copied tree.
        #. Copy this tree with recursive=False.
        #. Check that files and directories of sub directories are not exists.
        """
        self.info("Create a tree with many sub directories, files and symlinks.")
        base_dir = self.create_tree()

        self.info("Copy the tree with ignoring sub directory.")
        dir_name = self.random_string()
        dir_path = os.path.join(self.temp_path, dir_name)
        ignored_dir = [x for x in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, x))][0]
        j.sal.fs.copyDirTree(base_dir, dir_path, keepsymlinks=True, ignoredir=[ignored_dir])

        self.info("Check that this directory is not copied.")
        ignored_path = os.path.join(dir_path, ignored_dir)
        dest_dirs = [
            os.path.join(dir_path, x) for x in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, x))
        ]
        self.assertNotIn(ignored_dir, dest_dirs)

        self.info("Delete this tree")
        j.sal.fs.remove(dir_path)

        self.info("Copy this tree with ignoring list of files.")
        paths = [x for x in self.list_files_dirs_in_dir(base_dir) if ".txt" in x]

        names = []
        for path in paths:
            names.append(path.split("/")[-1])
        j.sal.fs.copyDirTree(base_dir, dir_path, keepsymlinks=True, ignorefiles=names, rsync=False)

        self.info("Check that these files are not in copied tree.")
        paths = [x for x in self.list_files_dirs_in_dir(dir_path) if ".txt" in x]
        for path in paths:
            self.assertFalse(os.path.exists(path))

    @parameterized.expand([(True,), (False,)])
    def test008_copy_dir_tree_rsync_delete(self, rsync_delete):
        """TC343
        Test case for copying tree with deleting files and directories before start copying.

        **Test scenario**
        #. Create a tree with many sub directories, files and symlinks.
        #. Copy this tree to directory contains different files with rsyncdelete=False.
        #. Check that the destination has its original files.
        #. Copy this tree to directory contains different files with rsyncdelete=True.
        #. Check that the destination has not its original files.
        """
        self.info("Create a tree with many sub directories, files and symlinks.")
        base_dir = self.create_tree()

        self.info(f"Copy this tree to directory contains different files with rsyncdelete={rsync_delete}.")
        base_dir_2 = self.create_tree()
        j.sal.fs.copyDirTree(base_dir, base_dir_2, keepsymlinks=True, rsyncdelete=rsync_delete)

        self.info("Check that the destination.")
        copied_md5 = self.md5sum(base_dir_2)
        origial_md5_new = self.md5sum(base_dir)
        if rsync_delete:
            self.assertEquals(copied_md5, origial_md5_new)
        else:
            self.assertNotEquals(copied_md5, origial_md5_new)

    @parameterized.expand([(True,), (False,)])
    def test009_copy_dir_tree_recursive(self, recursive):
        """TC343
        Test case for copying tree recursively.

        **Test scenario**
        #. Create a tree with many sub directories, files and symlinks.
        #. Copy this tree with recursive=False.
        #. Check that files and directories of sub directories are not exists.
        #. Copy this tree with recursive=True.
        #. Check that files and directories are exists.
        """
        self.info("Create a tree with many sub directories, files and symlinks.")
        base_dir = self.create_tree()

        self.info(f"Copy this tree with recursive={recursive}.")
        dir_name = self.random_string()
        dir_path = os.path.join(self.temp_path, dir_name)
        j.sal.fs.copyDirTree(base_dir, dir_path, keepsymlinks=True, recursive=recursive)

        self.info("Check that all sub directories.")
        if recursive:
            origial_md5 = self.md5sum(base_dir)
            copied_md5 = self.md5sum(dir_path)
            self.assertEquals(copied_md5, origial_md5)
        else:
            files = [os.path.join(dir_path, x) for x in os.listdir(dir_path)]
            for file in files:
                self.assertTrue(os.path.isfile(file))

    @parameterized.expand([(True,), (False,)])
    def test010_list_dirs_in_dir_recursively(self, recursive):
        """TC344
        Test case for listing directories in a directory recursively.

        **Test scenario**
        #. Create a tree with many subdirectories.
        #. List the parent directory of this tree with recursive=False, should return the full path of the children only.
        #. List the parent directory of this tree with recursive=True, should return the full path of all subdirectories.
        #. List the parent directory of this tree with dirNameOnly=True, should return only the names of directories.
        """
        self.info("Create a tree with many subdirectories.")
        base_dir = self.create_tree()

        self.info(f"List the parent directory of this tree with recursive={recursive}.")
        dirs_list = j.sal.fs.listDirsInDir(
            base_dir, recursive=recursive, followSymlinks=False, findDirectorySymlinks=True
        )
        if recursive:
            dirs_paths = self.list_files_dirs_in_dir(
                base_dir, files_list=False, dirs_list=True, followlinks=False, translate=False
            )
            self.assertEquals(sorted(dirs_paths), sorted(dirs_list))
        else:
            list_dirs = os.listdir(base_dir)
            list_dirs_paths = [
                os.path.join(base_dir, dir) for dir in list_dirs if os.path.isdir(os.path.join(base_dir, dir))
            ]
            self.assertEquals(dirs_list, list_dirs_paths)

        self.info("List the parent directory of this tree with dirNameOnly=True")
        dirs_list = j.sal.fs.listDirsInDir(base_dir, recursive=recursive, dirNameOnly=True)
        if recursive:
            list_dirs = self.list_files_dirs_in_dir(
                base_dir, dirs_list=True, files_list=False, followlinks=True, translate=False
            )
            list_dirs = [x.split(os.sep)[-1] for x in list_dirs]
            self.assertEquals(sorted(dirs_list), sorted(list_dirs))
        else:
            list_dirs = [dir for dir in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, dir))]
            self.assertEquals(dirs_list, list_dirs)

    @parameterized.expand([[True, True], [True, False], [False, True], [False, False]])
    def test011_list_dirs_in_dir_symlinks(self, followlinks, findDirectorySymlinks):
        """TC344
        Test case for listing directories in a directory recursively.

        **Test scenario**
        #. Create a tree with many subdirectories.
        #. List the parent directory of this tree with findDirectorySymlinks=True and followSymlinks=True, should return all directories paths (inculded symlinks)
        #. List the parent directory of this tree with findDirectorySymlinks=True and followSymlinks=False, should return this tree.
        #. List the parent directory of this tree with findDirectorySymlinks=False and followSymlinks=True, should return all directories without symlinks.
        #. List the parent directory of this tree with findDirectorySymlinks=False and followSymlinks=False, should return this tree without symlinks.
        """
        self.info("Create a tree with many subdirectories.")
        base_dir = self.create_tree()

        self.info(
            f"List the parent directory of this tree with findDirectorySymlinks={findDirectorySymlinks} and followSymlinks={followlinks}."
        )
        dirs_list = j.sal.fs.listDirsInDir(
            base_dir, recursive=True, findDirectorySymlinks=findDirectorySymlinks, followSymlinks=followlinks
        )
        dirs_paths = self.list_files_dirs_in_dir(
            base_dir,
            files_list=False,
            dirs_list=True,
            show_links=findDirectorySymlinks,
            followlinks=followlinks,
            translate=False,
        )
        self.assertEquals(sorted(dirs_paths), sorted(dirs_list))

    @parameterized.expand([(True,), (False,)])
    def test012_list_files_and_dirs_in_dir_recursively(self, recursive):
        """TC345
        Test case for listing files and directories in a directory recursively.

        **Test scenario**
        #. Create a tree with many sub directories and files.
        #. List the parent directory of this tree with recursive=False, should return the children only.
        #. List the parent directory of this tree with recursive=True, should return all sub directory.
        """
        self.info("Create a tree with many sub directories and files.")
        base_dir = self.create_tree()

        self.info("List the parent directory of this tree with recursive={recursive}")
        dirs_files_list = j.sal.fs.listFilesAndDirsInDir(
            base_dir, recursive=recursive, followSymlinks=False, listSymlinks=True
        )

        if recursive:
            list_dirs_files = self.list_files_dirs_in_dir(
                base_dir, files_list=True, dirs_list=True, followlinks=False, show_links=True, translate=False
            )
            self.assertEquals(sorted(dirs_files_list), sorted(list_dirs_files))
        else:
            list_dirs_files = os.listdir(base_dir)
            list_dirs_files_paths = [os.path.join(base_dir, dir) for dir in list_dirs_files]
            self.assertEquals(dirs_files_list, list_dirs_files_paths)

    def test013_list_files_and_dirs_in_dir_filter(self):
        """TC345
        Test case for listing files and directories in a directory with filter.

        **Test scenario**
        #. Create a tree with many sub directories and files.
        #. List the parent directory of this tree using filter=*.txt, should return all files and directories with .txt.
        #. List the parent directory of this tree with depth=1, should return only its children.
        #. List the parent directory of this tree with type="f", should return only the files.
        #. List the parent directory of this tree with type="d", should return only the directories.
        """
        self.info("Create a tree with many sub directories and files.")
        base_dir = self.create_tree()

        self.info(
            "List the parent directory of this tree using filter=*.txt, should return all files and directories with .txt."
        )
        dirs_files_list = j.sal.fs.listFilesAndDirsInDir(
            base_dir, recursive=True, followSymlinks=False, listSymlinks=False, filter="*.txt"
        )
        list_dirs_files = self.list_files_dirs_in_dir(
            base_dir, files_list=True, dirs_list=True, followlinks=False, show_links=False
        )
        filtered_list = [path for path in list_dirs_files if ".txt" in path.split("/")[-1]]
        self.assertEquals(sorted(dirs_files_list), sorted(filtered_list))

        self.info("List the parent directory of this tree with depth=1, should return only its children.")
        dirs_files_list = j.sal.fs.listFilesAndDirsInDir(
            base_dir, recursive=True, followSymlinks=False, listSymlinks=True, depth=1
        )
        list_dirs_files = os.listdir(base_dir)
        list_dirs_files_paths = [os.path.join(base_dir, dir) for dir in list_dirs_files]
        self.assertEquals(dirs_files_list, list_dirs_files_paths)

        self.info("List the parent directory of this tree with type='f', should return only the files.")
        dirs_files_list = j.sal.fs.listFilesAndDirsInDir(
            base_dir, recursive=True, followSymlinks=False, listSymlinks=False, type="f"
        )
        list_dirs_files = self.list_files_dirs_in_dir(
            base_dir, files_list=True, dirs_list=False, followlinks=False, show_links=False
        )
        self.assertEquals(sorted(dirs_files_list), sorted(list_dirs_files))

        self.info("List the parent directory of this tree with type='d', should return only the directories.")
        dirs_files_list = j.sal.fs.listFilesAndDirsInDir(
            base_dir, recursive=True, followSymlinks=False, listSymlinks=False, type="d"
        )
        list_dirs_files = self.list_files_dirs_in_dir(
            base_dir, files_list=False, dirs_list=True, followlinks=False, show_links=False
        )
        self.assertEquals(sorted(dirs_files_list), sorted(list_dirs_files))

    def test014_list_files_and_dirs_in_dir_modification_time(self):
        """TC345
        Test case for listing files and directories in a directory depending on modification time.

        **Test scenario**
        #. Create a tree with many sub directories and files.
        #. Modify a file and take timestamp of now (T1).
        #. List the parent directory of this tree with minmtime=T1 + 2, should not find the modified file.
        #. List the parent directory of this tree with minmtime=T1 - 2, should find the modified file.
        #. List the parent directory of this tree with maxmtime=T1 + 2, should find the modified file.
        #. List the parent directory of this tree with maxmtime=T1 - 2, should not find the modified file.
        """
        self.info("Create a tree with many sub directories and files.")
        base_dir = self.create_tree()

        self.info("Modify a file and take timestamp of now (T1).")
        list_dirs_files = os.listdir(base_dir)
        file = [file for file in list_dirs_files if os.path.isfile(os.path.join(base_dir, file))][0]
        dir_name = self.random_string()
        dir_path = os.path.join(base_dir, dir_name)
        file_path = os.path.join(dir_path, file)
        content = self.random_string()
        time.sleep(4)
        j.sal.fs.createDir(dir_path)
        j.sal.fs.writeFile(file_path, content)

        now = datetime.now().timestamp()

        self.info("List the parent directory of this tree with minmtime=T1 + 2, should not find the modified file.")
        dirs_files_list = j.sal.fs.listFilesAndDirsInDir(
            base_dir, recursive=True, followSymlinks=False, listSymlinks=False, minmtime=now + 2
        )
        self.assertNotIn(file_path, dirs_files_list)
        self.assertNotIn(dir_path, dirs_files_list)

        self.info("List the parent directory of this tree with minmtime=T1 - 2, should find the modified file.")
        dirs_files_list = j.sal.fs.listFilesAndDirsInDir(
            base_dir, recursive=True, followSymlinks=False, listSymlinks=False, minmtime=now - 2
        )
        self.assertIn(file_path, dirs_files_list)
        self.assertIn(dir_path, dirs_files_list)

        self.info("List the parent directory of this tree with maxmtime=T1 + 2, should find the modified file.")
        dirs_files_list = j.sal.fs.listFilesAndDirsInDir(
            base_dir, recursive=True, followSymlinks=False, listSymlinks=False, maxmtime=now + 2
        )
        self.assertIn(file_path, dirs_files_list)
        self.assertIn(dir_path, dirs_files_list)

        self.info("List the parent directory of this tree with maxmtime=T1 - 2, should not find the modified file.")
        dirs_files_list = j.sal.fs.listFilesAndDirsInDir(
            base_dir, recursive=True, followSymlinks=False, listSymlinks=False, maxmtime=now - 2
        )
        self.assertNotIn(file_path, dirs_files_list)
        self.assertNotIn(dir_path, dirs_files_list)

    @parameterized.expand([[True, True], [True, False], [False, True], [False, False]])
    def test015_list_files_and_dirs_in_dir_symlinks(self, list_links, follow_links):
        """TC345
        Test case for listing files and directories in a directory with following symlinks.

        **Test scenario**
        #. Create a tree with many sub directories and files.
        #. List the parent directory of this tree with listSymlinks=True and followSymlinks=True, should return all directories and files paths (inculded symlinks)
        #. List the parent directory of this tree with listSymlinks=True and followSymlinks=False, should return this tree.
        #. List the parent directory of this tree with listSymlinks=False and followSymlinks=True, should return all directories and files without symlinks.
        #. List the parent directory of this tree with listSymlinks=False and followSymlinks=False, should return this tree without symlinks.
        """
        self.info("Create a tree with many sub directories and files.")
        base_dir = self.create_tree()

        self.info(
            f"List the parent directory of this tree with listSymlinks={list_links} and followSymlinks={list_links}"
        )
        dirs_files_list = j.sal.fs.listFilesAndDirsInDir(
            base_dir, recursive=True, listSymlinks=list_links, followSymlinks=follow_links
        )
        list_dirs_files = self.list_files_dirs_in_dir(
            base_dir,
            files_list=True,
            dirs_list=True,
            show_links=list_links,
            followlinks=follow_links,
            translate=not list_links or follow_links,
        )
        self.assertEquals(sorted(dirs_files_list), sorted(list_dirs_files))

    @parameterized.expand([(True,), (False,)])
    def test016_list_files_in_dir_recursively(self, recursive):
        """TC346
        Test case for listing files in directory recursively.

        **Test scenario**
        #. Create a tree with many sub directories and files.
        #. List the parent directory of this tree with recursive=False, should return the children files only.
        #. List the parent directory of this tree with recursive=True, should return all files.
        """
        self.info("Create a tree with many sub directories and files.")
        base_dir = self.create_tree()

        self.info(
            f"List the parent directory of this tree with recursive={recursive}, should return the children files only."
        )
        files = j.sal.fs.listFilesInDir(base_dir, recursive=recursive, listSymlinks=True)

        if recursive:
            files_list = self.list_files_dirs_in_dir(
                base_dir, files_list=True, dirs_list=False, show_links=True, followlinks=False, translate=False
            )
            self.assertEquals(sorted(files), sorted(files_list))
        else:
            files_list = [
                os.path.join(base_dir, x) for x in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, x))
            ]
            self.assertEquals(sorted(files), sorted(files_list))

    def test017_list_files_in_dir_filter(self):
        """TC346
        Test case for listing files in directory with filter.

        **Test scenario**
        #. Create a tree with many sub directories and files.
        #. List the parent directory of this tree using filter=*.txt, should return all files with dot.
        #. List the parent directory of this tree with depth=1, should return only its children files.
        """
        self.info("Create a tree with many sub directories and files.")
        base_dir = self.create_tree()

        self.info("List the parent directory of this tree using filter=*.txt, should return all txt files.")
        files = j.sal.fs.listFilesInDir(base_dir, recursive=True, filter="*.txt")
        files_list = [
            x
            for x in self.list_files_dirs_in_dir(
                base_dir, files_list=True, dirs_list=False, show_links=False, followlinks=False, translate=False
            )
            if ".txt" in x
        ]
        self.assertEquals(sorted(files), sorted(files_list))

        self.info("List the parent directory of this tree with depth=1, should return only its children files.")
        files = j.sal.fs.listFilesInDir(base_dir, depth=1, listSymlinks=True)
        files_list = [
            os.path.join(base_dir, x) for x in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, x))
        ]
        self.assertEquals(sorted(files), sorted(files_list))

    def test018_list_files_in_dir_modification_time(self):
        """TC346
        Test case for listing files in directory depending on modification time.

        **Test scenario**
        #. Create a tree with many sub directories and files.
        #. Modify a file and take timestamp of now (T1).
        #. List the parent directory of this tree with minmtime=T1 + 2, should not find the modified file.
        #. List the parent directory of this tree with minmtime=T1 - 2, should file the modified file.
        #. List the parent directory of this tree with maxmtime=T1 + 2, should file the modified file.
        #. List the parent directory of this tree with maxmtime=T1 - 2, should not file the modified file.
        """
        self.info("Create a tree with many sub directories and files.")
        base_dir = self.create_tree()

        self.info("Modify a file and take timestamp of now (T1).")
        list_dirs_files = os.listdir(base_dir)
        file = [file for file in list_dirs_files if os.path.isfile(os.path.join(base_dir, file))][0]
        file_path = os.path.join(base_dir, file)
        content = self.random_string()
        time.sleep(4)
        j.sal.fs.writeFile(file_path, content)
        now = datetime.now().timestamp()

        self.info("List the parent directory of this tree with minmtime=T1 + 2, should not find the modified file.")
        files = j.sal.fs.listFilesInDir(
            base_dir, recursive=True, followSymlinks=False, listSymlinks=False, minmtime=now + 2
        )
        self.assertNotIn(file_path, files)

        self.info("List the parent directory of this tree with minmtime=T1 - 2, should file the modified file.")
        files = j.sal.fs.listFilesInDir(
            base_dir, recursive=True, followSymlinks=False, listSymlinks=False, minmtime=now - 2
        )
        self.assertIn(file_path, files)

        self.info("List the parent directory of this tree with maxmtime=T1 + 2, should file the modified file.")
        files = j.sal.fs.listFilesInDir(
            base_dir, recursive=True, followSymlinks=False, listSymlinks=False, maxmtime=now + 2
        )
        self.assertIn(file_path, files)

        self.info("List the parent directory of this tree with maxmtime=T1 - 2, should not file the modified file.")
        files = j.sal.fs.listFilesInDir(
            base_dir, recursive=True, followSymlinks=False, listSymlinks=False, maxmtime=now - 2
        )
        self.assertNotIn(file_path, files)

    @parameterized.expand(
        [
            ["insensitive", "insensitive"],
            ["sensitive", "insensitive"],
            ["insensitive", "sensitive"],
            ["sensitive", "sensitive"],
            ["os", "sensitive"],
            ["os", "insensitive"],
        ]
    )
    def test019_list_files_in_dir_exclude_with_sensitivity(self, filter_case, file_case):
        """TC346
        Test case for listing files in directory with excluding files with their case sensitvity.

        **Test scenario**
        #. Create a tree with many sub directories and files.
        #. Create a file (F1) with upper and lower cases in its name.
        #. List the parent directory of this tree with case_sensitive="insensitive" and exclude=[F1] (F1 should be case insensitive), should return all files except F1.
        #. List the parent directory of this tree with case_sensitive="sensitive" and exclude=[F1] (F1 should be case insensitive), should return all files.
        #. List the parent directory of this tree with case_sensitive="insensitive" and exclude=[F1] (F1 should be case sensitive), should return all files except F1.
        #. List the parent directory of this tree with case_sensitive="sensitive" and exclude=[F1] (F1 should be case sensitive), should return all files except F1.
        #. List the parent directory of this tree with case_sensitive="os" and exclude=[F1] (F1 should be case sensitive), should return all files except F1.
        #. List the parent directory of this tree with case_sensitive="os" and exclude=[F1] (F1 should be case insensitive), should return all files.
        """
        self.info("Create a tree with many sub directories and files.")
        base_dir = self.create_tree()

        self.info("Create a file (F1) with upper and lower cases in its name.")
        file_name = "TEST_file"
        file_path = os.path.join(base_dir, file_name)
        j.sal.fs.touch(file_path)

        self.info(
            f"List the parent directory of this tree with case_sensitive={filter_case} and exclude=[F1] (F1 should be case {file_case})."
        )
        if file_case == "insensitive":
            file_name = file_name.lower()

        files = j.sal.fs.listFilesInDir(base_dir, case_sensitivity=filter_case, exclude=[file_name])
        if filter_case in ["sensitive", "os"] and file_case == "insensitive":
            self.assertIn(file_path, files)
        else:
            self.assertNotIn(file_path, files)

    @parameterized.expand([[True, True], [True, False], [False, True], [False, False]])
    def test020_list_files_in_dir_symlinks(self, list_links, follow_links):
        """TC346
        Test case for listing files in directory with symlinks.

        **Test scenario**
        #. Create a tree with many sub directories and files.
        #. List the parent directory of this tree with listSymlinks=True and followSymlinks=True, should return all files paths (inculded symlinks).
        #. List the parent directory of this tree with listSymlinks=True and followSymlinks=False, should return this tree files.
        #. List the parent directory of this tree with listSymlinks=False and followSymlinks=True, should return all files without symlinks.
        #. List the parent directory of this tree with listSymlinks=False and followSymlinks=False, should return this tree files without symlinks.
        """
        self.info("Create a tree with many sub directories and files.")
        base_dir = self.create_tree()

        self.info(
            f"List the parent directory of this tree with listSymlinks={list_links} and followSymlinks={follow_links}."
        )
        files = j.sal.fs.listFilesInDir(base_dir, recursive=True, listSymlinks=list_links, followSymlinks=follow_links)
        files_list = self.list_files_dirs_in_dir(
            base_dir,
            files_list=True,
            dirs_list=False,
            show_links=list_links,
            followlinks=follow_links,
            translate=not list_links or follow_links,
        )
        self.assertEquals(sorted(files), sorted(files_list))

    def test_021_list_py_scrpits(self):
        """TC347
        Test case for listing python scripts using j.sal.fs.listPyScriptsInDir.

        **Test scenario**
        #. Create a tree with many sub directories and different files (must contain python files).
        #. List the parent directory of this tree with recursive=False, should return its children python scripts.
        #. List the parent directory of this tree with recursive=True, should return all python scripts under this tree.
        #. Create a python file with special word (W) in its name.
        #. List the parent directory of this tree with (W) as a filter, should return only this script.
        """
        self.info("Create a tree with many sub directories and different files (must contain python files).")
        base_dir = self.create_tree(symlinks=False)

        self.info(
            "List the parent directory of this tree with recursive=False, should return its children python scripts."
        )
        py_files_list = j.sal.fs.listPyScriptsInDir(base_dir, recursive=False)
        py_file = [os.path.join(base_dir, x) for x in os.listdir(base_dir) if ".py" in x]
        self.assertEquals(py_files_list, py_file)

        self.info(
            "List the parent directory of this tree with recursive=True, should return all python scripts under this tree."
        )
        py_files_list = j.sal.fs.listPyScriptsInDir(base_dir, recursive=True)
        py_files = [
            x
            for x in self.list_files_dirs_in_dir(
                base_dir, files_list=True, dirs_list=False, followlinks=False, show_links=False
            )
            if ".py" in x
        ]
        self.assertEquals(sorted(py_files_list), sorted(py_files))

        self.info("Create a python file with special word (W) in its name.")
        word = self.random_string()
        file_path = f"{base_dir}/{word}.py"
        j.sal.fs.createEmptyFile(file_path)

        self.info("List the parent directory of this tree with (W) as a filter, should return only this script. ")
        py_files_list = j.sal.fs.listPyScriptsInDir(base_dir, filter=f"{word}*", recursive=True)
        self.assertEquals([file_path], py_files_list)

    def test_022_file_permissions(self):
        """TC348
        Test case for changing files permissions.

        **Test scenario**
        #. Create an empty file.
        #. Change this file's permissions.
        #. Check the this file's permissions, should be changed.
        #. Create a user (U)
        #. Change this file's user to (U).
        #. Check that file's user has been changed.
        #. Change this file's group.
        #. Check that file's group has been changed.
        """
        self.info("Create an empty file.")
        file_name = self.random_string()
        file_path = os.path.join(self.temp_path, file_name)
        j.sal.fs.createEmptyFile(file_path)

        self.info("Change this file's permissions.")
        permissions = 0o646
        j.sal.fs.chmod(file_path, permissions)

        self.info("Check the this file's permissions, should be changed.")
        stat = os.stat(file_path).st_mode & 0o777
        self.assertEquals(stat, permissions)

        self.info("Create a user (U)")
        user_name = self.random_string()
        os.system("useradd {}".format(user_name))

        self.info("Change this file's user to (U).")
        j.sal.fs.chown(file_path, user_name)

        self.info("Check that file's user has been changed.")
        stat = os.stat(file_path)
        user_id = stat.st_uid
        group_id = stat.st_gid
        user = getpwuid(user_id).pw_name
        group = getpwuid(group_id).pw_name
        self.assertEquals(user, user_name)
        self.assertEquals(user, group)

        self.info("Change this file's group.")
        group_name = self.random_string()
        os.system("useradd {}".format(group_name))
        j.sal.fs.chown(file_path, user_name, group_name)

        self.info("Check that file's group has been changed")
        stat = os.stat(file_path)
        user_id = stat.st_uid
        group_id = stat.st_gid
        user = getpwuid(user_id).pw_name
        group = getpwuid(group_id).pw_name
        self.assertEquals(user, user_name)
        self.assertEquals(group_name, group)

        self.info("Delete these users has been added")
        os.system("userdel {}".format(group_name))
        os.system("userdel {}".format(user_name))

    def test023_file_linking(self):
        """TC349
        Test case for linking and unlinking files.

        **Test scenario**
        #. Create a file.
        #. Create a symlink (S) to this file.
        #. Check that (S) is a link with check_valid=True, should be a link.
        #. Delete the file.
        #. Check that (S) is a link with check_valid, should be a broken link.
        #. Create a directory (D1) and a file.
        #. Create a symlink and use target=D1, should fail.
        #. Create a symlink and use target=D1 with overwrite=True, should success.
        #. Check that the link is created.
        #. Remove the link and check that it is removed.
        #. Create a symlink (S) to this file.
        #. Delete this file.
        #. Check that (S) is a broken link with remove_if_broken=False, should return True and keep the file.
        #. Check that (S) is a broken link with remove_if_broken=True, should return True and remove the file.
        """
        self.info("Create a file.")
        file_name = self.random_string()
        file_path = os.path.join(self.temp_path, file_name)
        j.sal.fs.createEmptyFile(file_path)

        self.info("Create a symlink (S) to this file.")
        sym_name = self.random_string()
        sym_path = os.path.join(self.temp_path, sym_name)
        j.sal.fs.symlink(file_path, sym_path)

        self.info("Check that (S) is a link with check_valid=True, should be a link")
        self.assertTrue(os.path.islink(sym_path))
        self.assertTrue(j.sal.fs.isLink(sym_path, check_valid=True))
        self.assertFalse(j.sal.fs.isLinkAndBroken(sym_path, remove_if_broken=False))

        self.info("Delete the file.")
        j.sal.fs.remove(file_path)

        self.info("Check that (S) is a link with check_valid, should be a broken link.")
        self.assertTrue(j.sal.fs.isLink(sym_path, check_valid=False))
        self.assertTrue(os.path.islink(sym_path))
        self.assertFalse(j.sal.fs.isLink(sym_path, check_valid=True))
        self.assertFalse(os.path.islink(sym_path))

        self.info("Create a directory (D1).")
        dir_name = self.random_string()
        dir_path = os.path.join(self.temp_path, dir_name)
        j.sal.fs.createDir(dir_path)
        j.sal.fs.createEmptyFile(file_path)

        self.info("Create a symlink and use target=D1, should fail.")
        with self.assertRaises(Exception):
            j.sal.fs.symlink(file_path, dir_path, overwriteTarget=False)

        self.info("Create a symlink and use target=D1 with overwrite=True, should success.")
        j.sal.fs.symlink(file_path, dir_path, overwriteTarget=True)

        self.info("Check that the link is created.")
        os.path.islink(dir_path)

        self.info("Remove the link and check that it is removed.")
        j.sal.fs.unlink(dir_path)
        self.assertFalse(os.path.exists(dir_path))

        self.info("Create a symlink (S) to this file.")
        j.sal.fs.symlink(file_path, sym_path)

        self.info("Delete the file.")
        j.sal.fs.remove(file_path)

        self.info("Check that (S) is a broken link with remove_if_broken=False, should return False and keep the file.")
        self.assertTrue(j.sal.fs.isLinkAndBroken(sym_path, remove_if_broken=False))
        self.assertTrue(os.path.islink(sym_path))

        self.info(
            "Check that (S) is a broken link with remove_if_broken=True, should return False and remove the file."
        )
        self.assertTrue(j.sal.fs.isLinkAndBroken(sym_path, remove_if_broken=True))
        self.assertFalse(os.path.islink(sym_path))

    def test024_link_all_files_and_dirs_in_dir(self):
        """TC350
        Test case for linking all children files and directories in directory.

        **Test scenario**
        #. Create some files with different extension and directories under a directory (D1).
        #. Create symlinks for all files under (D1) and target a directory (D2) with includeDirs=False.
        #. Check that symlinks are created for files only.
        #. Create symlinks for all files under (D1) and target (D2) with includeDirs=True.
        #. Check that symlinks are created for all files and directories.
        #. Remove one of the symlinks and create a file with same name.
        #. Try to Create symlinks for all files and directories under (D1) and target (D2) with delete=False, should fail.
        #. Try again to Create symlinks for all files and directories under (D1) and target (D2) with delete=True, should success.
        #. Create symlinks for all files and directories under (D1) and target (D2) with makeExecutable=True.
        #. Check that the files created are executable.
        #. Remove all symlinks under (D2).
        #. Check that symlinks are removed.
        """
        self.info("Create some files with different extension and directories under a directory (D1).")
        dir_name = self.random_string()
        dir_path = os.path.join(self.temp_path, dir_name)
        j.sal.fs.createDir(dir_path)
        for _ in range(3):
            file_name = self.random_string()
            file_path = os.path.join(dir_path, file_name)
            j.sal.fs.createEmptyFile(file_path)

            subdir_name = self.random_string()
            subdir_path = os.path.join(dir_path, subdir_name)
            j.sal.fs.createDir(subdir_path)

        self.info("Create symlinks for all files under (D1) and target a directory (D2) with includeDirs=False.")
        dest_path = os.path.join(self.temp_path, self.random_string())
        j.sal.fs.symlinkFilesInDir(dir_path, dest_path, includeDirs=False)

        self.info("Check that symlinks are created for files only.")
        dest_list = [
            x
            for x in os.listdir(dest_path)
            if os.path.islink(os.path.join(dest_path, x)) and os.path.islink(os.path.join(dest_path, x))
        ]
        self.assertEquals(len(dest_list), 3)

        self.info("Create symlinks for all files under (D1) and target (D2) with includeDirs=True.")
        j.sal.fs.symlinkFilesInDir(dir_path, dest_path, includeDirs=True)

        self.info("Check that symlinks are created for all files and directories.")
        dest_list = [x for x in os.listdir(dest_path) if os.path.islink(os.path.join(dest_path, x))]
        self.assertEquals(len(dest_list), 6)

        self.info("Remove one of the symlinks and create a file with same name.")
        file_path = [os.path.join(dest_path, x) for x in os.listdir(dest_path)][0]
        j.sal.fs.remove(file_path)
        j.sal.fs.createEmptyFile(file_path)

        self.info(
            "Try to Create symlinks for all files and directories under (D1) and target (D2) with delete=False, should fail."
        )
        with self.assertRaises(Exception):
            j.sal.fs.symlinkFilesInDir(dir_path, dest_path, includeDirs=True, delete=False)

        self.info(
            "Try again to Create symlinks for all files and directories under (D1) and target (D2) with delete=True, should success."
        )
        j.sal.fs.symlinkFilesInDir(dir_path, dest_path, includeDirs=True, delete=True)

        self.info("Create symlinks for all files and directories under (D1) and target (D2) with makeExecutable=True.")
        j.sal.fs.symlinkFilesInDir(dir_path, dest_path, includeDirs=False, makeExecutable=True)

        self.info("Check that the files created are executable.")
        exec_list = [x for x in os.listdir(dir_path) if os.access(os.path.join(dir_path, x), os.X_OK)]
        self.assertEquals(len(exec_list), 6)

        self.info("Remove all symlinks under (D2).")
        j.sal.fs.removeLinks(dest_path)

        self.info("Check that symlinks are removed.")
        dest_list = os.listdir(dest_path)
        self.assertFalse(dest_list)

    def test025_get_information(self):
        """TC351
        Test case for getting information about files and directories.

        **Test scenario**
        #. Create a tree with many sub directories and files.
        #. Get base name of a directory (full path) and check that the return value eqauls to the directory's name.
        #. Get base name of a file (full path) with removeExtension=True and check the file's name without extension, should be the same.
        #. Get directory name of a file and check that it is returning parent directory(full path).
        #. Get directory name of a file with lastOnly=True and check that it is returning parent directory only.
        #. Get directory name of a file with levelUp=0 and check that it is returning parent directory only.
        #. Get file extension of a file and check the returning value is the file's extension.
        #. Get parent directory of a file and check this directory parent, should be the same.
        #. Get parent of a directory if this directory is exists, should return the parent.
        #. Delete this directory and try to get it again with die=True, should raise error.
        #. Try to get it again with die=False, should return None.
        """
        self.info("Create a tree with many sub directories and files.")
        base_dir = self.create_tree()

        self.info(
            "Get base name of a directory (full path) and check that the return value eqauls to the directory's name."
        )
        base_name = j.sal.fs.getBaseName(base_dir)
        dir_name = base_dir.split(os.sep)[-1]
        self.assertEquals(base_name, dir_name)

        self.info(
            "Get base name of a file (full path) with removeExtension and check the file's name without extension, should be the same."
        )
        file_name_ext = [
            x
            for x in os.listdir(base_dir)
            if os.path.isfile(os.path.join(base_dir, x)) and not os.path.islink(os.path.join(base_dir, x))
        ][-1]
        file_name, file_ext = file_name_ext.split(".")
        file_path = os.path.join(base_dir, file_name_ext)
        base_name = j.sal.fs.getBaseName(file_path, removeExtension=True)
        self.assertEquals(file_name, base_name)

        base_name = j.sal.fs.getBaseName(file_path, removeExtension=False)
        self.assertEquals(file_name_ext, base_name)

        self.info("Get directory name of a file and check that it is returning parent directory(full path).")
        dir_path = j.sal.fs.getDirName(file_path)
        self.assertEquals(os.path.normpath(dir_path), base_dir)

        self.info(
            "Get directory name of a file with lastOnly=True and check that it is returning parent directory only."
        )
        dir_name_2 = j.sal.fs.getDirName(file_path, lastOnly=True)
        self.assertEquals(dir_name, dir_name_2)

        self.info("Get directory name of a file with levelsUp=0 and check that it is returning parent directory only.")
        dir_name_2 = j.sal.fs.getDirName(file_path, levelsUp=0)
        self.assertEquals(dir_name, dir_name_2)

        self.info("Get file extension of a file and check the returning value is the file's extension.")
        ext = j.sal.fs.getFileExtension(file_path)
        self.assertEquals(ext, file_ext)

        self.info("Get parent directory of a file and check this directory parent, should be the same.")
        dir_path = j.sal.fs.getParent(file_path)
        self.assertEquals(os.path.normpath(dir_path), base_dir)

        self.info("Get parent of a directory if this directory is exists, should return the parent.")
        dir_path = j.sal.fs.getParentWithDirname(self.temp_path, dir_name)
        self.assertEquals(os.path.normpath(dir_path), self.temp_path)

        self.info("Delete this directory and try to get it again with die=True, should raise error.")
        j.sal.fs.remove(base_dir)
        with self.assertRaises(Exception):
            dir_path = j.sal.fs.getParentWithDirname(self.temp_path, dir_name, die=True)

        self.info("Try to get it again with die=False, should return None.")
        dir_path = j.sal.fs.getParentWithDirname(self.temp_path, dir_name, die=False)
        self.assertFalse(dir_path)

    def test026_get_path_of_running_function(self):
        """TC352
        Test case for getting path of a running function.

        **Test scenario**
        #. Get path of a method in the same file.
        #. Check that the path has been returned, should be the current file path.
        """
        self.info("Get path of a method in the same file.")
        func_path = j.sal.fs.getPathOfRunningFunction(self.create_tree)

        self.info("Check that the path has been returned, should be the current file path.")
        path = __file__
        self.assertEquals(func_path, path)

    def test027_get_tmp_directory_or_file(self):
        """TC353
        Test case for getting a temp directory or file.

        **Test scenario**
        #. Get temporary directory with create=False, should return a random path.
        #. Check that the random path is not exists.
        #. Get temporary directory with create=True, should return a random path.
        #. Check that the random path is exists.
        #. Get temporary directory with random name, should return a path.
        #. Check that this directory is created.
        #. Get random file and check that file is created.
        """
        self.info("Get temporary directory with create=False, should return a random path.")
        dir_path = j.sal.fs.getTmpDirPath(create=False)
        self.assertIn("/tmp", dir_path)

        self.info("Check that the random path is not exists.")
        self.assertFalse(os.path.exists(dir_path))

        self.info("Get temporary directory with create=True, should return a random path.")
        dir_path = j.sal.fs.getTmpDirPath(create=True)
        self.assertIn("/tmp", dir_path)

        self.info("Check that the random path is exists.")
        self.assertTrue(os.path.exists(dir_path))

        self.info("Delete the directory has been created")
        j.sal.fs.remove(dir_path)

        self.info("Get temporary directory with random name, should return a path.")
        name = self.random_string()
        dir_path_1 = j.sal.fs.getTmpDirPath(name=name, create=True)
        self.assertIn(name, dir_path_1)

        self.info("Check that this directory is created.")
        self.assertTrue(os.path.exists(dir_path_1))

        self.info("Delete the directory has been created")
        j.sal.fs.remove(dir_path_1)

        self.info("Get random file and check that file is created.")
        file_path = j.sal.fs.getTmpFilePath()
        self.assertTrue(os.path.exists(file_path))

        self.info("Delete the file has been created")
        j.sal.fs.remove(file_path)

    @parameterized.expand([(True,), (False,)])
    def test028_compress(self, followlinks):
        """TC354
        Test case for compress files.

        **Test scenario**
        #. Create a tree with many sub directories, files and symlinks.
        #. Compress this tree with followlinks=False, should not compress the content of symlinks.
        #. Compress this tree with followlinks=True, should compress the content of symlinks.
        """
        self.info("Create a tree with many sub directories, files and symlinks.")
        base_dir = self.create_tree()
        before_md5sum = self.md5sum(base_dir)

        self.info(f"Compress this tree with followlinks={followlinks}, should not compress the content of symlinks.")
        tar_dest = f"{self.random_string()}.tar.gz"
        tar_dest_path = os.path.join(self.temp_path, tar_dest)
        j.sal.fs.targzCompress(sourcepath=base_dir, destinationpath=tar_dest_path, followlinks=followlinks)

        untar_dest = self.random_string()
        untar_dest_path = os.path.join(self.temp_path, untar_dest)
        j.sal.fs.targzUncompress(sourceFile=tar_dest_path, destinationdir=untar_dest_path, removeDestinationdir=False)

        after_md5sum = self.md5sum(untar_dest_path)
        if followlinks:
            self.assertNotEquals(before_md5sum, after_md5sum)
        else:
            self.assertEquals(before_md5sum, after_md5sum)

    def test029_path_parse(self):
        """TC355
        Test case for path parsing.

        **Test scenario**
        #. Get path parsing for a directory with checkIsFile=False, should return (directory path, "", "", 0).
        #. Get path parsing for a directory with checkIsFile=True, should raise an error.
        #. Get path parsing for non-existing file with existCheck=False, should return (parent directory, file name, file extension, 0).
        #. Get path parsing for non-existing file with existCheck=True, should rasie an error.
        #. Get path parsing for a file, should return (parent directory, file name, file extension, 0).
        #. Get path parsing for a file with numeric character(N) at the beginning, should return (parent directory, file name, file extension, N).
        #. Get path parsing for a file with baseDir=parent directory, should return ("/", file name, file extension, 0).
        """
        self.info('Get path parsing for a directory with checkIsFile=False, should return (directory path, "", "", 0).')
        dir_path = "/tmp/{}/".format(self.random_string())
        j.sal.fs.createDir(dir_path)
        path_parse = j.sal.fs.pathParse(dir_path)
        excepted_parse = (dir_path, "", "", 0)
        self.assertEquals(path_parse, excepted_parse)

        self.info("Get path parsing for a directory with checkIsFile=True, should raise an error.")
        with self.assertRaises(Exception):
            path_parse = j.sal.fs.pathParse(dir_path, checkIsFile=True)

        self.info(
            "Get path parsing for non-existing file with existCheck=False, should return (parent directory, file name, file extension, 0)."
        )
        file_name = self.random_string()
        extension = "py"
        full_file_name = "{}.{}".format(file_name, extension)
        file_path = os.path.join(dir_path, full_file_name)
        path_parse = j.sal.fs.pathParse(file_path, existCheck=False)
        excepted_parse = (dir_path, file_name, extension, 0)
        self.assertEquals(path_parse, excepted_parse)

        self.info("Get path parsing for non-existing file with existCheck=True, should rasie an error.")
        with self.assertRaises(Exception):
            path_parse = j.sal.fs.pathParse(file_path, existCheck=True)

        self.info("Get path parsing for a file, should return (parent directory, file name, file extension, 0).")
        j.sal.fs.createEmptyFile(file_path)
        path_parse = j.sal.fs.pathParse(file_path)
        excepted_parse = (dir_path, file_name, extension, 0)
        self.assertEquals(path_parse, excepted_parse)

        self.info(
            "Get path parsing for a file with numeric character(N) at the beginning, should return (parent directory, file name, file extension, N)."
        )
        num = random.randint(1, 100)
        file_name = self.random_string()
        extension = "txt"
        full_file_name = "{}_{}.{}".format(num, file_name, extension)
        file_path = os.path.join(dir_path, full_file_name)
        j.sal.fs.createEmptyFile(file_path)
        path_parse = j.sal.fs.pathParse(file_path)
        excepted_parse = (dir_path, file_name, extension, str(num))
        self.assertEquals(path_parse, excepted_parse)

        self.info(
            'Get path parsing for a file with baseDir=parent directory, should return ("/", file name, file extension, 0).'
        )
        path_parse = j.sal.fs.pathParse(file_path, baseDir=dir_path)
        excepted_parse = ("/", file_name, extension, str(num))
        self.assertEquals(path_parse, excepted_parse)

        self.info("Delete the directoy has been created.")
        j.sal.fs.remove(dir_path)

    def test030_change_files_name(self):
        """TC356
        Test case for changing files names using j.sal.fs.changeFileNames.

        **Test scenario**
        #. Create a tree with many sub directories and files with a common word (W1) in their names.
        #. Change these files names by replacing (W1) with another word (W2) with recursive=False.
        #. Check that children files are only changed.
        #. Change these files names again by replacing (W1) with another word (W2) with recursive=True.
        #. Check that files names are changed.
        #. Create a file with (W1) and numeric character(N) at the beginning.
        #. Change these files names by replacing (W1) with another word (W2) with filter=N*.
        #. Check that only this file is changed.
        #. Change the files names depending on modification time.
        """
        self.info("Create a tree with many sub directories and files with a common word (W1) in their names.")
        base_dir = self.create_tree(symlinks=False)

        self.info("Change these files names by replacing (W1) with another word (W2) with recursive=False.")
        log_files = [
            os.path.splitext(x)[0]
            for x in self.list_files_dirs_in_dir(
                base_dir, files_list=True, dirs_list=False, followlinks=False, show_links=False
            )
            if ".log" in x
        ]
        child_log = [os.path.splitext(os.path.join(base_dir, x))[0] for x in os.listdir(base_dir) if ".log" in x]
        j.sal.fs.changeFileNames(toReplace=".log", replaceWith=".java", pathToSearchIn=base_dir, recursive=False)

        self.info("Check that children files are only changed.")
        changed_files = [
            os.path.splitext(x)[0]
            for x in self.list_files_dirs_in_dir(
                base_dir, files_list=True, dirs_list=False, followlinks=False, show_links=False
            )
            if ".java" in x
        ]
        self.assertEquals(changed_files, child_log)

        self.info("Change these files names again by replacing (W1) with another word (W2) with recursive=True.")
        j.sal.fs.changeFileNames(toReplace=".log", replaceWith=".java", pathToSearchIn=base_dir, recursive=True)

        self.info("Check that files names are changed.")
        java_files = [
            os.path.splitext(x)[0]
            for x in self.list_files_dirs_in_dir(
                base_dir, files_list=True, dirs_list=False, followlinks=False, show_links=False
            )
            if ".java" in x
        ]
        self.assertEquals(sorted(log_files), sorted(java_files))

        self.info("Get a .txt file name (N)")
        file_name_ext = [x for x in os.listdir(base_dir) if ".txt" in x][0]
        file_name = os.path.splitext(file_name_ext)[0]
        file_path = os.path.join(base_dir, file_name_ext)

        self.info("Change these files names by replacing (W1) with another word (W2) with filter=N*.")
        j.sal.fs.changeFileNames(
            toReplace=".txt", replaceWith=".js", pathToSearchIn=base_dir, recursive=True, filter=f"{file_name}*"
        )

        self.info("Check that only this file is changed.")
        changed_files = [
            x
            for x in self.list_files_dirs_in_dir(
                base_dir, files_list=True, dirs_list=False, followlinks=False, show_links=False
            )
            if ".js" in x
        ]
        self.assertEquals(len(changed_files), 1)
        self.assertFalse(os.path.exists(file_path))

        self.info("Create a new .py file")
        time.sleep(3)
        file_name = f"{self.random_string()}.py"
        file_path = os.path.join(base_dir, file_name)
        j.sal.fs.createEmptyFile(file_path)
        now = datetime.now().timestamp()

        self.info("Change the files names with modification time not more than 2 seconds ago.")
        j.sal.fs.changeFileNames(
            toReplace=".py", replaceWith=".html", pathToSearchIn=base_dir, recursive=True, minmtime=now - 2
        )

        changed_files = [
            x
            for x in self.list_files_dirs_in_dir(
                base_dir, files_list=True, dirs_list=False, followlinks=False, show_links=False
            )
            if ".html" in x
        ]
        self.assertEquals(len(changed_files), 1)
        self.assertFalse(os.path.exists(file_path))

    def test031_current_dir(self):
        """TC357
        Test case for getting and changing current working directory.

        **Test scenario**
        #. Get current working directory and check it.
        #. Change working directory and get it (CWD).
        #. Change working directory back to the origial one.
        #. Check that (CWD) is the second path.
        """
        self.info("Get current working directory and check it.")
        cur_path_1 = j.sal.fs.getcwd()
        path_1 = os.path.abspath(".")
        self.assertEquals(cur_path_1, path_1)

        self.info("Change working directory and get it (CWD).")
        path_2 = self.temp_path
        j.sal.fs.changeDir(path_2)
        cur_path_2 = j.sal.fs.getcwd()

        self.info("Change working directory back to the origial one.")
        j.sal.fs.changeDir(path_1)

        self.info("Check that (CWD) is the second path.")
        self.assertEquals(cur_path_2, path_2)

    def test032_write_read_check_size_binary_file(self):
        """TC358
        Test case for writting, reading and checking binary file.

        **Test scenario**
        #. Write binary file.
        #. Check that file has been created and it is a binary file.
        #. Read this file and check that its content.
        #. Get file size and check it.
        """
        self.info("Write binary file.")
        content = self.random_string()
        file_name = self.random_string()
        file_path = os.path.join(self.temp_path, file_name)
        with open(file_path, "wb") as f:
            pickle.dump(content, f)

        self.info("Check that file has been created and it is a binary file.")
        os.path.exists(file_path)
        self.assertTrue(j.sal.fs.isBinaryFile(file_path))

        self.info("Read this file and check that its content.")
        with open(file_path, "rb") as f:
            expected_content = f.read()
        result_content = j.sal.fs.readFile(file_path, binary=True)
        self.assertEquals(result_content, expected_content)

        self.info("Get file size and check it.")
        file_size = j.sal.fs.fileSize(file_path)
        size = os.stat(file_path).st_size
        self.assertEquals(file_size, size)

    def test033_md5sum(self):
        """TC359
        Test case for getting md5sum for a file and directory.

        **Test scenario**
        #. Create a file and get its md5sum.
        #. Calculate this file md5sum.
        #. Check that both md5sum are the same.
        #. Create a tree with some directories and files and copy it to another directory.
        #. Get the md5sum for the original directory.
        #. Get the md5sum for the copied directory.
        #. Check that both md5sum are the same.
        """
        self.info("Create a file and get its md5sum.")
        file_name = self.random_string()
        file_path = os.path.join(self.temp_path, file_name)
        content = self.random_string()
        j.sal.fs.writeFile(file_path, content)
        md5sum = j.sal.fs.md5sum(file_path)

        self.info("Calculate this file md5sum.")
        file_md5sum = self.md5sum(file_path)

        self.info("Check that both md5sum are the same.")
        self.assertEquals(md5sum, file_md5sum)

        self.info("Create a tree with some directories and files and copy it to another directory.")
        base_dir = self.create_tree()
        dir_name = self.random_string()
        dir_path = os.path.join(self.temp_path, dir_name)
        j.sal.fs.copyDirTree(base_dir, dir_path, keepsymlinks=True, recursive=True)

        self.info("Get the md5sum for the original directory.")
        orignal_md5sum = j.sal.fs.getFolderMD5sum(base_dir)

        self.info("Get the md5sum for the copied directory.")
        copied_md5sum = j.sal.fs.getFolderMD5sum(dir_path)

        self.info("Check that both md5sum are the same.")
        self.assertEquals(copied_md5sum, orignal_md5sum)

    def test034_write_read_obj_to_from_file(self):
        """TC424
        Test case for writing/reading object to/from file.

        **Test scenario**
        #. Write object to file.
        #. Check that file has been created.
        #. Read this object from the file.
        #. Check that this object can be used.
        """
        self.info("Write object to file.")
        test_obj = Testadd()
        file_name = self.random_string()
        file_path = os.path.join(self.temp_path, file_name)
        j.sal.fs.writeObjectToFile(file_path, test_obj)

        self.info("Check that file has been created.")
        self.assertTrue(os.path.exists(file_path))

        self.info("Read this object from the file.")
        obj = j.sal.fs.readObjectFromFile(file_path)

        self.info("Check that this object can be used.")
        a = random.randint(1, 100)
        b = random.randint(1, 100)
        result = obj.add(a, b)
        self.assertEquals(result, a + b)

    def test035_zip_files(self):
        """TC425
        Test case for compressing files using zip.
        
        **Test scenario**
        #. Create a file F1.
        #. Compress a file F1 using gzip.
        #. Check that a zip file has been created.
        #. Uncompress the output zip file.
        #. Check that the result file is the same as the original file F1.
        """
        self.info("Create a file F1")
        file_name = self.random_string()
        file_path = os.path.join(self.temp_path, file_name)
        content = self.random_string()
        j.sal.fs.writeFile(file_path, content)
        orignal_md5sum = self.md5sum(file_path)

        self.info("Compress a file F1 using gzip.")
        comp_name = self.random_string()
        comp_path = os.path.join(self.temp_path, comp_name)
        j.sal.fs.gzip(file_path, comp_path)

        self.info("Check that a zip file has been created.")
        self.assertTrue(os.path.exists(comp_path))

        self.info("Uncompress the output zip file.")
        dest_path = os.path.join(self.temp_path, self.random_string())
        j.sal.fs.gunzip(comp_path, dest_path)

        self.info("Check that the result file is the same as the original file F1.")
        self.assertTrue(os.path.exists(dest_path))
        dest_md5sum = self.md5sum(dest_path)
        self.assertEquals(dest_md5sum, orignal_md5sum)

    def test036_clean_up_string(self):
        """TC426
        Test case for cleaning up a string.

        **Test scenario**
        #. Clean a string with special characters, should replace these characters with '_'.
        #. Clean a string without special characters, should be that same.
        """
        self.info("Clean a string with special characters, should replace these characters with '_'.")
        special_characters = list(punctuation)
        special_character = random.choice(special_characters)
        name = self.random_string().replace("-", "") + special_character
        result = j.sal.fs.cleanupString(name)
        self.assertEquals(result, name.replace(special_character, "_"))

        self.info("Clean a string without special characters, should be that same.")
        name = self.random_string().replace("-", "")
        result = j.sal.fs.cleanupString(name)
        self.assertEquals(result, name)

    def test037_find(self):
        """TC427
        Test case for finding a file with a regex in a tree.
        
        **Test scenario**
        #. Create a tree with many files.
        #. Create a file with specific regex (R1) under this tree.
        #. Find in this tree what is matched with regex (R1), should return only this file.
        """
        self.info("Create a tree with many files.")
        base_dir = self.create_tree()

        self.info("Create a file with specific regex (R1) under this tree.")
        file_name = "1t2"
        file_path = os.path.join(base_dir, file_name)
        j.sal.fs.touch(file_path)

        self.info("Find in this tree what is matched with regex (R1), should return only this file.")
        result_path = j.sal.fs.find(base_dir, "[0-9][a-z][0-9]")
        self.assertEquals(result_path, [file_path])

    def test038_grep(self):
        """TC428
        Test case for finding a line in a file with a regex.
        
        **Test scenario**
        #. Create a file with some lines.
        #. Find in this file what is matched with regex (R1), should not found.
        #. Append to this file a line with specific regex(R1).
        #. Find in this file what is matched with regex (R1), should only this line.
        """
        self.info("Create a file with some lines.")
        file_name = self.random_string()
        file_path = os.path.join(self.temp_path, file_name)
        content = "\n".join([self.random_string(), self.random_string()])
        j.sal.fs.writeFile(file_path, content)

        self.info("Find in this file what is matched with regex (R1), should not found.")
        line = "1_2"
        cmd = f'kosmos "j.tools.logger.debug=True; j.sal.fs.grep(\\"{file_path}\\", \\"[0-9][_][0-9]\\")"'
        response = run(cmd, shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        self.assertNotIn(file_path, response.stdout)
        self.assertNotIn(line, response.stdout)

        self.info("Append to this file a line with specific regex(R1).")
        content = f"\n{line}"
        j.sal.fs.writeFile(file_path, content, append=True)

        self.info("Find in this file what is matched with regex (R1), should only this line.")
        cmd = f'kosmos "j.tools.logger.debug=True; j.sal.fs.grep(\\"{file_path}\\", \\"[0-9][_][0-9]\\")"'
        response = run(cmd, shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        self.assertIn(file_path, response.stdout)
        self.assertIn(line, response.stdout)

    def test039_is_mount_absolute(self):
        """TC429
        Test case for checking if the directory is mounted and absolute.

        **Test scenario**
        #. Check "/tmp" directory is mounted, should return False.
        #. Check "/dev" directory is mounted, should return True.
        #. Check a random name is absolute, should return False.
        #. Check a full path is absolute, should return True.
        """
        self.info('Check "/tmp" directory is mounted, should return False.')
        self.assertFalse(j.sal.fs.isMount("/tmp"))

        self.info('Check "/dev" directory is mounted, should return True.')
        self.assertTrue(j.sal.fs.isMount("/dev"))

        self.info("Check a random name is absolute, should return False.")
        name = self.random_string()
        self.assertFalse(j.sal.fs.isAbsolute(name))

        self.info("Check a full path is absolute, should return True.")
        path = os.path.join(self.temp_path, name)
        self.assertTrue(j.sal.fs.isAbsolute(path))

    def test040_ascii(self):
        """TC430
        Test case for writting, reading and checking ascii file.

        **Test scenario**
        #. Write ascii to a file.
        #. Check that file has been created and it is a ascii file.
        #. Read this file and check that its content.
        """
        self.info(" Write ascii to a file.")
        ascii_content = self.random_string().encode("ascii")
        file_name = self.random_string()
        file_path = os.path.join(self.temp_path, file_name)
        j.sal.fs.writeFile(file_path, ascii_content)

        self.info("Check that file has been created and it is a binary file.")
        os.path.exists(file_path)
        self.assertTrue(j.sal.fs.isAsciiFile(file_path))
        with open(file_path, "rb") as f:
            content = f.read()
        self.assertEquals(content, ascii_content)

        self.info("Read this file and check that its content.")
        content = j.sal.fs.readFile(file_path, binary=True)
        self.assertEquals(content, ascii_content)

    def test041_hard_link(self):
        """TC431
        Test case for making a hard link for a file.

        **Test scenario**
        #. Create a file.
        #. Create a hard link to this file.
        #. Check that the link file has been created.
        #. Change the content of the linked file.
        #. Check the original file is changed too.
        """
        self.info("Create a file.")
        file_name = self.random_string()
        file_path = os.path.join(self.temp_path, file_name)
        content = self.random_string()
        j.sal.fs.writeFile(file_path, content)

        self.info("Create a hard link to this file.")
        dest_path = os.path.join(self.temp_path, self.random_string())
        j.sal.fs.hardlinkFile(file_path, dest_path)

        self.info("Check that the link file has been created.")
        self.assertTrue(os.path.exists(dest_path))
        hard_links_number = os.stat(file_path).st_nlink
        self.assertEquals(hard_links_number, 2)

        self.info("Change the content of the linked file.")
        new_content = self.random_string()
        j.sal.fs.writeFile(dest_path, new_content, append=True)
        dest_content = j.sal.fs.readFile(dest_path)
        self.assertEquals(dest_content, content + new_content)

        self.info("Check the original file is changed too.")
        file_content = j.sal.fs.readFile(file_path)
        self.assertEquals(file_content, content + new_content)

    @parameterized.expand(["include", "exclude"])
    def test042_compress_include_exclude_path_regex(self, path_option):
        """TC432
        Test case for compressing files with including/excluding path regex.

        **Test scenario**
        #. Create a tree with some files and directories.
        #. Create a file with specific regex (R1) under this tree.
        #. Compress this tree with path include/exclude = (R1).
        #. Uncompress this output file, should /not find file only this file.
        """
        self.info("Create a tree with some files and directories.")
        base_dir = self.create_tree()
        before_md5sum = self.md5sum(base_dir)

        self.info("Create a file with specific regex (R1) under this tree.")
        file_name = "1_2"
        file_path = os.path.join(base_dir, file_name)
        j.sal.fs.touch(file_path)

        self.info(f"Compress this tree with path {path_option} = (R1).")
        tar_dest = f"{self.random_string()}.tar.gz"
        tar_dest_path = os.path.join(self.temp_path, tar_dest)
        if path_option == "include":
            j.sal.fs.targzCompress(
                sourcepath=base_dir, destinationpath=tar_dest_path, pathRegexIncludes=["[0-9][_][0-9]"]
            )
        else:
            j.sal.fs.targzCompress(
                sourcepath=base_dir, destinationpath=tar_dest_path, pathRegexExcludes=["[0-9][_][0-9]"]
            )

        self.info("Uncompress this output file")
        untar_dest = self.random_string()
        untar_dest_path = os.path.join(self.temp_path, untar_dest)
        j.sal.fs.targzUncompress(sourceFile=tar_dest_path, destinationdir=untar_dest_path, removeDestinationdir=False)

        self.info("Check the result files")
        if path_option == "include":
            include_file = os.path.join(untar_dest_path, file_name)
            dirs_files_list = self.list_files_dirs_in_dir(untar_dest_path)
            self.assertEquals(dirs_files_list, [include_file])
        else:
            after_md5sum = self.md5sum(untar_dest_path)
            self.assertEquals(before_md5sum, after_md5sum)

    @parameterized.expand(["include", "exclude"])
    def test043_compress_include_exclude_content_regex(self, content_option):
        """TC433
        Test case for compressing files with including/excluding content regex.

        **Test scenario**
        #. Create a tree with some files and directories.
        #. Create a file with specific regex in it's content (R1) under this tree.
        #. Compress this tree with content include/exclude = (R1).
        #. Uncompress this output file, should /not find file only this file.
        """
        self.info("Create a tree with some files and directories.")
        base_dir = self.create_tree()
        before_md5sum = self.md5sum(base_dir)

        self.info("Create a file with specific regex (R1) under this tree.")
        file_name = self.random_string()
        file_path = os.path.join(base_dir, file_name)
        content = "1_2"
        j.sal.fs.writeFile(file_path, content)

        self.info(f"Compress this tree with content {content_option} = (R1).")
        tar_dest = f"{self.random_string()}.tar.gz"
        tar_dest_path = os.path.join(self.temp_path, tar_dest)

        if content_option == "include":
            j.sal.fs.targzCompress(
                sourcepath=base_dir, destinationpath=tar_dest_path, contentRegexIncludes=["[0-9][_][0-9]"]
            )
        else:
            j.sal.fs.targzCompress(
                sourcepath=base_dir, destinationpath=tar_dest_path, contentRegexExcludes=["[0-9][_][0-9]"]
            )

        self.info("Uncompress this output file")
        untar_dest = self.random_string()
        untar_dest_path = os.path.join(self.temp_path, untar_dest)
        j.sal.fs.targzUncompress(sourceFile=tar_dest_path, destinationdir=untar_dest_path, removeDestinationdir=False)

        self.info("Check the result files")
        if content_option == "include":
            include_file = os.path.join(untar_dest_path, file_name)
            dirs_files_list = self.list_files_dirs_in_dir(untar_dest_path)
            self.assertEquals(dirs_files_list, [include_file])
        else:
            after_md5sum = self.md5sum(untar_dest_path)
            self.assertEquals(before_md5sum, after_md5sum)

    @parameterized.expand([(0,), (1,)])
    def test044_compress_depth(self, depth):
        """TC434
        Test case for compressing files with directories depth.

        **Test scenario**
        #. Create a tree with some files and directories.
        #. Compress this tree with depths=[0].
        #. Uncompress this output file, should find all files.
        #. Compress this tree with depths=[1].
        #. Uncompress this output file, should find sub directories with thier files.
        """
        self.info("Create a tree with some files and directories.")
        base_dir = self.create_tree()
        before_md5sum = self.md5sum(base_dir)

        self.info(f"Compress this tree with depths=[{depth}].")
        tar_dest = f"{self.random_string()}.tar.gz"
        tar_dest_path = os.path.join(self.temp_path, tar_dest)
        j.sal.fs.targzCompress(sourcepath=base_dir, destinationpath=tar_dest_path, depths=[depth])

        self.info("Uncompress this output file")
        untar_dest = self.random_string()
        untar_dest_path = os.path.join(self.temp_path, untar_dest)
        j.sal.fs.targzUncompress(sourceFile=tar_dest_path, destinationdir=untar_dest_path, removeDestinationdir=False)

        self.info("Check the result files")
        if depth:
            files = [
                os.path.join(base_dir, x) for x in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, x))
            ]
            for file in files:
                j.sal.fs.remove(file)
            before_md5sum = self.md5sum(base_dir)

        after_md5sum = self.md5sum(untar_dest_path)
        self.assertEquals(before_md5sum, after_md5sum)

    def test045_compress_with_extra_files(self):
        """TC435
        Test case for compressing files with extra files.

        **Test scenario**
        #. Create two tree with some files and directories.
        #. Compress the first tree with extrafiles using the second tree.
        #. Uncompress this output file.
        #. Check that second tree under the result directory.
        #. Remove the second tree, should the first tree remain.
        """
        self.info("Create two tree with some files and directories.")
        base_dir = self.create_tree()
        second_tree = self.create_tree()
        first_tree_md5sum = self.md5sum(base_dir)
        second_tree_md5sum = self.md5sum(second_tree)

        self.info(f"Compress the first tree with extrafiles using the second tree.")
        tar_dest = f"{self.random_string()}.tar.gz"
        tar_dest_path = os.path.join(self.temp_path, tar_dest)
        j.sal.fs.targzCompress(
            sourcepath=base_dir, destinationpath=tar_dest_path, extrafiles=[[second_tree, "second_tree"]]
        )

        self.info("Uncompress this output file.")
        untar_dest = self.random_string()
        untar_dest_path = os.path.join(self.temp_path, untar_dest)
        j.sal.fs.targzUncompress(sourceFile=tar_dest_path, destinationdir=untar_dest_path, removeDestinationdir=False)

        self.info("Check that second tree under the result directory.")
        second_tree_path = os.path.join(untar_dest_path, "second_tree")
        second_tree_md5sum_after = self.md5sum(second_tree_path)
        self.assertEquals(second_tree_md5sum_after, second_tree_md5sum)

        self.info("Remove the second tree, should the first tree remain.")
        j.sal.fs.remove(second_tree_path)
        first_tree_md5sum_after = self.md5sum(untar_dest_path)
        self.assertEquals(first_tree_md5sum_after, first_tree_md5sum)

    def test046_compress_with_dest(self):
        """TC436
        Test case for compressing files with specify the destination in tar.

        **Test scenario**
        #. Create a tree with some files and directories.
        #. Compress this tree with specify the destination (D1) in tar.
        #. Uncompress this output file, should find this tree under (D1).
        """
        self.info("Create a tree with some files and directories.")
        base_dir = self.create_tree()
        before_md5sum = self.md5sum(base_dir)

        self.info(f"Compress this tree with specify the destination (D1) in tar")
        tar_dest = f"{self.random_string()}.tar.gz"
        tar_dest_path = os.path.join(self.temp_path, tar_dest)
        dest = self.random_string()
        j.sal.fs.targzCompress(sourcepath=base_dir, destinationpath=tar_dest_path, destInTar=dest)

        self.info("Uncompress this output file")
        untar_dest = self.random_string()
        untar_dest_path = os.path.join(self.temp_path, untar_dest)
        j.sal.fs.targzUncompress(sourceFile=tar_dest_path, destinationdir=untar_dest_path, removeDestinationdir=False)

        self.info("Uncompress this output file, should find this tree under (D1).")
        list_dest = os.listdir(untar_dest_path)
        self.assertEquals(list_dest, [dest])

        dest_path = os.path.join(untar_dest_path, dest)
        after_md5sum = self.md5sum(dest_path)
        self.assertEquals(before_md5sum, after_md5sum)

    def test047_remove_irrelevant_files(self):
        """TC437
        Test case for removing irrelevant files in a directory.

        **Test scenario**
        #. Create a tree with some directories and files.
        #. Create a file with extention bak and pyc.
        #. Remove the irrelevant files, should only remove files with extention bak and pyc.
        """
        self.info("Create a tree with some directories and files.")
        base_dir = self.create_tree()

        self.info("Create a file with extention bak and pyc.")
        bak_file = self.random_string() + ".bak"
        bak_path = os.path.join(base_dir, bak_file)
        j.sal.fs.touch(bak_path)
        pyc_file = self.random_string() + ".pyc"
        pyc_path = os.path.join(base_dir, pyc_file)
        j.sal.fs.touch(pyc_path)
        dirs_files_list = self.list_files_dirs_in_dir(base_dir)

        self.assertIn(bak_path, dirs_files_list)
        self.assertIn(pyc_path, dirs_files_list)

        self.info("Remove the irrelevant files, should only remove files with extention bak and pyc.")
        j.sal.fs.removeIrrelevantFiles(base_dir)
        dirs_files_list = self.list_files_dirs_in_dir(base_dir)
        self.assertNotIn(bak_path, dirs_files_list)
        self.assertNotIn(pyc_path, dirs_files_list)

    def test048_validate_files_names(self):
        """TC438
        Test case for validate files names.

        **Test scenario**
        #. Check file name with special charater is valid.
        #. Check file name with "/" is not valid.
        #. Check file name with more than 255 charater is not valid.
        #. Check file name with 0x00 is not vaild.
        """
        self.info("Check file name with special charater is valid.")
        special_characters = list(punctuation)
        special_characters.remove("/")
        special_character = random.choice(special_characters)
        name = self.random_string() + special_character
        self.assertTrue(j.sal.fs.validateFilename(name))

        self.info("Check file name with '/' is not valid.")
        name = self.random_string() + "/"
        self.assertFalse(j.sal.fs.validateFilename(name))

        self.info("Check file name with more than 255 charater is not valid.")
        name = ""
        for i in range(256):
            name += str(i)
        self.assertFalse(j.sal.fs.validateFilename(name))

        self.info("Check file name with 0x00 is not vaild.")
        name = self.random_string() + "\0x00"
        self.assertFalse(j.sal.fs.validateFilename(name))
