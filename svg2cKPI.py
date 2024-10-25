#! /usr/bin/env python3

#
# Copyright 2024 NXP
#
# SPDX-License-Identifier: MIT
#

# Read SVG into a list of path objects and list of dictionaries of attributes 
# Update: You can now also extract the svg-attributes by setting
# return_svg_attributes=True, or with the convenience function svg2paths2
import sys
import json
import re
import numpy as np
from pathlib import Path
import os
import string
from svg_colors import *
from svg_global_callback_context import *

CB = get_global_callback_context()
from svg_paint_object import PaintObject
from svg_processing import BasicRect

def check_command_line_arguments():
    """
    Validate input parameters
    """
    # If user has not provided input file show usage instructions
    if len(sys.argv) == 1:
        print(f'ERROR: Please specify input svg file.', sep="---",file=sys.stderr)
        print("USAGE: svg2cKPI.py input.svg", sep="---",file=sys.stderr)
        sys.exit(1)

    # If input file is not readable give user proper error.
    input_file=sys.argv[1]
    if os.access(input_file, os.R_OK) == False:
        print(f'ERROR: {input_file} is not accessible.', sep="---",file=sys.stderr)
        print("USAGE: svg2cKPI.py input.svg", sep="---",file=sys.stderr)
        sys.exit(1)

check_command_line_arguments()

try:
    import svg_processing
except:
    print("ERROR: Please include \"python module\" svgpathtools in PYTHONPATH", sep="---",file=sys.stderr)
    sys.exit(1)

input_file=sys.argv[1]
paths, attributes, svg_attributes, solid_colors, linear_gradients, radial_gradients, g_np = svg_processing.svg_transform(input_file)

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

imageName_actual = Path(input_file).stem
# Replace special characters in file-name with underscore
# C/C++ langulage does not support special characters in variable names.
special_to_underscore = {c: '_' for c in string.punctuation}
special_to_underscore[' '] = ''
mapping_table = str.maketrans(special_to_underscore)
imageName = imageName_actual.translate(mapping_table)


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
print("    float bounding_box[4];" )
print("    uint8_t end_path_flag;" )
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

g_active_node_unique_id = ''
counter = 0
g_grad_index = 0
grad_found = False
generated_ids = []
stroke_fill = []
used_gradients = {}  # Mapping from fill name to index
end_path_ctrl = []
def generate_id(name):
    global counter, g_active_node_unique_id
    counter += 1
    g_active_node_unique_id = f"{name}_{counter}"
    return g_active_node_unique_id

def get_current_unique_id():
    global g_active_node_unique_id
    return g_active_node_unique_id

def get_input_file_cname():
    global imageName
    # Return file name which can be used C variable name
    return imageName

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

def is_url_prefix_present(color_str):
    return color_str.startswith("url")

def get_url_id(color_str):
    return color_str.replace('url(#', '').replace(')', '')

def parse_color(color_str):
    # As per specification default color is black
    paint_color = SVG_DEFAULT_BLACK_COLOR
    isSolidColor = False

    if color_str == None:
        # As per the SVG specification (https://lists.w3.org/Archives/Public/www-archive/2005May/att-0005/SVGT12_Main.pdf),
        # section 11.3 on Fill Properties, If the fill property is not specified for an element, 
        # its initial or default value is 'black'.
        return SVG_DEFAULT_BLACK_COLOR, isSolidColor

    if color_str.startswith('#'):
        if len(color_str) == 4:  # Shorthand hex color like #F60
            color_str = '#' + ''.join([c*2 for c in color_str[1:]])
        m = re.search(r'#([0-9a-fA-F]{6})', color_str)
        if m:
            color = m.group(1)
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            paint_color = f'0xff%02x%02x%02x' % ( r, g, b)
    elif color_str.startswith('rgb'):
        m = re.match(r'rgb\(\s*([\d\.]+)%?\s*,\s*([\d\.]+)%?\s*,\s*([\d\.]+)%?\s*\)', color_str)
        if m:
            r, g, b = m.groups()
            # Convert percentages to 0-255 scale if necessary
            if '%' in color_str:
                r, g, b = [int(float(val) * 2.55) for val in (r, g, b)]
            else:
                r, g, b = map(int, (r, g, b))
            paint_color = f'0xff%02x%02x%02x' % ( r, g, b)
    elif color_str in SVG_COLOR_TABLE:
        paint_color = SVG_COLOR_TABLE[color_str]
    elif is_url_prefix_present(color_str):
            fill_data = get_url_id(color_str)
            paint_color, isSolidColor = getSolidColor(fill_data)
    elif color_str == 'currentColor':
        # We need to traverse parent node to find color
        element = g_active_node
        paint_color_str  = g_np._get_parent_attribute(element, 'color')
        paint_color, dummy_var = parse_color(paint_color_str)
    else:
        print(f"Error: Fill value \"{color_str}\" not supported", sep="---",file=sys.stderr)

    return paint_color, isSolidColor

