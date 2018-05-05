#!/usr/bin/python
"""
nifxml.py

Parses nif.xml into dictionaries of classes grouped by XML tag type.

This file is part of nifxml <https://www.github.com/niftools/nifxml>
Copyright (c) 2017 NifTools

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

This file incorporates work covered by the following copyright and permission notice:
 Copyright (c) 2005, NIF File Format Library and Tools.
 All rights reserved.

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions
 are met:
   - Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
   - Redistributions in binary form must reproduce the above
     copyright notice, this list of conditions and the following
     disclaimer in the documentation and/or other materials provided
     with the distribution.
   - Neither the name of the NIF File Format Library and Tools
     project nor the names of its contributors may be used to endorse
     or promote products derived from this software without specific
     prior written permission.
 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 POSSIBILITY OF SUCH DAMAGE.
"""

from __future__ import unicode_literals

from xml.dom.minidom import Node, parse

import os
import re
import logging

from .utility import export

#
# Globals
#

# The script will reject any versions older than this
MIN_XML_VERSION = '0.9.1.0'

XML_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../nif.xml')

TYPES_NATIVE = {}
TYPES_NATIVE['TEMPLATE'] = 'T'
TYPES_BASIC = {}
TYPES_ENUM = {}
TYPES_FLAG = {}
TYPES_COMPOUND = {}
TYPES_BLOCK = {}
TYPES_VERSION = {}

NAMES_BASIC = []
NAMES_COMPOUND = []
NAMES_ENUM = []
NAMES_FLAG = []
NAMES_BLOCK = []
NAMES_VERSION = []

__all__ = ['TYPES_VERSION', 'TYPES_BASIC', 'TYPES_BLOCK', 'TYPES_COMPOUND', 'TYPES_ENUM', 'TYPES_FLAG', 'TYPES_NATIVE',
           'NAMES_VERSION', 'NAMES_BASIC', 'NAMES_BLOCK', 'NAMES_COMPOUND', 'NAMES_ENUM', 'NAMES_FLAG']

@export
def class_name(name_in): # type: (str) -> str
    """
    Formats a valid C++ class name from the name format used in the XML.
    """
    if name_in is None:
        return None
    try:
        return TYPES_NATIVE[name_in]
    except KeyError:
        return name_in.replace(' ', '_').replace(":", "_")

    if name_in is None:
        return None
    try:
        return TYPES_NATIVE[name_in]
    except KeyError:
        pass
    if name_in == 'TEMPLATE':
        return 'T'
    name_out = ''
    for i, char in enumerate(name_in):
        if char.isupper():
            if i > 0:
                name_out += '_'
            name_out += char.lower()
        elif char.islower() or char.isdigit():
            name_out += char
        else:
            name_out += '_'
    return name_out

@export
def define_name(name_in): # type: (str) -> str
    """
    Formats an all-uppercase version of the name for use in C++ defines.
    """
    name_out = ''
    for i, char in enumerate(name_in):
        if char.isupper():
            if i > 0:
                name_out += '_'
                name_out += char
            else:
                name_out += char
        elif char.islower() or char.isdigit():
            name_out += char.upper()
        else:
            name_out += '_'
    return name_out

@export
def member_name(name_in): # type: (str) -> str
    """
    Formats a version of the name for use as a C++ member variable.
    """
    if name_in is None or name_in == 'ARG':
        return name_in
    name_out = ''
    lower = True
    for char in name_in:
        if char == ' ':
            lower = False
        elif char.isalnum():
            if lower:
                name_out += char.lower()
            else:
                name_out += char.upper()
                lower = True
        elif char == '\\': # arg member access operator
            name_out += '.'
        else:
            name_out += '_'
            lower = True
    return name_out

@export
def version2number(s): # type: (str) -> int
    """
    Translates a legible NIF version number to the packed-byte numeric representation.
    For example, "10.0.1.0" is translated to 0x0A000100.
    """
    if not s:
        return None
    l = s.split('.')
    if len(l) > 4:
        assert False
        return int(s)
    if len(l) == 2:
        version = 0
        version += int(l[0]) << (3 * 8)
        if len(l[1]) >= 1:
            version += int(l[1][0]) << (2 * 8)
        if len(l[1]) >= 2:
            version += int(l[1][1]) << (1 * 8)
        if len(l[1]) >= 3:
            version += int(l[1][2:])
        return version
    else:
        version = 0
        for i, ver in enumerate(l):
            version += int(ver) << ((3-i) * 8)
        return version

