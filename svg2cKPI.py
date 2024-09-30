#! /usr/bin/env python3

# Read SVG into a list of path objects and list of dictionaries of attributes 
# Update: You can now also extract the svg-attributes by setting
# return_svg_attributes=True, or with the convenience function svg2paths2
from svgpathtools import svg2paths2
import sys
import json
import re
import numpy as np
from pathlib import Path

input_file=sys.argv[1]
paths, attributes, svg_attributes = svg2paths2(input_file, return_svg_attributes=True)

if svg_attributes.get('version') != "1.2" or svg_attributes.get('baseProfile') != "tiny":
    print("Error: SVG version must be 1.2 and baseProfile must be tiny.", sep="---",file=sys.stderr)
    sys.exit(1)

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
gradPresent = False
strokePresent = False
stroke_flag = False
color_data = []

data_type = "int32_t"
#data_type = "float"

VGLITE_DATA_TYPES = {
    "int8_t" : "VG_LITE_S8",
    "int16_t" : "VG_LITE_S16",
    "int32_t" : "VG_LITE_S32",
    "float"  :  "VG_LITE_FP32"
}

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
print("typedef struct stroke_info {")
print("    uint32_t dashPatternCnt;")
print("    float dashPhase;")
print("    float *dashPattern;")
print("    float strokeWidth;")
print("    float miterlimit;")
print("    uint32_t strokeColor;")
print("    vg_lite_cap_style_t linecap;")
print("    vg_lite_join_style_t linejoin;")
print("} stroke_info_t;")
print("")
print("typedef struct image_info {")
print("    char *image_name;")
print("    int  image_size[2];")
print("    vg_lite_format_t data_format;")
print("    float *transform;")
print("    int path_count;")
print("    stroke_info_t *stroke_info;")
print("    path_info_t paths_info[];")
print("} image_info_t;")
print("")
print("typedef struct stopValue {")
print("    float offset;")
print("    uint32_t stop_color;")
print("} stopValue_t;")
print("")
print("typedef struct linearGradient {")
print("    uint32_t num_stop_points;")
print("    vg_lite_linear_gradient_parameter_t linear_gradient;")
print("    stopValue_t *stops;")
print("} linearGradient_t;")
print("")
print("typedef struct radialGradient {")
print("    uint32_t num_stop_points;")
print("    vg_lite_radial_gradient_parameter_t radial_gradient;")
print("    stopValue_t *stops;")
print("} radialGradient_t;")
print("")
print("typedef struct hybridPath {")
print("    fill_mode_t fillType;")
print("    vg_lite_draw_path_type_t pathType;")
print("} hybridPath_t;")
print("")
print("typedef struct gradient_mode {")
print("    linearGradient_t **linearGrads;")
print("    radialGradient_t **radialGrads;")
print("    hybridPath_t *hybridPath;")
print("    vg_lite_fill_t *fillRule;")
print("}gradient_mode_t;")
print("")
print("#endif")
print("")
print("")

counter = 0
index = 0
grad_found = False
generated_ids = []
gradient_mapping = {}  # Mapping from fill name to index
def generate_id(name):
    global counter
    counter += 1
    return f"{name}_{counter}"

def convert_offset(offset):
    if offset.endswith('%'):
        return float(offset.strip('%')) / 100.0
    return float(offset)

def parse_coordinates(line):
    coordinates = re.findall(r'\d+\.\d+', line)
    return [float(num) for num in coordinates]

def get_min_max_coordinates(parsed_lines):
    min_x = min(coord[0] for coord in parsed_lines)
    max_x = max(coord[0] for coord in parsed_lines)
    min_y = min(coord[1] for coord in parsed_lines)
    max_y = max(coord[1] for coord in parsed_lines)
    return min_x, max_x, min_y, max_y

