#! /usr/bin/env python3

# Read SVG into a list of path objects and list of dictionaries of attributes 
# Update: You can now also extract the svg-attributes by setting
# return_svg_attributes=True, or with the convenience function svg2paths2
from svgpathtools import svg2paths2
import sys
import json
import re

from pathlib import Path

input_file=sys.argv[1]
paths, attributes, svg_attributes = svg2paths2(input_file, return_svg_attributes=True)

# Let's print out the first path object and the color it was in the SVG
# We'll see it is composed of two CubicBezier objects and, in the SVG file it 
# came from, it was red
#redpath = paths[0]
#redpath_attribs = attributes[0]


PATH_COMMANDS = [
        'M',
        'H', 'h', 'V', 'v',
        'L', 'l', 'C', 'c',
        'S', 's', 'A', 'a',
        'Q', 'q', 'T', 't'
]
def path_split(p_cmd_arg):
    cmd_arg_list = p_cmd_arg.split(' ')
    arg = []
    cmd = []
    for el in cmd_arg_list:
        if el in PATH_COMMANDS:
            cmd.extend([el])
        else:
            arg.extend([el])
    return (cmd,arg)

VGLITE_PATH_COMMANDS = [
    'M', 'L', 'C', 'Z'
]

VGLITE_PATH_COMMAND_MNEMONICS = {
    'M': "VLC_OP_MOVE",
    "L": "VLC_OP_LINE",
    "C": "VLC_OP_CUBIC",
    "Z": "VLC_OP_CLOSE"
}

VGLITE_PATH_COMMAND_ARGCNT = {
    "M": 2,
    "L": 2,
    "C": 6,
    "Z": 0
}

def path_convert2vglite(p_cmd_arg, p_datatype, p_x_offset, p_y_offset):
    cmd_arg_list = p_cmd_arg.split(' ')
    i = 0
    lines = []
    while i < len(cmd_arg_list):
        if cmd_arg_list[i] in VGLITE_PATH_COMMANDS:
            command = cmd_arg_list[i]
            i += 1
            if VGLITE_PATH_COMMAND_MNEMONICS[command]  == "VLC_OP_CLOSE":
                #ignore the close opcode. VSI VGLite does not handle it well.
                continue
            line = "    {.cmd=" + VGLITE_PATH_COMMAND_MNEMONICS[command] + "}, "
            argCnt = VGLITE_PATH_COMMAND_ARGCNT[command]
            for x in range(argCnt):
                coord = float(cmd_arg_list[i])
                #expect x coordinate is even and y coordinate is odd. This will fail for arc commands.
                if (x % 2):
                    coord += p_y_offset
                else:
                    coord += p_x_offset
                #line += "{.data=(" + p_datatype +")" + str(coord) + " }, "
                line += "{.data=(%s) %.2f}," % (p_datatype, coord)
                i += 1
            lines.append(line)
        else:
            print ("Unknown command "+cmd_arg_list[i] )
            assert 0
            i += 1
    return lines



TAGS = {
        "evenodd"   : 'E',
        "nonzero"   : 'N',
        "butt"      : 'B',
        "round"     : 'r',
        "square"    : 'U',
        "miter"     : 'R',
}


g_cmd = []
g_arg = []
i = 0

color_data = []

data_type = "int32_t"
#data_type = "float"

VGLITE_DATA_TYPES = {
    "int8_t" : "VG_LITE_S8",
    "int16_t" : "VG_LITE_S16",
    "int32_t" : "VG_LITE_S32",
    "float"  :  "VG_LITE_FP32"
}


def cmd_add(out_cmd, attributes, rule_name):
    if rule_name in attributes:
        out_cmd.extend(TAGS[attributes['fill-rule']])

imageName = Path(input_file).stem

print("#ifndef STATIC_PATH_DEFINES_H")
print("#define STATIC_PATH_DEFINES_H")
print("")
print("#include \"vg_lite.h\"")
print("")
print("typedef union data_mnemonic {")

if data_type == "float":
    print("    uint32_t cmd;")
else:
    print("    %s cmd;" % data_type)

print("    %s data;" % data_type)
print("} data_mnemonic_t;")
print("")
print("typedef struct path_info {")
print("    uint32_t  path_length;")
print("    %s  *path_data;" % data_type)
print("} path_info_t;")
print("")

print("typedef struct image_info {")
print("    char *image_name;")
print("    int  image_size[2];")
print("    vg_lite_format_t data_format;")
print("    int path_count;")
print("    path_info_t paths_info[];")
print("} image_info_t;")
print("")
print("#endif")
print("")
print("")