def convert_transform(array):
    return ', '.join(', '.join(f'{val:.1f}f' for val in row) for row in array)

def bgr_color_convert(colorCode):
    opa = (colorCode & 0xFF000000) >> 24
    r = (colorCode & 0x00FF0000) >> 16
    g = (colorCode & 0x0000FF00) >> 8
    b = (colorCode & 0x000000FF)
    bgr_format_color = (opa << 24) | (b << 16) | (g << 8) | r
    return bgr_format_color

def getSolidColor(name):
    isSolidColor = False
    bgr_color = SVG_DEFAULT_BLACK_COLOR
    if name in solid_colors:
        bgr_color, isSolidColor = parse_color(solid_colors[name])
    return bgr_color, isSolidColor

def check_for_z_cmd(path_data):
    if 'z' in path_data or 'Z' in path_data:
        return 0  # Indicates 'z' command was found
    else:
        return 1  # Indicates 'z' command was not found

def _get_stop_color(stop):
    hex_color = "0x%x" % 0xff000000
    offset = 0.0
    if 'offset' in stop:
        offset = convert_offset(stop['offset'])
    if 'stop-color' in stop:
        name = stop['stop-color']
        stop_color, isSolidColor2 = parse_color(name)
        if stop_color :
            hex_color = stop_color
        else:
            print("Error: stop color value not supported", sep="---",file=sys.stderr)
    return hex_color, offset

def get_used_gradient(key):
    global g_grad_index
    return used_gradients[key]

def make_paint_object(svg_color_data):
    # Note: svg_color_data
    # svg_color_data can use url prefix (for gradient and solid colors)
    # svg_color_data can be actual color value as well.
    global g_grad_index

    po = PaintObject()
    if is_url_prefix_present(svg_color_data):
        color_str = get_url_id(svg_color_data)
        # This can be gradient of solid color
        if color_str in linear_gradients:
            grad = linear_gradients[color_str]
            po.lg.parse(grad, parsed_lines)
            po.paint_mode = po.lg.get_fill_mode()
            if po.lg.is_valid():
                po.lg.set_name(grad["id"])
                po.lg.set_index(g_grad_index)
                used_gradients[svg_color_data] = g_grad_index
                g_grad_index += 1

        elif color_str in radial_gradients:
            grad = radial_gradients[color_str]
            po.rg.parse(grad, parsed_lines)
            po.paint_mode = po.rg.get_fill_mode()
            if po.rg.is_valid():
                po.rg.set_name(grad["id"])
                po.rg.set_index(g_grad_index)
                used_gradients[svg_color_data] = g_grad_index
                g_grad_index += 1
    else:
        # fill_color is actual ARGB color string
        fill_color, isSolidColor2 = parse_color(svg_color_data)
        po.solid.set_color(fill_color)

    return po

def process_painting(color_data):
    global lingrad_to_path_output, radgrad_to_path_output
    global grad_found

    po: PaintObject = make_paint_object(color_data)

    if po.lg.is_valid():
        print(po.lg.to_string(get_input_file_cname(), get_current_unique_id()))
        lingrad_to_path_output += f"    &{imageName}_linear_gradients_{po.lg.grad_index},\n"
        radgrad_to_path_output += f"    NULL,\n"
        grad_found = True
    elif po.rg.is_valid():
        print(po.rg.to_string(get_input_file_cname(), get_current_unique_id()))
        lingrad_to_path_output += f"    NULL,\n"
        radgrad_to_path_output += f"    &{imageName}_radial_gradients_{po.rg.grad_index},\n"
        grad_found = True

    return po

