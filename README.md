# SensorHealthMonitoring

[![DOI](https://zenodo.org/badge/670617252.svg)](https://zenodo.org/badge/latestdoi/670617252)

This is the official repository for Sensor Health Monitoring (SHM) of the ISTAR aircraft. 


## Getting started

To start, execute the ```main.py``` function in which a flight to be checked can be defined.

This starts the SHM process in the ```checkFunction/check_logic.py``` file which reads a flight from the skystash via API and checks it against the config provided in the ```checkFunctions/check_config.py``` file. In ```checkFunctions/level3.py``` additional logic for the Level 3 checks is contained. 

SHM results are uploaded to the skystash as JSON and attached to the respective flight. To visualize these results, the ```dashboard/stashboard.py``` function can be executed to open an interactive dashboard.