def parse_color(color_str):
    if color_str.startswith('#'):
        if len(color_str) == 4:  # Shorthand hex color like #F60
            color_str = '#' + ''.join([c*2 for c in color_str[1:]])
        m = re.search(r'#([0-9a-fA-F]{6})', color_str)
        if m:
            color = m.group(1)
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            return (255 << 24) | (r << 16) | (g << 8) | b
    elif color_str.startswith('rgb'):
        m = re.match(r'rgb\(\s*([\d\.]+)%?\s*,\s*([\d\.]+)%?\s*,\s*([\d\.]+)%?\s*\)', color_str)
        if m:
            r, g, b = m.groups()
            # Convert percentages to 0-255 scale if necessary
            if '%' in color_str:
                r, g, b = [int(float(val) * 2.55) for val in (r, g, b)]
            else:
                r, g, b = map(int, (r, g, b))
            return (255 << 24) | (r << 16) | (g << 8) | b
    elif color_str in colors:
        return colors[color_str] | 0xFF000000

def convert_transform(array):
    return ', '.join(', '.join(f'{val:.1f}f' for val in row) for row in array)

def bgr_color_convert(colorCode):
    opa = (colorCode & 0xFF000000) >> 24
    r = (colorCode & 0x00FF0000) >> 16
    g = (colorCode & 0x0000FF00) >> 8
    b = (colorCode & 0x000000FF)
    bgr_format_color = (opa << 24) | (b << 16) | (g << 8) | r
    return bgr_format_color

def getSolidColor(fill_data):
    isSolidColor = False
    bgr_color = 0
    for solid_color in attributes:
        if solid_color['name'] == 'solidColor':
            solidColorId = solid_color['id']
            if solidColorId == fill_data:
                if 'solid-color' in solid_color:
                    name = solid_color['solid-color']
                    HexColorCode = parse_color(name)
                    if HexColorCode:
                        isSolidColor = True
                        bgr_color = bgr_color_convert(HexColorCode)
    return bgr_color, isSolidColor

hybrid_path_output = f"hybridPath_t {imageName}_hybrid_path[] = {{\n"
strokeFeature = f"static stroke_info_t {imageName}_stroke_info_data[] = {{\n"
lingrad_to_path_output = f"static linearGradient_t *{imageName}_lingrad_to_path[] = {{\n"
radgrad_to_path_output = f"static radialGradient_t *{imageName}_radgrad_to_path[] = {{\n"
fill_path_grad = []
transform_output = f"static float {imageName}_transform_matrix[] = {{\n"
fill_rule_output = f"static vg_lite_fill_t {imageName}_fill_rule[] = {{\n"


