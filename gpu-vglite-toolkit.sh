
INPUT_FILE=/opt/BUILD/GTEC/VGLITE/SVGT12/$1

if [ ! -x $PWD/svgpathtools ]; then
    # External public MIT licensed repository
    #git clone https://github.com/mathandy/svgpathtools.git

    # Internal NXP development repository
    git clone -b vglite-tools-next ssh://git@bitbucket.sw.nxp.com/gtec/svgpathtools.git
fi

if [ ! -z "$2" ]; then
        OUTPUT_FILE=$2
else
        OUTPUT_FILE="svgt12_test.h"
fi

sed 's/xml:id/id/g' $INPUT_FILE > svgt12_test.svg

export PYTHONPATH=$PYTHONPATH:$PWD/svgpathtools
python3 svg2cKPI.py svgt12_test.svg > "$OUTPUT_FILE"
cp -v $OUTPUT_FILE R5_heaader_file/$(basename ${INPUT_FILE})_${OUTPUT_FILE}
