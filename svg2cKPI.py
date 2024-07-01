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
    'M', 'L', 'C', 'Q', 'S', 'T', 'V', 'H', 'Z'
]

VGLITE_PATH_COMMAND_MNEMONICS = {
    'M': "VLC_OP_MOVE",
    "L": "VLC_OP_LINE",
    "C": "VLC_OP_CUBIC",
    "Q": "VLC_OP_QUAD",
    "S": "VLC_OP_QUAD",
    "T": "VLC_OP_LINE",
    "V": "VLC_OP_LINE",
    "H": "VLC_OP_LINE",
    "Z": "VLC_OP_CLOSE"
}

VGLITE_PATH_COMMAND_ARGCNT = {
    "M": 2,
    "L": 2,
    "C": 6,
    "Q": 4,
    "S": 4,
    "T": 2,
    "V": 2,
    "H": 2,
    "Z": 0
}

colors = {
    "aliceblue": 0xfff0f8ff,
    "antiquewhite": 0xfffaebd7,
    "aqua": 0xff00ffff,
    "aquamarine": 0xff7fffd4,
    "azure": 0xfff0ffff,
    "beige": 0xfff5f5dc,
    "bisque": 0xffffe4c4,
    "black": 0xff000000,
    "blanchedalmond": 0xffffebcd,
    "blue": 0xff0000ff,
    "blueviolet": 0xff8a2be2,
    "brown": 0xffa52a2a,
    "burlywood": 0xffdeb887,
    "cadetblue": 0xff5f9ea0,
    "chartreuse": 0xff7fff00,
    "chocolate": 0xffd2691e,
    "coral": 0xffff7f50,
    "cornflowerblue": 0xff6495ed,
    "cornsilk": 0xfffff8dc,
    "crimson": 0xffdc143c,
    "cyan": 0xff00ffff,
    "darkblue": 0xff00008b,
    "darkcyan": 0xff008b8b,
    "darkgoldenrod": 0xffb8860b,
    "darkgray": 0xffa9a9a9,
    "darkgrey": 0xffa9a9a9,
    "darkgreen": 0xff006400,
    "darkkhaki": 0xffbdb76b,
    "darkmagenta": 0xff8b008b,
    "darkolivegreen": 0xff556b2f,
    "darkorange": 0xffff8c00,
    "darkorchid": 0xff9932cc,
    "darkred": 0xff8b0000,
    "darksalmon": 0xffe9967a,
    "darkseagreen": 0xff8fbc8f,
    "darkslateblue": 0xff483d8b,
    "darkslategray": 0xff2f4f4f,
    "darkslategrey": 0xff2f4f4f,
    "darkturquoise": 0xff00ced1,
    "darkviolet": 0xff9400d3,
    "deeppink": 0xffff1493,
    "deepskyblue": 0xff00bfff,
    "dimgray": 0xff696969,
    "dimgrey": 0xff696969,
    "dodgerblue": 0xff1e90ff,
    "firebrick": 0xffb22222,
    "floralwhite": 0xfffffaf0,
    "forestgreen": 0xff228b22,
    "fuchsia": 0xffff00ff,
    "gainsboro": 0xffdcdcdc,
    "ghostwhite": 0xfff8f8ff,
    "gold": 0xffffd700,
    "goldenrod": 0xffdaa520,
    "gray": 0xff808080,
    "grey": 0xff808080,
    "green": 0xff008000,
    "greenyellow": 0xffadff2f,
    "honeydew": 0xfff0fff0,
    "hotpink": 0xffff69b4,
    "indianred": 0xffcd5c5c,
    "indigo": 0xff4b0082,
    "ivory": 0xfffffff0,
    "khaki": 0xfff0e68c,
    "lavender": 0xffe6e6fa,
    "lavenderblush": 0xfffff0f5,
    "lawngreen": 0xff7cfc00,
    "lemonchiffon": 0xfffffacd,
    "lightblue": 0xffadd8e6,
    "lightcoral": 0xfff08080,
    "lightcyan": 0xffe0ffff,
    "lightgoldenrodyellow": 0xfffafad2,
    "lightgray": 0xffd3d3d3,
    "lightgrey": 0xffd3d3d3,
    "lightgreen": 0xff90ee90,
    "lightpink": 0xffffb6c1,
    "lightsalmon": 0xffffa07a,
    "lightseagreen": 0xff20b2aa,
    "lightskyblue": 0xff87cefa,
    "lightslategray": 0xff778899,
    "lightslategrey": 0xff778899,
    "lightsteelblue": 0xffb0c4de,
    "lightyellow": 0xffffffe0,
    "lime": 0xff00ff00,
    "limegreen": 0xff32cd32,
    "linen": 0xfffaf0e6,
    "magenta": 0xffff00ff,
    "maroon": 0xff800000,
    "mediumaquamarine": 0xff66cdaa,
    "mediumblue": 0xff0000cd,
    "mediumorchid": 0xffba55d3,
    "mediumpurple": 0xff9370d8,
    "mediumseagreen": 0xff3cb371,
    "mediumslateblue": 0xff7b68ee,
    "mediumspringgreen": 0xff00fa9a,
    "mediumturquoise": 0xff48d1cc,
    "mediumvioletred": 0xffc71585,
    "midnightblue": 0xff191970,
    "mintcream": 0xfff5fffa,
    "mistyrose": 0xffffe4e1,
    "moccasin": 0xffffe4b5,
    "navajowhite": 0xffffdead,
    "navy": 0xff000080,
    "oldlace": 0xfffdf5e6,
    "olive": 0xff808000,
    "olivedrab": 0xff6b8e23,
    "orange": 0xffffa500,
    "orangered": 0xffff4500,
    "orchid": 0xffda70d6,
    "palegoldenrod": 0xffeee8aa,
    "palegreen": 0xff98fb98,
    "paleturquoise": 0xffafeeee,
    "palevioletred": 0xffd87093,
    "papayawhip": 0xffffefd5,
    "peachpuff": 0xffffdab9,
    "peru": 0xffcd853f,
    "pink": 0xffffc0cb,
    "plum": 0xffdda0dd,
    "powderblue": 0xffb0e0e6,
    "purple": 0xff800080,
    "red": 0xffff0000,
    "rosybrown": 0xffbc8f8f,
    "royalblue": 0xff4169e1,
    "saddlebrown": 0xff8b4513,
    "salmon": 0xfffa8072,
    "sandybrown": 0xfff4a460,
    "seagreen": 0xff2e8b57,
    "seashell": 0xfffff5ee,
    "sienna": 0xffa0522d,
    "silver": 0xffc0c0c0,
    "skyblue": 0xff87ceeb,
    "slateblue": 0xff6a5acd,
    "slategray": 0xff708090,
    "slategrey": 0xff708090,
    "snow": 0xfffffafa,
    "springgreen": 0xff00ff7f,
    "steelblue": 0xff4682b4,
    "tan": 0xffd2b48c,
    "teal": 0xff008080,
    "thistle": 0xffd8bfd8,
    "tomato": 0xffff6347,
    "turquoise": 0xff40e0d0,
    "violet": 0xffee82ee,
    "wheat": 0xfff5deb3,
    "white": 0xffffffff,
    "whitesmoke": 0xfff5f5f5,
    "yellow": 0xffffff00,
    "yellowgreen": 0xff9acd32
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

counter = 0
generated_ids = []
def generate_id(name):
    global counter
    counter += 1
    return f"{name}_{counter}"

for redpath in paths:
    p_cmd_arg = redpath.d()
    if 'id' in attributes[i]:
        print(f"/*path id={attributes[i]['id']}*/")
    path_str = redpath.d().replace(',',' ')
    new_id_value = generate_id(attributes[i]['name'])
    generated_ids.append(new_id_value)
    print("static data_mnemonic_t %s_%s_data[] = {" % (imageName, new_id_value))
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

    if 'fill' in attributes[i] and attributes[i]['fill'] != 'none':
        cmd_add(out_cmd, attributes[i], 'fill-rule')
        cmd_add(out_cmd, attributes[i], 'fill-opacity')
        name = attributes[i]['fill']
        if name.startswith('#'):
            if len(name) == 4:  # Shorthand hex color like #F60
                name = '#' + ''.join([c*2 for c in name[1:]])
                m = re.search(r'#([0-9a-fA-F]{6})', name)
            else:
                m = re.search(r'#([0-9a-fA-F]{6})', attributes[i]['fill'])
        n = re.match(r'rgb\((\d+),(\d+),(\d+)\)', attributes[i]['fill'])
        if name in colors:
            opa = (colors[name] & 0xFF000000) >> 24 
            r = (colors[name] & 0x00FF0000) >> 16
            g = (colors[name] & 0x0000FF00) >> 8
            b = (colors[name] & 0x000000FF)
            color_data.append("%x" % ((opa << 24) | (b << 16) | (g << 8) | r))
        elif m:
            color = m.group(1)
            r = color[0:2]
            g = color[2:4]
            b = color[4:6]
            color_data.append("ff%s%s%s" % (b,g,r))
        elif n:
            r=int(m.group(1))
            g=int(m.group(2))
            b=int(m.group(3))
            color_data.append("0x%x" % (r * 65536 + g * 256 + b))
        else:
            print("Error: Fill value not supported", sep="---",file=sys.stderr)

    if 'fill' in attributes[i]:
        fill_value = attributes[i].get('fill')
        if fill_value == 'none':
            color = 0xff000000  # Black color value
            color = f"{color:08x}"
            color_data.append(color)

    if 'style' in attributes[i] and attributes[i]['style'] != 'none':
        # fill-paint
        #m = re.match(r'rgb\((\d+),(\d+),(\d+)\)', attributes[i]['fill'])
        m = re.search(r'fill:#(\w+)', attributes[i]['style'])
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
                print("Error: Style value not supported", sep="---",file=sys.stderr)
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
            print("Error: Stroke value not supported", sep="---",file=sys.stderr)

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
for i, new_id_value in enumerate(generated_ids):
    path_name = "%s_%s_data" % (imageName, new_id_value)
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
print("")

print("#if VGLITE_HEADER_VERSION <= 6");
print("#define TEST_DATA_MAX 10");
print("#define APP_VG_LITE_DRAW_ZERO               (VG_LITE_DRAW_STROKE_PATH)");
print("#define APP_VG_LITE_DRAW_STROKE_PATH        (VG_LITE_DRAW_STROKE_PATH)");
print("#define APP_VG_LITE_DRAW_FILL_PATH          (VG_LITE_DRAW_FILL_PATH)");
print("#define APP_VG_LITE_DRAW_FILL_STROKE_PATH   (VG_LITE_DRAW_FILL_STROKE_PATH)");
print("#define APP_PATH_FILL_TYPE  vg_lite_draw_path_type_t")

print("#else");
print("#define TEST_DATA_MAX 12");
print("#define APP_VG_LITE_DRAW_ZERO               (VG_LITE_DRAW_ZERO)");
print("#define APP_VG_LITE_DRAW_STROKE_PATH        (VG_LITE_DRAW_STROKE_PATH)");
print("#define APP_VG_LITE_DRAW_FILL_PATH          (VG_LITE_DRAW_FILL_PATH)");
print("#define APP_VG_LITE_DRAW_FILL_STROKE_PATH   (VG_LITE_DRAW_FILL_STROKE_PATH)");
print("#define APP_PATH_FILL_TYPE  vg_lite_path_type_t")
print("#endif");
print("")

lines = []
for i in range(len(paths)):
    if ('fill' in attributes[i] and attributes[i]['fill'] == 'none') and ('stroke' in attributes[i] and attributes[i]['stroke'] == 'none'):
        lines.append("APP_VG_LITE_DRAW_ZERO")
    elif ('fill' in attributes[i] and attributes[i]['fill'] == 'none') and ('stroke' in attributes[i] and attributes[i]['stroke'] != 'none'):
        lines.append("APP_VG_LITE_DRAW_STROKE_PATH")
    elif ('fill' in attributes[i] and attributes[i]['fill'] != 'none') and ('stroke' in attributes[i] and attributes[i]['stroke'] == 'none'):
        lines.append("APP_VG_LITE_DRAW_FILL_PATH")
    elif ('fill' in attributes[i] and attributes[i]['fill'] != 'none') and ('stroke' in attributes[i] and attributes[i]['stroke'] != 'none'):
        lines.append("APP_VG_LITE_DRAW_FILL_STROKE_PATH")
    else:
        lines.append("APP_VG_LITE_DRAW_FILL_PATH")

print("APP_PATH_FILL_TYPE %s_path_type[] = {" % imageName);
for i in range(len(lines)):
    if i == len(lines) - 1:
        print(lines[i])  # Last line without a trailing comma
    else:
        print(lines[i] + ",")
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
