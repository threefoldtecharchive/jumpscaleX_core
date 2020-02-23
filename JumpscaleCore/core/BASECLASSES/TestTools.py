import re
import time
import traceback
import types
from importlib import import_module, sys

import xmltodict
from Jumpscale import j

_VALID_TEST_NAME = re.compile("(?:^|[\b_\./-])[Tt]est")
_FAIL_LENGTH = 6
_ERROR_LENGTH = 7


_full_results = {
    "summary": {"passes": 0, "failures": 0, "errors": 0, "skips": 0},
    "testcases": [],
    "time_taken": 0,
}


class Skip(Exception):
    """Raise for skipping test"""


class TestTools:
    __show_tests_report = True
    _modules = []
    _results = {
        "summary": {"passes": 0, "failures": 0, "errors": 0, "skips": 0},
        "testcases": [],
        "time_taken": 0,
    }

    def _init_factory(self, xml_report=False, xml_path="test.xml", xml_testsuite_name="Jsx_Runner"):
        self._xml_report = xml_report
        self._xml_path = xml_path
        self._xml_testsuite_name = xml_testsuite_name

    @staticmethod
    def _skip(msg):
        """Skip is used as a decorator to skip tests with a message.

        :param msg: string message for final report.
        """

        def dec(func):
            def wrapper(*args, **kwargs):
                raise Skip(msg)

            wrapper.__name__ = func.__name__
            wrapper.__test_skip__ = True
            return wrapper

        return dec

    def _tests_run(self, name=""):
        """This method for jumpscale factories, it is used to run tests in "tests" directory beside jumpscale factory.
        This method should not be used outside jumpscale factories.

        :param name: file name or part of file name to run only this file.
        """

        def find_file(name, path):
            """Find a file in path with a part of its name.

            :param name: part of file name.
            :param path: parent path.
            """
            files = j.sal.fs.listPyScriptsInDir(path)
            for file in files:
                _, basename, _, _ = j.sal.fs.pathParse(file)
                if name in basename:
                    return file
            else:
                raise ValueError(f"Didn't find file with name {name}")

        if not hasattr(self, "_dirpath"):
            return 0
        path = j.sal.fs.joinPaths(self._dirpath, "tests")
        if name:
            path = find_file(name, path)

        self._discover_from_path(path)
        return self._execute_report_tests()

    def _run_from_path(self, path="", name=""):
        """Run tests from absolute or relative path.

        :param path: tests path.
        :param name: testcase name to be run in case of running only one test.
        """
        self._reset(modules=False)
        if not j.sal.fs.isAbsolute(path):
            path = j.sal.fs.joinPaths(j.sal.fs.getcwd(), path)
        self._discover_from_path(path, name)
        return self._execute_report_tests(name)

    def _run_tests_from_object(self, obj=None):
        """Run all test in object if object's methods are starting with "test".

        :param obj: this object should be jsx object (ex: j.data.schema)
                    or jsx group (ex: j.data)
                    or all jsx tests (j)
        """
        self._reset()
        if obj is None:
            return
        elif isinstance(obj, j.baseclasses.object):
            obj.__show_tests_report = False
            self._modules.append(obj)
        elif obj == j:
            for group_name, group in j.core._groups.items():
                self._discover_group(group_name, group)
        else:
            for group_name, group in j.core._groups.items():
                if obj == group:
                    self._discover_group(group_name, group)

        self.__show_tests_report = False
        self._execute_report_tests(report=False)
        global _full_results
        self._report(results=_full_results)
        fail_status = (_full_results["summary"]["failures"] > 0) or (_full_results["summary"]["errors"] > 0)
        self._reset(full=True)
        if fail_status:
            return 1
        return 0

    def _discover_group(self, group_name, group):
        """Discover all tests recursivily in jsx group.

        :param group_name: jsx group name.
        :param group: jsx group object.
        """
        for factory in dir(group):
            if not factory.startswith("_"):
                try:
                    attr = getattr(group, factory)
                except BaseException as error:
                    self._start_time = time.time()
                    factory_location = f"{group_name}.{factory}"
                    print(f"{factory_location}...")
                    self._add_error(factory_location, error)
                    continue
                if isinstance(attr, j.baseclasses.object):
                    attr.__show_tests_report = False
                    self._modules.append(attr)

    def _reset(self, modules=True, full=False):
        """Reset the test runner (results and modules has been discovered).

        :param modules: True to reset the modules.
        :param full: True to reset local and global results.
        """
        if full:
            for module in self._modules:
                module.__show_tests_report = True

            global _full_results
            _full_results = {
                "summary": {"passes": 0, "failures": 0, "errors": 0, "skips": 0},
                "testcases": [],
                "time_taken": 0,
            }
        if modules:
            self._modules = []
        self._results = {
            "summary": {"passes": 0, "failures": 0, "errors": 0, "skips": 0},
            "testcases": [],
            "time_taken": 0,
        }

    def _discover_from_path(self, path, test_name=""):
        """Discover and get modules that contains tests in a certain path.

        :param path: absolute path to be discovered.
        :param test_name: (optional) test name for getting only this test.
        """
        self._reset()
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

        dotted_path = relative_path[:-1].replace("/", ".")
        if dotted_path:
            basename = f".{basename}"
        module = import_module(name=basename, package=dotted_path)
        for mod in dir(module):
            if _VALID_TEST_NAME.match(mod):
                self._modules.append(module)
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
        self._modules.append(module)
        if test_name not in dir(module):
            raise AttributeError(f"Test {test_name} is not found")

    def _execute_report_tests(self, test_name="", report=True):
        """Run tests has been discovered using a discover method.

        :param test_name: (optional) test name for run only this test.
        :return: 0 in case of success or no test found, 1 in case of failure.
        """
        # We should keep track of every test (execution time)
        start_time = time.time()
        for module in self._modules:
            skip = self._before_all(module)
            if skip:
                continue
            if test_name:
                self._execute_test(test_name, module)
            else:
                for method in dir(module):
                    if not method.startswith("_") and _VALID_TEST_NAME.match(method):
                        self._execute_test(method, module)

            self._after_all(module)
        end_time = time.time()
        time_taken = end_time - start_time
        self._results["time_taken"] = time_taken
        fail_status = (self._results["summary"]["failures"] > 0) or (self._results["summary"]["errors"] > 0)
        if report and self.__show_tests_report:
            # in case of running test from path or jsx factory.
            self._report()
            self._reset()
        if not self.__show_tests_report:
            # in case of collecting all tests to be reported at the end.
            self._add_to_full_results()
            self._reset(modules=False)

        if fail_status:
            return 1
        return 0

    def _execute_test(self, method, module):
        """Execute one test.

        :param method: test name.
        :param module: module that contain this test.
        """
        module_location = self._get_module_location(module)
        test_name = f"{module_location}.{method}"

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

    def _get_module_location(self, module):
        if hasattr(module, "_location"):
            module_location = module._location
        else:
            module_location = module.__file__

        return module_location

    def _before_all(self, module):
        """Get and execute before_all in a module if it is exist.

        :param module: module that contains before_all.
        """
        self._start_time = time.time()
        module_location = self._get_module_location(module)
        if "before_all" in dir(module):
            before_all = getattr(module, "before_all")
            try:
                before_all()
            except Skip as sk:
                print(f"{module_location} ...")
                skip_msg = f"SkipTest: {sk.args[0]}\n"
                self._add_skip(module_location, skip_msg)
                return True
            except BaseException as error:
                self._add_helper_error(module_location, error)
                print("error\n")

        return False

    def _after_all(self, module):
        """Get and execute after_all in a module if it is exist.

        :param module: module that contains after_all.
        """
        module_location = self._get_module_location(module)
        if "after_all" in dir(module):
            after_all = getattr(module, "after_all")
            try:
                after_all()
            except BaseException as error:
                self._add_helper_error(module_location, error)
                print("error\n")

    def _before(self, module):
        """Get and execute before in a module if it is exist.

        :param module: module that contains before.
        """
        self._start_time = time.time()
        if "before" in dir(module):
            before = getattr(module, "before")
            before()

    def _after(self, module, test_name):
        """Get and execute after in a module if it is exist.

        :param module: module that contains after.
        """
        if "after" in dir(module):
            after = getattr(module, "after")
            try:
                after()
            except BaseException as error:
                self._add_helper_error(test_name, error)
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
        time_taken = self._time_taken()
        self._results["summary"]["passes"] += 1
        result = {"name": test_name, "status": "passed", "time": time_taken}
        self._results["testcases"].append(result)
        print("ok\n")

    def _add_failure(self, test_name, error):
        """Add a failed test.

        :param error: test exception error.
        """
        time_taken = self._time_taken()
        self._results["summary"]["failures"] += 1
        length = len(test_name) + _FAIL_LENGTH
        msg = "=" * length + f"\nFAIL: {test_name}\n" + "-" * length
        log_msg = j.core.tools.log("{RED}%s" % msg, stdout=False)
        str_msg = j.core.tools.log2str(log_msg)
        log_error = j.core.tools.log("", exception=error, stdout=False)
        str_error = j.core.tools.log2str(log_error)
        trace_back = traceback.format_exc()
        result = {
            "name": test_name,
            "traceback": trace_back,
            "msg": str_msg,
            "error": str_error,
            "status": "failure",
            "time": time_taken,
        }
        self._results["testcases"].append(result)
        print("fail\n")

    def _add_error(self, test_name, error):
        """Add a errored test.

        :param error: test exception error.
        """
        time_taken = self._time_taken()
        self._results["summary"]["errors"] += 1
        length = len(test_name) + _ERROR_LENGTH
        msg = "=" * length + f"\nERROR: {test_name}\n" + "-" * length
        log_msg = j.core.tools.log("{YELLOW}%s" % msg, stdout=False)
        str_msg = j.core.tools.log2str(log_msg)
        log_error = j.core.tools.log("", exception=error, stdout=False)
        str_error = j.core.tools.log2str(log_error)
        trace_back = traceback.format_exc()
        result = {
            "name": test_name,
            "traceback": trace_back,
            "msg": str_msg,
            "error": str_error,
            "status": "error",
            "time": time_taken,
        }
        self._results["testcases"].append(result)
        print("error\n")

    def _add_skip(self, test_name, skip_msg):
        """Add a skipped test.

        :param skip_msg: reason for skipping the test.
        """
        time_taken = self._time_taken()
        self._results["summary"]["skips"] += 1
        length = len(test_name) + _FAIL_LENGTH
        msg = "=" * length + f"\nSKIP: {test_name}\n" + "-" * length
        log_msg = j.core.tools.log("{BLUE}%s" % msg, stdout=False)
        str_msg = j.core.tools.log2str(log_msg)
        log_skip = j.core.tools.log("\n{BLUE}%s" % skip_msg, stdout=False)
        str_skip = j.core.tools.log2str(log_skip)
        result = {
            "name": test_name,
            "message": skip_msg,
            "msg": str_msg,
            "error": str_skip,
            "status": "skipped",
            "time": time_taken,
        }
        self._results["testcases"].append(result)
        print("skip\n")

    def _add_helper_error(self, test_name, error):
        """Add error that happens in a helper method (before_all, after, after_all).

        :param error: test exception error.
        """
        time_taken = self._time_taken()
        length = len(test_name) + _ERROR_LENGTH
        msg = "=" * length + f"\nERROR: {test_name}\n" + "-" * length
        log_msg = j.core.tools.log("{YELLOW}%s" % msg, stdout=False)
        str_msg = j.core.tools.log2str(log_msg)
        log_error = j.core.tools.log("", exception=error, stdout=False)
        str_error = j.core.tools.log2str(log_error)
        trace_back = traceback.format_exc()
        result = {
            "name": test_name,
            "traceback": trace_back,
            "msg": str_msg,
            "error": str_error,
            "status": "error",
            "time": time_taken,
        }
        self._results["testcases"].append(result)

    def _time_taken(self):
        diff_time = time.time() - self._start_time
        time_taken = "{0:.5f}".format(diff_time)
        return time_taken

    def _report(self, results=None):
        """Collect and print the final report.
        """
        if not results:
            results = self._results

        testcases_results = sorted(results["testcases"], key=lambda x: x["status"], reverse=True)
        for result in testcases_results:
            if result["status"] == "passed":
                continue
            msg = result["msg"].split(": ")
            msg = ": ".join(msg[1:])
            print(msg)
            error = result["error"].split(": ")
            error = ": ".join(error[1:])
            print(error)

        print("-" * 70)  # line To print the summary
        all_tests = sum(results["summary"].values())
        time_taken = "{0:.5f}".format(results["time_taken"])
        print(f"Ran {all_tests} tests in {time_taken}\n\n")
        result_log = j.core.tools.log(
            "{RED}%s Failed, {YELLOW}%s Errored, {GREEN}%s Passed, {BLUE}%s Skipped"
            % (
                results["summary"]["failures"],
                results["summary"]["errors"],
                results["summary"]["passes"],
                results["summary"]["skips"],
            )
        )
        result_str = j.core.tools.log2str(result_log)
        print(result_str.split(": ")[1], "\u001b[0m")
        self._generate_xml(results)

    def _add_to_full_results(self):
        """Add results from test runner to full result to report them once at the end.
        """
        global _full_results
        _full_results["summary"]["failures"] += self._results["summary"]["failures"]
        _full_results["summary"]["errors"] += self._results["summary"]["errors"]
        _full_results["summary"]["passes"] += self._results["summary"]["passes"]
        _full_results["summary"]["skips"] += self._results["summary"]["skips"]
        _full_results["time_taken"] += self._results["time_taken"]
        _full_results["testcases"].extend(self._results["testcases"])

    def _generate_xml(self, results=None):
        """Generate xml report for the last running tests in case of _xml_report is True.
            _xml_path: should be set at the object to determine xml file path (default: test.xml in the current working directory)
            _xml_testsuite_name: should be set at the object to determine testsuite name (default: Jsx Runner)

        :param results: jsx runner result to be converted from dict to xml.
        """
        if results is None:
            results = self._results

        if "_xml_report" in dir(self) and self._xml_report:
            testsuite_name = self._xml_testsuite_name
            path = self._xml_path
            all_tests = sum(results["summary"].values())
            all_results = {
                "testsuite": {
                    "name": testsuite_name,
                    "tests": all_tests,
                    "failures": results["summary"]["failures"],
                    "errors": results["summary"]["errors"],
                    "skip": results["summary"]["skips"],
                    "testcase": [],
                }
            }
            for result in results["testcases"]:
                needed_result = {"name": result["name"], "time": result["time"]}
                if result["status"] != "passed":
                    if result["status"] == "skipped":
                        needed_result[result["status"]] = {"message": result["message"]}
                    else:
                        needed_result[result["status"]] = {"content": result["traceback"]}

                all_results["testsuite"]["testcase"].append(needed_result)
            data = xmltodict.unparse(all_results)
            with open(path, "w") as f:
                f.write(data)
            print("-" * 70)
            if not j.sal.fs.isAbsolute(path):
                path = j.sal.fs.joinPaths(j.sal.fs.getcwd(), path)
            print(f"XML file has been generated in {path}")
            print("-" * 70)