@export
def scanBrackets(expr_str, fromIndex=0): # type: (str, int) -> Tuple[int, int]
    """Looks for matching brackets.

    >>> scanBrackets('abcde')
    (-1, -1)
    >>> scanBrackets('()')
    (0, 1)
    >>> scanBrackets('(abc(def))g')
    (0, 9)
    >>> s = '  (abc(dd efy 442))xxg'
    >>> startpos, endpos = scanBrackets(s)
    >>> print s[startpos+1:endpos]
    abc(dd efy 442)
    """
    startpos = -1
    endpos = -1
    scandepth = 0
    for scanpos in range(fromIndex, len(expr_str)):
        scanchar = expr_str[scanpos]
        if scanchar == "(":
            if startpos == -1:
                startpos = scanpos
            scandepth += 1
        elif scanchar == ")":
            scandepth -= 1
            if scandepth == 0:
                endpos = scanpos
                break
    else:
        if startpos != -1 or endpos != -1:
            raise ValueError("expression syntax error (non-matching brackets?)")
    return (startpos, endpos)

class Expression(object):
    """This class represents an expression.

    >>> class A(object):
    ...     x = False
    ...     y = True
    >>> a = A()
    >>> e = Expression('x || y')
    >>> e.eval(a)
    1
    >>> Expression('99 & 15').eval(a)
    3
    >>> bool(Expression('(99&15)&&y').eval(a))
    True
    >>> a.hello_world = False
    >>> def nameFilter(s):
    ...     return 'hello_' + s.lower()
    >>> bool(Expression('(99 &15) &&WoRlD', name_filter = nameFilter).eval(a))
    False
    >>> Expression('c && d').eval(a)
    Traceback (most recent call last):
        ...
    AttributeError: 'A' object has no attribute 'c'
    >>> bool(Expression('1 == 1').eval())
    True
    >>> bool(Expression('1 != 1').eval())
    False
    """
    operators = ['==', '!=', '>=', '<=', '&&', '||', '&', '|', '-', '+', '>', '<', '/', '*']
    def __init__(self, expr_str, name_filter=None):
        self._code = expr_str
        left, self._op, right = self._partition(expr_str)
        self._left = self._parse(left, name_filter)
        if right:
            self._right = self._parse(right, name_filter)
        else:
            self._right = ''

    def eval(self, data=None):
        """Evaluate the expression to an integer."""

        if isinstance(self._left, Expression):
            left = self._left.eval(data)
        elif isinstance(self._left, str):
            left = getattr(data, self._left) if self._left != '""' else ""
        else:
            assert isinstance(self._left, int) # debug
            left = self._left

        if not self._op:
            return left

        if isinstance(self._right, Expression):
            right = self._right.eval(data)
        elif isinstance(self._right, str):
            right = getattr(data, self._right) if self._right != '""' else ""
        else:
            assert isinstance(self._right, int) # debug
            right = self._right

        if self._op == '==':
            return int(left == right)
        elif self._op == '!=':
            return int(left != right)
        elif self._op == '>=':
            return int(left >= right)
        elif self._op == '<=':
            return int(left <= right)
        elif self._op == '&&':
            return int(left and right)
        elif self._op == '||':
            return int(left or right)
        elif self._op == '&':
            return left & right
        elif self._op == '|':
            return left | right
        elif self._op == '-':
            return left - right
        elif self._op == '+':
            return left + right
        elif self._op == '/':
            return left / right
        elif self._op == '*':
            return left * right
        elif self._op == '!':
            return not left
        else:
            raise NotImplementedError("expression syntax error: operator '" + self._op + "' not implemented")

    def __str__(self): # type: () -> str
        """Reconstruct the expression to a string."""

        left = str(self._left)
        if not self._op:
            return left
        right = str(self._right)
        return left + ' ' + self._op + ' ' + right

    def encode(self, encoding): # type: (str) -> str
        """
        To allow encode() to be called on an Expression directly as if it were a string
        (For Python 2/3 cross-compatibility.)
        """
        return self.__str__().encode(encoding)

    @classmethod
    def _parse(cls, expr_str, name_filter=None): # type: (str, Callable[[str], str]) -> str
        """Returns an Expression, string, or int, depending on the
        contents of <expr_str>."""
        # brackets or operators => expression
        if ("(" in expr_str) or (")" in expr_str):
            return Expression(expr_str, name_filter)
        for op in cls.operators:
            if expr_str.find(op) != -1:
                return Expression(expr_str, name_filter)

        mver = re.compile("[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+")
        iver = re.compile("[0-9]+")
        # try to convert it to an integer
        try:
            if mver.match(expr_str):
                return "0x%08X"%(version2number(expr_str))
            elif iver.match(expr_str):
                return str(int(expr_str))
        except ValueError:
            pass
        # failed, so return the string, passed through the name filter
        return name_filter(expr_str) if name_filter else expr_str

    @classmethod
    def _partition(cls, expr_str):
        """Partitions expr_str. See examples below.

        >>> Expression._partition('abc || efg')
        ('abc', '||', 'efg')
        >>> Expression._partition('abc||efg')
        ('abc', '||', 'efg')
        >>> Expression._partition('abcdefg')
        ('abcdefg', '', '')
        >>> Expression._partition(' abcdefg ')
        ('abcdefg', '', '')
        >>> Expression._partition(' (a | b) & c ')
        ('a | b', '&', 'c')
        >>> Expression._partition('(a | b)!=(b&c)')
        ('a | b', '!=', 'b&c')
        >>> Expression._partition('(a== b) &&(( b!=c)||d )')
        ('a== b', '&&', '( b!=c)||d')
        """
        # check for unary operators
        if expr_str.strip().startswith('!'):
            return expr_str.lstrip(' !'), '!', None
        lenstr = len(expr_str)
        # check if the left hand side starts with brackets
        # and if so, find the position of the starting bracket and the ending
        # bracket
        left_startpos, left_endpos = cls._scanBrackets(expr_str)
        if left_startpos >= 0:
            # yes, it is a bracketted expression
            # so remove brackets and whitespace,
            # and let that be the left hand side
            left_str = expr_str[left_startpos+1:left_endpos].strip()

            # the next token should be the operator
            # find the position where the operator should start
            op_startpos = left_endpos+1
            while op_startpos < lenstr and expr_str[op_startpos] == " ":
                op_startpos += 1
            if op_startpos < lenstr:
                # to avoid confusion between && and &, and || and |,
                # let's first scan for operators of two characters
                # and then for operators of one character
                for op_endpos in range(op_startpos+1, op_startpos-1, -1):
                    op_str = expr_str[op_startpos:op_endpos+1]
                    if op_str in cls.operators:
                        break
                else:
                    raise ValueError("expression syntax error: expected operator at '%s'"%expr_str[op_startpos:])
            else:
                return cls._partition(left_str)
        else:
            # it's not... so we need to scan for the first operator
            for op_startpos, ch in enumerate(expr_str):
                if ch == ' ':
                    continue
                if ch == '(' or ch == ')':
                    raise ValueError("expression syntax error: expected operator before '%s'"%expr_str[op_startpos:])
                # to avoid confusion between && and &, and || and |,
                # let's first scan for operators of two characters
                for op_endpos in range(op_startpos+1, op_startpos-1, -1):
                    op_str = expr_str[op_startpos:op_endpos+1]
                    if op_str in cls.operators:
                        break
                else:
                    continue
                break
            else:
                # no operator found, so we are done
                left_str = expr_str.strip()
                op_str = ''
                right_str = ''
                return left_str, op_str, right_str
            # operator found! now get the left hand side
            left_str = expr_str[:op_startpos].strip()

        return left_str, op_str, expr_str[op_endpos+1:].strip()

    @staticmethod
    def _scanBrackets(expr_str, fromIndex=0):
        """Looks for matching brackets.

        >>> Expression._scanBrackets('abcde')
        (-1, -1)
        >>> Expression._scanBrackets('()')
        (0, 1)
        >>> Expression._scanBrackets('(abc(def))g')
        (0, 9)
        >>> s = '  (abc(dd efy 442))xxg'
        >>> startpos, endpos = Expression._scanBrackets(s)
        >>> print s[startpos+1:endpos]
        abc(dd efy 442)
        """
        startpos = -1
        endpos = -1
        scandepth = 0
        for scanpos in range(fromIndex, len(expr_str)):
            scanchar = expr_str[scanpos]
            if scanchar == "(":
                if startpos == -1:
                    startpos = scanpos
                scandepth += 1
            elif scanchar == ")":
                scandepth -= 1
                if scandepth == 0:
                    endpos = scanpos
                    break
        else:
            if startpos != -1 or endpos != -1:
                raise ValueError("expression syntax error (non-matching brackets?)")
        return (startpos, endpos)

    def code(self, prefix='', brackets=True, name_filter=None): # type: (str, bool, Callable[[str], str]) -> str
        """Format an expression as a string."""
        lbracket = "(" if brackets else ""
        rbracket = ")" if brackets else ""
        if not self._op:
            if not self.lhs:
                return ''
            if isinstance(self.lhs, int):
                return self.lhs
            elif self.lhs in TYPES_BLOCK:
                return 'IsDerivedType(%s::TYPE)' % self.lhs
            else:
                return prefix + (name_filter(self.lhs) if name_filter else self.lhs)
        elif self._op == '!':
            lhs = self.lhs
            if isinstance(lhs, Expression):
                lhs = lhs.code(prefix, True, name_filter)
            elif lhs in TYPES_BLOCK:
                lhs = 'IsDerivedType(%s::TYPE)' % lhs
            elif lhs and not lhs.isdigit() and not lhs.startswith('0x'):
                lhs = prefix + (name_filter(lhs) if name_filter else lhs)
            return '%s%s%s%s'%(lbracket, self._op, lhs, rbracket)
        else:
            lhs = self.lhs
            rhs = self.rhs
            if isinstance(lhs, Expression):
                lhs = lhs.code(prefix, True, name_filter)
            elif lhs in TYPES_BLOCK:
                lhs = 'IsDerivedType(%s::TYPE)' % lhs
            elif lhs and not lhs.isdigit() and not lhs.startswith('0x'):
                lhs = prefix + (name_filter(lhs) if name_filter else lhs)
            if isinstance(rhs, Expression):
                rhs = rhs.code(prefix, True, name_filter)
            elif rhs in TYPES_BLOCK:
                rhs = 'IsDerivedType(%s::TYPE)' % rhs
            elif rhs and not rhs.isdigit() and not rhs.startswith('0x'):
                rhs = prefix + (name_filter(rhs) if name_filter else rhs)
            return '%s%s %s %s%s'%(lbracket, lhs, self._op, rhs, rbracket)

    def get_terminals(self):
        """Return all terminal names (without operators or brackets)."""
        if isinstance(self.lhs, Expression):
            for terminal in self.lhs.get_terminals():
                yield terminal
        elif self.lhs:
            yield self.lhs
        if isinstance(self.rhs, Expression):
            for terminal in self.rhs.get_terminals():
                yield terminal
        elif self.rhs:
            yield self.rhs

    def __getattr__(self, name):
        if name == 'lhs':
            return getattr(self, '_left')
        if name == 'rhs':
            return getattr(self, '_right')
        if name == 'op':
            return getattr(self, '_op')
        return object.__getattribute__(self, name)

    def isdigit(self):
        """ducktyping: pretend we're also a string with isdigit() method"""
        return False