for redpath in paths:
    p_cmd_arg = redpath.d()
    if 'id' in attributes[i]:
        print(f"/*path id={attributes[i]['id']}*/")
    path_str = redpath.d().replace(',',' ')
    new_id_value = generate_id(attributes[i]['name'])
    generated_ids.append(new_id_value)
    print("static data_mnemonic_t %s_%s_data[] = {" % (imageName, new_id_value))
    lines = path_convert2vglite(path_str, data_type, 0, 0)
    parsed_lines = []

    for line in lines:
        parsed_lines.append(parse_coordinates(line))
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

    fill_data = "" 
    if 'fill' in attributes[i] and attributes[i]['fill'] != 'none':
        name = attributes[i]['fill']

        fill_color = parse_color(name)
        if "url" in name:
            fill_data = (name.replace('url(#', '').replace(')', ''))
            fillColor, isSolidColor = getSolidColor(fill_data)
            color_data.append("%x" % fillColor)
        elif fill_color:
            bgr_fill_color = bgr_color_convert(fill_color)
            color_data.append("%x" % bgr_fill_color)
        else:
            print("Error: Fill value not supported", sep="---",file=sys.stderr)

    if 'fill' in attributes[i]:
        fill_value = attributes[i].get('fill')
        if fill_value == 'none':
            color = 0xff000000  # Black color value
            color = f"{color:08x}"
            color_data.append(color)

    if 'stroke' in attributes[i] and attributes[i]['stroke'] != "none":
        out_cmd.extend('S')
        strokePresent = True
        stroke_flag = True
        strokeFeature += f"    {{\n"
        if 'id' in attributes[i]:
            strokeFeature += f"/*path id={attributes[i]['id']}*/\n"
        if 'stroke-dasharray' in attributes[i]:
            if attributes[i]['stroke-dasharray'] != "none":
                dashPattern = f"static float stroke_dash_pattern_path{i+1}[] = {{\n"
                dashArray = list({attributes[i]['stroke-dasharray']})[0]
                #if dash array length is odd then double the length of dash array and double dash array elements
                if (len(dashArray.split(','))%2 != 0):
                    new_dashArray = attributes[i]['stroke-dasharray'] + "," + attributes[i]['stroke-dasharray']
                    dashPattern += f"        {new_dashArray}"
                    len_dashArray = 2*len(dashArray.split(','))
                else:
                    dashPattern += f"        {attributes[i]['stroke-dasharray']}"
                    len_dashArray = len(dashArray.split(','))
                dashPattern += "\n};\n"
                print(dashPattern)
                strokeFeature += f"        .dashPatternCnt = {len_dashArray},\n"
                strokeFeature += f"        .dashPattern = (float*)stroke_dash_pattern_path{i+1},\n"
            else:
                strokeFeature += f"        .dashPatternCnt = 0,\n"
                strokeFeature += f"        .dashPattern = NULL,\n"
        else:
            strokeFeature += f"        .dashPatternCnt = 0,\n"
            strokeFeature += f"        .dashPattern = NULL,\n"
        if 'stroke-dashoffset' in attributes[i]:
            strokeFeature += f"        .dashPhase = {attributes[i]['stroke-dashoffset']},\n"
        else:
            strokeFeature += f"        .dashPhase = 0,\n"
        if 'stroke-width' in attributes[i]:
            strokeFeature += f"        .strokeWidth = {attributes[i]['stroke-width']},\n"
        else:
            strokeFeature += f"        .strokeWidth = 1,\n"
        if 'stroke-miterlimit' in attributes[i]:
            strokeFeature += f"        .miterlimit = {attributes[i]['stroke-miterlimit']},\n"
        else:
            strokeFeature += f"        .miterlimit = 0,\n"
        name = attributes[i]['stroke']
        stroke_color = parse_color(name)
        if "url" in name:
            fill_data = (name.replace('url(#', '').replace(')', ''))
            fillColor, isSolidColor = getSolidColor(fill_data)
            if isSolidColor == True:
                strokeFeature += f"        .strokeColor = {hex(fillColor)},\n"
        elif stroke_color:
            bgr_stroke_color = bgr_color_convert(stroke_color)
            strokeFeature += f"        .strokeColor = {hex(bgr_stroke_color)},\n"
        else:
            print("Error: Fill value not supported", sep="---",file=sys.stderr)
        if 'stroke-linecap' in attributes[i]:
            if {attributes[i]['stroke-linecap']} == {'butt'}:
                strokeFeature += f"        .linecap = VG_LITE_CAP_BUTT,\n"
            elif {attributes[i]['stroke-linecap']} == {'round'}:
                strokeFeature += f"        .linecap = VG_LITE_CAP_ROUND,\n"
            elif {attributes[i]['stroke-linecap']} == {'square'}:
                strokeFeature += f"        .linecap = VG_LITE_CAP_SQUARE,\n"
        else:
            strokeFeature += f"        .linecap = VG_LITE_CAP_BUTT,\n"
        if 'stroke-linejoin' in attributes[i]:
            if {attributes[i]['stroke-linejoin']} == {'miter'}:
                strokeFeature += f"        .linejoin = VG_LITE_JOIN_MITER\n"
            elif {attributes[i]['stroke-linejoin']} == {'round'}:
                strokeFeature += f"        .linejoin = VG_LITE_JOIN_ROUND\n"
            elif {attributes[i]['stroke-linejoin']} == {'bevel'}:
                strokeFeature += f"        .linejoin = VG_LITE_JOIN_BEVEL\n"
        else:
            strokeFeature += f"        .linejoin = VG_LITE_JOIN_MITER\n"
        strokeFeature += f"    }},\n"

    stroke_value = ""
    if 'stroke' in attributes[i]:
        stroke_value = attributes[i].get('stroke')
        if stroke_value == 'none':
            strokeFeature += f"    {{\n"
            if 'id' in attributes[i]:
                strokeFeature += f"/*path id={attributes[i]['id']}*/\n"
            strokeFeature += f"        NULL,\n"
            strokeFeature += f"    }},\n"

    else:
        strokeFeature += f"    {{\n"
        if 'id' in attributes[i]:
            strokeFeature += f"/*path id={attributes[i]['id']}*/\n"
        strokeFeature += f"        NULL,\n"
        strokeFeature += f"    }},\n"

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

    grad_found = False
    for grad in attributes:
        if grad['name'] == 'linearGradient':
            grad_name = grad['id']
            if grad_name == fill_data:
                x1 = y1 = x2 = y2 = 0.0
                grad_found = True
                stop_values = []
                stop_values_output = f"static stopValue_t linearGrad_{new_id_value}[] = {{\n"
                num_stops = len(grad['stops'])
                offset = 0.0
                hex_color = "0x%x" % 0xff000000
                if 'stops' in grad and grad['stops']:
                    fill_path_grad.append("FILL_LINEAR_GRAD")
                    grad_len = len(grad['stops'])
                    for stop in grad['stops']:
                        if 'offset' in stop:
                            offset = convert_offset(stop['offset'])
                        if 'stop-color' in stop:
                            name = stop['stop-color']
                            stop_color = parse_color(name)
                            if stop_color :
                                hex_color = "0x%x" % stop_color
                            else:
                                print("Error: stop color value not supported", sep="---",file=sys.stderr)

                        stop_values_output += f"    {{ .offset = {offset}, .stop_color = {hex_color} }},\n"
                else:
                    # As per the SVG spec (https://www.w3.org/TR/SVG2/paths.html#PathDataMovetoCommands)
                    # If no stops are defined, then painting shall occur as if 'none' were specified as the paint style.
                    grad_len = 0
                    attributes[i]['fill'] = 'none'
                    fill_path_grad.append("STROKE")

                if num_stops > 0:
                    stop_values_output = stop_values_output[:-2]
                stop_values_output += "\n};\n\n"
                print(stop_values_output)
                min_x, max_x, min_y, max_y = get_min_max_coordinates(parsed_lines)
                if 'gradientUnits' in grad:
                    if (grad['gradientUnits'] == 'userSpaceOnUse'):
                        x1 = float(grad['x1'])
                        y1 = float(grad['y1'])
                        x2 = float(grad['x2'])
                        y2 = float(grad['y2'])
                if(('gradientUnits' not in grad) or (grad['gradientUnits'] == 'objectBoundingBox')):
                    if 'x1' in grad and 'y1' in grad and 'x2' in grad and 'y2' in grad:                        
                        x1 = min_x + (max_x - min_x) * float(grad['x1'])
                        y1 = min_y + (max_y - min_y) * float(grad['y1'])
                        x2 = min_x + (max_x - min_x) * float(grad['x2'])
                        y2 = min_y + (max_y - min_y) * float(grad['y2'])
                    else:
                        x1 = min_x
                        y1 = min_y
                        x2 = max_x
                        y2 = min_y
                linear_gradients_output = f"static linearGradient_t {imageName}_linear_gradients_{index}[] = {{\n"
                linear_gradients_output += f"    {{\n"
                linear_gradients_output += f"        /*grad id={grad_name}*/\n"
                linear_gradients_output += f"        .num_stop_points = {grad_len},\n"
                linear_gradients_output += f"        .linear_gradient = {{{x1}f, {y1}f, {x2}f, {y2}f}},\n"
                linear_gradients_output += f"        .stops = linearGrad_{new_id_value}\n"
                linear_gradients_output += f"    }},\n"
                linear_gradients_output += "\n};\n\n"
                print(linear_gradients_output)
                gradient_mapping[fill_data] = index  # Map the gradient name to its index
                index += 1

                if fill_data in gradient_mapping:
                    lingrad_to_path_output += f"    &{imageName}_linear_gradients_{gradient_mapping[fill_data]},\n"
                    radgrad_to_path_output += f"    NULL,\n"
                else:
                    lingrad_to_path_output += f"    &{imageName}_linear_gradients_{index},\n"
                    radgrad_to_path_output += f"    NULL,\n"

                gradPresent = True

        elif grad['name'] == 'radialGradient':
            grad_name = grad['id']
            if grad_name == fill_data:
                cx = cy = r = fx = fy = 0.0
                grad_found = True
                stop_values = []
                stop_values_output = f"static stopValue_t radialGrad_{new_id_value}[] = {{\n"
                num_stops = len(grad['stops'])
                offset = 0.0
                hex_color = "0x%x" % 0xff000000
                if 'stops' in grad and grad['stops']:
                    fill_path_grad.append("FILL_RADIAL_GRAD")
                    grad_len = len(grad['stops'])
                    for stop in grad['stops']:
                        if 'offset' in stop:
                            offset = convert_offset(stop['offset'])
                        if 'stop-color' in stop:
                            name = stop['stop-color']
                            stop_color = parse_color(name)
                            if stop_color :
                                hex_color = "0x%x" % stop_color
                            else:
                                print("Error: stop color value not supported", sep="---",file=sys.stderr)

                        stop_values_output += f"    {{ .offset = {offset}, .stop_color = {hex_color} }},\n"
                else:
                    grad_len = 0
                    attributes[i]['fill'] = 'none'
                    fill_path_grad.append("STROKE")                    


                if num_stops > 0:
                    stop_values_output = stop_values_output[:-2]
                stop_values_output += "\n};\n\n"
                print(stop_values_output)
                min_x, max_x, min_y, max_y = get_min_max_coordinates(parsed_lines)
                if 'gradientUnits' in grad:
                    if (grad['gradientUnits'] == 'userSpaceOnUse'):
                        #All gradient parameters are available
                        if all(key in grad for key in ('cx', 'cy', 'r')):
                            cx = float(grad['cx'])
                            cy = float(grad['cy'])
                            r = float(grad['r'])
                            fx = float(grad['cx'])
                            fy = float(grad['cy'])
                        #All gradient parameters are available
                        else:
                            cx = float(grad['cx'])
                            cy = float(grad['cy'])
                            r = float(grad['r'])
                            fx = float(grad['fx'])
                            fy = float(grad['fy'])
                if(('gradientUnits' not in grad) or (grad['gradientUnits'] == 'objectBoundingBox')):
                    #All gradient parameters are available
                    if all(key in grad for key in ('cx', 'cy', 'r', 'fx', 'fy')):
                        cx = min_x + (max_x - min_x) * convert_offset(grad['cx'])
                        cy = min_y + (max_y - min_y) * convert_offset(grad['cy'])
                        r = min(min_x + (max_x - min_x) * convert_offset(grad['r']), min_y + (max_y - min_y) * convert_offset(grad['r']))
                        fx = min_x + (max_x - min_x) * convert_offset(grad['fx'])
                        fy = min_y + (max_y - min_y) * convert_offset(grad['fy'])
                    #cx, cy and r gradient parameters are available but fx and fy is missing
                    if all(key in grad for key in ('cx', 'cy', 'r')):
                        cx = min_x + (max_x - min_x) * convert_offset(grad['cx'])
                        cy = min_y + (max_y - min_y) * convert_offset(grad['cy'])
                        r = min(min_x + (max_x - min_x) * convert_offset(grad['r']), min_y + (max_y - min_y) * convert_offset(grad['r']))
                        fx = cx
                        fy = cy
                    #cx, cy, r, fx and fy gradient parameters are missing
                    else:
                        cx = min_x + (max_x - min_x) * 0.5
                        cy = min_y + (max_y - min_y) * 0.5
                        r  = min(cx,cy)
                        fx = min_x + (max_x - min_x) * 0.5
                        fy = min_y + (max_y - min_y) * 0.5
                radial_gradients_output = f"static radialGradient_t {imageName}_radial_gradients_{index}[] = {{\n"
                radial_gradients_output += f"    {{\n"
                radial_gradients_output += f"        /*grad id={grad_name}*/\n"
                radial_gradients_output += f"        .num_stop_points = {grad_len},\n"
                radial_gradients_output += f"        .radial_gradient = {{{cx}f, {cy}f, {r}f, {fx}f, {fy}f}},\n"
                radial_gradients_output += f"        .stops = radialGrad_{new_id_value}\n"
                radial_gradients_output += f"    }},\n"
                radial_gradients_output += "\n};\n\n"
                print(radial_gradients_output)
                gradient_mapping[fill_data] = index  # Map the gradient name to its index
                index += 1

                if fill_data in gradient_mapping:
                    lingrad_to_path_output += f"    NULL,\n"
                    radgrad_to_path_output += f"    &{imageName}_radial_gradients_{gradient_mapping[fill_data]},\n"
                else:
                    lingrad_to_path_output += f"    NULL,\n"
                    radgrad_to_path_output += f"    &{imageName}_radial_gradients_{index},\n"

                gradPresent = True
    if 'transform' in attributes[i]:
        attributes[i]['path_transform'] = convert_transform(attributes[i]['path_transform'])
        transform_output += f"{attributes[i]['path_transform']},\n"
    else:
        transform_output += f"1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f,\n"

    if 'fill-rule' in attributes[i]:
        if (attributes[i]['fill-rule'] == "evenodd"):
            fill_rule_output += f"VG_LITE_FILL_EVEN_ODD,\n"
        else:
            fill_rule_output += f"VG_LITE_FILL_NON_ZERO,\n"
    else:
        fill_rule_output += f"VG_LITE_FILL_EVEN_ODD,\n"

    if not grad_found:
        lingrad_to_path_output += f"    NULL,\n"
        radgrad_to_path_output += f"    NULL,\n"
        if stroke_flag == True:
            fill_path_grad.append("STROKE")
            stroke_flag = False
        else:
            fill_path_grad.append("FILL_CONSTANT")
        index += 1

    # add the Path
    out_arg.extend([len(p_arg)])
    out_arg.extend(p_arg)
    out_cmd.extend(p_cmd)
    out_cmd.extend('E')

    i += 1