hybrid_path_output = f"hybridPath_t {imageName}_hybrid_path[] = {{\n"
strokeFeature = f"static stroke_info_t {imageName}_stroke_info_data[] = {{\n"
lingrad_to_path_output = f"static linearGradient_t *{imageName}_lingrad_to_path[] = {{\n"
radgrad_to_path_output = f"static radialGradient_t *{imageName}_radgrad_to_path[] = {{\n"
transform_output = f"static float {imageName}_transform_matrix[] = {{\n"
bounding_boxes = []
fill_rule_output = f"static vg_lite_fill_t {imageName}_fill_rule[] = {{\n"
g_active_node = None
INVALID_PAINT_OBJECT = PaintObject()

update_global_callback_context(parse_color)

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

    min_x, max_x, min_y, max_y = get_min_max_coordinates(parsed_lines)
    bounding_boxes.append(BasicRect(min_x, min_y, max_x, max_y))

    # In vg_lite_path_t, the add_end is set to zero by default, leading to an extra
    # path being rendered between the start and end points. Setting it to '1'
    # to avoid extra path rendering
    if 'd' in attributes[i]:
        end_path_ctrl.append(check_for_z_cmd(attributes[i]['d']))
    elif 'points' in attributes[i]:
        end_path_ctrl.append(check_for_z_cmd(attributes[i]['points']))
    else:
        end_path_ctrl.append(0)
    
    p_cmd,p_arg = path_split(p_cmd_arg)
    if p_cmd is None and p_arg is None:
        continue
    g_cmd.extend(p_cmd)
    g_arg.extend(p_arg)
    out_cmd = []
    out_arg = []
    fall_back_feature = False

    # Present SVG element for which we are creating drawing commands
    g_active_node = attributes[i]['minidom-node']

    fill_str = attributes[i]['fill']
    stroke_str = attributes[i]['stroke']
    fill_color, isSolidColor2 = parse_color(fill_str)
    color_data.append(fill_color)

    if stroke_str != None:
        out_cmd.extend('S')
        strokePresent = True
        stroke_flag = True
        strokeFeature += f"    {{\n"
        if 'id' in attributes[i]:
            strokeFeature += f"/*{attributes[i]['name']} id={attributes[i]['id']}*/\n"
        stroke_dasharry_str = attributes[i]['stroke-dasharray']
        if stroke_dasharry_str != None:
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

        def _map_with_dictionary(key, default_value, alist, const_map):
            vglite_value = default_value
            if key in alist and alist[key] != None:
                svg_value = alist[key]
                vglite_value = const_map[svg_value]
            return vglite_value

        def _map_with_constant(key, default_value, alist):
            vglite_value = default_value
            if key in alist and alist[key] != None:
                vglite_value = alist[key]
            return vglite_value

        _MAP_STROKE_LINECAP= {'butt':'VG_LITE_CAP_BUTT', 'round':'VG_LITE_CAP_ROUND', 'square':'VG_LITE_CAP_SQUARE'}
        _MAP_STROKE_LINEJOIN= {'miter':'VG_LITE_JOIN_MITER', 'round':'VG_LITE_JOIN_ROUND', 'bevel':'VG_LITE_JOIN_BEVEL'}

        # stroke-dashoffset defaults to zero
        value = _map_with_constant('stroke-dashoffset', '0', attributes[i])
        strokeFeature += f"        .dashPhase = {value},\n"

        # stroke-width defaults to one
        value = _map_with_constant('stroke-width', '1', attributes[i])
        strokeFeature += f"        .strokeWidth = {value},\n"

        # As per the SVG spec (https://lists.w3.org/Archives/Public/www-archive/2005May/att-0005/SVGT12_Main.pdf)
        # section 11.4 on Stroke Properties, If the miterlimit property is not specified for an element,
        # its initial or default value is '4'.
        value = _map_with_constant('stroke-miterlimit', '4', attributes[i])
        strokeFeature += f"        .miterlimit = {value},\n"

        stroke_color, isSolidColor2 = parse_color(stroke_str)
        strokeFeature += f"        .strokeColor = {stroke_color},\n"


        # Default stroke-linecap is VG_LITE_CAP_BUTT
        value = _map_with_dictionary('stroke-linecap', 'VG_LITE_CAP_BUTT', attributes[i], _MAP_STROKE_LINECAP)
        strokeFeature += f"        .linecap = {value},\n"

        # Default stroke-linejoin is VG_LITE_JOIN_MITER
        value = _map_with_dictionary('stroke-linejoin', 'VG_LITE_JOIN_MITER', attributes[i], _MAP_STROKE_LINEJOIN)
        strokeFeature += f"        .linejoin = {value}\n"
        strokeFeature += f"    }},\n"
    else:
        strokeFeature += f"    {{\n"
        if 'id' in attributes[i]:
            strokeFeature += f"/*path id={attributes[i]['id']}*/\n"
        strokeFeature += f"        NULL,\n"
        strokeFeature += f"    }},\n"

    if 'style' in attributes[i] and attributes[i]['style'] != None:
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
        color_data.append("0x%x" % ((opa << 24) | (b << 16) | (g << 8) | r))

    fill_po = INVALID_PAINT_OBJECT
    fillType_str = 'NO_FILL_MODE'
    pathType_str = 'VG_LITE_DRAW_ZERO'
    if fill_str != None:
        fill_po: PaintObject = process_painting(fill_str)
        if fill_po.paint_mode == None:
            fill_po.paint_mode = 'FILL_CONSTANT'
        fillType_str = fill_po.paint_mode
        pathType_str = 'VG_LITE_DRAW_FILL_PATH'
    hybrid_path_output += f"    {{ .fillType = {fillType_str}, .pathType = {pathType_str} }},\n"

    stroke_po = INVALID_PAINT_OBJECT
    fillType_str = 'NO_FILL_MODE'
    pathType_str = 'VG_LITE_DRAW_ZERO'
    if stroke_str != None:
        stroke_po: PaintObject = process_painting(stroke_str)
        if stroke_po.paint_mode == None:
            stroke_po.paint_mode = 'STROKE'
        fillType_str = stroke_po.paint_mode
        pathType_str = 'VG_LITE_DRAW_STROKE_PATH';
    hybrid_path_output += f"    {{ .fillType = {fillType_str}, .pathType = {pathType_str} }},\n"

    # When fill and stroke both don't utilize gradient
    if fill_po.has_valid_gradient() == False and stroke_po.has_valid_gradient() == False:
         lingrad_to_path_output += f"    NULL,\n"
         radgrad_to_path_output += f"    NULL,\n"

    if 'transform' in attributes[i]:
        attributes[i]['path_transform'] = convert_transform(attributes[i]['path_transform'])
        transform_output += f"{attributes[i]['path_transform']},\n"
    else:
        transform_output += f"1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f,\n"

    if 'fill-rule' in attributes[i] and attributes[i]['fill-rule'] != None:
        if (attributes[i]['fill-rule'] == "evenodd"):
            fill_rule_output += f"VG_LITE_FILL_EVEN_ODD,\n"
        else:
            fill_rule_output += f"VG_LITE_FILL_NON_ZERO,\n"
    else:
        fill_rule_output += f"VG_LITE_FILL_EVEN_ODD,\n"


    # add the Path
    out_arg.extend([len(p_arg)])
    out_arg.extend(p_arg)
    out_cmd.extend(p_cmd)
    out_cmd.extend('E')

    i += 1

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