for redpath in paths:
    p_cmd_arg = redpath.d()
    path_str = redpath.d().replace(',',' ')
    print("static data_mnemonic_t %s_%s_data[] = {" % (imageName, attributes[i]['id']))
    lines = path_convert2vglite(path_str, data_type, 0, 0)
     
    for line in lines:
        print(line)
    print("    {.cmd=VLC_OP_END}")
    print("};")
    print("")
    
    p_cmd,p_arg = path_split(p_cmd_arg)
    if p_cmd is None and p_arg is None:
        continue
    g_cmd.extend(p_cmd)
    g_arg.extend(p_arg)
    out_cmd = []
    out_arg = []

    if 'fill' in attributes and attributes[i]['fill'] != 'none':
        cmd_add(out_cmd, attributes[i], 'fill-rule')
        cmd_add(out_cmd, attributes[i], 'fill-opacity')
        # fill-paint
        m = re.match(r'rgb\((\d+),(\d+),(\d+)\)', attributes[i]['fill'])
        if m:
            r=int(m.group(1))
            g=int(m.group(2))
            b=int(m.group(3))
            color_data.append("0x%x" % (r * 65536 + g * 256 + b))
        else:
            print("ERROR")

    if 'style' in attributes[i] and attributes[i]['style'] != 'none':
        # fill-paint
        #m = re.match(r'rgb\((\d+),(\d+),(\d+)\)', attributes[i]['fill'])
        m = re.search(r'fill:#(\w+);', attributes[i]['style'])
        opacity = re.search(r'fill-opacity:(\d+);', attributes[i]['style'])
        if m:
            color = int(m.group(1), 16)
            r = (color & 0xFF0000) >> 16
            g = (color & 0x00FF00) >> 8
            b = (color & 0x0000FF)
        else:
            m = re.match(r'fill:.*rgb\((\d+),\s*(\d+),\s*(\d+)\)', attributes[i]['style'])
            if m:
                r=int(m.group(1))
                g=int(m.group(2))
                b=int(m.group(3))
            else:
                print("ERROR")
                assert(0)
        if opacity:
            opa = int(255*float(opacity.group(1)))
            opa = (opa & 0xFF)
        else:
            opa = 0xFF
        color_data.append("%x" % ((opa << 24) | (b << 16) | (g << 8) | r))


    if 'stroke' in attributes[i] and attributes[i]['stroke'] != "none":
        out_cmd.extend('S')
        if 'stroke-linecap' in attributes[i]:
            out_cmd.extend(TAGS[attributes[i]['stroke-linecap']])
        if 'stroke-linejoin' in attributes[i]:
            out_cmd.extend(TAGS[attributes[i]['stroke-linejoin']])
        if 'stroke-miterlimit' in attributes[i]:
            out_arg.extend([attributes[i]['stroke-miterlimit']])
        if 'stroke-width' in attributes[i]:
            out_arg.extend([attributes[i]['stroke-width']])

        # stroke-paint
        m = re.match(r'rgb\((\d+),(\d+),(\d+)\)', attributes[i]['stroke'])
        if m:
            r=int(m.group(1))
            g=int(m.group(2))
            b=int(m.group(3))
            out_arg.extend([r/255, g/255, b/255, 1.0])
        else:
            print("ERROR")

    # add the Path
    out_arg.extend([len(p_arg)])
    out_arg.extend(p_arg)
    out_cmd.extend(p_cmd)
    out_cmd.extend('E')

    i += 1

print("static image_info_t %s = {" % imageName)
print("    .image_name =\"%s\"," % imageName)
print("    .image_size = {%d, %d}," % (int(float(svg_attributes['width'])), int(float(svg_attributes['height']))))
print("    .data_format = %s," % VGLITE_DATA_TYPES[data_type])
print("    .path_count = %d," % len(paths))
print("    .paths_info = {")
for i in range(len(paths)):
    path_name = "%s_%s_data" % (imageName, attributes[i]['id'])
    if i == len(paths) - 1:
        print("        {.path_length = sizeof(%s), .path_data=(%s*)%s }" % (path_name, data_type, path_name))
    else:
        print("        {.path_length = sizeof(%s), .path_data=(%s*)%s }," % (path_name, data_type, path_name))
print("    },")
print("};")
print("")


print ("uint32_t %s_color_data[] = {" % imageName)
line = "    "
i = 0
for color in color_data:
    if (i < len(color_data)-1):
        line += "0x%s, " % color
    else:
        line += "0x%s" % color
    i += 1
    if (i % 4 == 0):
        print(line)
        line = "    "
    
print(line)

print("};")

#print(g_cmd)
#print(g_arg)
#print(json.dumps(attributes, indent=4))
print(f"==================", file=sys.stderr)
print(f"## {input_file}", file=sys.stderr)
print(f"    Nb.Paths    : {len(paths)}", file=sys.stderr)
print(f"    MoveTo      : {g_cmd.count('M')+g_cmd.count('m')}", file=sys.stderr)
print(f"    LineTo      : {g_cmd.count('L')+g_cmd.count('l')}", file=sys.stderr)
print(f"    Quadr Bezier: {g_cmd.count('Q')+g_cmd.count('q')}", file=sys.stderr)
print(f"    Cubic Bezier: {g_cmd.count('C')+g_cmd.count('c')}", file=sys.stderr)


# Commands used in Tiger
# Fill Type
#  N - None
#  F - Filled
#  E - Fill Rule is Even-Odd
# Stroke
#  N - None
#  S - Stroke Path
# Line Cap
#  B - Cap Butt
#  R - Cap Round
#  S - Cap Square
# Line Join
#  B - Join Bevel
#  R - Join Round
#  M - Join Mitter