for i in range(len(paths)):
    # Fill = none, Stroke = none
    # By default, a vector path is considered VG_LITE_DRAW_FILL_PATH.
    if ('fill' in attributes[i] and attributes[i]['fill'] == 'none') and ('stroke' in attributes[i] and attributes[i]['stroke'] == 'none'):
        hybrid_path_output += f"    {{ .fillType = NO_FILL_MODE, .pathType = VG_LITE_DRAW_ZERO }},\n"
        hybrid_path_output += f"    {{ .fillType = NO_FILL_MODE, .pathType = VG_LITE_DRAW_ZERO }},\n"
    # No fill or Fill = none, Stroke in attribute
    elif (('fill' in attributes[i] and attributes[i]['fill'] == 'none') or ('fill' not in attributes[i])) and ('stroke' in attributes[i] and attributes[i]['stroke'] != 'none'):
        # Stroke with gradient feature
        if ('url' in attributes[i]['stroke']):
            hybrid_path_output += f"    {{ .fillType = {fill_path_grad[i]}, .pathType = VG_LITE_DRAW_STROKE_PATH }},\n"
            hybrid_path_output += f"    {{ .fillType = NO_FILL_MODE, .pathType = VG_LITE_DRAW_ZERO }},\n"
        # Normal stroke
        else:
            hybrid_path_output += f"    {{ .fillType = {fill_path_grad[i]}, .pathType = VG_LITE_DRAW_STROKE_PATH }},\n"
            hybrid_path_output += f"    {{ .fillType = NO_FILL_MODE, .pathType = VG_LITE_DRAW_ZERO }},\n"
    # No stroke or stroke = none, Fill in attribute
    elif ('fill' in attributes[i] and attributes[i]['fill'] != 'none') and (('stroke' in attributes[i] and attributes[i]['stroke'] == 'none') or ('stroke' not in attributes[i])):
        # Fill with gradient feature
        if ('url' in attributes[i]['fill']):
            hybrid_path_output += f"    {{ .fillType = {fill_path_grad[i]}, .pathType = VG_LITE_DRAW_FILL_PATH }},\n"
            hybrid_path_output += f"    {{ .fillType = NO_FILL_MODE, .pathType = VG_LITE_DRAW_ZERO }},\n"
        # Normal fill
        else:
            hybrid_path_output += f"    {{ .fillType = {fill_path_grad[i]}, .pathType = VG_LITE_DRAW_FILL_PATH }},\n"
            hybrid_path_output += f"    {{ .fillType = NO_FILL_MODE, .pathType = VG_LITE_DRAW_ZERO }},\n"
    # Both stroke and fill in attribute
    elif ('fill' in attributes[i] and attributes[i]['fill'] != 'none') and ('stroke' in attributes[i] and attributes[i]['stroke'] != 'none'):
        # Fill with gradient feature
        if ('url' in attributes[i]['fill']):
            hybrid_path_output += f"    {{ .fillType = {fill_path_grad[i]}, .pathType = VG_LITE_DRAW_FILL_PATH }},\n"
            hybrid_path_output += f"    {{ .fillType = STROKE, .pathType = VG_LITE_DRAW_STROKE_PATH }},\n"
        # Stroke with gradient feature
        elif ('url' in attributes[i]['stroke']):
            hybrid_path_output += f"    {{ .fillType = {fill_path_grad[i]}, .pathType = VG_LITE_DRAW_STROKE_PATH }},\n"
            hybrid_path_output += f"    {{ .fillType = FILL_CONSTANT, .pathType = VG_LITE_DRAW_FILL_PATH }},\n"
        # Normal fill and stroke
        else:
            hybrid_path_output += f"    {{ .fillType = FILL_CONSTANT, .pathType = VG_LITE_DRAW_FILL_PATH }},\n"
            hybrid_path_output += f"    {{ .fillType = STROKE, .pathType = VG_LITE_DRAW_STROKE_PATH }},\n"
    else:
        hybrid_path_output += f"    {{ .fillType = {fill_path_grad[i]}, .pathType = VG_LITE_DRAW_FILL_PATH }},\n"
        hybrid_path_output += f"    {{ .fillType = NO_FILL_MODE, .pathType = VG_LITE_DRAW_ZERO }},\n"

