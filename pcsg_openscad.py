#! /usr/bin/python3.3
from __future__ import absolute_import, division, print_function, unicode_literals
import argparse
import sys
import json
import os
import subprocess

'''
Operation:
Evaluate and regenerate JSON tree by order...
required elements, parameters, parameter operations, elements, element operations
'''

class OpenSCADEngine:
    def __init__(self):
        self.level = 0
        self.output = ""
        self.operations = ["union", "difference", "intersection", "hull", "translate", "rotate"]
        self.elements = ["cube", "cylinder", "sphere", "cone"]

    def parseJSON(self, data):
        if data['category']:
            if data['category'] == "operation":
                if data['name'] in self.operations:
                    scadOperation = self.parseOperation(data)
                    self.output += " " * self.level * args.indent + scadOperation
                    for types in data['elements']:
                        self.level += 1
                        self.parseJSON(types)
                        self.level -= 1
                    self.output += " " * self.level * args.indent + "}\n"
                else:
                    a = "echo("+data['name']+");"
                    self.output += a
                    self.parseJSON(data['construction'])
            if data['category'] == "element":
                props = self.parseProperties(data)
                self.output += " " * self.level * args.indent + props
                if data['name'] in self.elements:
                    self.output += self.parseElement(data)
                else:
                    print("Found top level element " + data['name'])
                    print("Unrecognized by the parser... traversing to construction")
                    self.parseJSON(data['construction'])

    def parseOperation(self, data):
        """Parse an operation and generate an OpenSCAD equivalent"""
        tempStr = self.parseProperties(data)
        if data['name'] == "translate":
            tempStr += "translate(" + str(data['location']) + "){"
        if data['name'] == "rotate":
            tempStr += self.processRotation(data) + "{"
        else:
            tempStr = data['name'] + "(){\n"
        return tempStr

    def parseProperties(self, data):
        tempStr = ""
        if 'color' in data and len(data['color']) >= 3:
            tempStr += "color(" + str(data['color']) + ")"
        if 'location' in data:
            tempStr += "translate(" + str(data['location']) + ")"
        if 'rotation' in data:
            tempStr += "rotate(a=" + str(data['rotation']['angle']) + ", v=" + \
                        str(data['rotation']['axis']) + ")"
        return tempStr

    def parseElement(self, data):
        tempStr = ""
        if data['name'] == "cube":
            tempStr += self.makeCube(data)
        elif data['name'] == "sphere":
            tempStr += self.makeSphere(data)
        elif data['name'] == "cylinder":
            tempStr += self.makeCylinder(data)
        return tempStr

    def makeCube(self, data):
        """Take a python dictionary and make an OpenSCAD compatible Cube string"""
        tempStr = ""
        #apply centering
        centering = [0,0,0]
        for idx, val in enumerate(data['center']):
            if val:
                centering[idx] = -data['size'][idx]/2
        tempStr += "translate(" + str(centering) + ")"
        tempStr += "cube(size=" + str(data['size']) + ");\n"
        return a

    def makeSphere(self, data):
        """Take a python dictionary and make an OpenSCAD compatible Sphere string"""
        tempStr = ""
        #apply centering
        centering = [0,0,0]
        for idx, val in enumerate(data['center']):
            if not val:
                centering[idx] += data['radius']
        tempStr += "translate(" + str(centering) + ")"
        tempStr += "sphere(r=" + str(data['radius']) + ", $fn=" + str(data['radius']) + ");\n"
        return tempStr

    def makeCylinder(self, data):
        """Take a python dictionary and make an OpenSCAD compatible Cube string"""
        tempStr = ""
        #apply centering
        centering = [0,0,0]
        for idx, val in enumerate(data['center']):
            if not val and idx in [0,1]: 
                centering[idx] = data['radius']
            elif val and idx == 2:
                centering[idx] = -data['height']/2
        tempStr += "translate(" + str(centering) + ")"
        tempStr += "cylinder(r=" + str(data['radius']) + ", h=" + str(data['height']) \
              + ", $fn=" + str((data['radius'])*20) + ");\n"
        return tempStr

    def processRotation(self, data):
        return "rotate(a=" + str(data['rotation']['angle']) + ", v=" + \
                         str(data['rotation']['axis']) + ")"

    def makeTranslate(self, location):
        return "translate(" + str(location) + ")"

    def isAllZeros(self, vector):
        return all( v == 0 for v in vector)

if __name__=="__main__":
    #Setup Command line arguments
    parser = argparse.ArgumentParser(
        prog = "pcsg-openscad",
        usage = "%(prog)s [options] input...",
        description = "An engine for PCSG using OpenSCAD."
        )
    parser.add_argument("-o", "--output", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help = "Output file, defaults to stdout")
    parser.add_argument("input", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help = "Input file, defaults to stdin")
    parser.add_argument("-v", "--verbose", type=bool, help="verbose output while traversing PCSG file")
    parser.add_argument("-s", "--show", action='store_true', default=False, help="launch OpenSCAD with the file when finished")
    parser.add_argument("-i", "--indent", type=int, default=4, help="set number of spaces for indentation (default: 4)")
    parser.add_argument('--version', action='version', version="%(prog)s 0.0.1-dev")

    #Always output help by default
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0) # exit after help display

    args = parser.parse_args()

    j = json.loads(args.input.read())
    c = OpenSCADEngine()
    c.parseJSON(j)
    args.output.write(c.output)
    if args.show:
        subprocess.Popen(["openscad", os.path.abspath(args.output.name)])