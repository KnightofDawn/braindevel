#!/usr/bin/env python

import sys
import subprocess
import time

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: ./train_scripts/train_final_eval.py configfilename [start] [stop] [step] [train_flags]")
    config_filename = sys.argv[1]
    start = 1
    stop = 144
    step = 1
    if len(sys.argv) > 2:
        start = int(sys.argv[2])
    if len(sys.argv) > 3:
        stop = int(sys.argv[3])
    if len(sys.argv) > 4:
        step = int(sys.argv[4])
    if len(sys.argv) > 5:
        train_arg_string = " ".join(sys.argv[5:])
    else:
        train_arg_string = ""

    train_script_file = "./csp/train_on_cluster.py"

    for i_start in range(start,stop+1, step):
        if i_start > start:
            print("Sleeping 1 minute until starting next experiment...")
            time.sleep(60)
        i_stop = min(i_start + step - 1, stop)
        command = "{:s} {:s} --start {:d} --stop {:d} {:s}".format(
            train_script_file, config_filename, i_start, i_stop, 
            train_arg_string)
        subprocess.call([command],shell=True)
        #print command
