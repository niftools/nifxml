#!/usr/bin/python
"""
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
"""
from __future__ import unicode_literals

UL_ITEM = '<ul>\n{0}</ul>\n'
LI_LINK = '\t<li><a href="{0}.html">{1}</a></li>\n'
LI_LINK_DESC = '<li><a href="{0}.html"><b>{1}</b></a> | {2}</li>\n'
TYPE_LINK = '<a href="{0}.html"><b>{1}</b></a>'
TMPL_LINK = '&lt;<a href="{0}.html">{1}</a>&gt;'

MAIN_BEG = """<!doctype html>
<html lang="en">
<head>
\t<title>NIF File Format Documentation - {title}</title>
\t<link rel="stylesheet" href="nifdoc.css" type="text/css" />
\t<link rel="icon" href="favicon.ico" type="image/x-icon" />
</head>
<body>"""
MAIN_END = """
\t<p align="center"><a href="index.html">NIF Objects</a> | <a href="struct_list.html">Struct Types</a> 
\t| <a href="enum_list.html">Enum Types</a> | <a href="basic_list.html">Basic Types</a> | <a href="version_list.html">File Versions</a></p>
\t{contents}
</body>
</html>"""

# Main HTML template with and without H1 heading
MAIN_H1 = MAIN_BEG + '<center><h1>NIF File Format Documentation</h1></center>' + MAIN_END
MAIN_NO_H1 = MAIN_BEG + MAIN_END

# Attribute row with metadata
ATTR = """
<tr class="{row}">
\t<td class="aname">{attr_name}</td>
\t<td class="atype">{attr_type}</td>
\t<td class="aarg">{attr_arg}</td>
\t<td class="alength">{attr_length}</td>
\t<td class="awidth">{attr_width}</td>
\t<td class="acond">{attr_cond}</td>
\t<td class="adesc">{attr_desc}</td>
\t<td class="afrom">{attr_from}</td>
\t<td class="ato">{attr_to}</td>
</tr>
"""

# Attribute row without metadata
ATTR_NO_META = """
<tr class="{row}">
\t<td class="aname">{attr_name}</td>
\t<td class="atype">{attr_type}</td>
\t<td class="adesc">{attr_desc}</td>
</tr>
"""

# List for Found In
FOUND_IN = """
<h3>Found In</h3>
<ul>
{member_of}
</ul>
"""

# List for Parent Of
PARENT_OF = """
<h3>Parent Of</h3>
<ul>
{parent_of}
</ul>"""

# Basic layout
BASIC = """
<center><h2>{name}</h2></center>
{description}

<h3>Can Be Used As Array Size</h3>
<p>{count}</p>
""" + FOUND_IN

# Block with metadata columns
BLOCK = """
<center><h2>{name}</h2></center>
{description}
<h3>Attributes</h3>
<table>
\t<tr>
\t\t<th>Name</th>
\t\t<th>Type</th>
\t\t<th>Arg</th>
\t\t<th>Length</th>
\t\t<th>Width</th>
\t\t<th>Cond</th>
\t\t<th>Description</th>
\t\t<th>From</th><th>To</th>
\t</tr>
\t{attributes}
</table>
"""

# Block without metadata columns
BLOCK_NM = """
<center><h2>{name}</h2></center>
{description}
<h3>Attributes</h3>
<table>
\t<tr>
\t\t<th>Name</th>
\t\t<th>Type</th>
\t\t<th>Description</th>
\t</tr>
\t{attributes}
</table>
"""

# Struct and NiObject with and without metadata columns
STRUCT = BLOCK + FOUND_IN
NIOBJECT = BLOCK + PARENT_OF
STRUCT_NO_META = BLOCK_NM + FOUND_IN
NIOBJECT_NO_META = BLOCK_NM + PARENT_OF

# Object tree for index.html
HIERARCHY = """
<ul>{object_tree}</ul>"""

# Object list for *_list.html
LIST = """
<table>
\t<tr>
\t\t<th>{list_header}</th>
\t\t<th>Description</th>
\t</tr>
{list}
</table>"""

# Navbar
NAV = """<p align="center"><a href="index.html">Hierarchy</a> | <a href="niobject_list.html">List</a></p>
<center><h2>{title}</h2></center>
"""

# Nav plus contents
NAV_LIST = NAV + LIST
NAV_HIER = NAV + HIERARCHY

# Enum layout
ENUM = """
<h2>{name}</h2>
{description}

<h3>Choices</h3>
<table>
\t<tr class="{row}">
\t\t<th>Number</th>
\t\t<th>Name</th>
\t\t<th>Description</th>
\t</tr>
\t{choices}
</table>

<h3>Storage Type</h3>
<a href ="{storage}.html">{storage}</a>
""" + FOUND_IN

ENUM_ROW = """
<tr class="{row}">
\t<td>{enum_number}</td>
\t<td><b>{enum_name}</b></td>
\t<td>{enum_desc}</td>
</tr>
"""

INHERIT_ROW = """
<tr>
\t<th align="left" style="text-align:left;" colspan="9">From <a href ="{cinherit}.html">{inherit}</a></th>
</tr>
"""

INHERIT_NO_META = """
<tr>
\t<th align="left" style="text-align:left;" colspan="3">From <a href ="{cinherit}.html">{inherit}</a></th>
</tr>
"""

LIST_ROW = """
<tr class="{row}">
\t<td><b><a href="{list_cname}.html">{list_name}</a></b></td>
\t<td>{list_desc}</td>
</tr>"""

VERSION_ROW = """
<tr class="{row}">
\t<td><b>{list_name}</a></b></td>
\t<td>{list_desc}</td>
</tr>
"""
