import os
import re
import traceback
import types
from importlib import import_module, sys
import time

from Jumpscale import j

_VALID_TEST_NAME = re.compile("(?:^|[\b_\./-])[Tt]est")
_FAIL_LENGTH = 6
_ERROR_LENGTH = 7


class Skip(BaseException):
    """Raise for skipping test"""


class TestTools:
    modules = []
    results = {
        "summary": {"passes": 0, "failures": 0, "errors": 0, "skips": 0},
        "testcases": [],
        "time_taken": 0,
    }

    @staticmethod
    def _skip(msg):
        """Skip is used as a decorator to skip tests with a message.

        :param msg: string message for final report.
        """

        def dec(func):
            def wrapper(*args, **kwargs):
                raise Skip(msg)

            wrapper.__test_skip__ = True
            return wrapper

        return dec

    def _tests_run(self, path="", name=""):
        """Run tests in a certain path.

        :param path: relative or absolute path that contains tests.
        :return: 0 in case of success or no test found, 1 in case of failure.
        """

        def find_file(name, path):
            files = j.sal.fs.listPyScriptsInDir(path)
            for file in files:
                _, basename, _, _ = j.sal.fs.pathParse(file)
                if name in basename:
                    return file
            else:
                raise ValueError(f"Didn't find file with name {name}")

        if hasattr(self, "_dirpath") and not path:
            # This part for jsx factory
            path = j.sal.fs.joinPaths(self._dirpath, "tests")
            if name:
                path = find_file(name, path)
                name = ""

        if not j.sal.fs.isAbsolute(path):
            path = j.sal.fs.joinPaths(j.sal.fs.getcwd(), path)

        if name:
            self._discover(path, name)
            return self._run_tests(name)
        else:
            self._discover(path)
            return self._run_tests()

    def _discover(self, path, test_name=""):
        """Discover and get modules that conatains a tests in a certain path.

        :param path: absolute path to be discovered.
        :param test_name: (optional) test name for getting only this test.
        """
        self.modules = []
        if j.sal.fs.isFile(path):
            parent_path = j.sal.fs.getDirName(path)
            sys.path.insert(0, parent_path)
            if test_name:
                self._import_test_module(test_name, path, parent_path)
            else:
                self._import_file_module(path, parent_path)
        else:
            sys.path.insert(0, path)
            files_pathes = j.sal.fs.listPyScriptsInDir(path=path, recursive=True)
            for file_path in files_pathes:
                self._import_file_module(file_path, path)

    def _import_file_module(self, file_path, path):
        """Import module (file) if module contains a test.

        :param file_path: absolute file path.
        :param path: absolute path for one of file's parents.
        """
        relative_path, basename, _, p = j.sal.fs.pathParse(file_path, baseDir=path)
        if p:
            basename = f"{p}_{basename}"
        # if not _VALID_TEST_NAME.match(basename):
        #     return
        dotted_path = relative_path[:-1].replace("/", ".")
        if dotted_path:
            basename = f".{basename}"
        module = import_module(name=basename, package=dotted_path)
        for mod in dir(module):
            if _VALID_TEST_NAME.match(mod):
                self.modules.append(module)
                break

    def _import_test_module(self, test_name, file_path, path):
        """Import module (test) from file path.

        :param test_name: test name to be imported.
        :param file_path: absolute file path.
        :param path: absolute path for one of the file's parents.
        """
        relative_path, basename, _, _ = j.sal.fs.pathParse(file_path, baseDir=path)
        dotted_path = relative_path[:-1].replace("/", ".")
        if dotted_path:
            basename = f".{basename}"
        module = import_module(name=basename, package=dotted_path)
        self.modules.append(module)
        if test_name not in dir(module):
            raise AttributeError(f"Test {test_name} is not found")

    def _run_tests(self, test_name=""):
        """Run tests has been discovered using discover method.

        :param test_name: (optional) test name for run only this test.
        :return: 0 in case of success or no test found, 1 in case of failure.
        """
        self.results = {
            "summary": {"passes": 0, "failures": 0, "errors": 0, "skips": 0},
            "testcases": [],
            "time_taken": 0,
        }
        # We should keep track of every test (execution time)
        start_time = time.time()
        for module in self.modules:
            self._before_all(module)
            if test_name:
                self._run_test(test_name, module)
            else:
                for method in dir(module):
                    if not method.startswith("_") and _VALID_TEST_NAME.match(method):
                        self._run_test(method, module)

            self._after_all(module)
        end_time = time.time()
        time_taken = end_time - start_time
        self.results["time_taken"] = "{0:.5f}".format(time_taken)
        self._report()
        if (self.results["summary"]["failures"] > 0) or (self.results["summary"]["errors"] > 0):
            return 1
        return 0

    def _run_test(self, method, module):
        """Run one test.

        :param method: test name.
        :param module: module that contain this test.
        """
        module_name = module.__file__
        test_name = f"{module_name}:{method}"
        try:
            test = getattr(module, method)
            if not isinstance(test, (types.FunctionType, types.MethodType)):
                return
            print(test_name, "...")
            if not self._is_skipped(test):
                self._before(module)
            test()
            self._add_success(test_name)
        except AssertionError as error:
            self._add_failure(test_name, error)

        except Skip as sk:
            skip_msg = f"SkipTest: {sk.args[0]}\n"
            self._add_skip(test_name, skip_msg)

        except BaseException as error:
            self._add_error(test_name, error)

        if not self._is_skipped(test):
            self._after(module, test_name)

    def _before_all(self, module):
        """Get and execute before_all in a module if it is exist.

        :param module: module that contains before_all.
        """
        module_name = module.__file__
        if "before_all" in dir(module):
            before_all = getattr(module, "before_all")
            try:
                before_all()
            except BaseException as error:
                self._add_helper_error(module_name, error)
                print("error\n")

    def _after_all(self, module):
        """Get and execute after_all in a module if it is exist.

        :param module: module that contains after_all.
        """
        module_name = module.__file__
        if "after_all" in dir(module):
            after_all = getattr(module, "after_all")
            try:
                after_all()
            except BaseException as error:
                self._add_helper_error(module_name, error)
                print("error\n")

    def _before(self, module):
        """Get and execute before in a module if it is exist.

        :param module: module that contains before.
        """
        if "before" in dir(module):
            before = getattr(module, "before")
            before()

    def _after(self, module, test_name):
        """Get and execute after in a module if it is exist.

        :param module: module that contains after.
        """
        module_name = f"{module.__file__}:{test_name}"
        if "after" in dir(module):
            after = getattr(module, "after")
            try:
                after()
            except BaseException as error:
                self._add_helper_error(module_name, error)
                print("error\n")

    def _is_skipped(self, test):
        """Check if the test is skipped.

        :param test: test method.
        """
        if hasattr(test, "__test_skip__"):
            return getattr(test, "__test_skip__")

    def _add_success(self, test_name):
        """Add a succeed test.
        """
        self.results["summary"]["passes"] += 1
        print("ok\n")

    def _add_failure(self, test_name, error):
        """Add a failed test.

        :param error: test exception error.
        """
        self.results["summary"]["failures"] += 1
        length = len(test_name) + _FAIL_LENGTH
        msg = "=" * length + f"\nFAIL: {test_name}\n" + "-" * length
        log_msg = j.core.tools.log("{RED}%s" % msg, stdout=False)
        str_msg = j.core.tools.log2str(log_msg)
        log_error = j.core.tools.log("", exception=error, stdout=False)
        str_error = j.core.tools.log2str(log_error)
        result = {"msg": str_msg, "error": str_error}
        self.results["testcases"].append(result)
        print("fail\n")

    def _add_error(self, test_name, error):
        """Add a errored test.

        :param error: test exception error.
        """
        self.results["summary"]["errors"] += 1
        length = len(test_name) + _ERROR_LENGTH
        msg = "=" * length + f"\nERROR: {test_name}\n" + "-" * length
        log_msg = j.core.tools.log("{YELLOW}%s" % msg, stdout=False)
        str_msg = j.core.tools.log2str(log_msg)
        log_error = j.core.tools.log("", exception=error, stdout=False)
        str_error = j.core.tools.log2str(log_error)
        result = {"msg": str_msg, "error": str_error}
        self.results["testcases"].append(result)
        print("error\n")

    def _add_skip(self, test_name, skip_msg):
        """Add a skipped test.

        :param skip_msg: reason for skipping the test.
        """
        self.results["summary"]["skips"] += 1
        length = len(test_name) + _FAIL_LENGTH
        msg = "=" * length + f"\nSKIP: {test_name}\n" + "-" * length
        log_msg = j.core.tools.log("{BLUE}%s" % msg, stdout=False)
        str_msg = j.core.tools.log2str(log_msg)
        log_skip = j.core.tools.log("\n{BLUE}%s" % skip_msg, stdout=False)
        str_skip = j.core.tools.log2str(log_skip)
        result = {"msg": str_msg, "error": str_skip}
        self.results["testcases"].append(result)
        print("skip\n")

    def _add_helper_error(self, test_name, error):
        """Add error that happens in a helper method (before_all, after, after_all).

        :param error: test exception error.
        """
        length = len(test_name) + _ERROR_LENGTH
        msg = "=" * length + f"\nERROR: {test_name}\n" + "-" * length
        log_msg = j.core.tools.log("{YELLOW}%s" % msg, stdout=False)
        str_msg = j.core.tools.log2str(log_msg)
        log_error = j.core.tools.log("", exception=error, stdout=False)
        str_error = j.core.tools.log2str(log_error)
        result = {"msg": str_msg, "error": str_error}
        self.results["testcases"].append(result)

    def _report(self):
        """Collect and print the final report.
        """
        length = 70
        for result in self.results["testcases"]:
            msg = result["msg"].split(": ")
            msg = ": ".join(msg[1:])
            print(msg)
            error = result["error"].split(": ")
            error = ": ".join(error[1:])
            print(error)

        print("-" * length)
        all_tests = sum(self.results["summary"].values())
        print(f"Ran {all_tests} tests in {self.results['time_taken']}\n\n")
        result_log = j.core.tools.log(
            "{RED}%s Failed, {YELLOW}%s Errored, {GREEN}%s Passed, {BLUE}%s Skipped"
            % (
                self.results["summary"]["failures"],
                self.results["summary"]["errors"],
                self.results["summary"]["passes"],
                self.results["summary"]["skips"],
            )
        )
        result_str = j.core.tools.log2str(result_log)
        print(result_str.split(": ")[1], "\u001b[0m")

    def discover_obj(self, obj=None):
        for group_name, group in j.core._groups.items():
            import ipdb

            ipdb.set_trace()
            if not obj or obj == group:
                for factory in dir(group):
                    if not factory.startswith("_"):
                        try:
                            attr = getattr(group, factory)
                            attr.__file__ = f"{group_name}.{factory}"
                        except BaseException as error:
                            self._add_error(factory, error)
                            continue
                        self.modules.append(attr)
