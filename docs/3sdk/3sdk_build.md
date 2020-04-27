
# Build the 3sdk yourself

## <a name='Packagedinstallersdk'></a>Packaged installer (sdk)

To build the SDK yourself, you need to have:
* `python3`: 
    * ubuntu: `apt-get install python3`
    * macos: `brew install python3`
* `pip`: 
    * ubuntu: `apt-get install python3-pip`
    * macos (if not already part of the python3 installation, depends on the version): `brew install python3-pip`
* `upx` is used to compress binary executable, can be installed with:
    * ubuntu: `apt-get install upx`
    * macos (using brew): `brew install upx`
* `patchelf` (only needed on linux): 
    * ubuntu: `apt install patchelf`
* `pyinstaller` can be installed using `pip3 install pyinstaller --user`


### make sure you have jumpscale installed localy

in 3sdk
```
install
```

### <a name='Build:'></a>Build:

Run the packaging script:

```bash
cd install
./package.sh
```

If nothing goes wrong, you should find the final binary executable at `dist` directory.

Try running it with:

```bash
./dist/3sdk
```

