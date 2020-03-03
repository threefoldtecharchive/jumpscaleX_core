# Test Runner

## How to write a test

### Test shape

For add function

```python
def add (x, y):
    return x + y

```

Test should start with "test" like:

```python
def test():
    x = 1
    y = 2
    z = add(x, y)
    assert z == 3
```

### Fixtures

These fixtures should be defined in same module with the test.

#### 1- before_all

To run once before running all tests.

#### 2- before

To run before every test.

#### 3- after

To run after every test.

#### 4- after_all

To run once after running all tests.

### How to skip

#### 1- Skip one test

This can be done using skip decorator before the test.

```python
from Jumpscale import j
skip = j.baseclasses.testtools._skip

@skip("skip reason")
def test():
    x = 1
    y = 2
    z = add(x, y)
    assert z == 3
```

#### 2- Skip all tests in a module

This can be done using skip decorator before `before_all` fixture.

```python
from Jumpscale import j
skip = j.baseclasses.testtools._skip

@skip("skip reason")
def before_all():
    pass
```

#### 3- Skip parameterized test

```python
from parameterized import parameterized
from Jumpscale import j
skip = j.baseclasses.testtools._skip

@parameterized.expand(["1", "2", "3"])
@skip("skip reason")
def test_7(num):
    pass
```

## How to run 

### 1-From path

#### 1- Directory or file

```python
from Jumpscale import j
testrunner = j.baseclasses.testtools()
testrunner._run_from_path("path/to/tests")
```

#### 2- One test

```python
from Jumpscale import j
testrunner = j.baseclasses.testtools()
testrunner._run_from_path(path="path/to/tests", name="test_name")

```

### 2- From object

#### 1- One object

This object should inherit from `JSBASE` (`j.baseclasses.object`)

```python
from Jumpscale import j
testrunner = j.baseclasses.testtools()
testrunner._run_from_object(j.tools.timer)
```

#### 2- Group of objects

This will search for all objects under this group that contains test.

```python
from Jumpscale import j
testrunner = j.baseclasses.testtools()
testrunner._run_from_object(j.tools)
```

#### 3- All JSX tests

Using `j` object.

```python
from Jumpscale import j
testrunner = j.baseclasses.testtools()
testrunner._run_from_object(j)
```

### 3- From JSX factory

If there is more than one test for a factory, tests can be written under `tests` directory beside the factory, then the factory should inherit from test runner `j.baseclasses.testtools`, and define test method which will contain the runner method.

```python
class Myclass(j.baseclasses.object, j.baseclasses.testtools):

    def test(self, name):
        self._tests_run(name=name)
```

**Note:** `name` can be used for running only one of these test files under tests directory and it can be file name or part of the file name.

## Report

After the tests finishes, a report will be printed with number of passed, failed, errored and skipped tests, and collect all failed, errored and skipped tests.

### XML report

To get the full result report in xml file, test runner should be defined as folowing:

```python
from Jumpscale import j
testrunner = j.baseclasses.testtools(xml_report=True, xml_path="result.xml", xml_testsuite_name="my testsuite")
```
