#
# Copyright 2024 NXP
#
# SPDX-License-Identifier: MIT
#

#
# This application transforms SVG file into path drawing instructions
# which can be interpreted by VGLite driver
#
# Supported features
#   * shape support
#     * path
#     * rectangle
#     * circle
#     * ellipse
#     * polygon
#     * polyline
#     * line
#   * gradients
#     * linear gradient
#     * radial gradient
# 

# External dependencies
from __future__ import division, absolute_import, print_function
from xml.dom.minidom import parse
import sys
import numpy as np
import os
from io import StringIO
import re
import string
try:
    from os import PathLike as FilePathLike
except ImportError:
    FilePathLike = str

# Internal dependencies
from svgpathtools.parser import parse_path

from io import StringIO
from svgpathtools.svg_to_paths import *
from svg_path_transform import *
from svg_colors import *

g_counter = 0

# SVG elements that are responsible for drawing in output
# TODO: Implement 'text' support in next development phase
_SVG_DRAWABLE_LIST = {'rect', 'circle', 'ellipse', 'line', 'circle','path','polygon', 'polyline'}
# SVG elements which are container elements
_SVG_CONTAINER_LIST = {'svg', 'g'}
# SVG elements which we should discard
_SVG_DISCARD_LIST = {'#text','#comment', 'defs', 'image', 'text'}

# Following attributes are necessary for painting shape elements
_ATTRIB_NECESSARY_FOR_DRAWING = {'fill', 'fill-rule', 'stroke', 'stroke-width',
        'stroke-linecap', 'stroke-dasharray', 'stroke-linejoin',
        'stop-color', 'solid-color'}

# Following attributes support 'currentColor' value
_ATTRIB_SUPPORTING_CURRENT_COLOR = {'fill-rule', 'stroke', 'fill','solid-color','stop-color'}

# Mapping of arguments for each VG draw commands.
_CMD_PARAM_TABLE = {
    'M': 2, 'm': 2,
    'L': 2, 'l': 2,
    'T': 2, 't': 2,
    'H': 1, 'h': 1,
    'V': 1, 'v': 1,
    'C': 6, 'c': 6,
    'S': 4, 's': 4,
    'Q': 4, 'q': 4,
    'Z': 0, 'z': 0
}

# Enable code to configure debugging of node-traversal
_DEBUG=0
if _DEBUG==1:
    g_depth = 0
    g_spaces="          "


class BasicRect:
    def __init__(self, x=-1, y=-1, width=-1, height=-1):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

class SVGRoot(BasicRect):
    pass

class SVGViewBox(BasicRect):
    """
    A class that allow extraction of viewbox from SVG element
    """
    def parse(self, svg_node):
        viewbox_value = svg_node.getAttribute("viewBox")
        viewbox_value = viewbox_value.split()
        self.x = float(viewbox_value[0])
        self.y = float(viewbox_value[1])
        self.width = float(viewbox_value[2])
        self.height = float(viewbox_value[3])

    def transform(self, alist):
        # Transform list describes each individual transforms on path/shape
        transform_list = alist['transform']
        # parse_transform requires a single string of all successive transforms.
        attributes = parse_transform(' '.join(transform_list))
        if self.width > 0 and self.height > 0:
            attributes[0][2] = attributes[0][2] - self.x
            attributes[1][2] = attributes[1][2] - self.y
        return attributes