if len(used_gradients) > 0:
    print(lingrad_to_path_output)
    print(radgrad_to_path_output)

print(fill_rule_output)

print ("static gradient_mode_t %s_gradient_info = {" % imageName)

if len(used_gradients) > 0:
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
print("    .image_name =\"%s\"," % imageName_actual)
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
        print("        {.path_length = sizeof(%s), .path_data=(%s*)%s, .end_path_flag=%d, .bounding_box = {%0.2f, %0.2f, %0.2f, %0.2f} }" %
              (path_name, data_type, path_name, end_path_ctrl[i],
               bounding_boxes[i].x,
               bounding_boxes[i].y,
               bounding_boxes[i].width,
               bounding_boxes[i].height))
    else:
        print("        {.path_length = sizeof(%s), .path_data=(%s*)%s, .end_path_flag=%d, .bounding_box = {%0.2f, %0.2f, %0.2f, %0.2f} }," %
              (path_name, data_type, path_name, end_path_ctrl[i],
               bounding_boxes[i].x,
               bounding_boxes[i].y,
               bounding_boxes[i].width,
               bounding_boxes[i].height))
print("    },")
print("};")
print("")


print ("uint32_t %s_color_data[] = {" % imageName)
line = "    "
i = 0
for color in color_data:
    if (i < len(color_data)-1):
        line += "%s, " % color
    else:
        line += "%s" % color
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