class Expr(Expression):
    """
    Represents a mathmatical expression?
    @ivar lhs: The left hand side of the expression?
    @ivar clhs: The C++ formatted version of the left hand side of the expression?
    @ivar op: The operator used in the expression.  ==, &&, !=, etc.
    @ivar rhs: The right hand side of the expression?
    """
    def __init__(self, n, name_filter=None):
        """
        This constructor takes the expression in the form of a string and tokenizes it into left-hand side,
        operator, right hand side, and something called clhs.
        @param n: The expression to tokenize.
        @type n: string
        """
        Expression.__init__(self, n, name_filter)

    def code(self, prefix='', brackets=True, name_filter=None):
        if not name_filter:
            name_filter = member_name
        return Expression.code(self, prefix, brackets, name_filter)

class Option:
    """
    This class represents an option in an option list.
    @ivar value: The C++ value of option variable.  Comes from the "value" attribute of the <option> tag.
    @ivar name: The name of this member variable.  Comes from the "name" attribute of the <option> tag.
    @ivar description: The description of this option.  Comes from the text between <option> and </option>.
    @ivar cname: The name of this member for use in C++.
    """
    def __init__(self, element):
        """
        This constructor converts an XML <option> element into an Option object.
        """
        assert element.tagName == 'option'
        #parent = element.parentNode
        #sisters = parent.getElementsByTagName('option')

        # member attributes
        self.value = element.getAttribute('value') # type: str
        self.name = element.getAttribute('name') # type: str
        self.description = self.name # type: str
        if element.firstChild:
            assert element.firstChild.nodeType == Node.TEXT_NODE
            self.description = element.firstChild.nodeValue.strip()
        self.cname = self.name.upper().replace(" ", "_").replace("-", "_").replace("/", "_").replace("=", "_").replace(":", "_") # type: str

