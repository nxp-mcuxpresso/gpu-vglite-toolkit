#!/bin/bash

#
# This is top-level script to use gpu-vglite-toolkit applicaiton in Linux.
# gpu-vglite-toolkit application uses svgpathtools as third-party component
# To parse SVG files. NXP has done some improvements in this open-source library
# and they need to be at specific path for gpu-vglite-toolkit to operate.
# As a result on 1st execution of this script, it setup's necessary environment.
#
# Usage:
#  gpu-vglite-tests.sh paint-color-01-t.svg
#     Without output filename it generartes svgt12_test.h
#     e.g. 
#        svgt12_test.h as output heaader with graphics artifacts
#        paint-color-01-t.err for path summary, and any error during SVG to header conversion
#
#  gpu-vglite-tests.sh paint-color-01-t.svg paint-color-01-t.h
#     With output file name it generated user-specified output file.
#     e.g. 
#        paint-color-01-t.h as output heaader with graphics artifacts
#        paint-color-01-t.err for path summary, and any error during SVG to header conversion
#

INPUT_FILE=$1

if [ ! -x $PWD/svgpathtools/.git ]; then
    pip3 install -r requirements.txt
    git submodule init
    git submodule update
fi

if [ ! -z "$2" ]; then
        OUTPUT_FILE=$2
else
        OUTPUT_FILE="svgt12_test.h"
fi

# Name of output file as header
#OUT_NAME=$(echo $(basename ${INPUT_FILE}) | sed 's/\.svg/\.h/')
# File to capture errors from 
OUT_ERR=$(echo $(basename ${INPUT_FILE}) | sed 's/\.svg/\.err/')

# Property setup svgpathtools module path
export PYTHONPATH=$PYTHONPATH:$PWD/svgpathtools

# Actual SVG -> header Conversion
python3 svg2h.py ${INPUT_FILE} 1>"${OUTPUT_FILE}" 2>"${OUT_ERR}"
echo Created ${OUTPUT_FILE} from ${INPUT_FILE}

