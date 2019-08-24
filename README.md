**Development:**  
[![Build Status](http://188.165.233.148:6010/status?project=build)](http://188.165.233.148:6010/status?project=build&&file=True)
[![Builders Status](http://188.165.233.148:6010/status?project=builders)](http://188.165.233.148:6010/status?project=builders&&file=True)

# Jumpscale

Jumpscale is a cloud automation product and a branch from what used to be 
Pylabs. About 9 years ago Pylabs was the basis of a cloud automation product 
which was acquired by SUN Microsystems from Q-Layer. In the mean time we are 
4 versions further and we have rebranded it to Jumpscale. 
Our newest release is version 10, called JSX.

- [Jumpscale](#jumpscale)
  - [About Jumpscale](#about-jumpscale)
  - [Installing Jumpscale](docs/Installation/README.md)
  - [Usage](#usage)
  - [Tutorials](#tutorials)
  - [Collaboration Conventions](#collaboration-conventions)

## About Jumpscale

Some tools available in jumpscale

* [Config Manager](docs/config/configmanager.md)
  The config manager is a secure way to manage configuration instances.
  Anything saved to the file system is NACL encrypted and only decrypted on
  the fly when accessed.

* [Executors](docs/Internals/Executors.md)
  Jumpscale comes with its own executors that abstract working locally or
  remotely.  Of these executors:

  * SSH Executor (for remote execution)
  * Local Executor (for local execution)
  * Docker Executor (for executing on dockers)

* [Builders](docs/Internals/builders/Builders.md)
  Builder tools is a set of tools to perform the common tasks in your builder (e.g read a file , write to a file, execute bash commands and many other handy methods that you will probably need in your builder) \
  To create a builder see [documentation](docs/howto/Create\ a\ new\ Builder.md)

## Install and use Jumpscale

[See installation doc](/docs/Installation/README.md)

## Running Tests
To run unittests you can execute the following command
```bash
source /sandbox/env.sh; pytest /sandbox/code/github/threefoldtech/jumpscaleX/
```

You can also run Integration tests by running the command
```bash
source /sandbox/env.sh; pytest  --integration /sandbox/code/github/threefoldtech/jumpscaleX/
```

To annotate the one of your tests is an itegeration test rather than a unittests, you can add the following docorator to the test
```python
@pytest.mark.integration
def test_main(self)
```

## Tutorials

[Check Documentation](docs/howto/README.md)


## Collaboration

[please read more here about how to collaborate](https://github.com/threefoldtech/home/tree/master/contribution)