@export
class Member:
    """
    This class represents the nif.xml <add> tag.
    @ivar name:  The name of this member variable.  Comes from the "name" attribute of the <add> tag.
    @ivar arg: The argument of this member variable.  Comes from the "arg" attribute of the <add> tag.
    @ivar template: The template type of this member variable.  Comes from the "template" attribute of the <add> tag.
    @ivar arr1: The first array size of this member variable.  Comes from the "arr1" attribute of the <add> tag.
    @ivar arr2: The first array size of this member variable.  Comes from the "arr2" attribute of the <add> tag.
    @ivar cond: The condition of this member variable.  Comes from the "cond" attribute of the <add> tag.
    @ivar func: The function of this member variable.  Comes from the "func" attribute of the <add> tag.
    @ivar default: The default value of this member variable.  Comes from the "default" attribute of the <add> tag.
        Formatted to be ready to use in a C++ constructor initializer list.
    @ivar ver1: The first version this member exists.  Comes from the "ver1" attribute of the <add> tag.
    @ivar ver2: The last version this member exists.  Comes from the "ver2" attribute of the <add> tag.
    @ivar userver: The user version where this member exists.  Comes from the "userver" attribute of the <add> tag.
    @ivar userver2: The user version 2 where this member exists.  Comes from the "userver2" attribute of the <add> tag.
    @ivar vercond: The version condition of this member variable.  Comes from the "vercond" attribute of the <add> tag.
    @ivar is_public: Whether this member will be declared public.  Comes from the "public" attribute of the <add> tag.
    @ivar is_abstract: Whether this member is abstract.  This means that it does not factor into read/write.
    @ivar description: The description of this member variable.  Comes from the text between <add> and </add>.
    @ivar uses_argument: Specifies whether this attribute uses an argument.
    @ivar type_is_native: Specifies whether the type is implemented natively
    @ivar is_duplicate: Specifies whether this is a duplicate of a previously declared member
    @ivar arr2_dynamic: Specifies whether arr2 refers to an array (?)
    @ivar arr1_ref: Names of the attributes it is a (unmasked) size of (?)
    @ivar arr2_ref: Names of the attributes it is a (unmasked) size of (?)
    @ivar cond_ref: Names of the attributes it is a condition of (?)
    @ivar cname: Unlike default, name isn't formatted for C++ so use this instead?
    @ivar ctype: Unlike default, type isn't formatted for C++ so use this instead?
    @ivar carg: Unlike default, arg isn't formatted for C++ so use this instead?
    @ivar ctemplate: Unlike default, template isn't formatted for C++ so use this instead?
    @ivar carr1_ref: Unlike default, arr1_ref isn't formatted for C++ so use this instead?
    @ivar carr2_ref: Unlike default, arr2_ref isn't formatted for C++ so use this instead?
    @ivar ccond_ref: Unlike default, cond_ref isn't formatted for C++ so use this instead?
    @ivar next_dup: Next duplicate member
    @ivar is_manual_update: True if the member value is manually updated by the code
    """
    def __init__(self, element):
        """
        This constructor converts an XML <add> element into a Member object.
        Some sort of processing is applied to the various variables that are copied from the XML tag...
        Seems to be trying to set reasonable defaults for certain types, and put things into C++ format generally.
        @param prefix: An optional prefix used in some situations?
        @type prefix: string
        @return The expression formatted into a string?
        @rtype: string?
        """
        assert element.tagName == 'add'
        #parent = element.parentNode
        #sisters = parent.getElementsByTagName('add')

        # member attributes
        self.name      = element.getAttribute('name') # type: str
        self.suffix    = element.getAttribute('suffix') # type: str
        self.type      = element.getAttribute('type') # type: str
        self.arg       = element.getAttribute('arg') # type: str
        self.template  = element.getAttribute('template') # type: str
        self.arr1      = Expr(element.getAttribute('arr1')) # type: Expr
        self.arr2      = Expr(element.getAttribute('arr2')) # type: Expr
        self.cond      = Expr(element.getAttribute('cond')) # type: Expr
        self.func      = element.getAttribute('function') # type: str
        self.default   = element.getAttribute('default') # type: str
        self.orig_ver1 = element.getAttribute('ver1') # type: str
        self.orig_ver2 = element.getAttribute('ver2') # type: str
        self.ver1      = version2number(element.getAttribute('ver1')) # type: int
        self.ver2      = version2number(element.getAttribute('ver2')) # type: int
        xint = lambda s: int(s) if s else None
        self.userver   = xint(element.getAttribute('userver')) # type: Optional[int]
        self.userver2  = xint(element.getAttribute('userver2')) # type: Optional[int]
        self.vercond   = Expr(element.getAttribute('vercond')) # type: Expr
        self.is_public = (element.getAttribute('public') == "1") # type: bool
        self.is_abstract = (element.getAttribute('abstract') == "1") # type: bool
        self.next_dup  = None # type: Optional[Member]
        self.is_manual_update = False # type: bool
        self.is_calculated = (element.getAttribute('calculated') == "1") # type: bool

        # Get description from text between start and end tags
        self.description = "" # type: str
        if element.firstChild:
            assert element.firstChild.nodeType == Node.TEXT_NODE
            self.description = element.firstChild.nodeValue.strip()
        elif self.name.lower().find("unk") == 0:
            self.description = "Unknown."

        # Format default value so that it can be used in a C++ initializer list
        if not self.default and (not self.arr1.lhs and not self.arr2.lhs):
            if self.type in ["unsigned int", "unsigned short", "byte", "int", "short", "char"]:
                self.default = "0"
            elif self.type == "bool":
                self.default = "false"
            elif self.type in ["Ref", "Ptr"]:
                self.default = "NULL"
            elif self.type in "float":
                self.default = "0.0"
            elif self.type == "HeaderString":
                pass
            elif self.type == "Char8String":
                pass
            elif self.type == "StringOffset":
                self.default = "-1"
            elif self.type in NAMES_BASIC:
                self.default = "0"
            elif self.type in NAMES_FLAG or self.type in NAMES_ENUM:
                self.default = "0"
        if self.default:
            if self.default[0] == '(' and self.default[-1] == ')':
                self.default = self.default[1:-1]
            if self.arr1.lhs: # handle static array types
                if self.arr1.lhs.isdigit():
                    sep = (',(%s)'%class_name(self.type))
                    self.default = self.arr1.lhs + sep + sep.join(self.default.split(' ', int(self.arr1.lhs)))
            elif self.type == "string" or self.type == "IndexString":
                self.default = "\"" + self.default + "\""
            elif self.type == "float":
                # Cast to float then back to string to add any missing ".0"
                self.default = str(float(self.default)) + "f"
            elif self.type in ["Ref", "Ptr", "bool", "Vector3"]:
                pass
            elif self.default.find(',') != -1:
                pass
            else:
                self.default = "(%s)%s"%(class_name(self.type), self.default)

        # calculate other stuff
        self.uses_argument = (self.cond.lhs == '(ARG)' or self.arr1.lhs == '(ARG)' or self.arr2.lhs == '(ARG)') # type: bool
        # true if the type is implemented natively
        self.type_is_native = self.name in TYPES_NATIVE # type: bool

        # calculate stuff from reference to previous members
        # true if this is a duplicate of a previously declared member
        self.is_duplicate = False # type: bool
        # true if arr2 refers to an array
        self.arr2_dynamic = False # type: bool
        sis = element.previousSibling
        while sis:
            if sis.nodeType == Node.ELEMENT_NODE:
                sis_name = sis.getAttribute('name')
                if sis_name == self.name and not self.suffix:
                    self.is_duplicate = True
                sis_arr1 = Expr(sis.getAttribute('arr1'))
                sis_arr2 = Expr(sis.getAttribute('arr2'))
                if sis_name == self.arr2.lhs and sis_arr1.lhs:
                    self.arr2_dynamic = True
            sis = sis.previousSibling

        # Calculate stuff from reference to next members
        # Names of the attributes it is a (unmasked) size of
        self.arr1_ref = [] # type: List[str]
        # Names of the attributes it is a (unmasked) size of
        self.arr2_ref = [] # type: List[str]
        # Names of the attributes it is a condition of
        self.cond_ref = [] # type: List[str]
        sis = element.nextSibling
        while sis != None:
            if sis.nodeType == Node.ELEMENT_NODE:
                sis_name = sis.getAttribute('name')
                sis_arr1 = Expr(sis.getAttribute('arr1'))
                sis_arr2 = Expr(sis.getAttribute('arr2'))
                sis_cond = Expr(sis.getAttribute('cond'))
                if sis_arr1.lhs == self.name and (not sis_arr1.rhs or sis_arr1.rhs.isdigit()):
                    self.arr1_ref.append(sis_name)
                if sis_arr2.lhs == self.name and (not sis_arr2.rhs or sis_arr2.rhs.isdigit()):
                    self.arr2_ref.append(sis_name)
                if sis_cond.lhs == self.name:
                    self.cond_ref.append(sis_name)
            sis = sis.nextSibling

        # C++ names
        self.cname     = member_name(self.name if not self.suffix else self.name + "_" + self.suffix) # type: str
        self.ctype     = class_name(self.type) # type: str
        self.carg      = member_name(self.arg) # type: str
        self.ctemplate = class_name(self.template) # type: str
        self.carr1_ref = [member_name(n) for n in self.arr1_ref] # type: List[str]
        self.carr2_ref = [member_name(n) for n in self.arr2_ref] # type: List[str]
        self.ccond_ref = [member_name(n) for n in self.cond_ref] # type: List[str]

