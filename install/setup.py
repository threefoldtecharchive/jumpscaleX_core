#!/usr/bin/env python3
import setuptools

setuptools.setup(
    name="3sdk",
    version="0.1",
    description="SDK to get started with threefold tech",
    author="Threefold Tech",
    author_email="info@threefold.tech",
    url="http://github.com/threefoldtech/jumpscaleX_core",
    install_requires=["requests", "ptpython==2.0.4", "pudb", "jedi"],
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": ["3sdk=threesdk.cli:main"]},
)
