
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

echo ${INPUT_FILE}
OUT_NAME=$(echo $(basename ${INPUT_FILE}) | sed 's/\.svg/\.h/')

OUT_ERR=$(echo $(basename ${INPUT_FILE}) | sed 's/\.svg/\.err/')
export PYTHONPATH=$PYTHONPATH:$PWD/svgpathtools
python3 svg2cKPI.py svgt12_test.svg > "$OUTPUT_FILE" 2>${OUT_ERR}
cp -v ${OUTPUT_FILE} /opt/BUILD/GTEC/VGLITE_FINAL/MCUSDK/source/${OUTPTU_FILE}
mv -fv ${OUTPUT_FILE} R5_header_file/${OUT_NAME}
mv -fv ${OUT_ERR} R5_header_file/${OUT_ERR}
