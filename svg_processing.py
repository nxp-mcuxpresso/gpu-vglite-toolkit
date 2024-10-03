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
# Known Limitations
#  * Opacitity is not supported
#  * font support will be available by Dec 2024
#  * Line with less than 0.5 pixels don't render
#  * TODO: there are additional limitations discovered during SVGT12 testing

# External dependencies
from __future__ import division, absolute_import, print_function
from xml.dom.minidom import parse
import sys
import numpy as np
import os
from io import StringIO
import re
try:
    from os import PathLike as FilePathLike
except ImportError:
    FilePathLike = str

# Internal dependencies
from .parser import parse_path

from io import StringIO
from svg_to_paths import *

# SVG elements that are responsible for drawing in output
_SVG_DRAWABLE_LIST = {'rect', 'circle', 'ellipse', 'line', 'circle','path','polygon','text'}
# SVG elements which are container elements
_SVG_CONTAINER_LIST = {'svg', 'g'}
# SVG elements which we should discard
_SVG_DISCARD_LIST = {'#text','#comment'}

# Following attributes are necessary for painting shape elements
_ATTRIB_NECESSARY_FOR_DRAWING = {'fill', 'fill-rule', 'stroke', 'stroke-width',
        'stroke-linecap', 'stroke-dasharray', 'stroke-linejoin',
        'stop-color', 'solid-color'}

# Following attributes support 'currentColor' value
_ATTRIB_SUPPORTING_CURRENT_COLOR = {'fill-rule', 'stroke', 'fill','solid-color'}

# Mapping of arguments for each VG draw commands.
_CMD_PARAM_TABLE: dict[str, int] = {
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

class BasicRect:
    def __init__(self):
        self.x = -1
        self.y = -1
        self.width = -1
        self.height = -1

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

    def transform(self, e):
        attribute = e.get('transform',0)
        # Get 1st transform values if available
        attribute = attribute[0]
        attributes = parse_transform(attribute)
        #if len(viewbox_value) == 4:
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
            self.svg.width = int(width_str[:-1])
        else:
            self.svg.width = vb.width

        if (height_str is not None) and (not height_str.endswith('%')):
                self.svg.height = int(height_str[:-1])
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

    def _process_node(self, e):
        # Embed unique svg_id in attribute list
        e.setAttribute("svg_id",f"unique_id{self.svg_id}")
        self.svg_id = self.svg_id +1

        strings = ""
        print(f'{e.tagName}\n')
        
        # Get attribute list
        #alist = [self._make_attrib_dictionary(e)]
        alist = self._make_attrib_dictionary(e)
        if e.tagName == "path":
            strings = [e['d']]
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

        if 'transform' in alist:
            attributes = self.vb.transform(alist)
            alist['path_transform'] = attributes

        if len(strings) > 0:
            self.d_strings.append(strings)

        if len(alist) > 0:
            self.attribute_dictionary_list.append(alist)

    def _depth_first(self, root):
        """
        Iterate SVG elements in depth-first order
        """
        for node in root.childNodes:
            element_name=node.nodeName
            if element_name in _SVG_DISCARD_LIST:
                continue
            #print("%s" %(element_name))
            if element_name in _SVG_CONTAINER_LIST:
                # self._process_node(node)
                self._depth_first(node)
            # Is supported node
            if element_name in _SVG_DRAWABLE_LIST:
                self._process_node(node)

    def depth_first(self):
        # Get ViewBox of SVG element to find display area for vector drawing
        #vb_x, vb_y = _get_viewbox(doc.getElementsByTagName('svg')[0])
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
            path_transforms = ' '.join(path_transforms)

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
            
            num_params = 2 #_CMD_PARAM_TABLE.get(cmd,0)
            i += num_params
            
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
            else:
                raise ValueError(f"Unexpected token: {cmd}")

            if cmd == 'm':
                last_command = 'l'
            elif cmd == 'M':
                last_command = 'L'

        return ' '.join(path_commands)

    def _make_attrib_dictionary(self, element):
        """
        Parse Element attributes and prepare a dictionary
        """
        keys = list(element.attributes.keys())
        values = [val.value for val in list(element.attributes.values())]

        # Append SVG element name into attribute name
        keys.append("name");
        values.append(element.tagName);

        if element.tagName == 'svg':
            # SVG tag has viewbox attribute
            keys.append("width")
            values.append(self.svg.width)

            keys.append("height")
            values.append(self.svg.height)

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
                value = '#000000'

        # If current element don't have required property, or it contains 'inherit'
        # traverse parent node and get required properties
        for key in _ATTRIB_NECESSARY_FOR_DRAWING:
            if value := self._get_parent_attribute(element, key):
                if key in _ATTRIB_SUPPORTING_CURRENT_COLOR and (element.hasAttribute(key) and attr_dict[key] == 'currentColor'):
                    value = self._get_parent_attribute(element, 'color')
            attr_dict[key] = value

        return attr_dict

def svg_transform(svg_file_location):
    # strings are interpreted as file location everything else is treated as
    # file-like object and passed to the xml parser directly
    #from_filepath = isinstance(svg_file_location, str) or isinstance(svg_file_location, FilePathLike)
    #svg_file_location = os.path.abspath(svg_file_location) if from_filepath else svg_file_location

    np = NodeProcessor(svg_file_location)
    np.depth_first()

    return np.paths, np.attribute_dictionary_list, np.svg_attributes