class Nifxml:
    """This class represents the nif.xml <niftoolsxml> tag."""
    def __init__(self, element):
        self.version = version2number(element.getAttribute('version')) # type: int

    def is_supported(self): # type: () -> bool
        """If the nif.xml version meets the requirements."""
        return self.version >= version2number(MIN_XML_VERSION)

@export
class Version:
    """This class represents the nif.xml <version> tag."""
    def __init__(self, element):
        self.num = element.getAttribute('num') # type: str
        # Treat the version as a name to match other tags
        self.name = self.num # type: str
        self.description = element.firstChild.nodeValue.strip() # type: str

@export
class Basic:
    """This class represents the nif.xml <basic> tag."""
    def __init__(self, element, ntypes):
        self.name = element.getAttribute('name') # type: str
        assert self.name # debug
        self.cname = class_name(self.name) # type: str
        self.description = "" # type: str
        if element.firstChild and element.firstChild.nodeType == Node.TEXT_NODE:
            self.description = element.firstChild.nodeValue.strip()
        elif self.name.lower().find("unk") == 0:
            self.description = "Unknown."

        self.count = element.getAttribute('count') # type: str
        self.template = (element.getAttribute('istemplate') == "1") # type: bool
        self.options = [] # type: List[Option]

        self.is_link = False # type: bool
        self.is_crossref = False # type: bool
        self.has_links = False # type: bool
        self.has_crossrefs = False # type: bool

        self.nativetype = None  # type: Optional[str]
        if ntypes:
            self.nativetype = ntypes.get(self.name)
            if self.nativetype:
                TYPES_NATIVE[self.name] = self.nativetype
                if self.nativetype == "Ref":
                    self.is_link = True
                    self.has_links = True
                if self.nativetype == "*":
                    self.is_crossref = True
                    self.has_crossrefs = True