class NodeProcessor:
    """
    A class to allow traversing SVG tree in some specific order

    """

    def update_svg_dimension(self, svg_node, vb):

        keys = list(svg_node.attributes.keys())
        values = [val.value for val in list(svg_node.attributes.values())]
        alist = dict(list(zip(keys,values)))

        x_str = alist.get("x", None)
        y_str = alist.get("y", None)
        width_str = alist.get("width", None)
        height_str = alist.get("height", None)

        self.svg.x = int(x_str) if x_str is not None else 0
        self.svg.y = int(y_str) if y_str is not None else 0

        # if % is specified in width or heigh of SVG element then 
        # use corrosponding viewbox dimension
        self.svg.width = vb.width
        if (width_str is not None) and (not width_str.endswith('%')):
            self.svg.width = float(width_str)
        else:
            self.svg.width = vb.width

        if (height_str is not None) and (not height_str.endswith('%')):
                self.svg.height = float(height_str)
        else:
            self.svg.height = vb.height
        # Update overall width, height in svg attribute list        
        alist["width"] = self.svg.width
        alist["height"] = self.svg.height
        self.svg_attributes = alist

    def __init__(self, file_name):
        """
        Iterator to traverse SVG tree in depth first order
        """
        self.svg_id = 0
        self.file_name = file_name
        self.doc = parse(file_name)

        self.svg_node = self.doc.getElementsByTagName('svg')[0]
        # Get ViewBox of SVG element to find display area for vector drawing
        self.vb = SVGViewBox()
        self.svg = SVGRoot()
        self.vb.parse(self.svg_node)
        self.update_svg_dimension(self.svg_node, self.vb)

        # Arrays that will contains resultant things
        self.d_strings = []
        self.shapeTrans = []
        self.attribute_dictionary_list = []

        # Finally processed paths
        self.paths = []

    def line2pathd(self, alist):
        x1 = alist.get('x1', 0)
        y1 = alist.get('y1', 0)
        x2 = alist.get('x2', 0)
        y2 = alist.get('y2', 0)
        return f'M {x1} {y1} L {x2} {y2}'

    def is_url_prefix_present(self, color_str):
        return color_str.startswith("url")

    def get_url_id(self, color_str):
        return color_str.replace('url(#', '').replace(')', '')

    def _process_node(self, e):
        # Embed unique svg_id in attribute list
        e.setAttribute("svg_id",f"unique_id{self.svg_id}")
        self.svg_id = self.svg_id +1

        strings = ""
        #print(f'{e.tagName}\n')
        
        # Get attribute list
        #alist = [self._make_attrib_dictionary(e)]
        alist = self._make_attrib_dictionary(e)
        if e.tagName == "path":
            strings = [alist['d']]
            strings = ' '.join(strings)
            strings = strings.replace(',',' ')
            # Add space between values and command
            strings = re.sub(r'([a-zA-Z])([0-9\-])', r'\1 \2', strings)
            strings = re.sub(r'([0-9])([a-zA-Z])', r'\1 \2', strings)
            # Find commands and numerical values from the string
            commands = re.findall(r'[a-zA-Z]|-?\d*\.?\d+|\.\d+', strings)
            strings = self.insert_missing_path_commands(commands)

        elif e.tagName in ["polyline","polygon"]:
            if e.tagName == "polygon":
                is_polygon = True 
            else:
                is_polygon = False 
            strings = polygon2pathd(alist, is_polygon)

        elif e.tagName in ["circle","ellipse"]:
            if e.tagName == "ellipse":
                if (alist['rx'] == "0") or (alist['ry'] == "0"):
                    if 'stroke' in alist:
                        alist['stroke'] = 'none'
            strings = ellipse2pathd(alist)

        elif e.tagName in ["rect"]:
            if (alist['width'] == "0") or (alist['height'] == "0"):
                if 'stroke' in alist:
                    alist['stroke'] = 'none'
            strings = rect2pathd(alist)
        elif e.tagName in ['line']:
            strings = self.line2pathd(alist)

        if 'transform' in alist:
            attributes = self.vb.transform(alist)
            alist['path_transform'] = attributes

        if alist['fill'] == 'none':
            alist['fill'] = None

        if alist['stroke-dasharray'] == 'none':
            alist['stroke-dasharray'] = None

        fill_str = alist['fill']
        if fill_str != None and self.is_url_prefix_present(fill_str):
            # When fill is referring to colur using URL,
            # paint method(linear/radial/solid-fill) must be valid.
            color_name = color_str = self.get_url_id(fill_str)
            color_is_valid = False
            if color_name in self.linear_gradients:
                color_is_valid += 1
            if color_name in self.radial_gradients:
                color_is_valid += 1
            if color_name in self.solor_colors:
                color_is_valid += 1
            if color_is_valid == False:
                # Discard this fill value since no valid paiting color/method exists
                alist['fill'] = None

        if alist['stroke'] == 'none':
            alist['stroke'] = None

        if alist['stroke'] == None and alist['fill'] == None:
            # e.g. refer to shapes-intro-01-t.svg with zero-width/height cases (e.g. Zero-width-stroked-rect)
            # Since there is no drawing operation, we can safely discard this path
            # it is not going to result in any rendering on screen.
            return

        if len(strings) > 0:
            self.d_strings.append(strings)

        if len(alist) > 0:
            self.attribute_dictionary_list.append(alist)

    def _depth_first(self, root):
        global g_depth
        """
        Iterate SVG elements in depth-first order
        """
        if _DEBUG==1:
            g_depth += 1
        for node in root.childNodes:
            element_name=node.nodeName
            if element_name in _SVG_DISCARD_LIST:
                continue
            if _DEBUG==1:
                print(f'{g_spaces[:g_depth*2]} {element_name} {node.getAttribute("id")}')
            if element_name in _SVG_CONTAINER_LIST:
                self._depth_first(node)
            # Is supported node
            elif element_name in _SVG_DRAWABLE_LIST:
                self._process_node(node)
        if _DEBUG==1:
            g_depth -= 1

    def depth_first(self):
        # Get ViewBox of SVG element to find display area for vector drawing
        #vb_x, vb_y = _get_viewbox(doc.getElementsByTagName('svg')[0])
        if _DEBUG==1:
            print(f'Processing {self.file_name}')
        self._depth_first(self.svg_node)
        self.paths = [parse_path(d) for d in self.d_strings]

    def _get_parent_attribute(self, element, attribute):
        """
        Iterate from given element towards root element in SVG tree
        Check for requests 'attribute' in parents.
        If attribute is found, it returns its value
        If attribute value is 'inherit' it continue searching in parents
        """
        while element is not None and element.nodeType == element.ELEMENT_NODE:
            if element.hasAttribute(attribute):
                attr_value = element.getAttribute(attribute)
                if attr_value != 'inherit':
                    return attr_value
            element = element.parentNode
        return None
        
    def _get_transform_list(self, element):
        # Lookup transform of current and parents nodes.
        # Then create a sequence of transforms that needs to be applied
        path_transforms = []
        parent = element
        while parent is not None and parent.nodeType == element.ELEMENT_NODE:
            if parent.hasAttribute("transform"):
                path_transforms.append(parent.getAttribute("transform"))
            parent=parent.parentNode
        
        if len(path_transforms) > 1:
            path_transforms.reverse()

        # Return a list of transform
        return path_transforms

    def insert_missing_path_commands(self, commands):
        path_commands = []
        last_command = None

        i = 0
        while i < len(commands):
            cmd = commands[i]
            if cmd.isalpha():
                last_command = cmd
                i += 1
            else:
                cmd = last_command
            
            num_params:int = _CMD_PARAM_TABLE[str(cmd)]
            
            if num_params >= 0:
                if num_params == 2:
                    path_commands.append(f'{cmd} {float(commands[i])} {float(commands[i+1])}')
                elif num_params == 1:
                    path_commands.append(f'{cmd} {float(commands[i])}')
                elif num_params == 6:
                    path_commands.append(f'{cmd} {float(commands[i])} {float(commands[i+1])} {float(commands[i+2])} {float(commands[i+3])} {float(commands[i+4])} {float(commands[i+5])}')
                elif num_params == 4:
                    path_commands.append(f'{cmd} {float(commands[i])} {float(commands[i+1])} {float(commands[i+2])} {float(commands[i+3])}')
                elif num_params == 0:
                    path_commands.append(f'Z')
                i += num_params
            else:
                raise ValueError(f"Unexpected token: {cmd}")

            if cmd == 'm':
                last_command = 'l'
            elif cmd == 'M':
                last_command = 'L'

        return ' '.join(path_commands)

    def _parse_style(self, alist, style_str):
        if style_str == None:
            return

        # style properties examples
        #    style="fill:#cdcccb;fill-opacity:1;fill-rule:evenodd;stroke:none"
        #    style="fill: rgb(55, 55, 55); fill-opacity: 1; fill-rule: evenodd; stroke: none;"
        #    style="fill: rgb(61, 109, 190); fill-opacity: 1; fill-rule: evenodd; stroke: none;"
        # Properties are seperated by ';'
        properties=style_str.split(';')
        for p in properties:
            # key,value pair is seperated by ':'
            kv = p.split(':')
            if len(kv) != 2:
                continue
            if alist.get(kv[0], None) != None:
                # Warn user when SVG specifies style and element attribute both for same property
                print(f"WARNING: style property {kv[0]}={kv[1]} overrides element attribute {kv[0]}={alist[kv[0]]}",file=sys.stderr)
            # Add parsed style properties in attribute list
            alist[kv[0]] = kv[1].strip()

    def _make_attrib_dictionary(self, element):
        """
        Parse Element attributes and prepare a dictionary
        """
        keys = list(element.attributes.keys())
        values = [val.value for val in list(element.attributes.values())]

        # Append SVG element name into attribute name
        keys.append("name");
        values.append(element.tagName);

        # Special key 'node' to access SVG node object
        keys.append("minidom-node")
        values.append(element)

        tx_list = self._get_transform_list(element)
        if tx_list:
            # If transform is available add it into attribute list
            keys.append("transform")
            values.append(tx_list)
            keys.append("path_transform")
            values.append(0)

        attr_dict = dict(list(zip(keys,values)))

        # When SVG does not specify stop-color and solid-color
        # set default as black color.
        for key in ['solid-color' , 'stop-color']:
            if key not in attr_dict:
                # Set default as black color
                value = SVG_DEFAULT_BLACK_COLOR
                attr_dict[key] = value
                element.setAttribute(key,SVG_DEFAULT_BLACK_COLOR)

        # If current element don't have required property, or it contains 'inherit'
        # traverse parent node and get required properties
        for key in _ATTRIB_NECESSARY_FOR_DRAWING:
            if value := self._get_parent_attribute(element, key):
                if key in _ATTRIB_SUPPORTING_CURRENT_COLOR and (element.hasAttribute(key) and attr_dict[key] == 'currentColor'):
                    value = self._get_parent_attribute(element, 'color')
            attr_dict[key] = value

        # SVGT12 test suite uses xml:id, replicate it by id in dictionary
        if ('xml:id' in attr_dict) and ('id' not in attr_dict):
            attr_dict['id'] = attr_dict['xml:id']

        if 'style' in attr_dict:
            # Parse style attribute if 'fill' and 'stroke' are absent
            self._parse_style(attr_dict, attr_dict['style'])

        return attr_dict

    def _get_element_id(self, alist):
        global g_counter
        if "id" in alist:
            return alist["id"]
        elif "xml:id" in alist:
            return alist["xml:id"]
        else:
            alist["id"] = f"svg_id{g_counter}"
            return alist["id"]

    def _make_gradient_list(self, parent_node):
        glist=[]
        keys = []
        values = []
        for e in self.svg_node.getElementsByTagName(parent_node):
            grad_dict = self._make_attrib_dictionary(e)
            stops = [self._make_attrib_dictionary(stop)
                     for stop in e.getElementsByTagName('stop')]

            # From SVGT12 Specification
            # 11.2 Specifying paint describes currentColor interpretation
            if 'color' in grad_dict:
                for s in stops:
                    if s['stop-color'] == 'currentColor':
                        s['stop-color'] = grad_dict['color']

            grad_dict['stops'] = stops
            if "gradientUnits" not in grad_dict:
                # Ensure we have dummy strings to simplify checks in main svg_paint_object
                grad_dict['gradientUnits'] = None
            # Gradients are valid if it has stop points
            if len(stops) > 0:
                key = self._get_element_id(grad_dict)
                keys.append(key)
                values.append(grad_dict)
        if parent_node == 'linearGradient':
            self.linear_gradients = dict(list(zip(keys,values)))
        elif parent_node == 'radialGradient':
            self.radial_gradients = dict(list(zip(keys,values)))

    def _make_solidColor_dictionary(self):
        solid_color = dict()
        keys = []
        values = []
        # NOTE: This tool does not support animation feature.
        # So, only following is supported
        #  <solidColor solid-color="constant" solid-opacity="0.7"/>
        #  VGLite h/w does not support opacity
        for e in self.svg_node.getElementsByTagName('solidColor'):
            alist = self._make_attrib_dictionary(e)
            key = self._get_element_id(alist)
            value = alist["solid-color"]
            keys.append(key)
            values.append(value)
        self.solor_colors = dict(list(zip(keys,values)))

def svg_transform(svg_file_location):
    np = NodeProcessor(svg_file_location)
    np._make_gradient_list('linearGradient')
    np._make_gradient_list('radialGradient')
    np._make_solidColor_dictionary()
    np.depth_first()

    return np.paths, np.attribute_dictionary_list, np.svg_attributes, np.solor_colors, np.linear_gradients, np.radial_gradients, np

