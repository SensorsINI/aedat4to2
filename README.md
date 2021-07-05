# aedat4to2
Convert AEDAT4 files from Inivation's DV https://gitlab.com/inivation/dv/dv-python into AEDAT-2.0 files for jAER https://github.com/SensorsINI/jaer/. 

Based on AEDAT file format specifications in https://inivation.github.io/inivation-docs/Software%20user%20guides/AEDAT_file_formats.html

Python is required (recommend Anaconda).

Started from useful script https://github.com/bald6354/aedat4tomat

Recommended: Make a conda environment....
````shell
conda create --name aedat4to2 python=3.8
````
Install the dv module...
```
pip install dv
```

Install the requirements....
````shell
pip install -r requirements.txt
````

Example Conversion:
```console
foo@bar:~$ python /home/username/aedat4to2.py -i "dvFile.aedat4" -o "dvFile.aedat"
```

You can also make a simple bash script that will process all aedat4 files in a directory into .aedat version 2 files. 

This code only writes DVS brightness change events from with aedat4 files for now. Pls request IMU samples and frames.