if lingrad_to_path_output.endswith(",\n"):
    lingrad_to_path_output = lingrad_to_path_output[:-2]

if radgrad_to_path_output.endswith(",\n"):
    radgrad_to_path_output = radgrad_to_path_output[:-2]

if transform_output.endswith(",\n"):
    transform_output = transform_output[:-2]

if fill_rule_output.endswith(",\n"):
    fill_rule_output = fill_rule_output[:-2]

hybrid_path_output += "\n};\n"
lingrad_to_path_output += "\n};\n\n"
radgrad_to_path_output += "\n};\n\n"
strokeFeature += "\n};\n\n"
transform_output += "\n};\n"
fill_rule_output += "\n};\n"

if strokePresent == True:
    print(strokeFeature)
print(hybrid_path_output)

if gradPresent == True:
    print(lingrad_to_path_output)
    print(radgrad_to_path_output)

print(fill_rule_output)

print ("static gradient_mode_t %s_gradient_info = {" % imageName)

if gradPresent == True:
    print(f"    .linearGrads = {imageName}_lingrad_to_path,")
    print(f"    .radialGrads = {imageName}_radgrad_to_path,")
else:
    print(f"    .linearGrads = NULL,")
    print(f"    .radialGrads = NULL,")
print(f"    .hybridPath = {imageName}_hybrid_path,")
print(f"    .fillRule = {imageName}_fill_rule")
print("};")
print("")
print(transform_output)


print("static image_info_t %s = {" % imageName)
print("    .image_name =\"%s\"," % imageName)
print("    .image_size = {%d, %d}," % (int(float(svg_attributes['width'])), int(float(svg_attributes['height']))))
print("    .data_format = %s," % VGLITE_DATA_TYPES[data_type])
print("    .transform = %s_transform_matrix," % imageName)
print("    .path_count = %d," % len(paths))
if strokePresent == True:
    print(f"    .stroke_info = {imageName}_stroke_info_data,")
else:
    print(f"    .stroke_info = NULL,")
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
