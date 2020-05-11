## Running Installation tests 
### Clone this repo
git clone https://github.com/threefoldtech/jumpscaleX -b master

### Install requirements
cd jumpscaleX/install/tests
for linux run :
  - pip3 install -r linux_requirements.txt
for mac run :
   - pip3 install -r mac_requirements.txt
### For Docker installtion tests
cd jumpscaleX/install/tests
nosetests-3.4 -v -s test_installtion:TestInstallationInDocker

### For in system installtion tests
cd jumpscaleX/install/tests
nosetests-3.4 -v -s test_installtion:TestInstallationInSystem


### Testcases 
you can check the options tests cover from here
https://docs.google.com/spreadsheets/d/1-VjAoOtl4rasbbTdu1KK_th-lvWeAU_lpRqC0KhoPAs/edit#gid=746161841

