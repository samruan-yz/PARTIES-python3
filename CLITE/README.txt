README

The folder contains two files:

1. clite.py -> This file runs CLITE in real time along with other LC and BG applications. Adjust the variables declared at the top of the file according the specific requirements. All python libraries required are listed at the top of the files. Intel processors with cache allocation technology (CAT) and memory bandwidth allocation (MBA) features are required to use CLITE in the given form. Modify the variables according to the available and desired resource partitions. The code can also be modified according to the desired overhead/time of optimization by adjusting the appropriate variables (see comments in the code).

2. gen_all_configs.py -> This file simply generates a list of all possible configurations given a set of applications and resources. This file can be used to generate and test arbitrary configurations and calculate the size of the configuration space.