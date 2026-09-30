
import cmake_vcxproj

import locale

import argparse
import os

def dir_file(path):
    if os.path.isfile(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"readable_file:{path} is not a valid file path")

def makeelementwtext(elname, text):
    elret = ET.Element(elname)
    elret.text = text
    return elret

parser = argparse.ArgumentParser()
parser.add_argument("filename",type=dir_file)
parser.add_argument("--autofilter", action='store_true')
args = parser.parse_args()

vcxlist = cmake_vcxproj.converter_to_vcxproj(args.filename, args.autofilter)

for entry in vcxlist:
    name = entry["name"]
    vcxbuffer = entry["projbuffer"]
    vcxfilterbuffer = entry["projfilterbuffer"]

    wheretosavevcxproj = name + ".vcxproj"
    wheretosavevcxprojfilters = name + ".vcxproj.filters"

    #main proj
    with open(wheretosavevcxproj, "a") as f:
        f.truncate(0)
        f.write(vcxbuffer)

    #filters
    with open(wheretosavevcxprojfilters, "a") as f:
        f.truncate(0)
        f.write(vcxfilterbuffer)

print("done!\n")