@export
class Enum(Basic):
    """This class represents the nif.xml <enum> tag."""
    def __init__(self, element, ntypes):
        Basic.__init__(self, element, ntypes)

        self.storage = element.getAttribute('storage')
        self.prefix = element.getAttribute('prefix')
        # Find the native storage type
        self.storage = TYPES_BASIC[self.storage].nativetype if TYPES_BASIC[self.storage].nativetype else TYPES_BASIC[self.storage].name
        self.description = element.firstChild.nodeValue.strip()

        self.nativetype = self.cname
        TYPES_NATIVE[self.name] = self.nativetype

        # Locate all special enumeration options
        for option in element.getElementsByTagName('option'):
            if self.prefix and option.hasAttribute('name'):
                option.setAttribute('name', self.prefix + "_" + option.getAttribute('name'))
            self.options.append(Option(option))

@export
class Flag(Enum):
    """This class represents the nif.xml <bitflags> tag."""
    def __init__(self, element, ntypes):
        Enum.__init__(self, element, ntypes)
        for option in self.options:
            option.bit = option.value
            option.value = 1 << int(option.value)

@export
class Compound(Basic):
    """This class represents the nif.xml <compound> tag."""
    def __init__(self, element, ntypes):
        Basic.__init__(self, element, ntypes)

        self.members = [] # type: List[Member]
        self.argument = False # type: bool

        # store all attribute data & calculate stuff
        for member in element.getElementsByTagName('add'):
            x = Member(member)

            # Ignore infinite recursion on already visited compounds
            if x in self.members:
                continue

            self.members.append(x)

            # detect argument
            self.argument = bool(x.uses_argument)

            # detect links & crossrefs
            mem = None
            try:
                mem = TYPES_BASIC[x.type]
            except KeyError:
                try:
                    mem = TYPES_COMPOUND[x.type]
                except KeyError:
                    pass
            if mem:
                if mem.has_links:
                    self.has_links = True
                if mem.has_crossrefs:
                    self.has_crossrefs = True

        # create duplicate chains for items that need it (only valid in current object scope)
        #  prefer to use iterators to avoid O(n^2) but I dont know how to reset iterators
        for outer in self.members:
            atx = False
            for inner in self.members:
                if atx:
                    if outer.name == inner.name: # duplicate
                        outer.next_dup = inner
                        break
                elif outer == inner:
                    atx = True

    def find_member(self, name, inherit=False): # type: (str, bool) -> Optional[Member]
        """Find member by name"""
        for mem in self.members:
            if mem.name == name:
                return mem
        return None

    def find_first_ref(self, name): # type: (str) -> Optional[Member]
        """Find first reference of name in class."""
        for mem in self.members:
            if mem.arr1 and mem.arr1.lhs == name:
                return mem
            elif mem.arr2 and mem.arr2.lhs == name:
                return mem
        return None

    def has_arr(self): # type: () -> bool
        """Tests recursively for members with an array size."""
        for mem in self.members:
            if mem.arr1.lhs or (mem.type in TYPES_COMPOUND and TYPES_COMPOUND[mem.type].has_arr()):
                return True
        return False

