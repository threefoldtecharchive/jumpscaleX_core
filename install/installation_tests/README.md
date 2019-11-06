## Running Installation tests 
### Clone this repo
git clone https://github.com/threefoldtech/jumpscaleX -b development_jumpscale

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

### Test cases Requirement Traceability Matrix: 

|  **ID** | **Requiements** |  |  |  | **TC ID** | **TC URL** | **TC Title** | **Execute Type** |
| :---: | :---: | --- | --- | --- | :---: | :---: | :---: | :---: |
|  **R001** | **Docker** | container-install | --no-interactive | Linux | TC103 & TC149 | https://jsx.testquality.com/project/7543/plan/13826/test/183335 | [Linux os][ no-interactive] Test docker option | automated |
|   |  |  |  |  |  | https://jsx.testquality.com/project/7543/plan/13826/test/183381 | [Linux os][ no-interactive] Test  installtion inside jumpscale docker | automated |
|  **R002** |  |  |  | Mac | TC150 & TC152 | https://jsx.testquality.com/project/7543/plan/13826/test/183382 | [mac_os][no-interactive] Test docker option | automated |
|   |  |  |  |  |  | https://jsx.testquality.com/project/7543/plan/13826/test/183382 | [Mac os][no-interactive]Test  jumpscale installtion inside jumpscale docker | automated |
|  **R003** |  |  | interactive | Linux |  |  |  | manual |
|  **R004** |  |  |  | Mac |  |  |  | manual |
|  **R005** |  |  | --no-interactive -d(reinstall) | Linux | TC200 | https://jsx.testquality.com/project/7543/plan/13826/test/183929 | [Linux os][ no-interactive] Test container-install -d option |  |
|  **R006** |  |  |  | Mac | TC201 | https://jsx.testquality.com/project/7543/plan/13826/test/183930 | [mac os][ no-interactive] Test container-install -d option |  |
|  **R007** |  |  | interactive  -d(reinstall) | Linux |  |  |  |  |
|  **R008** |  |  |  | Mac |  |  |  |  |
|  **R009** |  | container-kosmos | Mac |  | TC150 | https://jsx.testquality.com/project/7543/plan/13826/test/183382 | [mac_os][no-interactive] Test docker option | automated |
|  **R010** |  |  | Linux |  | TC103 | https://jsx.testquality.com/project/7543/plan/13826/test/183335 | [Linux os][ no-interactive] Test docker option | automated |
|  **R011** |  | container-shell | Mac |  | TC150 | https://jsx.testquality.com/project/7543/plan/13826/test/183382 | [mac_os][no-interactive] Test docker option | automated |
|  **R012** |  |  | Linux |  | TC103 | https://jsx.testquality.com/project/7543/plan/13826/test/183335 | [Linux os][ no-interactive] Test docker option | automated |
|  **R013** |  | container-start | Mac |  | TC151 | https://jsx.testquality.com/project/7543/plan/13826/test/183383 | [Mac os] [no-interactive] Test container-stop and container-start options | automated |
|  **R014** |  |  | Linux |  | TC148 | https://jsx.testquality.com/project/7543/plan/13826/test/183380 | [Linux os][ no-interactive] Test container-stop and container-start options | automated |
|  **R015** |  | container-stop | Mac |  | TC151 | https://jsx.testquality.com/project/7543/plan/13826/test/183383 | [Mac os] [no-interactive] Test container-stop and container-start options | automated |
|  **R016** |  |  | Linux |  | TC148 | https://jsx.testquality.com/project/7543/plan/13826/test/183380 | [Linux os][ no-interactive] Test container-stop and container-start options | automated |
|  **R017** |  | container-delete | Mac |  | TC170 | https://jsx.testquality.com/project/7543/plan/13826/test/183447 | [linux-os] [no-interactive] Test container-delete option | automated |
|  **R018** |  |  | Linux |  | TC171 | https://jsx.testquality.com/project/7543/plan/13826/test/183448 | [mac-os] [no-interactive] Test container-delete option | automated |
|  **R019** |  | containers-reset | Mac |  | TC175 | https://jsx.testquality.com/project/7543/plan/13826/test/183452 | [mac-os] [no-interactive] Test containers-reset option | automated |
|  **R020** |  |  | Linux |  | TC174 | https://jsx.testquality.com/project/7543/plan/13826/test/183451 | [linux] [no-interactive] Test containers-reset option | automated |
|  **R021** |  | container-import | Mac |  | TC178 | https://jsx.testquality.com/project/7543/plan/13826/test/183862 | [mac] [no-interactive] Test containers-import and container-export option |  |
|  **R022** |  |  | Linux |  | TC177 | https://jsx.testquality.com/project/7543/plan/13826/test/183861 | [linux] [no-interactive] Test container-import option and container-export option |  |
|  **R023** |  | container-export | Mac |  | TC178 | https://jsx.testquality.com/project/7543/plan/13826/test/183862 | [mac] [no-interactive] Test containers-import and container-export option |  |
|  **R024** |  |  | Linux |  | TC177 | https://jsx.testquality.com/project/7543/plan/13826/test/183861 | [linux] [no-interactive] Test container-import option and container-export option |  |
|  **R025** |  | container-clean | Mac |  | TC181 | https://jsx.testquality.com/project/7543/plan/13826/test/183865 | [mac] [no-interactive] Test container-clean option |  |
|  **R026** |  |  | Linux |  | TC179 | https://jsx.testquality.com/project/7543/plan/13826/test/183863 | [linux] [no-interactive] Test container-clean option |  |
|  **R027** |  | configure | Mac |  | TC103 | https://jsx.testquality.com/project/7543/plan/13826/test/183335 | [Mac os][ no-interactive] Test docker option |  |
|  **R028** |  |  | Linux |  | TC150 | https://jsx.testquality.com/project/7543/plan/13826/test/183382 | [Linux os][ no-interactive] Test docker option |  |
|  **R029** | **wireguard** | **???????????** |  |  |  |  |  |  |
|  **R030** | Insystem | install | --no-interactive | Linux | TC153 & TC154 | https://jsx.testquality.com/project/7543/plan/13826/test/183385 | [linux os] [no-interactive ]Test in system option | automated |
|   |  |  |  |  |  | https://jsx.testquality.com/project/7543/plan/13826/test/183386 | [ Linux os ][no-interactive]Test JSX installation insystem | automated |
|  **R031** |  |  |  | Mac | TC155  & TC173 | https://jsx.testquality.com/project/7543/plan/13826/test/183387 | [Mac os ][no-interactive]Test Jumpscale installation with in system option | automated |
|   |  |  |  |  |  | https://jsx.testquality.com/project/7543/plan/13826/test/183450 | [ Mac OS ] [no-interactive ] Test JSX installation insystem | automated |
|  **R032** |  |  | interactive | Linux | TC172 | https://jsx.testquality.com/project/7543/plan/13826/test/183449 | [linux os][interactive]Test insystem option | manual |
|  **R033** |  |  |  | Mac | TC202 | https://jsx.testquality.com/project/7543/plan/13826/test/184064 | [mac os][interactive]Test insystem option | manual |
|  **R034** |  |  | --no-interactive --reinstall | Linux | TC156 & TC157 & TC158 | https://jsx.testquality.com/project/7543/plan/13826/test/183388 | [linux os][no-interactive]Test in system reinstall  without JSX installed before | automated |
|   |  |  |  |  |  | https://jsx.testquality.com/project/7543/plan/13826/test/183389 | [linux os] [no-interactive]Test in system reinstall in jsx machine | automated |
|   |  |  |  |  |  | https://jsx.testquality.com/project/7543/plan/13826/test/183388 | [linux os][no-interactive]Test in system reinstall  after interrupted jsx installation | manual |
|  **R035** |  |  |  | Mac | TC161 & TC162 & TC163 | https://jsx.testquality.com/project/7543/plan/13826/test/183437 | [mac os][no-interactive]Test in system reinstall  without JSX installed before | automated |
|   |  |  |  |  |  | https://jsx.testquality.com/project/7543/plan/13826/test/183438 | [mac os] [no-interactive]Test in system reinstall in jsx machine | automated |
|   |  |  |  |  |  | https://jsx.testquality.com/project/7543/plan/13826/test/183439 | [mac os][no-interactive]Test in system reinstall  after interrupted jsx installation | manual |
|  **R036** |  |  | interactive  --reinstall | Linux | TC164 & TC165  & TC166 | https://jsx.testquality.com/project/7543/plan/13826/test/183440 | [linux os][interactive]Test in system reinstall without JSX installed before | manual |
|   |  |  |  |  |  | https://jsx.testquality.com/project/7543/plan/13826/test/183441 | [linux os] [interactive]Test in system reinstall in jsx machine | manual |
|   |  |  |  |  |  | https://jsx.testquality.com/project/7543/plan/13826/test/183442 | [linux os][interactive] Test in system reinstall  after interrupted jsx installation | manual |
|  **R037** |  |  |  | Mac | TC167 & TC168 & TC169 | https://jsx.testquality.com/project/7543/plan/13826/test/183443 | [mac os][interactive]Test in system reinstall  without JSX installed before | manual |
|   |  |  |  |  |  | https://jsx.testquality.com/project/7543/plan/13826/test/183445 | [mac os] [interactive]Test in system reinstall in jsx machine | manual |
|   |  |  |  |  |  | https://jsx.testquality.com/project/7543/plan/13826/test/183446 | [mac os][interactive] Test in system reinstall  after interrupted jsx installation | manual |
|  **R038** |  | kosmos | Linux |  | TC154 | https://jsx.testquality.com/project/7543/plan/13826/test/183386 | [ Linux os ][no-interactive]Test JSX installation insystem | automated |
|  **R039** |  |  | Mac |  | TC173 | https://jsx.testquality.com/project/7543/plan/13826/test/183450 | [ Mac OS ] [no-interactive ] Test JSX installation insystem | automated |
|  **R040** |  | generate | Linux |  | TC154 | https://jsx.testquality.com/project/7543/plan/13826/test/183386 | [ Linux os ][no-interactive]Test JSX installation insystem | automated |
|  **R041** |  |  | Mac |  | TC173 | https://jsx.testquality.com/project/7543/plan/13826/test/183450 | [ Mac OS ] [no-interactive ] Test JSX installation insystem | automated |
|  **R042** |  | modules-install | Linux |  | TC207 | https://jsx.testquality.com/project/7543/plan/13826/test/184116 | [Linux OS] test modules-install option in system | automated |
|  **R043** |  |  | Mac |  | TC208 |  | [mac OS] test modules-install option in system | automated |
|  **R044** |  | check | Linux |  | TC205 | https://jsx.testquality.com/project/7543/plan/13826/test/184114 | [Linux OS] test check option insystem | automated |
|  **R045** |  |  | Mac |  | TC206 | https://jsx.testquality.com/project/7543/plan/13826/test/184115 | [Mac OS] test check option insystem | automated |
|  **R046** |  | configure | Linux |  | TC153 | https://jsx.testquality.com/project/7543/plan/13826/test/183385 | [linux os] [no-interactive ]Test in system option | automated |
|  **R047** |  |  | Mac |  | TC155 | https://jsx.testquality.com/project/7543/plan/13826/test/183387 | [Mac os ][no-interactive]Test Jumpscale installation with in system option | automated |
|  **R048** |  | bcdb-system-delete | Linux |  | TC203 | https://jsx.testquality.com/project/7543/plan/13826/test/184065 | [linux os] test bcdb_system_delete option | automated |
|  **R049** |  |  | Mac |  | TC204 | https://jsx.testquality.com/project/7543/plan/13826/test/184110 | [mac os] test bcdb_system_delete option | automated |
