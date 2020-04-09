# Installer

## Packaged installer (sdk)

To build, you need to have:
* `python3`
* `pip`
* `upx` is used to compress binary executable, can be installed with:
    * ubuntu: `apt-get install upx`
    * macos (using brew): `brew install upx`
* `pyinstaller` can be installed using `pip3 install pyinstaller --user`



### Build:

Run the packaging script:

```bash
cd install
./package.sh
```

If nothing gone wrong, you should find the final binary executable at `dist` directory.

Try running it with:

```bash
./dist/3sdk
```

## Running a new container

to start a new container `sdk start name:mycontainer`	