@export
class Block(Compound):
    """This class represents the nif.xml <niobject> tag."""
    def __init__(self, element, ntypes):
        Compound.__init__(self, element, ntypes)
        self.is_ancestor = (element.getAttribute('abstract') == "1")
        inherit = element.getAttribute('inherit')
        self.inherit = TYPES_BLOCK[inherit] if inherit else None
        self.has_interface = (element.getElementsByTagName('interface') != [])

    def find_member(self, name, inherit=False): # type: (str, bool) -> Optional[Member]
        """Find member by name"""
        ret = Compound.find_member(self, name)
        if not ret and inherit and self.inherit:
            ret = self.inherit.find_member(name, inherit)
        return ret

    def find_first_ref(self, name): # type: (str) -> Optional[Member]
        """Find first reference of name in class"""
        ret = None
        if self.inherit:
            ret = self.inherit.find_first_ref(name)
        if not ret:
            ret = Compound.find_first_ref(self, name)
        return ret

    def ancestors(self): # type: () -> List[Block]
        """List all ancestors of this block"""
        ancestors = []
        parent = self
        while parent:
            ancestors.append(parent)
            parent = parent.inherit
        return ancestors

@export
def parse_xml(ntypes=None, path=XML_PATH): # type: (Optional[Dict[str, str]], str) -> bool
    """Import elements into our NIF classes"""
    if os.path.exists(path):
        xml = parse(path)
    else:
        raise ImportError("nif.xml not found")

    # Logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('nifxml')

    nifxml = Nifxml(xml.documentElement)
    if not nifxml.is_supported():
        logger.error("The nif.xml version you are trying to parse is not supported by nifxml.py.")
        return False

    for element in xml.getElementsByTagName('version'):
        instance = Version(element)
        TYPES_VERSION[instance.num] = instance
        NAMES_VERSION.append(instance.num)

    for element in xml.getElementsByTagName('basic'):
        instance = Basic(element, ntypes)
        assert not instance.name in TYPES_BASIC
        TYPES_BASIC[instance.name] = instance
        NAMES_BASIC.append(instance.name)

    for element in xml.getElementsByTagName('enum'):
        instance = Enum(element, ntypes)
        assert not instance.name in TYPES_ENUM
        TYPES_ENUM[instance.name] = instance
        NAMES_ENUM.append(instance.name)

    for element in xml.getElementsByTagName('bitflags'):
        instance = Flag(element, ntypes)
        assert not instance.name in TYPES_FLAG
        TYPES_FLAG[instance.name] = instance
        NAMES_FLAG.append(instance.name)

    for element in xml.getElementsByTagName('compound'):
        instance = Compound(element, ntypes)
        assert not instance.name in TYPES_COMPOUND
        TYPES_COMPOUND[instance.name] = instance
        NAMES_COMPOUND.append(instance.name)

    for element in xml.getElementsByTagName('niobject'):
        instance = Block(element, ntypes)
        assert not instance.name in TYPES_BLOCK
        TYPES_BLOCK[instance.name] = instance
        NAMES_BLOCK.append(instance.name)

    return validate_xml()

def validate_xml(): # type: () -> bool
    """Perform some basic validation on the data retrieved from the XML"""
    val = lambda x, y: x and y and len(x) == len(y) and all(n for n in y)
    res = (val(TYPES_VERSION, NAMES_VERSION) and val(TYPES_BASIC, NAMES_BASIC) and val(TYPES_COMPOUND, NAMES_COMPOUND)
           and val(TYPES_BLOCK, NAMES_BLOCK) and val(TYPES_ENUM, NAMES_ENUM) and val(TYPES_FLAG, NAMES_FLAG))
    if not res:
        logger = logging.getLogger('nifxml')
        logger.error("The parsing of nif.xml did not pass validation.")
    return res
