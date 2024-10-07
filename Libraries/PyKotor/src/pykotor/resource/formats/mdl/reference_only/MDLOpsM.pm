#! perl
#
###########################################################
# MDLOpsM.pm version 1.0.2
# Copyright (C) 2004 Chuck Chargin Jr. (cchargin@comcast.net)
#
# (With some changes by JdNoa (jdnoa@hotmail.com) between
# November 2006 and May 2007.)
#
# (With some more changes by VarsityPuppet and Fair Strides
# (tristongoucher@gmail.com) during January 2016.)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
##########################################################
# History:
#
# July 1 2004:		First public release of MDLOpsM.pm version 0.1
#                
# July 17 2004: 	Added "writerawbinarymdl" and "makeraw" subs 
#               	    for use with replacer functionality (not working yet)
#			    Now supports vertex normals (Thanks JRC24)
#
# August 4, 2004: 	Fixed a division by zero bug in the vertex normals (thanks Svosh)
#
# October 2, 2004:  	version 0.3
#	                    Now ignores overlapping vertices
#        	            fixed a bug that caused some controllers to be ignored (thanks T7nowhere and Svosh)                 
#                	    updated docs on how texture maps work in kotor (thanks T7nowhere and Svosh)
#                  	    updated model tutorial
#                   
# November 18, 2004: 	Version 0.4
#                   	    added replacer function (idea originally suggested to me by tk102)
#                   	    gui does not get built when using command line (thanks Fred Tetra)
#                  	    added ability to rename textures in binary models (thanks darkkender)
#                   	    cool new icon created by Svosh.  Thanks Svosh!
#
# March 8, 2005: 	Version 0.5
#                   	    figured out that some meshes have 2 textures (thanks Fred Tetra)
#                   	    added fix for meshes that have 0 verticies (thanks Fred Tetra)
#                   	    added support for Kotor 2.  The model is bigger by only 8 bytes per mesh!
#                   	    the program will auto-detect if a binary model is from kotor 1 or kotor 2
#                   
# March 9, 2006: 	Version 0.6alpha4
#                   	    Added aabb support (thanks Fred Tetra)
#                   	    Vastly improved ascii import speed (optimized the adjacent face routine)
#                   	    Added partial support for aurora lights
#                   	    ANIMATIONS! MUCH MUCH thanks to JdNoa for her cracking of the compressed quaternion format
#                     	    and for writing the animation delta code!
#
# May 21, 2007:		version 0.6.1alpha1 (changes by JdNoa)
#	                    Added support for compiling animations.  Code mostly ported from Torlack's NWN compiler.
#       	            Added controllers for lights and emitters, but not tested yet.
#
# January 13, 2016:	Version 0.7alpha
#			    Reworked calculations of face normals
#			    Reworked calculations of vertex normals
#
# Summer, 2017:         Version 1.0.0
#                           Reworked calculations of face, vertex normals, plane distances, adjacent faces
#                           Added tangent space calculations
#                           Added emitter and finished light node support
#                           Added walkmesh support (DWK/PWK/WOK)
#                           Added lightsaber mesh support and conversion
#                           Added bezier controller support and fixed existing controller list
#                           Added normalization of vertex data into MDX form
#                           Added detection of real smoothgroups
#                           Added reference node support
#                           Added super model node number construction
#                           Fixed replacer for many cases
#                           Unicode path/filename support
#                           Many more small fixes and features
#
# January, 2017:        Version 1.0.1
#                           Fixed compression and decompression of quaternions
#                           Fixed axis-angle to quaternion conversion
#                           Fixed walkmesh use point encoding, off-by-one
#                           Fixed ascii walkmesh node naming
#                           Fixed walkmesh compatibility with mdledit/kmax
#
# June, 2020:           Version 1.0.2
#                           Fixed cross-mesh smoothing by using world-space normals
#                           Added vertex equality test matching mdledit
#                           Fixed walkmesh floating point number parser
#
##########################################################
# MUCH MUCH MUCH thanks to Torlack for his NWN MDL info!
# without that this script could not exist!
# 
# Thanks to my testers:
#   T7nowhere
#   Svosh
#   Seprithro
#   ChAiNz.2da
#   
# Thanks to all at Holowan Laboratories for your input
# and support.
#
# What is this?
# 
# This is a Perl module that contains functions for 
# importing and extracting models from
# Star Wars Knight of the Old Republic 1 and 2
#
# see the readme for more info
#
# Dedicated to Cockatiel
# 
package MDLOpsM;

BEGIN {
  use Exporter;
  our @EXPORT = qw(modeltype readbinarymdl writeasciimdl readasciimdl writebinarymdl buildtree writerawbinarymdl replaceraw modelversion);
  our @ISA = qw(Exporter);
  use vars qw($VERSION);
  $VERSION = '1.0.1';
}

#use Time::HiRes qw(usleep ualarm gettimeofday tv_interval);
use Time::HiRes qw(gettimeofday tv_interval);
use strict;
use Math::Trig;       # quaternions? I have to convert quaternions?
use Scalar::Util qw(openhandle);


# add helpful debug library from perl core
use Data::Dumper;

# turn this on for maximum verbosity
our $printall = 0;

# for use with $model{'geoheader'}{'unpacked'}[  ]
use constant ROOTNODE => 3;
# use constant NODENUM => 4;
# for use with $model{'modelheader'}{'unpacked'}[  ]
use constant ANIMROOT => 5;
# for use with $model{'nodes'}{0}{'header'}{'unpacked'}[  ]
use constant NODETYPE => 0;
use constant NODEINDEX => 2;
#use constant PARENTNODE => 5;
# for use with $model{'nodes'}{0}{'subhead'}{'unpacked'}[  ]
#use constant DATAEXTLEN => 62;
#use constant TEXTURENUM => 63;
#use constant MDXLOC => 70;
#use constant DATAEXT1LOC => 71;
#use constant DATAEXT2LOC => 72;
#use constant DATAEXT3LOC => 73;
#use constant DATAEXT4LOC => 74;

our %structs;
$structs{'fileheader'} =  {loc =>   0, num =>  3, size =>  4, dnum => 1, name => "file_header",  tmplt => "lll"};
$structs{'geoheader'} =   {loc =>  12, num =>  1, size => 80, dnum => 1, name => "geo_header",   tmplt => "llZ[32]lllllllllCCCC"};
$structs{'modelheader'} = {loc =>  92, num =>  1, size => 92, dnum => 1, name => "model_header", tmplt => "CCCClllllffffffffZ[32]L"};
$structs{'nameheader'} =  {loc => 180, num =>  1, size => 28, dnum => 1, name => "name_header",  tmplt => "lllllll"};
$structs{'nameindexes'} = {loc =>   4, num =>  5, size =>  4, dnum => 1, name => "name_indexes", tmplt => "l*"};
$structs{'names'} =       {loc =>  -1, num => -1, size => -1, dnum => 1, name => "names",        tmplt => "Z*"};
$structs{'animindexes'} = {loc =>   5, num =>  6, size =>  4, dnum => 1, name => "anim_indexes", tmplt => "l*"};
$structs{'animheader'} =  {loc =>  -1, num =>  1, size => 56, dnum => 1, name => "anim_header",  tmplt => "ffZ[32]llll"};
$structs{'animevents'} =  {loc =>   3, num =>  4, size => 36, dnum => 1, name => "anim_event",   tmplt => "fZ[32]"};

$structs{'nodeheader'} =  {loc =>  -1, num =>  1, size => 80, dnum => 1, name => "node_header",   tmplt => "SSSSllffffffflllllllll"};
$structs{'nodechildren'} ={loc =>  13, num => 14, size =>  4, dnum => 1, name => "node_children", tmplt => "l*"};

$structs{'subhead'}{'3k1'} =  {loc => -1, num => 1, size =>  92, dnum => 1, name => "light_header",     tmplt => "f[4]L[12]l*"};
#$structs{'subhead'}{'5k1'} =  {loc => -1, num => 1, size => 224, dnum => 1, name => "emitter_header",   tmplt => "f[3]L[5]Z[32]Z[32]Z[32]Z[32]Z[16]L[2]SCZ[37]"};
$structs{'subhead'}{'5k1'} =  {loc => -1, num => 1, size => 224, dnum => 1, name => "emitter_header",   tmplt => "f[3]L[5]Z[32]Z[32]Z[32]Z[32]Z[16]L[2]SCZ[32]CL"};
$structs{'subhead'}{'17k1'} = {loc => -1, num => 1, size => 36,  dnum => 1, name => "reference_header", tmplt => "Z[32]L"};
#$structs{'subhead'}{'33k1'} = {loc => -1, num => 1, size => 332, dnum => 1, name => "trimesh_header",   tmplt => "l[5]f[16]lZ[32]Z[32]l[19]f[6]l[13]SSSSSSf[2]ll"}; # kotor
$structs{'subhead'}{'33k1'} = {loc => -1, num => 1, size => 332, dnum => 1, name => "trimesh_header",   tmplt => "L[5]f[16]LZ[32]Z[32]Z[12]Z[12]L[9]l[3]C[8]lf[4]l[13]SSC[6]SfL[3]"}; # kotor
$structs{'subhead'}{'97k1'} = {loc => -1, num => 1, size => 432, dnum => 1, name => "skin_header",      tmplt => $structs{'subhead'}{'33k1'}->{tmplt} . 'l[16]S*'};
$structs{'subhead'}{'161k1'}= {loc => -1, num => 1, size => 388, dnum => 1, name => "animmesh_header",  tmplt => $structs{'subhead'}{'33k1'}->{tmplt} . 'fL[3]f[9]'};
$structs{'subhead'}{'289k1'}= {loc => -1, num => 1, size => 360, dnum => 1, name => "dangly_header",    tmplt => $structs{'subhead'}{'33k1'}->{tmplt} . 'l[3]f[3]l'};
$structs{'subhead'}{'545k1'} = {loc => -1, num => 1, size => 336, dnum => 1, name => "walkmesh_header", tmplt => $structs{'subhead'}{'33k1'}->{tmplt} . 'l'};
$structs{'subhead'}{'2081k1'}={loc => -1, num => 1, size => 352, dnum => 1, name => "saber_header",     tmplt => $structs{'subhead'}{'33k1'}->{tmplt} . 'l*'};

$structs{'subhead'}{'3k2'} =  {loc => -1, num => 1, size =>  92, dnum => 1, name => "light_header",    tmplt => "f[4]L[12]l*"};
#$structs{'subhead'}{'5k2'} =  {loc => -1, num => 1, size => 224, dnum => 1, name => "emitter_header",  tmplt => "f[3]L[5]Z[32]Z[32]Z[32]Z[32]Z[16]L[2]SCZ[37]"};
$structs{'subhead'}{'5k2'} =  {loc => -1, num => 1, size => 224, dnum => 1, name => "emitter_header",  tmplt => "f[3]L[5]Z[32]Z[32]Z[32]Z[32]Z[16]L[2]SCZ[32]CL"};
$structs{'subhead'}{'17k2'} = {loc => -1, num => 1, size => 36,  dnum => 1, name => "reference_header", tmplt => "Z[32]L"};
#$structs{'subhead'}{'33k2'} = {loc => -1, num => 1, size => 340, dnum => 1, name => "trimesh_header",  tmplt => "l[5]f[16]lZ[32]Z[32]l[19]f[6]l[13]SSSSSSf[2]llll"}; # kotor2
$structs{'subhead'}{'33k2'} = {loc => -1, num => 1, size => 340, dnum => 1, name => "trimesh_header",  tmplt => "L[5]f[16]LZ[32]Z[32]Z[12]Z[12]L[9]l[3]C[8]lf[4]l[13]SSC[6]SL[2]fL[3]"}; # kotor2
$structs{'subhead'}{'97k2'} = {loc => -1, num => 1, size => 440, dnum => 1, name => "skin_header",     tmplt => $structs{'subhead'}{'33k2'}->{tmplt} . 'l[16]S*'};
$structs{'subhead'}{'161k2'}= {loc => -1, num => 1, size => 396, dnum => 1, name => "animmesh_header", tmplt => $structs{'subhead'}{'33k2'}->{tmplt} . 'fL[3]f[9]'};
$structs{'subhead'}{'289k2'}= {loc => -1, num => 1, size => 368, dnum => 1, name => "dangly_header",   tmplt => $structs{'subhead'}{'33k2'}->{tmplt} . 'l[3]f[3]l'};
$structs{'subhead'}{'545k2'}= {loc => -1, num => 1, size => 344, dnum => 1, name => "walkmesh_header", tmplt => $structs{'subhead'}{'33k2'}->{tmplt} . 'l'};
$structs{'subhead'}{'2081k2'}={loc => -1, num => 1, size => 360, dnum => 1, name => "saber_header",    tmplt => $structs{'subhead'}{'33k2'}->{tmplt} . 'l*'};

$structs{'controllers'} =  {loc => 16, num => 17, size => 16, dnum => 9, name => "controllers",     tmplt => "lssssCCCC"};
$structs{'controllerdata'}={loc => 19, num => 20, size =>  4, dnum => 1, name => "controller_data", tmplt => "f*"};

$structs{'data'}{3}[0]={loc =>  1, num =>  2, size =>  0, dnum => 1, name => "unknown",          tmplt => "l*"};
$structs{'data'}{3}[1]={loc =>  4, num =>  5, size =>  0, dnum => 1, name => "flare_sizes",      tmplt => "f*"};
$structs{'data'}{3}[2]={loc =>  7, num =>  8, size =>  0, dnum => 1, name => "flare_pos",        tmplt => "f*"};
$structs{'data'}{3}[3]={loc => 10, num => 11, size =>  0, dnum => 1, name => "flare_color",      tmplt => "f*"};
$structs{'data'}{3}[4]={loc => 13, num => 14, size =>  0, dnum => 1, name => "texture_names",    tmplt => "C*"};
$structs{'data'}{33} = {loc => 78, num => 64, size => 12, dnum => 3, name => "vertcoords",       tmplt => "f*"};
$structs{'data'}{97} = {loc => 78, num => 64, size => 12, dnum => 3, name => "vertcoords",       tmplt => "f*"};
$structs{'data'}{289}= {loc => 78, num => 64, size => 12, dnum => 3, name => "vertcoords",       tmplt => "f*"};
$structs{'data'}{545}= {loc => 78, num => 64, size => 12, dnum => 3, name => "vertcoords",       tmplt => "f*"};
$structs{'data'}{2081}[0] = {loc => 78, num => 64, size => 12, dnum => 3, name => "vertcoords",  tmplt => "f*"};
$structs{'data'}{2081}[1] = {loc => 79, num => 64, size => 12, dnum => 3, name => "vertcoords2", tmplt => "f*"};
$structs{'data'}{2081}[2] = {loc => 80, num => 64, size =>  8, dnum => 2, name => "tverts+",     tmplt => "f*"};
$structs{'data'}{2081}[3] = {loc => 81, num => 64, size => 12, dnum => 2, name => "data2081-3",  tmplt => "f*"};

$structs{'mdxdata'}{33} = {loc => 77, num => 64, size => 24, dnum => 1, name => "mdxdata33",  tmplt => "f*"};
$structs{'mdxdata'}{97} = {loc => 77, num => 64, size => 56, dnum => 1, name => "mdxdata97",  tmplt => "f*"};
$structs{'mdxdata'}{545}= {loc => 77, num => 64, size => 24, dnum => 1, name => "mdxdata545", tmplt => "f*"};
$structs{'mdxdata'}{289}= {loc => 77, num => 64, size => 24, dnum => 1, name => "mdxdata289", tmplt => "f*"};

$structs{'darray'}[0] = {loc =>  2, num =>  3, size => 32, dnum =>  11, name => "faces",            tmplt => "fffflssssss"};
$structs{'darray'}[1] = {loc => 26, num => 27, size =>  4, dnum =>   1, name => "pntr_to_vert_num", tmplt => "l"};
$structs{'darray'}[2] = {loc => 29, num => 30, size =>  4, dnum =>   1, name => "pntr_to_vert_loc", tmplt => "l"};
$structs{'darray'}[3] = {loc => 32, num => 33, size =>  4, dnum =>   1, name => "array3",           tmplt => "l"};

#num and loc for darray4 are extracted from darray1 and darray2 respectively
$structs{'darray'}[4] = {loc => -1, num => -1, size =>  2, dnum =>   3, name => "vertindexes",  tmplt => "s*"};
$structs{'darray'}[5] = {loc => 84, num => 85, size =>  4, dnum =>   1, name => "bonemap",      tmplt => "f"};
$structs{'darray'}[6] = {loc => 86, num => 87, size => 16, dnum =>   4, name => "qbones",       tmplt => "f[4]"};
$structs{'darray'}[7] = {loc => 89, num => 90, size => 12, dnum =>   3, name => "tbones",       tmplt => "f[3]"};
$structs{'darray'}[8] = {loc => 92, num => 93, size =>  4, dnum =>   2, name => "array8",       tmplt => "SS"};
$structs{'darray'}[9] = {loc => 79, num => 80, size => 16, dnum =>   1, name => "constraints+", tmplt => "f[4]"};
$structs{'darray'}[10]= {loc => 79, num => -1, size => 40, dnum =>   6, name => "aabb",         tmplt => "ffffffllll"};

our %nodelookup = ('dummy' => 1, 'light' => 3, 'emitter' => 5, 'reference' => 17, 'trimesh' => 33,
                   'skin' => 97, 'animmesh' => 161, 'danglymesh' => 289, 'aabb' => 545, 'lightsaber' => 2081);

our %classification = ('Effect' => 0x01, 'Tile' => 0x02, 'Character' => 0x04,
                       'Door' => 0x08, 'Lightsaber' => 0x10, 'Placeable' => 0x20,
                       'Flyer' => 0x40, 'Other' => 0x00);

our %reversenode  = reverse %nodelookup;
our %reverseclass = reverse %classification;

# MDX Row data bitmap masks
# The common mesh header contains offsets for 11 different potential row fields,
# 7 have been identified, 6 are (thought) unused in kotor games, 4 are unknown.
use constant MDX_VERTICES               => 0x00000001;
use constant MDX_TEX0_VERTICES          => 0x00000002;
use constant MDX_TEX1_VERTICES          => 0x00000004;
use constant MDX_TEX2_VERTICES          => 0x00000008; # unconfirmed
use constant MDX_TEX3_VERTICES          => 0x00000010; # unconfirmed
use constant MDX_VERTEX_NORMALS         => 0x00000020;
#use constant MDX_???                    => 0x00000040; # unknown
use constant MDX_VERTEX_COLORS          => 0x00000040; # unconfirmed
use constant MDX_TANGENT_SPACE          => 0x00000080;
#use constant MDX_???                    => 0x00000100; # unknown
#use constant MDX_???                    => 0x00000200; # unknown
#use constant MDX_???                    => 0x00000400; # unknown
# Type-specific MDX row data:
# the following are all 'made up' and do not appear in vanilla MDXDataBitmap fields,
# they are set while reading type-specific sub-headers from binary models
# so that the MDXDataBitmap will contain a full view of MDX row data
# Skin mesh:
use constant MDX_BONE_WEIGHTS           => 0x00000800;
use constant MDX_BONE_INDICES           => 0x00001000;

# MDX Row definitions
#  bitfield: the mdxdatabitmap value for the data
#  num: the number of floats composing the data
#  offset_i: the index of the data into an array of 11 mdx offsets in the common mesh header (ascii read)
#  offset: the key where the data's row offset is stored in a node (when read from binary)
#  data: the key where the data should be stored in a node (when read from binary)
$structs{'mdxrows'} = [
  { bitfield => MDX_VERTICES,       num => 3, offset_i => 0,  offset => 'mdxvertcoordsloc',  data => 'verts' },
  { bitfield => MDX_VERTEX_NORMALS, num => 3, offset_i => 1,  offset => 'mdxvertnormalsloc', data => 'vertexnormals' },
  { bitfield => MDX_TEX0_VERTICES,  num => 2, offset_i => 3,  offset => 'mdxtex0vertsloc',   data => 'tverts' },
  { bitfield => MDX_TEX1_VERTICES,  num => 2, offset_i => 4,  offset => 'mdxtex1vertsloc',   data => 'tverts1' },
  { bitfield => MDX_TEX2_VERTICES,  num => 2, offset_i => 5,  offset => 'mdxtex2vertsloc',   data => 'tverts2' },
  { bitfield => MDX_TEX3_VERTICES,  num => 2, offset_i => 6,  offset => 'mdxtex3vertsloc',   data => 'tverts3' },
  { bitfield => MDX_VERTEX_COLORS,  num => 3, offset_i => 2,  offset => 'mdxvertcolorsloc',  data => 'colors' },
  { bitfield => MDX_TANGENT_SPACE,  num => 9, offset_i => 7,  offset => 'mdxtanspaceloc',    data => 'tangentspace' },
  { bitfield => MDX_BONE_WEIGHTS,   num => 4, offset_i => -1, offset => 'mdxboneweightsloc', data => 'boneweights' },
  { bitfield => MDX_BONE_INDICES,   num => 4, offset_i => -1, offset => 'mdxboneindicesloc', data => 'boneindices' },
];

# Node Type bitmasks
# Types are combinations of these, use for bitwise logic comparisons
use constant NODE_HAS_HEADER    => 0x00000001;
use constant NODE_HAS_LIGHT     => 0x00000002;
use constant NODE_HAS_EMITTER   => 0x00000004;
use constant NODE_HAS_CAMERA    => 0x00000008;
use constant NODE_HAS_REFERENCE => 0x00000010;
use constant NODE_HAS_MESH      => 0x00000020;
use constant NODE_HAS_SKIN      => 0x00000040;
use constant NODE_HAS_ANIM      => 0x00000080;
use constant NODE_HAS_DANGLY    => 0x00000100;
use constant NODE_HAS_AABB      => 0x00000200;
use constant NODE_HAS_SABER     => 0x00000800;

# node types quick reference
# dummy =       NODE_HAS_HEADER =                                   0x001 = 1
# light =       NODE_HAS_HEADER + NODE_HAS_LIGHT =                  0x003 = 3
# emitter =     NODE_HAS_HEADER + NODE_HAS_EMITTER =                0x005 = 5
# reference =   NODE_HAS_HEADER + NODE_HAS_REFERENCE =              0x011 = 17
# mesh =        NODE_HAS_HEADER + NODE_HAS_MESH =                   0x021 = 33
# skin mesh =   NODE_HAS_SKIN + NODE_HAS_MESH + NODE_HAS_HEADER =   0x061 = 97
# anim mesh =   NODE_HAS_ANIM + NODE_HAS_MESH + NODE_HAS_HEADER =   0x0a1 = 161
# dangly mesh = NODE_HAS_DANGLY + NODE_HAS_MESH + NODE_HAS_HEADER = 0x121 = 289
# aabb mesh =   NODE_HAS_AABB + NODE_HAS_MESH + NODE_HAS_HEADER =   0x221 = 545
# saber mesh =  NODE_HAS_SABER + NODE_HAS_MESH + NODE_HAS_HEADER =  0x821 = 2081

# Node Type constants
# These are still used directly sometimes and should be retained for code legibility
use constant NODE_DUMMY         => 1;
use constant NODE_LIGHT         => 3;
use constant NODE_EMITTER       => 5;
use constant NODE_REFERENCE     => 17;
use constant NODE_TRIMESH       => 33;
use constant NODE_SKIN          => 97;
use constant NODE_DANGLYMESH    => 289;
use constant NODE_AABB          => 545;
use constant NODE_SABER         => 2081;

# index controllers by node type, since at least one (100) is used twice... gee, thanks, Bioware.
# note that I'm copying emitter and light information from the NWN model format (ie Torlack's NWNMdlComp).  Hopefully it's compatible...
our %controllernames;

$controllernames{+NODE_HAS_HEADER}{8}   = "position";
$controllernames{+NODE_HAS_HEADER}{20}  = "orientation";
$controllernames{+NODE_HAS_HEADER}{36}  = "scale";
$controllernames{+NODE_HAS_HEADER}{132} = "alpha"; # was 128

# got rid of this name because scale was already hardcoded elsewhere
#$controllernames{+NODE_HAS_HEADER}{36}  = "scaling";

# notes from fx_flame01.mdl:
# should be no wirecolor.  missed shadowradius (should be 5). radius, color fine. 
# lightpriority is 5 instead of 4? need: flareradius 30, texturenames 1 _ fxpa_flare, flaresizes 1 _ 3, flarepositions 1 _ 1,
# flarecolorshifts 1 _ 0 0 0.  where did flare 0 come from? missed verticaldisplacement (should be 2).  somehow the nwn model has shadowradius 5 and shadowradius 15.

$controllernames{+NODE_HAS_LIGHT}{76}  = "color";
$controllernames{+NODE_HAS_LIGHT}{88}  = "radius";
$controllernames{+NODE_HAS_LIGHT}{96}  = "shadowradius";
$controllernames{+NODE_HAS_LIGHT}{100} = "verticaldisplacement";
$controllernames{+NODE_HAS_LIGHT}{140} = "multiplier";

# nodes on emitter data: thread called "New/Updated/Corrected Semi Complete Emitter Information by Danmar and BigfootNZ
# http://nwn.bioware.com/forums/viewtopic.html?topic=241936&forum=48
# looks like emitter controllers have been changed around.  changes are guesses based on comparing fx_flame01.mdl...
# thankfully they recompiled at least one model with the new controllers. :)
#fx_flame01.mdl includes these controllers:
# in Flame: 8, 20, 392, 380, 84, 80, 144, 148, 152, 156, 112, 108, 88, 120, 124, 160, 136, 168, 140, 104, 172, 176, 92, 180,
#           184, 188, 192, 128, 132, 96, 100, 116, 164
#should be no alpha.

$controllernames{+NODE_HAS_EMITTER}{80}   = "alphaEnd"; 	# same
$controllernames{+NODE_HAS_EMITTER}{84}   = "alphaStart";	# same - fx_flame01
$controllernames{+NODE_HAS_EMITTER}{88}   = "birthrate"; 	# same - fx_flame01
$controllernames{+NODE_HAS_EMITTER}{92}   = "bounce_co";
$controllernames{+NODE_HAS_EMITTER}{96}   = "combinetime"; 	# was 120
$controllernames{+NODE_HAS_EMITTER}{100}  = "drag";
$controllernames{+NODE_HAS_EMITTER}{104}  = "fps";      	# was 128 - fx_flame01
$controllernames{+NODE_HAS_EMITTER}{108}  = "frameEnd"; 	# was 132 - fx_flame01
$controllernames{+NODE_HAS_EMITTER}{112}  = "frameStart"; 	# was 136
$controllernames{+NODE_HAS_EMITTER}{116}  = "grav";		# was 140
$controllernames{+NODE_HAS_EMITTER}{120}  = "lifeExp";  	# was 144 - fx_flame01 (why did I have 240?)
$controllernames{+NODE_HAS_EMITTER}{124}  = "mass";     	# was 148 -> fx_flame01
$controllernames{+NODE_HAS_EMITTER}{128}  = "p2p_bezier2"; 	# was 152
$controllernames{+NODE_HAS_EMITTER}{132}  = "p2p_bezier3"; 	# was 156
$controllernames{+NODE_HAS_EMITTER}{136}  = "particleRot"; 	# was 160
$controllernames{+NODE_HAS_EMITTER}{140}  = "randvel";    	# was 164 - fx_flame01
$controllernames{+NODE_HAS_EMITTER}{144}  = "sizeStart";  	# was 168 - fx_flame01
$controllernames{+NODE_HAS_EMITTER}{148}  = "sizeEnd";    	# was 172 - fx_flame01 (mass same value)
$controllernames{+NODE_HAS_EMITTER}{152}  = "sizeStart_y"; 	# was 176
$controllernames{+NODE_HAS_EMITTER}{156}  = "sizeEnd_y";  	# was 180
$controllernames{+NODE_HAS_EMITTER}{160}  = "spread";     	# was 184
$controllernames{+NODE_HAS_EMITTER}{164}  = "threshold";  	# was 188
$controllernames{+NODE_HAS_EMITTER}{168}  = "velocity";   	# was 192 - fx_flame01
$controllernames{+NODE_HAS_EMITTER}{172}  = "xsize";      	# was 196
$controllernames{+NODE_HAS_EMITTER}{176}  = "ysize";      	# was 200
$controllernames{+NODE_HAS_EMITTER}{180}  = "blurlength"; 	# was 204 - fx_flame01
$controllernames{+NODE_HAS_EMITTER}{184}  = "lightningDelay"; 	# was 208
$controllernames{+NODE_HAS_EMITTER}{188}  = "lightningRadius"; 	# was 212
$controllernames{+NODE_HAS_EMITTER}{192}  = "lightningScale"; 	# was 216
$controllernames{+NODE_HAS_EMITTER}{196}  = "lightningSubDiv";	#
$controllernames{+NODE_HAS_EMITTER}{200}  = "lightningzigzag";	#
$controllernames{+NODE_HAS_EMITTER}{216}  = "alphaMid";   	# was 464
$controllernames{+NODE_HAS_EMITTER}{220}  = "percentStart"; 	# was 480
$controllernames{+NODE_HAS_EMITTER}{224}  = "percentMid"; 	# was 481
$controllernames{+NODE_HAS_EMITTER}{228}  = "percentEnd"; 	# was 482
$controllernames{+NODE_HAS_EMITTER}{232}  = "sizeMid";    	# was 484
$controllernames{+NODE_HAS_EMITTER}{236}  = "sizeMid_y";   	# was 488
$controllernames{+NODE_HAS_EMITTER}{240}  = "m_fRandomBirthRate"; #
$controllernames{+NODE_HAS_EMITTER}{252}  = "targetsize"; 	#
$controllernames{+NODE_HAS_EMITTER}{256}  = "numcontrolpts"; 	#
$controllernames{+NODE_HAS_EMITTER}{260}  = "controlptradius";	#
$controllernames{+NODE_HAS_EMITTER}{264}  = "controlptdelay"; 	#
$controllernames{+NODE_HAS_EMITTER}{268}  = "tangentspread"; 	#
$controllernames{+NODE_HAS_EMITTER}{272}  = "tangentlength"; 	#
$controllernames{+NODE_HAS_EMITTER}{284}  = "colorMid"; 	# was 468
$controllernames{+NODE_HAS_EMITTER}{380}  = "colorEnd"; 	# was 96 - fx_flame01
$controllernames{+NODE_HAS_EMITTER}{392}  = "colorStart"; 	# was 108 - fx_flame01
$controllernames{+NODE_HAS_EMITTER}{502}  = "detonate"; 	# was 228

$controllernames{+NODE_HAS_MESH}{100} = "selfillumcolor";


##########################################################
# read in the first 4 bytes of a file to see if the model is
# binary or ascii
sub modeltype
{
    my ($filepath) = (@_);
    my ($fh, $buffer);
  
    MDLOpsM::File::open(\$fh, '<', $filepath) or die "can't open MDL file: $filepath\n";
    binmode($fh);
    seek($fh, 0, 0);

    # read in the first 4 bytes of the file
    read($fh, $buffer, 4);
    MDLOpsM::File::close($fh);
  
    # if the first 4 bytes of the file are nulls we have a binary model
    # else we have an ascii model
    if ($buffer eq "\000\000\000\000")
    {
        return "binary";
    }
    else
    {
        return "ascii";
    }
}

##########################################################
# read in the first 4 bytes of the geometry header to see if the model is
# kotor 1 or kotor 2
sub modelversion
{
    my ($filepath) = (@_);
    my ($fh, $buffer);
  
    MDLOpsM::File::open(\$fh, '<', $filepath) or die "can't open MDL file: $filepath\n";
    binmode($fh);
    seek($fh, 12, 0);

    # read in the first 4 bytes of the geometry header
    read($fh, $buffer, 4);
    MDLOpsM::File::close($fh);
  
    if (unpack("l",$buffer) eq 4285200)
    {
        return "k2";
    }
    else
    {
        return "k1";
    }
}
##############################################################
# calculate a face's surface area
#
sub facearea
{
  my ($v1, $v2, $v3) = (@_);

  my ($a, $b, $c, $s);

  $a = sqrt(($v1->[0] - $v2->[0]) ** 2 +
            ($v1->[1] - $v2->[1]) ** 2 +
            ($v1->[2] - $v2->[2]) ** 2);

  $b = sqrt(($v1->[0] - $v3->[0]) ** 2 +
            ($v1->[1] - $v3->[1]) ** 2 +
            ($v1->[2] - $v3->[2]) ** 2);

  $c = sqrt(($v2->[0] - $v3->[0]) ** 2 +
            ($v2->[1] - $v3->[1]) ** 2 +
            ($v2->[2] - $v3->[2]) ** 2);

  $s = ($a + $b + $c) / 2;

  my $inter = $s * ($s - $a) * ($s - $b) * ($s - $c);

  return $inter > 0.0 ? sqrt($inter) : 0.0;
}
##############################################################
# calculate a face's normalized normal vector and plane distance
#
sub facenormal
{
  my ($v1, $v2, $v3) = (@_);
  my $normal;
  my $pd;
  $normal = [
    $v1->[1] * ($v2->[2] - $v3->[2]) + $v2->[1] * ($v3->[2] - $v1->[2]) + $v3->[1] * ($v1->[2] - $v2->[2]),
    $v1->[2] * ($v2->[0] - $v3->[0]) + $v2->[2] * ($v3->[0] - $v1->[0]) + $v3->[2] * ($v1->[0] - $v2->[0]),
    $v1->[0] * ($v2->[1] - $v3->[1]) + $v2->[0] * ($v3->[1] - $v1->[1]) + $v3->[0] * ($v1->[1] - $v2->[1]),
  ];
  $pd = (-1.0 * $v1->[0]) * ($v2->[1] * $v3->[2] - $v3->[1] * $v2->[2]) -
        $v2->[0] * ($v3->[1] * $v1->[2] - $v1->[1] * $v3->[2]) -
        $v3->[0] * ($v1->[1] * $v2->[2] - $v2->[1] * $v1->[2]);
  my $norm_factor = sqrt($normal->[0]**2 + $normal->[1]**2 + $normal->[2]**2);
  if ($norm_factor != 0.0) {
    $pd /= $norm_factor;
  }
  return ($pd, $normal);
}


##############################################################
# calculate a patch's vertex normal vector
#
sub patchnormal {
  my ($model, $pos_data, $mode) = @_;
  #print Dumper(keys %model);
  #print Dumper($pos_data);
  if (!defined($mode)) {
    # mode = area, angle, both, none
    $mode = 'area';
  }
  # translate to world space orientation
  my $vertnorm = &quaternion_apply(
    $model->{nodes}{$pos_data->{mesh}}{transform}{orientation},
    $model->{nodes}{$pos_data->{mesh}}{vertexnormals}[$pos_data->{vertex}]
  );
  my $testnorm = [ 0.0, 0.0, 0.0 ];
  for my $face_index (@{$pos_data->{faces}}) {
    # this one is normalized...
    # translate to world space orientation
    my $facenorm = &quaternion_apply(
      $model->{nodes}{$pos_data->{mesh}}{transform}{orientation},
      [ @{$model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index]}[0..2] ]
    );
#            my $facenorm = facenormal(
#              @{$model->{nodes}{$pos_data->{mesh}}{verts}}[
#                @{$model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index]}[8..10]
#              ]
#            );
    my $facearea = 1.0;
    if ($mode eq 'area' || $mode eq 'both') {
      $facearea = facearea(
        @{$model->{nodes}{$pos_data->{mesh}}{verts}}[
          @{$model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index]}[8..10]
        ]
      );
    }
    my $angle = 1.0;
    if ($mode eq 'angle' || $mode eq 'both') {
      if (vertex_equals(
        $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[$pos_data->{vertex}],
        $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[
          $model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index][8]
        ], 4
      )) {
        $angle = compute_vertex_angle(
          $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[
            $model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index][8]
          ],
          $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[
            $model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index][9]
          ],
          $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[
            $model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index][10]
          ]
        );
      } elsif (vertex_equals(
        $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[$pos_data->{vertex}],
        $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[
          $model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index][9]
        ], 4
      )) {
        $angle = compute_vertex_angle(
          $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[
            $model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index][9]
          ],
          $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[
            $model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index][8]
          ],
          $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[
            $model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index][10]
          ]
        );
      } elsif (vertex_equals(
        $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[$pos_data->{vertex}],
        $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[
          $model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index][10]
        ], 4
      )) {
        $angle = compute_vertex_angle(
          $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[
            $model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index][10]
          ],
          $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[
            $model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index][8]
          ],
          $model->{'nodes'}{$pos_data->{mesh}}{transform}{'verts'}[
            $model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index][9]
          ]
        );
      }
    }
    #print Dumper($facenorm);
    #print Dumper([
    #  @{$model->{nodes}{$pos_data->{mesh}}{Bfaces}[$face_index]}[8..10]
    #]);
    #printf("mesh %u face %u area %.5g\n", $pos_data->{mesh}, $face_index, $facearea);
    $testnorm = [ map {
      $testnorm->[$_] += ($facearea * $angle * $facenorm->[$_]);
    } (0..2) ];
    #print Dumper($testnorm);
  }
  #print "final norm for group:\n";
  #$testnorm = normalize_vector($testnorm);
  return $testnorm;
}


##############################################################
# test whether a particular edge bounds a smoothing island
#
sub boundary_check {
  my ($pgs, $edge_idx, $edge_faces, $edge_endpoints) = @_;
  #print "edge boundary: $edge_idx\n";
  my $ef = $edge_faces->[$edge_idx];
  if (scalar @{$ef} < 2) { return 1; }
  my $ep = $edge_endpoints->[$edge_idx];
  #print Dumper($ef);
  #print Dumper($ep->[0]);
  #print Dumper($ep->[1]);
  #print Dumper($pgs->{$ep->[0]});
  #print Dumper($pgs->{$ep->[1]});
  if ((!defined($pgs->{$ep->[0]}) || scalar @{$pgs->{$ep->[0]}} < 2) &&
      (!defined($pgs->{$ep->[1]}) || scalar @{$pgs->{$ep->[1]}} < 2)) { return 0; }
  my ($ega, $egb) = ([], []);
  defined($pgs->{$ep->[0]}) and $ega = [ @{$pgs->{$ep->[0]}} ];
  defined($pgs->{$ep->[1]}) and $egb = [ @{$pgs->{$ep->[1]}} ];
  #print "ega ".Dumper($ega);
  #print Dumper([
  #  grep { scalar(grep { $ef->[0] == $_ } @{$ega->[$_]}) ||
  #         scalar(grep { $ef->[1] == $_ } @{$ega->[$_]}) } keys @{$ega}
  #]);
  if (scalar(
    grep { scalar(grep { $ef->[0] == $_ } @{$ega->[$_]}) ||
           scalar(grep { $ef->[1] == $_ } @{$ega->[$_]}) } keys @{$ega}
  ) > 1) { return 1; }
  if (scalar(
    grep { scalar(grep { $ef->[0] == $_ } @{$egb->[$_]}) ||
           scalar(grep { $ef->[1] == $_ } @{$egb->[$_]}) } keys @{$egb}
  ) > 1) { return 1; }
  return 0;
}


##############################################################
# based on Math::Subsets::List
# but different because it just returns a set of combinations
# so we can actually return/next out of it reasonably
sub combinations {
  my $l = 0;
  my @p = ();
  my @P = @_;
  my $n = scalar(@P);
  my $list = [];

  # limit of 12 here is semi-reasonable for a precomputed factorial list
  # 12 takes < 1 second, 14 takes 12 seconds, more...
  if ($n > 16) {
    print "Truncated $n! combinations needed...\n";
    $n = 16;
  }

  my $p; $p = sub {
    if ($l < $n) {
      ++$l;
      &$p();
      push @p, $P[$l-1];
      &$p();
      pop @p;
      --$l
    } elsif (scalar(@p)) {
      #print "$l \n";
      #print "p @p\n";
      #$list = [ @{$list}, [ @p ] ];
      push(@{$list}, [ @p ]);
    }
    return $list;
  };
  $list = &$p;
  $p = undef;

  return @{$list};
}


##############################################################
# reduce vector diff to single float score
sub score_vector {
  my ($test_vector, $ref_vector) = @_;
  my $score = 0.0;
  my $work = [ 0.0 x scalar(@{$ref_vector}) ];
  for my $test_key (0..scalar(@{$ref_vector}) - 1) {
    if (!defined($test_vector->[$test_key])) {
      last;
    }
    $work->[$test_key] = abs($ref_vector->[$test_key] - $test_vector->[$test_key]);
  }
  map { $score += $_ } @{$work};
  return $score;
}


##############################################################
#read in a binary model
#
sub readbinarymdl
{
    my ($buffer, $extractanims, $version, $options) = (@_);
    my %model;
    my ($temp, $file, $filepath, %bitmaps);

    # handle options, fill in default values
    if (!defined($options)) {
      $options = {};
    }
    # write animations in ascii model
    if (!defined($options->{extract_anims})) {
      #$options->{extract_anims} = 1;
      # once the UI is updated, remove legacy params
      $options->{extract_anims} = $extractanims;
    }
    # compute real smoothgroup numbers for visible meshes
    # default value is on
    if (!defined($options->{compute_smoothgroups})) {
      $options->{compute_smoothgroups} = 1;
    }
    # weld model vertices
    # default value is off
    if (!defined($options->{weld_model})) {
      $options->{weld_model} = 0;
    }
    # read the mdx file
    # default value is on (used for supermodel loading)
    if (!defined($options->{use_mdx})) {
      $options->{use_mdx} = 1;
    }


    #extract just the name of the model
    $buffer =~ /(.*[\\\/])*(.*)\.mdl/i;
    $file = $2;
    $model{'filename'} = $2;
  
    $buffer =~ /(.*)\.mdl/i;
    $filepath = $1;

    MDLOpsM::File::open(\*MODELMDL, '<', $filepath.".mdl") or die "can't open MDL file: $filepath\n";
    binmode(MODELMDL);

    if ($options->{use_mdx}) {
      MDLOpsM::File::open(\*MODELMDX, '<', $filepath.".mdx") or die "can't open MDX file\n";
      binmode(MODELMDX);
    }

    $model{'source'} = "binary";
    $model{'filepath+name'} = $filepath;
  
    #read in the geometry header
    seek(MODELMDL, $structs{'geoheader'}{'loc'},0);
    print("$structs{'geoheader'}{'name'} " . tell(MODELMDL)) if $printall;

    $model{'geoheader'}{'start'} = tell(MODELMDL);
    read(MODELMDL, $buffer, 80);
    print(" " . (tell(MODELMDL) - 1) . "\n") if $printall;

    $model{'geoheader'}{'end'} = tell(MODELMDL)-1;
    $model{'geoheader'}{'raw'} = $buffer;
    $model{'geoheader'}{'unpacked'} = [unpack($structs{'geoheader'}{'tmplt'}, $buffer)];
    $model{'name'} = $model{'geoheader'}{'unpacked'}[2];
    $model{'rootnode'} = $model{'geoheader'}{'unpacked'}[3];
    $model{'totalnumnodes'} = $model{'geoheader'}{'unpacked'}[4];
    $model{'modeltype'} = $model{'geoheader'}{'unpacked'}[12];

    #read in the model header
    print("$structs{'modelheader'}{'name'} " .tell(MODELMDL)) if $printall;
    $model{'modelheader'}{'start'} = tell(MODELMDL);
    read(MODELMDL, $buffer, $structs{'modelheader'}{'size'});
    print(" " . (tell(MODELMDL) - 1) . "\n") if $printall;

    $model{'modelheader'}{'end'} = tell(MODELMDL)-1;
    $model{'modelheader'}{'raw'} = $buffer;
    $model{'modelheader'}{'unpacked'} = [unpack($structs{'modelheader'}{'tmplt'}, $buffer)];
    $model{'classification'} = $reverseclass{$model{'modelheader'}{'unpacked'}[0]};
    $model{'classification_unk1'} = $model{'modelheader'}{'unpacked'}[1];
    $model{'ignorefog'} = !$model{'modelheader'}{'unpacked'}[3];
    $model{'animstart'} = $model{'modelheader'}{'unpacked'}[5];
    $model{'numanims'} = $model{'modelheader'}{'unpacked'}[6];
    $model{'bmin'} = [@{$model{'modelheader'}{'unpacked'}}[9..11]];
    $model{'bmax'} = [@{$model{'modelheader'}{'unpacked'}}[12..14]];
    $model{'radius'} = $model{'modelheader'}{'unpacked'}[15];
    $model{'animationscale'} = $model{'modelheader'}{'unpacked'}[16];
    $model{'supermodel'} = $model{'modelheader'}{'unpacked'}[17];
    $model{'node1'} = $model{'modelheader'}{'unpacked'}[18];
  
  #$structs{'modelheader'} = {loc =>  92, num =>  1, size => 88, dnum => 1, name => "model_header", tmplt => "CCCClllllffffffffZ[32]"};

    #read in the part name array header
    seek(MODELMDL, $structs{'nameheader'}{'loc'},0);
    print("$structs{'nameheader'}{'name'} " . tell(MODELMDL)) if $printall;
    $model{'nameheader'}{'start'} = tell(MODELMDL);

    read(MODELMDL, $buffer, $structs{'nameheader'}{'size'});
    print(" " . (tell(MODELMDL) - 1) . "\n") if $printall;
    $model{'nameheader'}{'end'} = tell(MODELMDL)-1;
    $model{'nameheader'}{'raw'} = $buffer;
    $model{'nameheader'}{'unpacked'} = [unpack($structs{'nameheader'}{'tmplt'}, $buffer)];
  
    #read in the part name array indexes
    $temp = $model{'nameheader'}{'unpacked'}[$structs{'nameindexes'}{'loc'}] + 12;
    seek(MODELMDL, $temp, 0);
    print("$structs{'nameindexes'}{'name'} " . tell(MODELMDL)) if $printall;

    $model{'nameindexes'}{'start'} = tell(MODELMDL);
    read(MODELMDL, $buffer, $structs{'nameindexes'}{'size'} * $model{'nameheader'}{'unpacked'}[$structs{'nameindexes'}{'num'}]);
    print(" " . (tell(MODELMDL) - 1) . "\n") if $printall;

    $model{'nameindexes'}{'end'} = tell(MODELMDL)-1;
    $model{'nameindexes'}{'raw'} = $buffer;
    $model{'nameindexes'}{'unpacked'} = [unpack($structs{'nameindexes'}{'tmplt'}, $buffer)];

    #read in the part names
    $temp = tell(MODELMDL);
    $model{'names'}{'start'} = tell(MODELMDL);
    print("Array_names $temp") if $printall;

    read(MODELMDL, $buffer, $model{'modelheader'}{'unpacked'}[ANIMROOT] - ($model{'nameheader'}{'unpacked'}[4] + (4 * $model{'nameheader'}{'unpacked'}[5])));
    print(" " . (tell(MODELMDL) - 1) . "\n") if $printall;

    $model{'names'}{'end'} = tell(MODELMDL)-1;
    $model{'names'}{'raw'} = $buffer;
    $model{'partnames'} = [unpack($structs{'names'}{'tmplt'} x $model{'nameheader'}{'unpacked'}[5], $buffer)];

    $temp = 0;
    foreach ( @{$model{'partnames'}} )
    {
        $model{'nodeindex'}{lc($_)} = $temp++;
    }
  
    #read in the geometry nodes
    $model{'nodes'} = {};
    $model{'nodes'}{'truenodenum'} = 0;
    # $tree, $parent, $startnode, $model, $version

    # pre-walk geometry nodes to get node order, may differ from name order
    getnodeorder(\%model, $model{'geoheader'}{'unpacked'}[ROOTNODE]);
    #print Dumper($model{order2nameindex});

    $temp = getnodes('nodes', undef, $model{'geoheader'}{'unpacked'}[ROOTNODE], \%model, $version);

    # test whether model root node points at "first" node
    if ($model{node1} != $model{rootnode}) {
      # model root node points to a subnode in the hierarchy, this is a head model
      $model{headlink} = 1;
    }
    printf "%u %u\n", $model{'node1'}, $model{'rootnode'} if $printall;

    #$options->{compute_smoothgroups} = 1;
    #$options->{weld_model} = 1;
    # compute the data structures for smoothgroup number detection/computation
    # and producing models with vertices welded
    my $face_by_pos = {};
    #my $pos_by_face = {};
    # face map, a flattened list, index => "mesh_index.face_index"
    my $face_map = {};
    # face map inverted, "mesh_index.face_index" => index
    my $face_map_inv = {};
    # edge user faces, indices are edge index
    my $edge_faces = [];
    # edge vertex endpoint positions, indices are edge index
    my $edge_endpoints = [];
    # edges by face, "mesh_index.face_index" => edge_index
    my $face_edges = {};
    if ($options->{compute_smoothgroups} ||
        $options->{weld_model}) {
        # construct node global position/orientation transforms
        for (my $i = 0; $i < $model{'nodes'}{'truenodenum'}; $i++) {
            my $ancestry = [ $i ];
            my $parent = $model{'nodes'}{$i};
            # walk up to the root from the node, prepending each ancestor node number
            # so that we get a flat list of children from root to node
            while ($parent->{'parentnodenum'} != -1 &&
                   !($parent->{'parent'} =~ /^null$/i)) {
                $ancestry = [ $parent->{'parentnodenum'}, @{$ancestry} ];
                $parent = $model{'nodes'}{$parent->{'parentnodenum'}};
            }
            # initialize the node's transform structure which contains
            # the model-global position and orientation, and,
            # a list of transformed vertex positions
            $model{'nodes'}{$i}{transform} = {
                position    => [ 0.0, 0.0, 0.0 ],
                orientation => [ 0.0, 0.0, 0.0, 1.0 ],
                verts       => []
            };
            for my $ancestor (@{$ancestry}) {
                if (defined($model{'nodes'}{$ancestor}{'Bcontrollers'}) &&
                    defined($model{'nodes'}{$ancestor}{'Bcontrollers'}{8})) {
                    # node has a position, add it to current value
                    map { $model{'nodes'}{$i}{transform}{position}->[$_] +=
                          $model{'nodes'}{$ancestor}{Bcontrollers}{8}{values}->[0][$_] } (0..2);
                }
                if (defined($model{'nodes'}{$ancestor}{'Bcontrollers'}) &&
                    defined($model{'nodes'}{$ancestor}{'Bcontrollers'}{20})) {
                    # node has an orientation, multiply quaternions to combine orientations
                    $model{'nodes'}{$i}{transform}{orientation} = &quaternion_multiply(
                        $model{'nodes'}{$i}{transform}{orientation},
                        $model{'nodes'}{$ancestor}{'Bcontrollers'}{20}{values}->[0]
                    );
                }
            }
        }
        # construct vertex position index
        for (my $i = 0; $i < $model{'nodes'}{'truenodenum'}; $i++) {
            if (!($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH) ||
                ($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER) ||
                ($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_AABB) ||
                !($model{'nodes'}{$i}{render}))
            {
                next;
            }
            # add mesh faces to flat mesh.face indexed maps
            for my $face_index (keys @{$model{'nodes'}{$i}{'Bfaces'}}) {
              my $map_index = scalar keys %{$face_map};
              $face_map->{$map_index} = "$i.$face_index";
              $face_map_inv->{"$i.$face_index"} = $map_index;
            }
            # step through the vertices, storing the index in $work
            for my $work (keys @{$model{'nodes'}{$i}{'verts'}})
            {
                # apply rotation to the vertex position
                my $vert_pos = &quaternion_apply($model{'nodes'}{$i}{transform}{orientation},
                                                 $model{'nodes'}{$i}{'verts'}[$work]);
                # add position (this effectively makes the previous rotation around this point)
                $vert_pos = [
                    map { $model{'nodes'}{$i}{transform}{position}->[$_] + $vert_pos->[$_] } (0..2)
                ];
                # store translated vertex position
                $model{'nodes'}{$i}{transform}{verts}->[$work] = $vert_pos;
                # generate string key based on translated vertex position
                my $vert_key = sprintf('%.4g,%.4g,%.4g', @{$vert_pos});
                if (!defined($face_by_pos->{$vert_key})) {
                    $face_by_pos->{$vert_key} = [];
                }
                if (!defined($model{'nodes'}{$i}{'vertfaces'}{$work})) {
                    $model{'nodes'}{$i}{'vertfaces'}{$work} = [];
                }
                # append this vertex's data to the data list for this position
                push(@{$face_by_pos->{$vert_key}},
                    {
                        mesh  => $i,
                        #meshname => $model{partnames}[$i],
                        faces => [ @{$model{'nodes'}{$i}{'vertfaces'}{$work}} ],
                        vertex => $work,
                        vertex_key => $vert_key,
                    }
                );
                #$pos_by_face->{"$i.$work"} = $face_by_pos->{$vert_key};
            }
        }
        #use Time::HiRes qw(gettimeofday);
        #printf "index edges %u\n", ((scalar keys %{$face_map}) - 0) * 3;
        #my $t0 = [gettimeofday];
        for my $edge_index (0..((scalar keys %{$face_map}) - 0) * 3 - 1) {
            my $face_index = int($edge_index / 3);
            my $edge_face_index = $edge_index % 3;
            my ($mesh, $face) = split(/\./, $face_map->{$face_index});
            #print "$edge_index $face_index $mesh $face\n";
            my $edge_vert_indices = [
                $model{'nodes'}{$mesh}{'Bfaces'}[$face][8 + $edge_face_index ],
                $model{'nodes'}{$mesh}{'Bfaces'}[$face][8 + $edge_face_index + ($edge_face_index == 2 ? -2 : 1)]
            ];
            my $edge_vert_positions = [
                sprintf('%.4g,%.4g,%.4g', @{$model{'nodes'}{$mesh}{transform}{verts}[$edge_vert_indices->[0]]}),
                sprintf('%.4g,%.4g,%.4g', @{$model{'nodes'}{$mesh}{transform}{verts}[$edge_vert_indices->[1]]})
            ];
            my $edge_vert_faces = [
                { map { my $m = $_->{mesh}; map { ("$m.$_" => 1) } @{$_->{faces}} }
                  @{$face_by_pos->{$edge_vert_positions->[0]}} },
                { map { my $m = $_->{mesh}; map { ("$m.$_" => 1) } @{$_->{faces}} }
                  @{$face_by_pos->{$edge_vert_positions->[1]}} },
            ];
            #print Dumper($edge_vert_faces);
            #$edge_faces = [
            #    @{$edge_faces},
            #    [ grep { defined($edge_vert_faces->[1]{$_}) } keys %{$edge_vert_faces->[0]} ]
            #];
            push(@{$edge_faces}, [
                grep { defined($edge_vert_faces->[1]{$_}) } keys %{$edge_vert_faces->[0]}
            ]);
            #$edge_endpoints = [
            #    @{$edge_endpoints},
            #    [ @{$edge_vert_positions} ]
            #];
            push(@{$edge_endpoints}, $edge_vert_positions);
            for my $face_key (@{$edge_faces->[-1]}) {
                if (!defined($face_edges->{$face_key})) {
                    $face_edges->{$face_key} = [];
                }
                #$face_edges->{$face_key} = [ @{$face_edges->{$face_key}}, $edge_index ];
                push(@{$face_edges->{$face_key}}, $edge_index);
            }
            #if ((scalar(keys @{$edge_faces}) % 10000) == 0) {
            #  print scalar keys @{$edge_faces};
            #  printf " %f", [gettimeofday]->[0] - $t0->[0];
            #  print "\n";
            #if (scalar keys @{$edge_faces} > 20) {
            #  print Dumper($edge_faces);die;
            #  print Dumper($edge_endpoints);die;
            #  print Dumper($face_edges);die;
            #}
        }
        #print "indexed edges\n";
    }
    if ($options->{compute_smoothgroups}) {
        # construct list of patches per mesh, patch is connected faces
        #for (my $i = 0; $i < $model{'nodes'}{'truenodenum'}; $i++) {
        #    if (!($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH) ||
        #        ($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER))
        #    {
        #        next;
        #    }
        #}
        #for (my $i = 0; $i < $model{'nodes'}{'truenodenum'}; $i++) {
        #    if (!($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH) ||
        #        ($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER))
        #    {
        #        next;
        #    }
        #}
        # for every vertex position
        # patch: mesh, vertex, smoothinggroups, faces, smoothedpatches, smoothinggroupnumbers
        my $protogroups = {};
        for my $vert_key (keys %{$face_by_pos}) {
          if (scalar(@{$face_by_pos->{$vert_key}}) == 1) {
            # faces touching this position are all part of patch
            next;
          }
          #print Dumper($face_by_pos->{$vert_key});
          my $norm_used = {};
          if (!defined($protogroups->{$vert_key})) {
            $protogroups->{$vert_key} = [];
          }
          my $patchnorms = [ map { &patchnormal(\%model, $_) } @{$face_by_pos->{$vert_key}} ];
          my $poskey_combos = [
            # make sure all is always first, even if it considered twice
            [ keys @{$face_by_pos->{$vert_key}} ],
            reverse combinations(keys @{$face_by_pos->{$vert_key}})
          ];
          for my $pos_key (keys @{$face_by_pos->{$vert_key}}) {
            if (defined($norm_used->{$pos_key})) {
              next;
            }
            $norm_used->{$pos_key} = 1;
            my $pos_data = $face_by_pos->{$vert_key}[$pos_key];
            my $vertnorm = $model{nodes}{$pos_data->{mesh}}{vertexnormals}[$pos_data->{vertex}];
            #my $testnorm = [ 0.0, 0.0, 0.0 ];
            my $cur_group = [
              #map { [ $pos_data->{mesh}, $_ ] } @{$pos_data->{faces}}
              map { $pos_data->{mesh} . '.' . $_  } @{$pos_data->{faces}}
            ];
            my $testnorm = $patchnorms->[$pos_key];
            #$testnorm = &$patch_normal($pos_data);
            #$testnorm = normalize_vector($testnorm);
            my $base_score = score_vector(normalize_vector($testnorm), $vertnorm);
            #print "base score: $base_score\n";
            if (!vertex_equals(normalize_vector($testnorm), $vertnorm, 4) && $base_score > 0.001) {
#              print Dumper($testnorm);
#              print Dumper($vertnorm);
              my $othernorms = {};
              for my $other_key (grep {$_ != $pos_key} keys @{$face_by_pos->{$vert_key}}) {
                #$othernorms->{$other_key} = &$patch_normal($face_by_pos->{$vert_key}[$other_key]);
                $othernorms->{$other_key} = $patchnorms->[$other_key];
              }
              #print "onorm initial\n";
#              print Dumper($othernorms);
              my $subtestnorm;
              #subsets {
              #  print "presubset: @_\n";
              #} keys %{$othernorms};
#print "dump\n";
#print Dumper(combinations(keys %{$othernorms}));
              my $matched = 0;
              #for my $combo (combinations(keys %{$othernorms})) {
              for my $combo (grep { defined($othernorms->{$_}) } @{$poskey_combos}) {
                $subtestnorm = [ @{$testnorm} ];
#                print "subset: ".@{$combo}."\n";
#                print Dumper($combo);
                for my $okey (@{$combo}) {
                  $subtestnorm = [ map {
                    $subtestnorm->[$_] += $othernorms->{$okey}[$_];
                  } (0..2) ];
                }
                my $sub_score = score_vector(normalize_vector($subtestnorm), $vertnorm);
                if (vertex_equals(normalize_vector($subtestnorm), $vertnorm, 4) ||
                    ($sub_score < 0.001 && $sub_score < $base_score)) {
                  #print "@{$combo} matched\n";
                  map { $norm_used->{$_} = 1; } @{$combo};
                  $matched = 1;
                  for my $okey (@{$combo}) {
                    $cur_group = [
                      @{$cur_group},
                      #map { [ $face_by_pos->{$vert_key}[$okey]{mesh}, $_ ] } @{$face_by_pos->{$vert_key}[$okey]{faces}}
                      map { $face_by_pos->{$vert_key}[$okey]{mesh} .'.'. $_ } @{$face_by_pos->{$vert_key}[$okey]{faces}}
                    ];
                  }
                  last;
                } else {

                }
              }
              #keys %{$othernorms};
              if (!$matched) {
                #print "NO MATCH $vert_key $pos_key $pos_data->{mesh} $pos_data->{vertex}\n";
                #print Dumper($face_by_pos->{$vert_key}[$pos_key]);
              }
              #print Dumper($subtestnorm);
              #print Dumper(normalize_vector($subtestnorm));
              #my $attempted = 1;
              #my $total = 1;
              #my $i = 1;
              #$total *= ++$i while $i < scalar(keys %{$othernorms});
              #while ($attempted < $total) {
              #}
#              print "others\n";
#              print Dumper($othernorms);
#              print Dumper([ map {normalize_vector($othernorms->{$_})} keys %{$othernorms} ]);
            }
            #$protogroups->{$vert_key} = [
            push(
              @{$protogroups->{$vert_key}}, [ @{$cur_group} ]
            );
            #];
          #print "$vert_key: " . Dumper($protogroups->{$vert_key});
          }
          #print Dumper($protogroups);
          #print Dumper([
          #  map {$protogroups->{$_}} sort {
          #    scalar(@{$protogroups->{$b}}) <=> scalar(@{$protogroups->{$a}})
          #  } keys %{$protogroups}
          #]);
        }

      my $poly_groups = [];
      my $poly_stack = [];
      my $poly_prev = 0;
      my $totpoly = scalar keys %{$face_edges};
      #print "tot $totpoly\n";
      my $edge_borders = [];
      my $tot_group = 0;
      my $count = 0;
      while (1) {
        my ($poly, $bit_poly_group_mask, $poly_group_id, $ps_curr_idx, $ps_end_idx);
        $bit_poly_group_mask = 0;
        $ps_curr_idx = 0;
        $ps_end_idx = 0;
        #print "poly1 $poly\n";
        for my $i ($poly_prev..$totpoly - 1) {
          #print "$i\n";
          if (!defined($poly_groups->[$i]) || $poly_groups->[$i] == 0) {
            $poly = $i;
            last;
          }
        }
        #print "poly2 $poly\n";
        if (!defined($poly) || $poly == $totpoly - 1) {
          last;
        }
        #print "poly $poly / $totpoly\n";
        $poly_group_id = 3;
        $poly_prev = $poly + 1;
        $poly_groups->[$poly] = $poly_group_id;
        #print "set ps $ps_end_idx\n";
        $poly_stack = [];
        $poly_stack->[$ps_end_idx++] = $poly;
        while ($ps_curr_idx != $ps_end_idx) {
          my ($mp, $ml, $j, $map_ele);
          $poly = $poly_stack->[$ps_curr_idx++];
          #print "while poly $poly $ps_curr_idx $ps_end_idx\n";
          #assert
          $mp = $face_edges->{$face_map->{$poly}};
          #my $me_idx;
          #for my $me_idx ((shift @{$mp})) {
          for my $me_idx (@{$mp}) {
            #print "me: $me_idx\n";
            $map_ele = $edge_faces->[$me_idx];
            if (!boundary_check($protogroups, $me_idx, $edge_faces, $edge_endpoints)) {
              #print "not boundary $me_idx\n";
              for my $p (@{$map_ele}) {
                #print "p $p $poly_group_id $ps_end_idx\n";
                my $pi = $face_map_inv->{$p};
                if (!defined($poly_groups->[$pi]) || $poly_groups->[$pi] == 0) {
                  $poly_groups->[$pi] = $poly_group_id;
                  $poly_stack->[$ps_end_idx++] = $pi;
                }
              }
            } else {
              #if (scalar grep { $_ == $me_idx } @{$edge_borders}) {
              #print "yes boundary $me_idx\n";
                for my $p (@{$map_ele}) {
                  my $pi = $face_map_inv->{$p};
                  my $bit = $poly_groups->[$pi];
                  if (!($bit_poly_group_mask & $bit)) {
                    $bit_poly_group_mask |= $bit;
                  }
                }
              #}
            }
          }
        }
        #print Dumper($poly_stack);
        my ($i, $p, $gid_bit, $poly_group_id);
        $gid_bit = 0;
        $poly_group_id = 1;
        while (($poly_group_id & $bit_poly_group_mask) && ($gid_bit < 32)) {
          $poly_group_id <<= 1;
          $gid_bit += 1;
        }
        if ($gid_bit > $tot_group) {
          $tot_group = $gid_bit;
        }
        for my $p (@{$poly_stack}) {
          #print "$p $poly_groups->[$p] => $poly_group_id\n";
          $poly_groups->[$p] = $poly_group_id;
        }
      }
      $tot_group++;

      #print Dumper($poly_groups);
      #printf "tot group $tot_group %u\n", scalar(@{$poly_groups});

      for my $face_index (0..scalar(@{$poly_groups}) - 1) {
        my ($mesh, $face) = split(/\./, $face_map->{$face_index});
        my @Aface = split(
          /\s+/, $model{nodes}{$mesh}{Afaces}[$face]
        );
        $model{nodes}{$mesh}{Afaces}[$face] = join(
          ' ',
          (@Aface)[0..2],
          $poly_groups->[$face_index],
          (@Aface)[4..7]
        );
      }
      # end smoothgroup calculation
    }
    if ($options->{weld_model}) {
      # weld the model's vertices
      my $removed = { map { $_ => [] } keys %{$model{nodes}} };
      # welding first pass, identify removed vertices,
      # reindex removed vertices in binary face structure
      for my $vert_key (keys %{$face_by_pos}) {
        next unless scalar(@{$face_by_pos->{$vert_key}}) > 1;
        my $verts_use = {};
        for my $group (@{$face_by_pos->{$vert_key}}) {
          if (!defined($verts_use->{$group->{mesh}})) {
            # first vertex for this mesh for this position, we will use it
            $verts_use->{$group->{mesh}} = $group->{vertex};
            next;
          }
          # record extra vertex to be removed
          $removed->{$group->{mesh}}[$group->{vertex}] = $verts_use->{$group->{mesh}};
          # change this face index on all faces it is present on
          for my $face_index (@{$group->{faces}}) {
            $model{nodes}{$group->{mesh}}{Bfaces}[$face_index] = [
              @{$model{nodes}{$group->{mesh}}{Bfaces}[$face_index]}[0..7],
              map {
                $_ == $group->{vertex} ? $verts_use->{$group->{mesh}} : $_
              } @{$model{nodes}{$group->{mesh}}{Bfaces}[$face_index]}[8..10],
            ];
          }
        }
      }
      # welding second pass, reconstruct vertices,
      # reindex all vertices in ascii face structure
      for my $mesh (keys %{$removed}) {
        next unless scalar(@{[ grep {defined} @{$removed->{$mesh}} ]});
        # keys is a list of the indices being kept, and since it is a list,
        # it winds up being a map of new index => old vertex
        my @keys = grep {
          !defined($removed->{$mesh}[$_])
        } (0..$model{nodes}{$mesh}{vertcoordnum} - 1);
        # reconstruct ascii faces, keep smoothgroup number through material ID,
        # but get (and adjust) vertex indices from equivalent binary face
        $model{nodes}{$mesh}{Afaces} = [
          map {
            $model{nodes}{$mesh}{Afaces}[$_] =~ /^\s*\S+\s+\S+\s+\S+\s+(\S+\s*\S+\s+\S+\s+\S+\s+\S+)\s*$/;
            join(' ', map {
              $_ - scalar(@{[ grep {defined} @{$removed->{$mesh}}[0..$_] ]})
            } @{$model{nodes}{$mesh}{Bfaces}[$_]}[8..10]) . " $1"
          } keys @{$model{nodes}{$mesh}{Bfaces}}
        ];
        # record new number of vertices
        $model{nodes}{$mesh}{vertcoordnum} = scalar(@keys);
        # reconstruct verts, bones, and constraints by using @keys to slice
        $model{nodes}{$mesh}{verts} = [ @{$model{nodes}{$mesh}{verts}}[@keys] ];
        if ($model{nodes}{$mesh}{nodetype} & NODE_HAS_SKIN) {
          $model{nodes}{$mesh}{Abones} = [ @{$model{nodes}{$mesh}{Abones}}[@keys] ];
        }
        if ($model{nodes}{$mesh}{nodetype} & NODE_HAS_DANGLY) {
          $model{nodes}{$mesh}{constraints} = [ @{$model{nodes}{$mesh}{constraints}}[@keys] ];
        }
      }
    }
        #die;

    #read in the animation indexes
    if ($model{'numanims'} != 0 && $options->{extract_anims})
    {
        $temp = $model{'animstart'} + 12;
        seek(MODELMDL, $temp, 0);
        print("Anim_indexes " . tell(MODELMDL)) if $printall;

        $model{'anims'}{'indexes'}{'start'} = tell(MODELMDL);
        read(MODELMDL, $buffer, $structs{'animindexes'}{'size'} * $model{'numanims'});
        print(" " . (tell(MODELMDL) - 1) . "\n") if $printall;

        $model{'anims'}{'indexes'}{'end'} = tell(MODELMDL)-1;
        $model{'anims'}{'indexes'}{'raw'} = $buffer;
        $model{'anims'}{'indexes'}{'unpacked'} = [unpack($structs{'animindexes'}{'tmplt'}, $buffer)];

        #read in the animations
        for (my $i = 0; $i < $model{'numanims'}; $i++)
        {
            #animations start off with a geoheader, so get it
            $temp = $model{'anims'}{'indexes'}{'unpacked'}[$i] + 12;
            seek(MODELMDL, $temp, 0);
            print("Anim_geoheader$i " . tell(MODELMDL)) if $printall;

            $model{'anims'}{$i}{'geoheader'}{'start'} = tell(MODELMDL);
            read(MODELMDL, $buffer, $structs{'geoheader'}{'size'});
            print(" " . (tell(MODELMDL) - 1) . "\n") if $printall;

            $model{'anims'}{$i}{'geoheader'}{'end'}      = tell(MODELMDL)-1;
            $model{'anims'}{$i}{'geoheader'}{'raw'}      = $buffer;
            $model{'anims'}{$i}{'geoheader'}{'unpacked'} = [unpack($structs{'geoheader'}{'tmplt'}, $buffer)];
            $model{'anims'}{$i}{'name'}                  = $model{'anims'}{$i}{'geoheader'}{'unpacked'}[2];

            #next are 56 bytes that is the animation header
            print("Anim_animheader$i " . tell(MODELMDL)) if $printall;

            $model{'anims'}{$i}{'animheader'}{'start'} = tell(MODELMDL);
            read(MODELMDL, $buffer, $structs{'animheader'}{'size'});
            print(" " . (tell(MODELMDL) - 1) . "\n") if $printall;

            $model{'anims'}{$i}{'animheader'}{'end'} = tell(MODELMDL)-1;
            $model{'anims'}{$i}{'animheader'}{'raw'} = $buffer;
            $model{'anims'}{$i}{'animheader'}{'unpacked'} = [unpack($structs{'animheader'}{'tmplt'}, $buffer)];

            $model{'anims'}{$i}{'length'} = $model{'anims'}{$i}{'animheader'}{'unpacked'}[0]; 
            $model{'anims'}{$i}{'transtime'} = $model{'anims'}{$i}{'animheader'}{'unpacked'}[1];
            $model{'anims'}{$i}{'animroot'} = $model{'anims'}{$i}{'animheader'}{'unpacked'}[2];
            $model{'anims'}{$i}{'eventsloc'} = $model{'anims'}{$i}{'animheader'}{'unpacked'}[3]; 
            $model{'anims'}{$i}{'eventsnum'} = $model{'anims'}{$i}{'animheader'}{'unpacked'}[4]; 

            # read in the animation events (if any)
            if ($model{'anims'}{$i}{'eventsnum'} != 0)
            {
                print("anim_event$i " . tell(MODELMDL)) if $printall;

                $model{'anims'}{$i}{'animevents'}{'start'} = tell(MODELMDL);
                $temp = $model{'anims'}{$i}{'eventsnum'};
                read(MODELMDL, $buffer, $structs{'animevents'}{'size'} * $temp);

                $model{'anims'}{$i}{'animevents'}{'raw'} = $buffer;
                $model{'anims'}{$i}{'animevents'}{'unpacked'} = [unpack($structs{'animevents'}{'tmplt'} x $temp,$buffer)];

                foreach(0..($temp - 1))
                {
                    $model{'anims'}{$i}{'animevents'}{'ascii'}[$_] = sprintf(
                        '% .7g %s',
                        $model{'anims'}{$i}{'animevents'}{'unpacked'}[$_ * 2],
                        $model{'anims'}{$i}{'animevents'}{'unpacked'}[($_ * 2) + 1]
                    );
                }
                print(" " . (tell(MODELMDL) - 1) . "\n") if $printall;
                $model{'anims'}{$i}{'animevents'}{'end'} = tell(MODELMDL)-1;
            }      
      
            #next are the animation nodes
            $model{'anims'}{$i}{'nodes'} = {};
            # $tree, $parent, $startnode, $model, $version
            getnodes("anims.$i", undef, $model{'anims'}{$i}{'geoheader'}{'unpacked'}[ROOTNODE], \%model, $version);
        }
    }
    else
    {
        print ("No animations\n") if $printall;
    }

    #write out the bitmaps file
    foreach (0..$model{'nodes'}{'truenodenum'} - 1)
    {
        if (defined($model{'nodes'}{$_}{'bitmap'}) &&
            lc($model{'nodes'}{$_}{'bitmap'}) ne "null")
        {
            #print("$_:$model{'nodes'}{$_}{'bitmap'}\n");
            $bitmaps{lc($model{'nodes'}{$_}{'bitmap'})}++;
        }
    }
    if (scalar(keys %bitmaps))
    {
        my $tex_file = "$filepath-textures.txt";
        if (MDLOpsM::File::open(\*BITMAPSOUT, '>', $tex_file))
        {
            foreach (keys %bitmaps)
            {
                 print(BITMAPSOUT "$_\n");
            }
            MDLOpsM::File::close(*BITMAPSOUT);
        }
        else
        {
            print "error: can't open textures out file: $tex_file\n";
        }
    }

    #open(MODELHINT, ">", $filepath."-out-hint.txt") or die "can't open model hint file\n";

    if ($options->{use_mdx}) {
      MDLOpsM::File::close(*MODELMDX);
    }
    MDLOpsM::File::close(*MODELMDL);

    return \%model;
}

#######################################################################
# called only by getnodes
# a recursive sub to read in AABB nodes
sub readaabb
{
    my ($ref, $node, $start) = (@_);
    my $buffer;
    my @temp;
    my $count = 1;

  
    seek(MODELMDL, $start, 0);
    read(MODELMDL, $buffer, $structs{'darray'}[10]{'size'});
    $ref->{$node}{ $structs{'darray'}[10]{'name'} }{'raw'} .= $buffer;
    @temp = unpack($structs{'darray'}[10]{'tmplt'}, $buffer);

    #print("Node: " . ($start - 12) . " Child1: " . $temp[6] . " Child2: " . $temp[7] . " Node/leaf: " . $temp[8] . "\n");
  
    if ($temp[6] != 0)
    {
        $count += readaabb($ref, $node, $temp[6] + 12);
    }
  
    if ($temp[7] != 0)
    {
        $count += readaabb($ref, $node, $temp[7] + 12);
    }

    return $count;
}

#######################################################################
# called only by writebinarymdl
# a recursive sub to write AABB nodes
sub writeaabb
{
    my ($ref, $modelnode, $aabbnode, $start) = (@_);
    my ($lastwritepos, $child1, $child2, $buffer, $me);

    $me = $aabbnode;
    #print("aabbnode: " . $aabbnode . " start: " . $start . "|" . $ref->{'nodes'}{$modelnode}{'aabbnodes'}[$aabbnode][6] . "\n");
  
    seek(BMDLOUT, $start, 0);
    $buffer = pack("ffffff", $ref->{'nodes'}{$modelnode}{'aabbnodes'}[$aabbnode][0],
                             $ref->{'nodes'}{$modelnode}{'aabbnodes'}[$aabbnode][1],
                             $ref->{'nodes'}{$modelnode}{'aabbnodes'}[$aabbnode][2],
                             $ref->{'nodes'}{$modelnode}{'aabbnodes'}[$aabbnode][3],
                             $ref->{'nodes'}{$modelnode}{'aabbnodes'}[$aabbnode][4],
                             $ref->{'nodes'}{$modelnode}{'aabbnodes'}[$aabbnode][5]);
    print(BMDLOUT $buffer);
  
    if($ref->{'nodes'}{$modelnode}{'aabbnodes'}[$aabbnode][6] != -1)
    {
        $buffer = pack("llll", 0, 0, $ref->{'nodes'}{$modelnode}{'aabbnodes'}[$aabbnode][6], 0);
        print(BMDLOUT $buffer);
        $lastwritepos = tell(BMDLOUT);
    }
    else
    {
        # calculate start pos for child1 node
        $child1 = $start + 40;

        # write child1 node
        ($aabbnode, $child2) = writeaabb($ref, $modelnode, ($aabbnode + 1), $child1);

        # write child2 node
        ($aabbnode, $lastwritepos) = writeaabb($ref, $modelnode, ($aabbnode + 1), $child2);

        # finish off this node by writing child pointers and rest of data
        seek(BMDLOUT, $start + 24, 0);
        $buffer = pack("llll", ($child1 - 12), ($child2 - 12), -1, 0);
        print(BMDLOUT $buffer);
    }
  
    #print($me . " returning (aabbnode,lastritepos): " . $aabbnode . "|" . $lastwritepos . "\n");
    return ($aabbnode, $lastwritepos);
}
  

#####################################################################
# called only by readbinarymdl
# a recursive sub to read in geometry node order, required by skin nodes
sub getnodeorder {
  my ($model, $startnode) = @_;
  my ($buffer, $unpacked);

  # initialize order list on first iteration
  if (!defined($model->{order2nameindex})) {
    $model->{order2nameindex} = [];
  }

  # adjust starting offset to factor in file header
  $startnode += 12;

  # read node header: node name index, 'part number'
  seek(MODELMDL, $startnode + 4, 0);
  read(MODELMDL, $buffer, 4);
  my $name_index = unpack('S', $buffer);
  push @{$model->{order2nameindex}}, $name_index;

  # read node header: child array info
  seek(MODELMDL, $startnode + 44, 0);
  read(MODELMDL, $buffer, 8);
  my ($child_array_offset, $child_array_length) = unpack('LL', $buffer);
  printf "order map %u => %u\n",
         scalar(@{$model->{order2nameindex}}) - 1, $name_index if $printall;
  print "child array $child_array_length\@$child_array_offset\n" if $printall;

  # read node header: child array offset values
  seek(MODELMDL, $child_array_offset + 12, 0);
  read(MODELMDL, $buffer, $child_array_length * 4);
  my $child_offsets = [ unpack('L*', $buffer) ];

  # recursively call on each child
  foreach (@{$child_offsets}) {
    getnodeorder($model, $_);
  }
}


#####################################################################
# called only by readbinarymdl
# a recursive sub to read in geometry and animation nodes
sub getnodes {
  my ($tree, $parent, $startnode, $model, $version) = (@_);
  my ($buffer, $work, @children) = ("",1,());
  my ($nodetype, $animnum);
  my ($node, $numchildren, $temp, $temp2, $temp3, $template, $uoffset);  
  my $ref;

  if ($version eq 'k1') {
    # a kotor 1 model
    $uoffset = -2;  # offset for unpacked values
  } elsif ($version eq 'k2') {
    # a kotor 2 model
    $uoffset = 0;
  } else {
    return;
  }
    
  #check if we are called for main nodes or animation nodes
  if ($tree =~ /^anims/) {
    #animations nodes needed.  Find the two hashes and set $ref
    $tree =~ /(.*)\.(.*)/;
    $animnum = $2;
    $ref = $model->{lc($1)}{$animnum}{'nodes'};
  } else {
    #main nodes needed, so just pass the node root hash
    $ref = $model->{lc($tree)};
  }

  $ref->{'truenodenum'}++;
  
  #seek to the start of the node and read in the header
  seek(MODELMDL, $startnode + 12, 0);
  read(MODELMDL, $buffer, $structs{'nodeheader'}{'size'});
  #get the "node number" from the raw data
  $node = unpack("x[ss]s", $buffer);
  $ref->{$node}{'header'}{'raw'} = $buffer;
  $ref->{$node}{'header'}{'unpacked'}  = [unpack($structs{'nodeheader'}{'tmplt'}, $buffer)];
  $temp = $ref->{$node}{'header'}{'unpacked'}[0];
  $temp = $startnode + 12;
  $ref->{$node}{'nodetype'} = $ref->{$node}{'header'}{'unpacked'}[0];
  
  $ref->{$node}{'supernode'} = $ref->{$node}{'header'}{'unpacked'}[1];
  $ref->{$node}{'nodenum'} = $node;
  #$ref->{$node}{'parent'} = $parent;
  #$ref->{$node}{'parentnodenum'} = $model->{'nodeindex'}{lc($parent)};
  $ref->{$node}{'parent'} = defined($parent) ? $model->{partnames}[$parent->{nodenum}] : 'NULL';
  $ref->{$node}{'parentnodenum'} = defined($parent) ? $parent->{nodenum} : -1;
  $ref->{$node}{'positionheader'} = [@{$ref->{$node}{'subhead'}{'unpacked'}}[6..8]];
  $ref->{$node}{'rotationheader'} = [@{$ref->{$node}{'subhead'}{'unpacked'}}[9..12]]; #quaternion order: w x y z
  $ref->{$node}{'childrenloc'} = $ref->{$node}{'header'}{'unpacked'}[13];
  $ref->{$node}{'childcount'} = $ref->{$node}{'header'}{'unpacked'}[14];
  $ref->{$node}{'controllerloc'} = $ref->{$node}{'header'}{'unpacked'}[16];
  $ref->{$node}{'controllernum'} = $ref->{$node}{'header'}{'unpacked'}[17];
  $ref->{$node}{'controllerdataloc'} = $ref->{$node}{'header'}{'unpacked'}[19];
  $ref->{$node}{'controllerdatanum'} = $ref->{$node}{'header'}{'unpacked'}[20];
  print("$tree-$ref->{$node}{'header'}{'unpacked'}[NODEINDEX]_header " . ($startnode+12) ) if $printall;
  $ref->{$node}{'header'}{'start'} = $startnode+12;
  if ($tree =~ /^anims/) {
    $model->{'nodesort'}{$animnum}{$startnode+12} = $node . "-header";
  }
  print (" " . (tell(MODELMDL) - 1) . "\n") if $printall;
  $ref->{$node}{'header'}{'end'} = tell(MODELMDL) - 1;
  $nodetype = $ref->{$node}{'header'}{'unpacked'}[NODETYPE];

  #record node number in parent's childindexes{nums}
  if (lc($ref->{$node}{'parent'}) ne 'null' &&
      defined($ref->{$ref->{$node}{'parentnodenum'}})) {
    # store actual child index (nodenum) in parent's childindexes, not just locations
    # this gives us a properly traversable tree without having to search by node start location
    push @{$ref->{$ref->{$node}{'parentnodenum'}}{'childindexes'}{'nums'}}, $node;
  }

  #check if node "controller info" has any data to read in
  if ($ref->{$node}{'controllernum'} != 0) {
    $temp = $ref->{$node}{'controllerloc'} + 12;
    seek(MODELMDL, $temp, 0);
    print("$tree-$ref->{$node}{'header'}{'unpacked'}[NODEINDEX]_controllers " . tell(MODELMDL)) if $printall;
    $ref->{$node}{'controllers'}{'start'} = tell(MODELMDL);
    if ($tree =~ /^anims/) {
      $model->{'nodesort'}{$animnum}{tell(MODELMDL)} = $node . "-controllers";
    }

my $dothis = 0;

    read(MODELMDL, $buffer, $structs{'controllers'}{'size'} * $ref->{$node}{'controllernum'});
    print(" " . (tell(MODELMDL)-1) . "\n") if $printall;
    $ref->{$node}{'controllers'}{'end'} = tell(MODELMDL)-1;
    $ref->{$node}{'controllers'}{'raw'} = $buffer;
    $ref->{$node}{'controllers'}{'unpacked'} = [unpack($structs{'controllers'}{'tmplt'} x $ref->{$node}{'controllernum'}, $buffer)];
    $ref->{$node}{'controllers'}{'bezier'} = {};
    for (my $i = 0; $i < $ref->{$node}{'controllernum'}; $i++) {
      if($ref->{$node}{'controllers'}{'unpacked'}[($i * 9)] == 36 && $dothis == 0)
      {
          $dothis = 1;
#          print "Controller data for $node, row $i:\n";
#          print "Piece 1: $ref->{$node}{'controllers'}{'unpacked'}[($i * 9)]\n";
#          print "Piece 2: $ref->{$node}{'controllers'}{'unpacked'}[($i * 9) + 1]\n";
#          print "Piece 3: $ref->{$node}{'controllers'}{'unpacked'}[($i * 9) + 2]\n";
#          print "Piece 4: $ref->{$node}{'controllers'}{'unpacked'}[($i * 9) + 3]\n";
#          print "Piece 5: $ref->{$node}{'controllers'}{'unpacked'}[($i * 9) + 4]\n";
#          print "Piece 6: $ref->{$node}{'controllers'}{'unpacked'}[($i * 9) + 5]\n";
#          print "Piece 7: $ref->{$node}{'controllers'}{'unpacked'}[($i * 9) + 6]\n";
#          print "Piece 8: $ref->{$node}{'controllers'}{'unpacked'}[($i * 9) + 7]\n";
#          print "Piece 9: $ref->{$node}{'controllers'}{'unpacked'}[($i * 9) + 8]\n\n";
      }

      $ref->{$node}{'controllers'}{'cooked'}[$i][0] = $ref->{$node}{'controllers'}{'unpacked'}[($i * 9)];
      $ref->{$node}{'controllers'}{'cooked'}[$i][1] = $ref->{$node}{'controllers'}{'unpacked'}[($i * 9)+1];
      $ref->{$node}{'controllers'}{'cooked'}[$i][2] = $ref->{$node}{'controllers'}{'unpacked'}[($i * 9)+2];
      $ref->{$node}{'controllers'}{'cooked'}[$i][3] = $ref->{$node}{'controllers'}{'unpacked'}[($i * 9)+3];
      $ref->{$node}{'controllers'}{'cooked'}[$i][4] = $ref->{$node}{'controllers'}{'unpacked'}[($i * 9)+4];
      $ref->{$node}{'controllers'}{'cooked'}[$i][5] = $ref->{$node}{'controllers'}{'unpacked'}[($i * 9)+5];
      $ref->{$node}{'controllers'}{'cooked'}[$i][6] = $ref->{$node}{'controllers'}{'unpacked'}[($i * 9)+6];
      $ref->{$node}{'controllers'}{'cooked'}[$i][7] = $ref->{$node}{'controllers'}{'unpacked'}[($i * 9)+7];
      $ref->{$node}{'controllers'}{'cooked'}[$i][8] = $ref->{$node}{'controllers'}{'unpacked'}[($i * 9)+8];
    }
  }

  #check if node "controller data" has any data to read in
  # controller data is a bunch of floats.  The structure to these
  # floats is determined by the controllers above.
  if ($ref->{$node}{'controllerdatanum'} != 0) {
    $temp = $ref->{$node}{'controllerdataloc'} + 12;
    seek(MODELMDL, $temp, 0);
    print("$tree-$ref->{$node}{'header'}{'unpacked'}[NODEINDEX]_$structs{'controllerdata'}{'name'} " . tell(MODELMDL)) if $printall;
    $ref->{$node}{'controllerdata'}{'start'} = tell(MODELMDL);
    if ($tree =~ /^anims/) {
      $model->{'nodesort'}{$animnum}{tell(MODELMDL)} = $node . "-controllerdata";
    }
    read(MODELMDL, $buffer, $structs{'controllerdata'}{'size'} * $ref->{$node}{'controllerdatanum'});
    print(" " . (tell(MODELMDL)-1) . "\n") if $printall;
    $ref->{$node}{'controllerdata'}{'end'} = tell(MODELMDL)-1;
    $ref->{$node}{'controllerdata'}{'raw'} = $buffer;
    $template = "";
    foreach (@{$ref->{$node}{'controllers'}{'cooked'}}) {
      # $_->[0] = controller type
      # $_->[1] = unknown
      # $_->[2] = number of rows of controller data
      # $_->[3] = offset of first time key
      # $_->[4] = offset of first data byte
      # $_->[5] = columns of data
      # the rest is unknown values
      # detect bezier key usage
      my $bezier = 0;
      if ($_->[5] & 16) {
        # this is a bezier keyed controller
        # (according to Torlack and experimental verification)
        $bezier = 1;
        # record a list of the bezierkeyed controllers
        $ref->{$node}{'controllers'}{'bezier'}{$_->[0]} = 1;
      }
      # add template for key time values
      $template .= "f" x $_->[2];
      if ($_->[1] != 128) {
        # check for controller type 20 and column count 2:
        # special compressed quaternion, only read one value here
        if ($_->[0] == 20 && $_->[5] == 2) {
          # a compressed quaternion is found, record that this models uses them
          $model->{'compress_quaternions'} = 1;
          $template .= "L" x ($_->[2]);
        #} elsif ($_->[0] == 8 && ($_->[5] > 16)) {
        } elsif ($bezier) {
          # bezier key support expands data values to 3 values per column
          $template .= "f" x ( $_->[2] * ( ($_->[5] - 16) * 3) );
        } else {
          $template .= "f" x ($_->[2] * $_->[5]); 
        }
      } else {
        $template .= "s" x (($_->[2] * $_->[5]) * 2); 
      }
    }
    
    $ref->{$node}{'controllerdata'}{'unpacked'} = [unpack($template,$buffer)];
  }

  # cook the controllers
  $temp2 = $ref->{$node}{'controllerdata'}{'unpacked'};
  #for (my $i = 0; $i < $ref->{$node}{'controllerdatanum'}; $i++) {
  foreach (@{$ref->{$node}{'controllers'}{'cooked'}}) {

    #get the controller info
    my ($controllertype, $controllerinfo, $datarows, $timestart, $datastart, $datacolumns) = @{$_}[0..5];

    # check for controller type 20 and column count 2:
    # special compressed quaternion, only read one value here
    if ($controllertype == 20 && $datacolumns == 2) {
      $datacolumns = 1;
    }
    # check for bezier key usage
    if ($datacolumns >= 16 && $datacolumns & 16) {
      $ref->{$node}{'controllers'}{'bezier'}{$controllertype} = 1;
      #$datacolumns &= 0xEF;
      # subtract off the bezier key flag (16)
      $datacolumns -= 16;
      # multiply by values per column (3)
      $datacolumns *= 3;
    }
            
    # loop through the data rows    
    for (my $j = 0; $j < $datarows; $j++) {
      # add keyframe time value to ascii controllers,
      # this is a good time to set precision on controller time values
      $ref->{$node}{'Acontrollers'}{$controllertype}[$j] = sprintf('%.7g', $temp2->[$timestart + $j]);
      $ref->{$node}{'Bcontrollers'}{$controllertype}{'times'}[$j] = $temp2->[$timestart + $j];
      # loop through the datacolumns
      $ref->{$node}{'Bcontrollers'}{$controllertype}{'values'}[$j] = [];
      for (my $k = 0; $k < $datacolumns; $k ++) {
        # add controller data value to ascii controllers
        if ($controllertype == 20 || $controllertype == 8) {
          # further processing, don't set precision (leave in native format)
          $ref->{$node}{'Acontrollers'}{$controllertype}[$j] .= ' ' . $temp2->[$datastart + $k + ($j * $datacolumns)];
        } else {
          # no further processing, set precision now
          $ref->{$node}{'Acontrollers'}{$controllertype}[$j] .= sprintf(" % .7g", $temp2->[$datastart + $k + ($j * $datacolumns)]);
        }
        #$ref->{$node}{'Bcontrollers'}{$controllertype}{'values'}[($j * $datacolumns) + $k] = $temp2->[$datastart + $k + ($j * $datacolumns)];
        push @{$ref->{$node}{'Bcontrollers'}{$controllertype}{'values'}[$j]}, $temp2->[$datastart + $k + ($j * $datacolumns)];
      }
    }
  }

  if ($ref->{$node}{'controllernum'} == 0 && $ref->{$node}{'controllerdatanum'} > 0) {
    $ref->{$node}{'Bcontrollers'}{0}{'values'}[0] = [];
    $ref->{$node}{'Acontrollers'}{0}[0] = "";
    for (my $i = 0; $i < $ref->{$node}{'controllerdatanum'}; $i++) {
      $ref->{$node}{'Acontrollers'}{0}[0] .= " " . $temp2->[$i];
      push @{$ref->{$node}{'Bcontrollers'}{0}{'values'}[0]}, $temp2->[$i];
    }
  }

  # now we have to convert the quaternions to rotation axis and angle.
  # Ever heard of a quaternion?  I didn't until I started this script project!
  # the order of quaternions in controllers is: x y z w

  if (defined($ref->{$node}{'Acontrollers'}{20})) {
    foreach (@{$ref->{$node}{'Acontrollers'}{20}}) {
      # check for controller type 20 and column count 2:
      # decode the special compressed quaternion
      my @quatVals = split /\s+/;
      if (@quatVals == 2) {
        ($quatVals[0], $quatVals[1]) = @quatVals;     
        $temp = $quatVals[1];

        # extract q.x
        $quatVals[1] = (-1.0 + ((($temp & 0x7ff) / 2046.0) / 0.5));

        # extract q.y
        $quatVals[2] = (-1.0 + (((($temp >> 11) & 0x7ff) / 2046.0) / 0.5));

        # extract q.z
        $quatVals[3] = (-1.0 + ((($temp >> 22) / 1022.0) / 0.5));

        # calculate q.w
        # q.x^2 + q.y^2 + q.z^2 + q.w^2 = 1 for normalized quaternions
        # only normalized quaternions can be compressed
        $temp = ($quatVals[1] * $quatVals[1]) + ($quatVals[2] * $quatVals[2]) + ($quatVals[3] * $quatVals[3]);
        if ($temp < 1.0) {
          $quatVals[4] = sqrt(1.0 - $temp);
        } else {
          $quatVals[4] = 0.0;
        }
      } # if (@quatVals == 2) {
      # now convert quaternions (however we got them) to axis-angle.
      # 2016 replaced w/ better algorithm from:
      # http://www.opengl-tutorial.org/assets/faq_quaternions/index.html
      $temp = $quatVals[4]; # cos_a
      $quatVals[4] = acos($temp) * 2;
      my $sin_a = sqrt(1.0 - $temp ** 2);
      if (abs($sin_a) < 0.00005) {
          $sin_a = 1;
      }
      $quatVals[1] /= $sin_a;
      $quatVals[2] /= $sin_a;
      $quatVals[3] /= $sin_a;
      $_ = join(' ', map { sprintf('% .7g', $_) } @quatVals);
    } # foreach (@{$ref->{$node}{'Acontrollers'}{20}}) {
  } # if (defined($ref->{$node}{'Acontrollers'}{20})) {

  # Positions in animations are deltas from the initial position.
  if ($tree =~ /^anims/ && defined($ref->{$node}{'Acontrollers'}{8})) {
    my @initialPosVals = (0, 0, 0);
    if (defined($model->{'nodes'}{$node})) {
      @initialPosVals = split /\s+/, $model->{'nodes'}{$node}{'Acontrollers'}{8}[0];
    }
    # handle bezier key value expansion here. method designed for list like:
    # 0, 1, 2, 3
    # bezier list is like
    # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
    # 1, 2, 3 are main data,
    # 4, 5, 6 are left control point, 7, 8, 9 are right control handle
    # control handle values are relative to main data values,
    # and located at 1/3 time between keyframes
    foreach (@{$ref->{$node}{'Acontrollers'}{8}}) {
      my @curPosVals = split /\s+/;
      for ($temp = 1; $temp <= 3; $temp++) {
        $curPosVals[$temp] += $initialPosVals[$temp];
      }
      $_ = join(' ', map { sprintf('% .7g', $_) } @curPosVals);
    }
  }

  #check the "node type" and read in the subheader for it
  if ( $nodetype != NODE_DUMMY ) {
    $temp = $startnode + 92;
    seek(MODELMDL, $temp, 0);
    print("$tree-$ref->{$node}{'header'}{'unpacked'}[NODEINDEX]_$structs{'subhead'}{$nodetype . $version}{'name'} " . tell(MODELMDL)) if $printall;
    $ref->{$node}{'subhead'}{'start'} = tell(MODELMDL);
    read(MODELMDL, $buffer, $structs{'subhead'}{$nodetype . $version}{'size'});
    print(" " . (tell(MODELMDL)-1) . "\n") if $printall;
    $ref->{$node}{'subhead'}{'end'} = tell(MODELMDL)-1;
    $ref->{$node}{'subhead'}{'raw'} = $buffer;
    $ref->{$node}{'subhead'}{'unpacked'} = [unpack($structs{'subhead'}{$nodetype . $version}{'tmplt'}, $buffer)];
  }

  if ( $nodetype == NODE_LIGHT ) { # light
    # to do: flare radius, flare sizes array, flare positions array, flare color shifts array, flare texture names char pointer array
    $ref->{$node}{'flareradius'} = $ref->{$node}{'subhead'}{'unpacked'}[0];
    $ref->{$node}{'flaresizesloc'} = $ref->{$node}{'subhead'}{'unpacked'}[4];
    $ref->{$node}{'flaresizesnum'} = $ref->{$node}{'subhead'}{'unpacked'}[5];
    $ref->{$node}{'flarepositionsloc'} = $ref->{$node}{'subhead'}{'unpacked'}[7];
    $ref->{$node}{'flarepositionsnum'} = $ref->{$node}{'subhead'}{'unpacked'}[8];
    $ref->{$node}{'flarecolorshiftsloc'} = $ref->{$node}{'subhead'}{'unpacked'}[10];
    $ref->{$node}{'flarecolorshiftsnum'} = $ref->{$node}{'subhead'}{'unpacked'}[11];
    $ref->{$node}{'texturenamesloc'} = $ref->{$node}{'subhead'}{'unpacked'}[13];
    $ref->{$node}{'texturenamesnum'} = $ref->{$node}{'subhead'}{'unpacked'}[14];

    $ref->{$node}{'lightpriority'} = $ref->{$node}{'subhead'}{'unpacked'}[16];
    $ref->{$node}{'ambientonly'} = $ref->{$node}{'subhead'}{'unpacked'}[17];
    $ref->{$node}{'ndynamictype'} = $ref->{$node}{'subhead'}{'unpacked'}[18];
    $ref->{$node}{'affectdynamic'} = $ref->{$node}{'subhead'}{'unpacked'}[19];
    $ref->{$node}{'shadow'} = $ref->{$node}{'subhead'}{'unpacked'}[20];
    $ref->{$node}{'flare'} = $ref->{$node}{'subhead'}{'unpacked'}[21];
    $ref->{$node}{'fadinglight'} = $ref->{$node}{'subhead'}{'unpacked'}[22];

    # now read any flare data
    # do our reads in commonly laid out order, texturenames, then flare values in ascending order
    if (defined($ref->{$node}{'texturenamesnum'}) && $ref->{$node}{'texturenamesnum'} > 0) {
      $ref->{$node}{'texturenames'} = [];
      $ref->{$node}{'texturenameslength'} = 0;
      #while (scalar(@{$ref->{$node}{'texturenames'}}) < $ref->{$node}{'texturenamesnum'}) {
      for my $name_pointer_num (0..$ref->{$node}{'texturenamesnum'} - 1) {
        # get the pointer at offset
        my $name = '';
        my $name_ptr = 0;
        seek(MODELMDL, ($ref->{$node}{'texturenamesloc'} + 12) + (4 * $name_pointer_num), 0);
        read(MODELMDL, $name_ptr, 4);
        $name_ptr = unpack('L', $name_ptr);
        #print "NAME PTR = $name_ptr\n";
        seek(MODELMDL, $name_ptr + 12, 0);
        read(MODELMDL, $name, 12);
        #print "NAME  = $name " . length($name) . "\n";
        $name = unpack('Z[12]', $name);
        #print "NAME  = $name " . length($name) . "\n";
        $ref->{$node}{'texturenameslength'} += (length($name) + 1); # extra +1 for trailing null
        $ref->{$node}{'texturenames'} = [ @{$ref->{$node}{'texturenames'}}, $name ];
      }
    }

    if (defined($ref->{$node}{'flaresizesnum'}) && $ref->{$node}{'flaresizesnum'} > 0) {
      $ref->{$node}{'flaresizes'} = [];
      $buffer = '';
      for my $flare_size_num (0..$ref->{$node}{'flaresizesnum'} - 1) {
        seek(MODELMDL, ($ref->{$node}{'flaresizesloc'} + 12) + (4 * $flare_size_num), 0);
        read(MODELMDL, $buffer, 4);
        $ref->{$node}{'flaresizes'} = [ @{$ref->{$node}{'flaresizes'}}, unpack('f', $buffer) ];
      }
    }

    if (defined($ref->{$node}{'flarepositionsnum'}) && $ref->{$node}{'flarepositionsnum'} > 0) {
      $ref->{$node}{'flarepositions'} = [];
      $buffer = '';
      for my $flare_position_num (0..$ref->{$node}{'flarepositionsnum'} - 1) {
        seek(MODELMDL, ($ref->{$node}{'flarepositionsloc'} + 12) + (4 * $flare_position_num), 0);
        read(MODELMDL, $buffer, 4);
        $ref->{$node}{'flarepositions'} = [ @{$ref->{$node}{'flarepositions'}}, unpack('f', $buffer) ];
      }
    }

    if (defined($ref->{$node}{'flarecolorshiftsnum'}) && $ref->{$node}{'flarecolorshiftsnum'} > 0) {
      $ref->{$node}{'flarecolorshifts'} = [];
      $buffer = '';
      for my $flare_colorshift_num (0..$ref->{$node}{'flarecolorshiftsnum'} - 1) {
        seek(MODELMDL, ($ref->{$node}{'flarecolorshiftsloc'} + 12) + (12 * $flare_colorshift_num), 0);
        read(MODELMDL, $buffer, 12);
        $ref->{$node}{'flarecolorshifts'} = [ @{$ref->{$node}{'flarecolorshifts'}}, [ unpack('fff', $buffer) ] ];
      }
    }

    # reposition file read position to after light subheader and data
    seek(MODELMDL, $ref->{$node}{'subhead'}{'end'} + (
      ($ref->{$node}{'flaresizesnum'} * 4) +
      ($ref->{$node}{'flarepositionsnum'} * 4) +
      ($ref->{$node}{'flarecolorshiftsnum'} * (4 * 3)) +
      ($ref->{$node}{'texturenamesnum'} * 4) +
      (defined($ref->{$node}{'texturenameslength'})
         ? $ref->{$node}{'texturenameslength'} : 0)
    ), 0);
  }
#tmplt => "f[3]L[5]Z[32]Z[32]Z[32]Z[32]Z[16]L[2]SCZ[32]CL"};
  if ( $nodetype == NODE_EMITTER ) { # emitter
    $ref->{$node}{'deadspace'} = $ref->{$node}{'subhead'}{'unpacked'}[0];
    $ref->{$node}{'blastRadius'} = $ref->{$node}{'subhead'}{'unpacked'}[1];
    $ref->{$node}{'blastLength'} = $ref->{$node}{'subhead'}{'unpacked'}[2];
    $ref->{$node}{'numBranches'} = $ref->{$node}{'subhead'}{'unpacked'}[3];
    $ref->{$node}{'controlptsmoothing'} = $ref->{$node}{'subhead'}{'unpacked'}[4];
    $ref->{$node}{'xgrid'} = $ref->{$node}{'subhead'}{'unpacked'}[5];
    $ref->{$node}{'ygrid'} = $ref->{$node}{'subhead'}{'unpacked'}[6];
    $ref->{$node}{'spawntype'} = $ref->{$node}{'subhead'}{'unpacked'}[7]; #spacetype??
    $ref->{$node}{'update'} = $ref->{$node}{'subhead'}{'unpacked'}[8];
    $ref->{$node}{'render'} = $ref->{$node}{'subhead'}{'unpacked'}[9];
    $ref->{$node}{'blend'} = $ref->{$node}{'subhead'}{'unpacked'}[10];
    $ref->{$node}{'texture'} = $ref->{$node}{'subhead'}{'unpacked'}[11];
    $ref->{$node}{'chunkname'} = $ref->{$node}{'subhead'}{'unpacked'}[12];
    $ref->{$node}{'twosidedtex'} = $ref->{$node}{'subhead'}{'unpacked'}[13];
    $ref->{$node}{'loop'} = $ref->{$node}{'subhead'}{'unpacked'}[14];
    $ref->{$node}{'renderorder'} = $ref->{$node}{'subhead'}{'unpacked'}[15];
    $ref->{$node}{'m_bFrameBlending'} = $ref->{$node}{'subhead'}{'unpacked'}[16];
    $ref->{$node}{'m_sDepthTextureName'} = $ref->{$node}{'subhead'}{'unpacked'}[17];
    # initial study might point to one or both of these being bitfields aka flags,
    # possibly some of my complete guess flags (or others) are in these.
    $ref->{$node}{'m_bUnknown1'} = $ref->{$node}{'subhead'}{'unpacked'}[18];
    $ref->{$node}{'emitterflags'} = $ref->{$node}{'subhead'}{'unpacked'}[19];

    $ref->{$node}{'p2p'} = ($ref->{$node}{'emitterflags'} & 0x0001) ? 1 : 0;
    $ref->{$node}{'p2p_sel'} = ($ref->{$node}{'emitterflags'} & 0x0002) ? 1 : 0;
    $ref->{$node}{'affectedByWind'} = ($ref->{$node}{'emitterflags'} & 0x0004) ? 1 : 0;
    $ref->{$node}{'m_isTinted'} = ($ref->{$node}{'emitterflags'} & 0x0008) ? 1 : 0;
    $ref->{$node}{'bounce'} = ($ref->{$node}{'emitterflags'} & 0x0010) ? 1 : 0;
    $ref->{$node}{'random'} = ($ref->{$node}{'emitterflags'} & 0x0020) ? 1 : 0;
    $ref->{$node}{'inherit'} = ($ref->{$node}{'emitterflags'} & 0x0040) ? 1 : 0;
    $ref->{$node}{'inheritvel'} = ($ref->{$node}{'emitterflags'} & 0x0080) ? 1 : 0;
    $ref->{$node}{'inherit_local'} = ($ref->{$node}{'emitterflags'} & 0x0100) ? 1 : 0;
    $ref->{$node}{'splat'} = ($ref->{$node}{'emitterflags'} & 0x0200) ? 1 : 0;
    $ref->{$node}{'inherit_part'} = ($ref->{$node}{'emitterflags'} & 0x0400) ? 1 : 0;
    # the following are complete guesses
    $ref->{$node}{'depth_texture'} = ($ref->{$node}{'emitterflags'} & 0x0800) ? 1 : 0;
    $ref->{$node}{'emitterflag13'} = ($ref->{$node}{'emitterflags'} & 0x1000) ? 1 : 0;
    #$ref->{$node}{'renderorder'} = ($ref->{$node}{'emitterflags'} & 0x1000) ? 1 : 0;
  }
  # subheader flag data snagged from http://nwn-j3d.cvs.sourceforge.net/nwn-j3d/nwn/c-src/mdl2ascii.cpp?revision=1.31&view=markup

  if ( $nodetype == NODE_REFERENCE ) { # reference
    $ref->{$node}{'refModel'} = $ref->{$node}{'subhead'}{'unpacked'}[0];
    $ref->{$node}{'reattachable'} = $ref->{$node}{'subhead'}{'unpacked'}[1];
  }

  if ( $nodetype & NODE_HAS_MESH ) {
    $ref->{$node}{'facesloc'} = $ref->{$node}{'subhead'}{'unpacked'}[2];
    $ref->{$node}{'facesnum'} = $ref->{$node}{'subhead'}{'unpacked'}[3];
    $ref->{$node}{'bboxmin'} = [@{$ref->{$node}{'subhead'}{'unpacked'}}[5..7]];
    $ref->{$node}{'bboxmax'} = [@{$ref->{$node}{'subhead'}{'unpacked'}}[8..10]];
    $ref->{$node}{'radius'} = $ref->{$node}{'subhead'}{'unpacked'}[11];
    $ref->{$node}{'average'} = [@{$ref->{$node}{'subhead'}{'unpacked'}}[12..14]];
    $ref->{$node}{'diffuse'} = [@{$ref->{$node}{'subhead'}{'unpacked'}}[15..17]];
    $ref->{$node}{'ambient'} = [@{$ref->{$node}{'subhead'}{'unpacked'}}[18..20]];
    $ref->{$node}{'transparencyhint'} = $ref->{$node}{'subhead'}{'unpacked'}[21];
    $ref->{$node}{'bitmap'} = $ref->{$node}{'subhead'}{'unpacked'}[22];
    $ref->{$node}{'bitmap2'} = $ref->{$node}{'subhead'}{'unpacked'}[23];
    $ref->{$node}{'texture0'} = $ref->{$node}{'subhead'}{'unpacked'}[24];
    $ref->{$node}{'texture1'} = $ref->{$node}{'subhead'}{'unpacked'}[25];
    $ref->{$node}{'vertnumloc'} = $ref->{$node}{'subhead'}{'unpacked'}[26];
    $ref->{$node}{'vertlocloc'} = $ref->{$node}{'subhead'}{'unpacked'}[29];
    $ref->{$node}{'unknown'} = $ref->{$node}{'subhead'}{'unpacked'}[32];
    # the following 5 things are hypothetical at this point
    $ref->{$node}{'animateuv'} = $ref->{$node}{'subhead'}{'unpacked'}[46];
    if ($ref->{$node}{'animateuv'}) {
      # animateuv = 1 but still check for garbage just in case
      $ref->{$node}{'uvdirectionx'} = $ref->{$node}{'subhead'}{'unpacked'}[47] !~ /(?:nan|inf)/i
                                        ? $ref->{$node}{'subhead'}{'unpacked'}[47] : 0.0;
      $ref->{$node}{'uvdirectiony'} = $ref->{$node}{'subhead'}{'unpacked'}[48] !~ /(?:nan|inf)/i
                                        ? $ref->{$node}{'subhead'}{'unpacked'}[48] : 0.0;
      $ref->{$node}{'uvjitter'} = $ref->{$node}{'subhead'}{'unpacked'}[49] !~ /(?:nan|inf)/i
                                    ? $ref->{$node}{'subhead'}{'unpacked'}[49] : 0.0;
      $ref->{$node}{'uvjitterspeed'} = $ref->{$node}{'subhead'}{'unpacked'}[50] !~ /(?:nan|inf)/i
                                         ? $ref->{$node}{'subhead'}{'unpacked'}[50] : 0.0;
    } else {
      # zero the values that bioware left as garbage
      $ref->{$node}{'uvdirectionx'}  = 0.0;
      $ref->{$node}{'uvdirectiony'}  = 0.0;
      $ref->{$node}{'uvjitter'}      = 0.0;
      $ref->{$node}{'uvjitterspeed'} = 0.0;
    }
    $ref->{$node}{'mdxdatasize'} = $ref->{$node}{'subhead'}{'unpacked'}[51];
    # the MDX data bitmap contains a bit for each element present in MDX data rows
    $ref->{$node}{'mdxdatabitmap'} = $ref->{$node}{'subhead'}{'unpacked'}[52];
    #$ref->{$node}{'loc61'} = $ref->{$node}{'subhead'}{'unpacked'}[54];
    #$ref->{$node}{'loc62'} = $ref->{$node}{'subhead'}{'unpacked'}[55];
    #$ref->{$node}{'loc65'} = $ref->{$node}{'subhead'}{'unpacked'}[58];
    # offset to vertices in MDX row
    $ref->{$node}{'mdxvertcoordsloc'} = $ref->{$node}{'subhead'}{'unpacked'}[53];
    # offset to vertex normals in MDX row
    $ref->{$node}{'mdxvertnormalsloc'} = $ref->{$node}{'subhead'}{'unpacked'}[54];
    # offset to vertex colors in MDX row
    $ref->{$node}{'mdxvertcolorsloc'} = $ref->{$node}{'subhead'}{'unpacked'}[55];
    # offset to texture0 tvertices in MDX row
    $ref->{$node}{'mdxtex0vertsloc'} = $ref->{$node}{'subhead'}{'unpacked'}[56];
    # offset to texture1 tvertices in MDX row
    $ref->{$node}{'mdxtex1vertsloc'} = $ref->{$node}{'subhead'}{'unpacked'}[57];
    # offset to texture2 tvertices in MDX row
    $ref->{$node}{'mdxtex2vertsloc'} = $ref->{$node}{'subhead'}{'unpacked'}[58];
    # offset to texture3 tvertices in MDX row
    $ref->{$node}{'mdxtex3vertsloc'} = $ref->{$node}{'subhead'}{'unpacked'}[59];
    # offset to tangent space (bumpmap) info in MDX row
    $ref->{$node}{'mdxtanspaceloc'} = $ref->{$node}{'subhead'}{'unpacked'}[60];

    $ref->{$node}{'vertcoordnum'} = $ref->{$node}{'subhead'}{'unpacked'}[64];
    $ref->{$node}{'texturenum'} = $ref->{$node}{'subhead'}{'unpacked'}[65];

    $ref->{$node}{'lightmapped'} = $ref->{$node}{'subhead'}{'unpacked'}[66];
    $ref->{$node}{'rotatetexture'} = $ref->{$node}{'subhead'}{'unpacked'}[67];
    $ref->{$node}{'m_bIsBackgroundGeometry'} = $ref->{$node}{'subhead'}{'unpacked'}[68];
    $ref->{$node}{'shadow'} = $ref->{$node}{'subhead'}{'unpacked'}[69];
    $ref->{$node}{'beaming'} = $ref->{$node}{'subhead'}{'unpacked'}[70];
    $ref->{$node}{'render'} = $ref->{$node}{'subhead'}{'unpacked'}[71];

    if ($uoffset == 0) {
        # SLL 72,73,74 = should be CCSSCCCC
        my $k2_fields = [ unpack('CCSSCCCC', pack('SLL',  @{$ref->{$node}{'subhead'}{'unpacked'}}[72..74])) ];
        # kotor2 specific things: dirt_enabled, dirt_texture, dirt_worldspace, hologram_donotdraw
        # these are not specifically/correctly unpacked by the main template
        #$ref->{$node}{'dirt_enabled'} = unpack('C', pack('C[2]', $ref->{$node}{'subhead'}{'unpacked'}[72]));
        $ref->{$node}{'dirt_enabled'}    = $k2_fields->[0];
        $ref->{$node}{'dirt_texture'}    = $k2_fields->[2];
        $ref->{$node}{'dirt_worldspace'} = $k2_fields->[3];
        # prevent tongue & teeth from showing up inside closed mouths in holograms:
        $ref->{$node}{'hologram_donotdraw'} = $k2_fields->[4];
        #$ref->{$node}{'hologram_donotdraw'} = $ref->{$node}{'subhead'}{'unpacked'}[74] % 2;
    }

    #XXX not sure this is really a thing ... testing:
    $ref->{$node}{'totalarea'} = $ref->{$node}{'subhead'}{'unpacked'}[75 + $uoffset];

    $ref->{$node}{'MDXdataloc'} = $ref->{$node}{'subhead'}{'unpacked'}[77 + $uoffset];
    $ref->{$node}{'vertcoordloc'} = $ref->{$node}{'subhead'}{'unpacked'}[78 + $uoffset];
    if ( $nodetype == NODE_DANGLYMESH ) {
      $ref->{$node}{'displacement'} = $ref->{$node}{'subhead'}{'unpacked'}[82 + $uoffset];
      $ref->{$node}{'tightness'} = $ref->{$node}{'subhead'}{'unpacked'}[83 + $uoffset];
      $ref->{$node}{'period'} = $ref->{$node}{'subhead'}{'unpacked'}[84 + $uoffset];
    } elsif ( $nodetype == NODE_SKIN ) {
      # MDX row offsets for skin-specific data, bone weights & bone indices
      $ref->{$node}{'mdxboneweightsloc'} = $ref->{$node}{'subhead'}{'unpacked'}[82 + $uoffset];
      $ref->{$node}{'mdxboneindicesloc'} = $ref->{$node}{'subhead'}{'unpacked'}[83 + $uoffset];
      $ref->{$node}{'mdxdatabitmap'} |= MDX_BONE_WEIGHTS | MDX_BONE_INDICES;
      # weights
      $ref->{$node}{'weightsloc'} = $ref->{$node}{'subhead'}{'unpacked'}[84 + $uoffset];
      $ref->{$node}{'weightsnum'} = $ref->{$node}{'subhead'}{'unpacked'}[85 + $uoffset];
      # qbone_ref_inv
      $ref->{$node}{'qbone_ref_invloc'} = $ref->{$node}{'subhead'}{'unpacked'}[86 + $uoffset];
      $ref->{$node}{'qbone_ref_invnum'} = $ref->{$node}{'subhead'}{'unpacked'}[87 + $uoffset];
      # tbone_ref_inv
      $ref->{$node}{'tbone_ref_invloc'} = $ref->{$node}{'subhead'}{'unpacked'}[89 + $uoffset];
      $ref->{$node}{'tbone_ref_invnum'} = $ref->{$node}{'subhead'}{'unpacked'}[90 + $uoffset];
      # boneconstantindices
      $ref->{$node}{'boneconstantindicesloc'} = $ref->{$node}{'subhead'}{'unpacked'}[92 + $uoffset];
      $ref->{$node}{'boneconstantindicesnum'} = $ref->{$node}{'subhead'}{'unpacked'}[93 + $uoffset];
    } elsif ( $nodetype == NODE_AABB ) {
      $ref->{$node}{'aabbloc'} = $ref->{$node}{'subhead'}{'unpacked'}[79 + $uoffset];
    } elsif ( $nodetype == NODE_SABER) {
      # don't yet know much about these values, but let's record them so we can start using them
      $ref->{$node}{'saber1loc'} = $ref->{$node}{'subhead'}{'unpacked'}[79 + $uoffset];
      $ref->{$node}{'saber2loc'} = $ref->{$node}{'subhead'}{'unpacked'}[80 + $uoffset];
      $ref->{$node}{'saber3loc'} = $ref->{$node}{'subhead'}{'unpacked'}[81 + $uoffset];
      $ref->{$node}{'inv_count1'} = $ref->{$node}{'subhead'}{'unpacked'}[82 + $uoffset]; # ???
      $ref->{$node}{'inv_count2'} = $ref->{$node}{'subhead'}{'unpacked'}[83 + $uoffset]; # ???
    }
  } # if 97 or 33 or 289 or 2081
  
  # if we have "node type 33" or "node type 2081" or "node type 97" 
  # read in the vertex coordinates
  #print("vertcoordnum: " . $ref->{$node}{'vertcoordnum'} . "\n");
  
  if ($nodetype & NODE_HAS_SABER) {
    #node type 2081 seems to have 4 vertex data sections
    for (my $i = 0; $i < 4; $i++) {
      $temp = $ref->{$node}{'subhead'}{'unpacked'}[$structs{'data'}{$nodetype}[$i]{'loc'} + $uoffset] + 12;
      seek(MODELMDL, $temp, 0);
      print("$tree-$ref->{$node}{'header'}{'unpacked'}[NODEINDEX]_" . $structs{'data'}{$nodetype}[$i]{'name'} . " " . tell(MODELMDL)) if $printall;
      $ref->{$node}{$structs{'data'}{$nodetype}[$i]{'name'}}{'start'} = tell(MODELMDL);
      $temp = $ref->{$node}{'subhead'}{'unpacked'}[$structs{'data'}{$nodetype}[$i]{'num'}] * ($structs{'data'}{$nodetype}[$i]{'size'});
      read(MODELMDL, $buffer, $temp);
      print(" " . (tell(MODELMDL)-1) . "\n") if $printall;
      $ref->{$node}{$structs{'data'}{$nodetype}[$i]{'name'}}{'end'} = tell(MODELMDL)-1;
      $ref->{$node}{$structs{'data'}{$nodetype}[$i]{'name'}}{'raw'} = $buffer;
      if ($i == 6) {
        $temp = $ref->{$node}{'subhead'}{'unpacked'}[$structs{'data'}{$nodetype}[$i]{'num'}];
        $template = "f" x $temp . "s" x $temp;
      } else {
        $template = $structs{'data'}{$nodetype}[$i]{'tmplt'};
      }
      $ref->{$node}{$structs{'data'}{$nodetype}[$i]{'name'}}{'unpacked'} = [unpack($template, $buffer)];
    }
  } elsif ( ($nodetype & NODE_HAS_MESH) && ($ref->{$node}{'vertcoordnum'} > 0) ) {
    $temp = $ref->{$node}{'vertcoordloc'} + 12;
    seek(MODELMDL, $temp, 0);
    print($tree . "-" . $ref->{$node}{'header'}{'unpacked'}[NODEINDEX] . "_" . $structs{'data'}{$nodetype}{'name'} . " " . tell(MODELMDL)) if $printall;
    $ref->{$node}{'vertcoords'}{'start'} = tell(MODELMDL);
    $temp = $ref->{$node}{'vertcoordnum'} * $structs{'data'}{$nodetype}{'size'};
    read(MODELMDL, $buffer, $temp);
    print(" " . (tell(MODELMDL)-1) . "\n") if $printall;
    $ref->{$node}{'vertcoords'}{'end'} = tell(MODELMDL)-1;
    $ref->{$node}{'vertcoords'}{'raw'} = $buffer;
    $ref->{$node}{'vertcoords'}{'unpacked'} = [unpack($structs{'data'}{$nodetype}{'tmplt'}, $buffer)];
  } # if 2081 elsif 33 or 97 or 289 or 545

  # read in any arrays found in node subhead
  if ($nodetype & NODE_HAS_MESH)  {
    for (my $i = 0; $i < 10; $i++ ) {
      # data arrays 0-4 do not need the k1/k2 offest correction
      if ($i < 5) {
        $temp2 = 0;
      } else {
        $temp2 = $uoffset;
      }   
      if ($ref->{$node}{'subhead'}{'unpacked'}[$structs{'darray'}[$i]{'num'} + $temp2] != 0 && $i != 4) {
        if ($i == 5 && ($nodetype & NODE_HAS_DANGLY)) {next;}      
        if ($i == 9 && !($nodetype & NODE_HAS_DANGLY)) {next;}
        $temp = $ref->{$node}{'subhead'}{'unpacked'}[$structs{'darray'}[$i]{'loc'} + $temp2] + 12;
        seek(MODELMDL, $temp, 0);
        print("$tree-$ref->{$node}{'header'}{'unpacked'}[NODEINDEX]_$structs{'darray'}[$i]{'name'} " . tell(MODELMDL)) if $printall;
        $ref->{$node}{$structs{'darray'}[$i]{'name'}}{'start'} = tell(MODELMDL);
        read(MODELMDL, $buffer, $ref->{$node}{'subhead'}{'unpacked'}[$structs{'darray'}[$i]{'num'} + $temp2] * $structs{'darray'}[$i]{'size'});
        print(" " . (tell(MODELMDL)-1) . "\n") if $printall;
        $ref->{$node}{$structs{'darray'}[$i]{'name'}}{'end'} = tell(MODELMDL)-1;
        $ref->{$node}{$structs{'darray'}[$i]{'name'}}{'raw'} = $buffer;
        $temp = $ref->{$node}{'subhead'}{'unpacked'}[$structs{'darray'}[$i]{'num'} + $temp2];
        $ref->{$node}{$structs{'darray'}[$i]{'name'}}{'unpacked'} = [unpack($structs{'darray'}[$i]{'tmplt'} x $temp, $buffer)];
      }
    }
    # "data array4" is actually pointed to by "data array1" and "data array2"
    # so yes it is strictly not really a data array, but I don't want another
    # list branch yet.
    if ($ref->{$node}{'subhead'}{'unpacked'}[$structs{'darray'}[2]{'num'}] != 0) {
      #if we have a "data array2" then we have a "data array4" so read it in
      # "data array2" holds the location of "data array4"
      $temp = $ref->{$node}{$structs{'darray'}[2]{'name'}}{'unpacked'}[0] + 12;
      seek(MODELMDL, $temp, 0);
      print("$tree-$ref->{$node}{'header'}{'unpacked'}[NODEINDEX]_$structs{'darray'}[4]{'name'} " . tell(MODELMDL)) if $printall;
      $ref->{$node}{$structs{'darray'}[4]{'name'}}{'start'} = tell(MODELMDL);
      # "data array1" holds the number of elements of "data array4"
      read(MODELMDL, $buffer, $ref->{$node}{$structs{'darray'}[1]{'name'}}{'unpacked'}[0] * $structs{'darray'}[4]{'size'});
      print(" " . (tell(MODELMDL)-1) . "\n") if $printall;
      $ref->{$node}{$structs{'darray'}[4]{'name'}}{'end'} = tell(MODELMDL)-1;
      $ref->{$node}{$structs{'darray'}[4]{'name'}}{'raw'} = $buffer;
      $ref->{$node}{$structs{'darray'}[4]{'name'}}{'unpacked'} = [unpack($structs{'darray'}[4]{'tmplt'}, $buffer)];
    }

   #if this is an AABB node read in the AABB tree
   if($nodetype & NODE_HAS_AABB ) {
      #$temp = $ref->{$node}{'subhead'}{'unpacked'}[$structs{'darray'}[10]{'loc'} + $temp2] + 12;
      $temp = $ref->{$node}{'aabbloc'} + 12;
      seek(MODELMDL, $temp, 0);
      print("$tree-$ref->{$node}{'header'}{'unpacked'}[NODEINDEX]_$structs{'darray'}[10]{'name'} " . tell(MODELMDL)) if $printall;
      $ref->{$node}{$structs{'darray'}[10]{'name'}}{'start'} = tell(MODELMDL);

      $ref->{$node}{ $structs{'darray'}[10]{'name'} }{'raw'} = "";
      
      $temp = readaabb($ref, $node, $temp);
      
      $ref->{$node}{$structs{'darray'}[10]{'name'}}{'unpacked'} = [unpack($structs{'darray'}[10]{'tmplt'} x $temp, $ref->{$node}{ $structs{'darray'}[10]{'name'} }{'raw'})];
      
      print(" " . (tell(MODELMDL)-1) . "\n") if $printall;
      $ref->{$node}{$structs{'darray'}[10]{'name'}}{'end'} = tell(MODELMDL)-1;

      $temp--;
      
      $ref->{$node}{'aabbnodes'} = [];
      foreach(0..$temp) {
        $ref->{$node}{'aabbnodes'}[$_] = [];
        $ref->{$node}{'aabbnodes'}[$_][0] = $ref->{$node}{$structs{'darray'}[10]{'name'}}{'unpacked'}[($_ * 10)];
        $ref->{$node}{'aabbnodes'}[$_][1] = $ref->{$node}{$structs{'darray'}[10]{'name'}}{'unpacked'}[($_ * 10) + 1];
        $ref->{$node}{'aabbnodes'}[$_][2] = $ref->{$node}{$structs{'darray'}[10]{'name'}}{'unpacked'}[($_ * 10) + 2];
        $ref->{$node}{'aabbnodes'}[$_][3] = $ref->{$node}{$structs{'darray'}[10]{'name'}}{'unpacked'}[($_ * 10) + 3];
        $ref->{$node}{'aabbnodes'}[$_][4] = $ref->{$node}{$structs{'darray'}[10]{'name'}}{'unpacked'}[($_ * 10) + 4];
        $ref->{$node}{'aabbnodes'}[$_][5] = $ref->{$node}{$structs{'darray'}[10]{'name'}}{'unpacked'}[($_ * 10) + 5];
        $ref->{$node}{'aabbnodes'}[$_][6] = $ref->{$node}{$structs{'darray'}[10]{'name'}}{'unpacked'}[($_ * 10) + 8];
      }
   }

   # store the inverse mesh sequence counter from array3
   if (defined($ref->{$node}{array3}) &&
       defined($ref->{$node}{array3}{unpacked}) &&
       scalar(@{$ref->{$node}{array3}{unpacked}})) {
     $ref->{$node}{inv_count1} = $ref->{$node}{array3}{unpacked}[0];
   }

   #prepare the faces list
   $ref->{$node}{vertfaces} = {};
   # tvert indices per face
   $ref->{$node}{texindices} = [];
   for (my $i = 0; $i < $ref->{$node}{'facesnum'}; $i++) {
      $temp = ($i * 11);
      $ref->{$node}{'Afaces'}[$i] = $ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 8];
      $ref->{$node}{'Afaces'}[$i] .=" ".$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 9];
      $ref->{$node}{'Afaces'}[$i] .=" ".$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 10];
      # some models have non-bitflag-compatible smoothgroup numbers.
      # the theory w/ bitflag smooth-group numbers is that there can only be 32 max.
      # in p_bastilba in k1, there are smooth-groups numbered 251 ... an FF byte missing the 4 bit
      # of course, the vanilla models don't use bitfields in the first place so this is done for nwmax?
      # for now, just passing through sg numbers that are gt 32, also a commented technique to force it into 32 range
      $ref->{$node}{'Afaces'}[$i] .= sprintf(
        " %u", $ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 4] < 33
                 ? 2**($ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 4] - 1)
                 : $ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 4]
                 #: 2**(($ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 4] % 32) - 1)
      );
      #$ref->{$node}{'Afaces'}[$i] .=" 1";
      $ref->{$node}{'Afaces'}[$i] .=" ".$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 8];
      $ref->{$node}{'Afaces'}[$i] .=" ".$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 9];
      $ref->{$node}{'Afaces'}[$i] .=" ".$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 10];
      # store texture indices as a separate thing for convenience later
      $ref->{$node}{texindices}[$i] = [
        @{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}}[$temp + 8..$temp + 10]
      ];
      if ($nodetype & NODE_HAS_AABB) {
        # surface/material ID is important/meaningful for AABB nodes
        $ref->{$node}{'Afaces'}[$i] .= sprintf(' %u', $ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 4]);
      } else {
        # otherwise, use material "1", which will get the selected texture(s)
        $ref->{$node}{'Afaces'}[$i] .= sprintf(' %u', $ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 4]);
        #$ref->{$node}{'Afaces'}[$i] .=" 1";
      }
      #$ref->{$node}{'Afaces'}[$i] .=" ".$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 4];
      $ref->{$node}{'Bfaces'}[$i] = [@{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}}[$temp..$temp+10]];
      if (!defined($ref->{$node}{vertfaces}{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 8]})) {
        $ref->{$node}{vertfaces}{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 8]} = [];
      }
      if (!defined($ref->{$node}{vertfaces}{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 9]})) {
        $ref->{$node}{vertfaces}{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 9]} = [];
      }
      if (!defined($ref->{$node}{vertfaces}{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 10]})) {
        $ref->{$node}{vertfaces}{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 10]} = [];
      }
      $ref->{$node}{vertfaces}{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 8]} = [
        @{$ref->{$node}{vertfaces}{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 8]}}, $i
      ];
      $ref->{$node}{vertfaces}{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 9]} = [
        @{$ref->{$node}{vertfaces}{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 9]}}, $i
      ];
      $ref->{$node}{vertfaces}{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 10]} = [
        @{$ref->{$node}{vertfaces}{$ref->{$node}{$structs{'darray'}[0]{'name'}}{'unpacked'}[$temp + 10]}}, $i
      ];
    }
  }

  # if we have nodetype 97 (skin mesh node) cook the bone map stored in data array 5
  if ($nodetype & NODE_HAS_SKIN) {
    $temp = $ref->{$node}{'subhead'}{'unpacked'}[$structs{'darray'}[5]{'num'} + $uoffset];
    for (my $i = 0; $i < $temp; $i++) {
      # bonemap uses node order, not the numbers stored in node header,
      # which are, apparently, more like 'name index'
      my $node_order_index = $model->{order2nameindex}[$i];
      $ref->{$node}{'node2index'}[$node_order_index] = $ref->{$node}{'bonemap'}{'unpacked'}[$i];
      if ($ref->{$node}{'node2index'}[$node_order_index] != -1) {
        $ref->{$node}{'index2node'}[ $ref->{$node}{'bonemap'}{'unpacked'}[$i] ] = $node_order_index;
      }
    }
  }

  # if this mesh has tangent space data in the MDX, then the texture is supposed to be bump-mapped,
  # record that fact at the model level
  if ($ref->{$node}{'mdxdatabitmap'} & MDX_TANGENT_SPACE) {
    $model->{'bumpmapped_texture'}{lc $ref->{$node}{'bitmap'}} = 1;
  }

  #if we have a non-saber mesh node then we have MDX data to read in
  if (openhandle(*MODELMDX) && ($nodetype & NODE_HAS_MESH) && !($nodetype & NODE_HAS_SABER) && ($ref->{$node}{'vertcoordnum'} > 0) ) {
    $ref->{$node}{'verts'} = [];
    #we will be reading from the MDX, so no need to add 12 to addresses
    seek(MODELMDX, $ref->{$node}{'MDXdataloc'}, 0);
    print("mdx-$tree-$ref->{$node}{'header'}{'unpacked'}[NODEINDEX]_$structs{'mdxdata'}{$nodetype}{'name'} " . tell(MODELMDX)) if $printall;
    $ref->{$node}{'mdxdata'}{'start'} = tell(MODELMDX);
    $ref->{$node}{'mdxdata'}{'dnum'} = $ref->{$node}{'mdxdatasize'}/4;
    # the replacer method is actually sensitive to MDX data being fully read,
    # including all padding. it seems like MDX data is 32-byte aligned, enforce it.
    # use 32 % size or size % 32 depending on whether size is less than 32
    # examples: 32 % 24 = 8 (correct) & 64 % 32 = 0 (correct)
    my $alignment_padding = (
      (($ref->{$node}{'mdxdatasize'} % 16) + (
        ($ref->{$node}{'mdxdata'}{'start'} +
         (($ref->{$node}{'vertcoordnum'} + 1) * $ref->{$node}{'mdxdatasize'})) % 16
      )) % 16
    );
    read(MODELMDX, $buffer, ($ref->{$node}{'mdxdatasize'} * ($ref->{$node}{'vertcoordnum'} + 1)) + $alignment_padding);
    printf(" %u (%u align pad)\n", (tell(MODELMDX) - 1), $alignment_padding) if $printall;
    $ref->{$node}{'mdxdata'}{'end'} = tell(MODELMDX)-1;
    $ref->{$node}{'mdxdata'}{'raw'} = $buffer;
    #$ref->{$node}{'mdxdata'}{'unpacked'} = [unpack($structs{'mdxdata'}{$nodetype}{'tmplt'}, $buffer)];
    $ref->{$node}{'mdxdata'}{'unpacked'} = [unpack("f*", $buffer)];

    $temp = $ref->{$node}{'mdxdatasize'}/4;  # divide by 4 cuz the data is unpacked
    for (my $i = 0; $i < $ref->{$node}{'vertcoordnum'}; $i++) {
      ### NEW APPROACH TO READING MDX:
      my $row_index = $i * $temp;
      my $row_offset = 0;
      # go through all the types of MDX data
      #XXX we could copy & filter the MDX struct for each node before entering row loop
      for my $mdx_data_type (@{$structs{'mdxrows'}}) {
        if (!($ref->{$node}{'mdxdatabitmap'} & $mdx_data_type->{bitfield}) ||
            !defined($ref->{$node}{$mdx_data_type->{offset}}) ||
            $ref->{$node}{$mdx_data_type->{offset}} == -1) {
          # this type of data is not present in the MDX row
          next;
        }
        # convert from number of bytes to unpacked array index offset
        $row_offset = $ref->{$node}{$mdx_data_type->{offset}} / 4;
        # read the number of values from the row into the specified node data field
        for my $datum_index (0..$mdx_data_type->{num} - 1) {
          $ref->{$node}{$mdx_data_type->{data}}[$i][$datum_index] = $ref->{$node}{'mdxdata'}{'unpacked'}[$row_index + $row_offset + $datum_index];
        }
        # the following is too verbose even for normal verbose
        #print "read mdx $mdx_data_type->{offset} vert $i\n" if $printall;
      } # for $mdx_data_type

      ### MDX DATA POST-PROCESSING
      # if this is a skin node, cook the weights for this vertex
      if ($nodetype & NODE_HAS_SKIN) {
        # construct text representation of bone weights map
        $ref->{$node}{'Abones'}[$i] = '';
        for my $weight_num (0..3) {
          if ($ref->{$node}{'boneweights'}[$i][$weight_num] == 0 ||
              $ref->{$node}{'boneindices'}[$i][$weight_num] == -1) {
            # skip 0 value weights and -1 bone indices
            # in the ASCII bone weight construction
            next;
          }
          my $bone_name = $model->{'partnames'}[
            $ref->{$node}{'index2node'}[$ref->{$node}{'boneindices'}[$i][$weight_num]]
          ];
          $ref->{$node}{'Abones'}[$i] .= sprintf('%s %.7g ', $bone_name, $ref->{$node}{'boneweights'}[$i][$weight_num]);
        }
        # clean off the superfluous trailing space character
        $ref->{$node}{'Abones'}[$i] =~ s/\s+$//;
        # construct binary representation of bone weights map
        $ref->{$node}{'Bbones'}[$i] = [ @{$ref->{$node}{'boneweights'}[$i]},
                                        @{$ref->{$node}{'boneindices'}[$i]} ];
      }
      # if this is a dangly node, cook the constraints for this vertex
      # NOTE: this is here for historical reasons, and isn't even MDX data...
      # according to the original situation of the code,
      # it should only run on textured danglymesh?
      if ($nodetype & NODE_HAS_DANGLY) {
        $ref->{$node}{'constraints'}[$i] = $ref->{$node}{$structs{'darray'}[9]{'name'}}{'unpacked'}[$i];
      }
    } # for $i
  } # if 33 or 97 or 289 or 545
  
  if ($nodetype & NODE_HAS_SABER) {
    $temp = $ref->{$node}{'subhead'}{'unpacked'}[$structs{'data'}{$nodetype}[0]{'num'}];
    for (my $i = 0; $i < $temp; $i++) {
      $ref->{$node}{'verts'}[$i][0] = $ref->{$node}{'vertcoords'}{'unpacked'}[($i * 3) + 0];
      $ref->{$node}{'verts'}[$i][1] = $ref->{$node}{'vertcoords'}{'unpacked'}[($i * 3) + 1];
      $ref->{$node}{'verts'}[$i][2] = $ref->{$node}{'vertcoords'}{'unpacked'}[($i * 3) + 2];
      if ($ref->{$node}{'texturenum'} != 0) {
        $ref->{$node}{'tverts'}[$i][0] = $ref->{$node}{'tverts+'}{'unpacked'}[($i * 2) + 0];
        $ref->{$node}{'tverts'}[$i][1] = $ref->{$node}{'tverts+'}{'unpacked'}[($i * 2) + 1];
      }
      # these are the vertices that saber mesh uses
      $ref->{$node}{'saber_verts'}[$i][0] = $ref->{$node}{'vertcoords2'}{'unpacked'}[($i * 3) + 0];
      $ref->{$node}{'saber_verts'}[$i][1] = $ref->{$node}{'vertcoords2'}{'unpacked'}[($i * 3) + 1];
      $ref->{$node}{'saber_verts'}[$i][2] = $ref->{$node}{'vertcoords2'}{'unpacked'}[($i * 3) + 2];
      # the face/vertex normals for the saber mesh plane
      $ref->{$node}{'saber_norms'}[$i][0] = $ref->{$node}{'data2081-3'}{'unpacked'}[($i * 3) + 0];
      $ref->{$node}{'saber_norms'}[$i][1] = $ref->{$node}{'data2081-3'}{'unpacked'}[($i * 3) + 1];
      $ref->{$node}{'saber_norms'}[$i][2] = $ref->{$node}{'data2081-3'}{'unpacked'}[($i * 3) + 2];
    }
  } # if 2081

  
  #if this node has any children then we call this function again
  $numchildren = $ref->{$node}{'childcount'};
  if ($numchildren != 0) {
    $temp = $ref->{$node}{'childrenloc'} + 12;
    seek(MODELMDL, $temp, 0);
    $ref->{$node}{'childindexes'}{'start'} = tell(MODELMDL);
    if ($tree =~ /^anims/) {
      $model->{'nodesort'}{$animnum}{tell(MODELMDL)} = $node . "-childindexes";
    }
    read(MODELMDL, $buffer, $numchildren * 4);
    $ref->{$node}{'childindexes'}{'end'} = tell(MODELMDL)-1;
    @children = unpack("l[$numchildren]", $buffer);
    $ref->{$node}{'childindexes'}{'raw'} = $buffer;
    $ref->{$node}{'childindexes'}{'unpacked'} = [@children];
    # a list of childindex nodenums, rather than byte offsets
    $ref->{$node}{'childindexes'}{'nums'} = [];
    foreach (@children) {
      $work = $work + getnodes($tree, $ref->{$node}, $_, $model, $version) ;
    }    
  }
  return $work;
}

#########################################################
# get a list of the nodes in the order they should be encountered,
# this means traversing the node tree to produce a flattened list.
# recursive, called by writeasciimdl
#
sub getnodelist {
  my ($model, $node_num) = (@_);
  # nodes is the list of node numbers, indexes into model->{nodes},
  # initialize it with the number of current/starting node
  my $nodes = [ $node_num ];
  # hold a convenient reference to the current/starting node
  my $node = $model->{'nodes'}{$node_num};

  if ($node->{'childcount'} && scalar(@{$node->{'childindexes'}{'nums'}})) {
    foreach (@{$node->{'childindexes'}{'nums'}}) {
      # append child node numbers list, recursing
      $nodes = [ @{$nodes}, @{getnodelist($model, $_)} ];
    }
  }

  return $nodes;
}


#########################################################
# this function will remap all the needed data from a saber mesh node
# into a trimesh node, suitable for ASCII output
sub convert_saber_to_trimesh {
  my ($model, $nodenumber) = @_;
  my $sabernode = $model->{nodes}{$nodenumber};

  # start with a copy of the saber mesh node
  my $meshnode = { %{$sabernode} };

  # set node type
#printf("%d\n", $meshnode->{nodetype} );
  $meshnode->{nodetype} = NODE_TRIMESH;
  #
  # change node name
  my $orig_name = $model->{'partnames'}[$nodenumber];
  $model->{'partnames'}[$nodenumber] = '2081__' . $model->{'partnames'}[$nodenumber];
  delete $model->{nodeindex}{$orig_name};
  $model->{nodeindex}{$model->{'partnames'}[$nodenumber]} = $nodenumber;

  # find blade width as vertex position difference
  my $blade_width = [ map {
    $sabernode->{verts}[4][$_] - $sabernode->{verts}[0][$_]
  } (0..2) ];
#  print Dumper($blade_width);
#  print Dumper([@{$sabernode->{verts}}[0..3]]);
#  print Dumper([@{$sabernode->{verts}}[88..91]]);

  # convert vertex positions list
  $meshnode->{verts} = [
    @{$sabernode->{verts}}[0..3],
    map { my $vert = $_; [ map {
      $vert->[$_] + $blade_width->[$_]
    } (0..2) ] } @{$sabernode->{verts}}[0..3]
  ];
  # for some inexplicable reason, this breaks when you do it in one statement,
  # so i broke up blade1 & blade2 vert translation into two statements. wtf?
  # i think it was a lack of parenthesis wrapping on the map clauses
  $meshnode->{verts} = [
    @{$meshnode->{verts}},
    @{$sabernode->{verts}}[88..91],
    map { my $vert = $_; [ map {
      $vert->[$_] - $blade_width->[$_]
    } (0..2) ] } @{$sabernode->{verts}}[88..91]
  ];
  # update vertex coordinates total
  $meshnode->{vertcoordnum} = scalar(@{$meshnode->{verts}});
#  printf("%d\n", $meshnode->{vertcoordnum});
#  print Dumper([@{$meshnode->{verts}}[4..7]]);
#  print Dumper([@{$meshnode->{verts}}[12..15]]);
#  print Dumper($meshnode->{verts});
#print Dumper($meshnode->{verts});
#die;
#print Dumper($sabernode->{tverts});
#printf("tverts: %u\n", scalar(@{$sabernode->{tverts}}));
#print Dumper($sabernode->{tverts}[0]);
#printf("tverts+: %u\n", scalar(@{$sabernode->{'tverts+'}}));

  # convert tverts
  $meshnode->{tverts} = [
    @{$sabernode->{tverts}}[0..7,88..95]
  ];
#print Dumper($meshnode->{tverts});
  # faces is good?
#print Dumper($meshnode->{Afaces});

  # use known/pre-canned face structure
  $meshnode->{Afaces} = [
    '5 4 0 1 5 4 0 0',
    '0 1 5 1 0 1 5 0',
    '13 8 12 1 13 8 12 0',
    '8 13 9 1 8 13 9 0',
    '6 5 1 1 6 5 1 0',
    #'2 6 5 1 2 6 5 0',
    '1 2 6 1 1 2 6 0',
    #'1 2 5 1 1 2 5 0',
    '10 9 13 1 10 9 13 0',
    '13 14 10 1 13 14 10 0',
    '3 6 2 1 3 6 2 0',
    '6 3 7 1 6 3 7 0',
    '15 11 14 1 15 11 14 0',
    '10 14 11 1 10 14 11 0',
  ];
#print Dumper($meshnode->{Afaces});

  # synthesize MDXbitmap
  $meshnode->{mdxdatabitmap} = MDX_VERTICES | MDX_VERTEX_NORMALS | MDX_TEX0_VERTICES;

  return $meshnode;
}


#########################################################
# this function will remap all the needed data from a plane trimesh node
# into a lightsaber mesh node, suitable for binary output
sub convert_trimesh_to_saber {
  my ($model, $nodenumber) = @_;
  my $meshnode = $model->{nodes}{$nodenumber};

  # start with a copy of the trimesh node
  my $sabernode = { %{$meshnode} };

  # find our key points by face
  #print Dumper($meshnode->{Afaces});
  #print Dumper($meshnode->{Bfaces});

  # original, symmetrical planes had a nice feature,
  # each vertex could be identified by the number of faces it touched
  # outside corners             = 1 x 4
  # inner edge (rows 0,1,3)     = 2 x 6
  # row 2                       = 3 x 4
  # row one outer edge          = 4 x 2
  # unfortunately for us, bioware messed up interpreting this structure,
  # inverting the geometry of the first blade,
  # we export it as it will be seen in the game,
  # so we need to convert from more difficult, wrong geometry
  # blade1 - bioware/wrong edition:
  # outside corners             = 1
  # inner edge (rows 0,2,3)     = 2
  # row 1                       = 3
  # row 2 outer edge            = 4

  # it would be possible to do *some* welding before reaching here,
  # but you'd probably weld the center line, or whatever parts of it
  # might be overlapping, which isn't great

  # count adjacent faces of each vertex for each face
  my $facecounts = {};
  for my $face (@{$meshnode->{Bfaces}}) {
    for my $vert_index (@{$face}[8..10]) {
      if (!defined($facecounts->{$vert_index})) {
        $facecounts->{$vert_index} = 0;
      }
      $facecounts->{$vert_index} += 1;
    }
  }
  #print Dumper($facecounts);

  # handle kotormax doubled number of faces,
  # added because max's 2-sided support seems weak
  my $plane_faces = 12;
  my $count_factor = 1;
  if (scalar(@{$meshnode->{Bfaces}}) > $plane_faces) {
    $count_factor = int(scalar(@{$meshnode->{Bfaces}}) / $plane_faces);
  }

  # now classify the vertex indices by 'role' or 'type'
  my $corners = [
    grep { $facecounts->{$_} == 1 * $count_factor } keys %{$facecounts}
  ];
  #print "corners\n";
  #print Dumper($corners);
  my $row_two = [
    grep { $facecounts->{$_} == 3 * $count_factor } keys %{$facecounts}
  ];
  #print "row two\n";
  #print Dumper($row_two);
  my $inner_edge = [
    grep { $facecounts->{$_} == 2 * $count_factor } keys %{$facecounts}
  ];
  #print "inner edge\n";
  #print Dumper($inner_edge);
  my $row_one_outer = [
    grep { $facecounts->{$_} == 4 * $count_factor } keys %{$facecounts}
  ];
  #print "row one outer edge\n";
  #print Dumper($row_one_outer);

  # two blades, 8 verts per blade, examples:
  # blade 1 inner edge bottom: [0][0][0]
  # blade 1 outer edge top:    [0][3][1]
  # blade 2 inner edge bottom: [1][0][0]
  # blade 2 outer edge top:    [1][3][1]

  # start off by just assigning blade1 and blade2,
  # using the 2 vertices we know cannot be in the same blade,
  # the ones touching 4 faces,
  # we will swap them later if we got it wrong
  my $blades = [
    # blade1
    [ [-1,-1], [-1, $row_one_outer->[0]], [-1,-1], [-1,-1] ],
    # blade2
    [ [-1,-1], [-1, $row_one_outer->[1]], [-1,-1], [-1,-1] ],
  ];

  # hash of vertex indices, classified by blade, vert index => true
  my $verts_by_blade = {
    blade1 => {},
    blade2 => {},
  };
  # lists of face indices, classified by blade, face index => true
  my $faces_by_blade = {
    blade1 => {},
    blade2 => {},
  };

  # the following is a search through the geometry, by index,
  my $vertices_crawled = 0;
  my ($b1vert, $b2vert);
  # starting from each of our two known points in the 2 blades
  my @b1search = ($row_one_outer->[0]);
  my @b2search = ($row_one_outer->[1]);
  my $searched = {};
  # while we have indices remaining to search
  while (scalar(@b1search) || scalar(@b2search)) {
    # grab a vertex index for blade1 if any remain
    if (scalar(@b1search)) {
      $b1vert = shift @b1search;
    } else {
      $b1vert = undef;
    }
    # grab a vertex index for blade2 if any remain
    if (scalar(@b2search)) {
      $b2vert = shift @b2search;
    } else {
      $b2vert = undef;
    }
    # test each face in the mesh node
    for my $index (keys @{$meshnode->{Bfaces}}) {
      my $face = $meshnode->{Bfaces}[$index];
      # v0 of this face is the blade1 search vertex
      if (defined($b1vert) && $face->[8] == $b1vert) {
        $verts_by_blade->{blade1}{$b1vert} = 1;
        $faces_by_blade->{blade1}{$index} = 1;
        # first time this face has matched a search,
        # add its other two vertices to the search list
        if (!defined($searched->{$face->[9]})) {
          $searched->{$face->[9]} = 1;
          push @b1search, $face->[9];
        }
        if (!defined($searched->{$face->[10]})) {
          $searched->{$face->[10]} = 1;
          push @b1search, $face->[10];
        }
      }
      # v1 of this face is the blade1 search vertex
      if (defined($b1vert) && $face->[9] == $b1vert) {
        $verts_by_blade->{blade1}{$b1vert} = 1;
        $faces_by_blade->{blade1}{$index} = 1;
        # first time this face has matched a search,
        # add its other two vertices to the search list
        if (!defined($searched->{$face->[8]})) {
          $searched->{$face->[8]} = 1;
          push @b1search, $face->[8];
        }
        if (!defined($searched->{$face->[10]})) {
          $searched->{$face->[10]} = 1;
          push @b1search, $face->[10];
        }
      }
      # v2 of this face is the blade1 search vertex
      if (defined($b1vert) && $face->[10] == $b1vert) {
        $verts_by_blade->{blade1}{$b1vert} = 1;
        $faces_by_blade->{blade1}{$index} = 1;
        # first time this face has matched a search,
        # add its other two vertices to the search list
        if (!defined($searched->{$face->[8]})) {
          $searched->{$face->[8]} = 1;
          push @b1search, $face->[8];
        }
        if (!defined($searched->{$face->[9]})) {
          $searched->{$face->[9]} = 1;
          push @b1search, $face->[9];
        }
      }
      # v0 of this face is the blade2 search vertex
      if (defined($b2vert) && $face->[8] == $b2vert) {
        $verts_by_blade->{blade2}{$b2vert} = 1;
        $faces_by_blade->{blade2}{$index} = 1;
        # first time this face has matched a search,
        # add its other two vertices to the search list
        if (!defined($searched->{$face->[9]})) {
          $searched->{$face->[9]} = 1;
          push @b2search, $face->[9];
        }
        if (!defined($searched->{$face->[10]})) {
          $searched->{$face->[10]} = 1;
          push @b2search, $face->[10];
        }
      }
      # v1 of this face is the blade2 search vertex
      if (defined($b2vert) && $face->[9] == $b2vert) {
        $verts_by_blade->{blade2}{$b2vert} = 1;
        $faces_by_blade->{blade2}{$index} = 1;
        # first time this face has matched a search,
        # add its other two vertices to the search list
        if (!defined($searched->{$face->[8]})) {
          $searched->{$face->[8]} = 1;
          push @b2search, $face->[8];
        }
        if (!defined($searched->{$face->[10]})) {
          $searched->{$face->[10]} = 1;
          push @b2search, $face->[10];
        }
      }
      # v2 of this face is the blade2 search vertex
      if (defined($b2vert) && $face->[10] == $b2vert) {
        $verts_by_blade->{blade2}{$b2vert} = 1;
        $faces_by_blade->{blade2}{$index} = 1;
        # first time this face has matched a search,
        # add its other two vertices to the search list
        if (!defined($searched->{$face->[8]})) {
          $searched->{$face->[8]} = 1;
          push @b2search, $face->[8];
        }
        if (!defined($searched->{$face->[9]})) {
          $searched->{$face->[9]} = 1;
          push @b2search, $face->[9];
        }
      }
    }
  }
  #print Dumper($faces_by_blade);
  #print Dumper($verts_by_blade);

  # we now have the faces and vertices separated into two blades,
  # but we need to determine which is blade1 and which is blade2,
  # with borked bioware layout,
  # test whether the 4 point Z coord > 3 point Z coords, if so, blade1
  # $row_one_outer has 4 points, $row_two has 3 points
  my $b1_test = {};
  my $b1_4point;
  #print Dumper($meshnode->{verts});
  # go through list of row one outer points
  for my $test (@{$row_one_outer}) {
    # only testing blade1 vertices though
    if (defined($verts_by_blade->{blade1}{$test})) {
      $b1_4point = $test;
      $b1_test->{$test} = $meshnode->{verts}[$test];
      last;
    }
  }
  for my $test (@{$row_two}) {
    if (defined($verts_by_blade->{blade1}{$test})) {
      $b1_test->{$test} = $meshnode->{verts}[$test];
    }
  }
  # b1_test hash now contains blade1 row_one_outer and all blade1 row_two,
  # sort the list by z coordinate (not testing inside/outside, but top/bottom)
  my $b1_sort = [ sort { $b1_test->{$a}[2] <=> $b1_test->{$b}[2] } keys %{$b1_test} ];
  #print Dumper($b1_4point);
  #print Dumper($b1_sort);
  #print Dumper($b1_test);
  #print "tested\n";
  # if the first element in the sorted list is b1 row_one_outer,
  # then the 4-point is closer to the hilt and this is actually blade2
  if ($b1_sort->[0] == $b1_4point) {
    # swap the blade data via temporary items
    #print "BLADE2 FOUND, SWITCH\n";
    #print Dumper($verts_by_blade);
    $verts_by_blade->{blade3} = { %{$verts_by_blade->{blade1}} };
    $verts_by_blade->{blade1} = { %{$verts_by_blade->{blade2}} };
    $verts_by_blade->{blade2} = $verts_by_blade->{blade3};
    delete $verts_by_blade->{blade3};
    #print Dumper($verts_by_blade);
    #print Dumper($faces_by_blade);
    $faces_by_blade->{blade3} = { %{$faces_by_blade->{blade1}} };
    $faces_by_blade->{blade1} = { %{$faces_by_blade->{blade2}} };
    $faces_by_blade->{blade2} = $faces_by_blade->{blade3};
    delete $faces_by_blade->{blade3};
    #print Dumper($faces_by_blade);
    #print Dumper($blades);
    $blades->[2] = [ @{$blades->[0]} ];
    $blades->[0] = $blades->[1];
    $blades->[1] = [ @{$blades->[2]} ];
    delete $blades->[2];
    $blades->[0][2][1] = $blades->[0][1][1];
    $blades->[0][1][1] = -1;
    #print Dumper($blades);
  }

  # finish filling in the blades structure now that we know which blade is which
  # we're doing row selection based on mostly z comparisons
  my $blade_keys = { blade1 => 0, blade2 => 1 };
  for my $blade_key (keys %{$blade_keys}) {
    my $blade_index = $blade_keys->{$blade_key};
    # start with the corners
    my $b1_corners = {};
    for my $corner (@{$corners}) {
      if (defined($verts_by_blade->{$blade_key}{$corner})) {
        $b1_corners->{$corner} = $meshnode->{verts}[$corner];
      }
    }
    my $corner_sort = [ sort { $b1_corners->{$a}[2] <=> $b1_corners->{$b}[2] } keys %{$b1_corners} ];
    $blades->[$blade_index][0][1] = $corner_sort->[0];
    $blades->[$blade_index][3][1] = $corner_sort->[1];

    # then the inner edge
    my $b1_inner_edge = {};
    for my $ie (@{$inner_edge}) {
      if (defined($verts_by_blade->{$blade_key}{$ie})) {
        $b1_inner_edge->{$ie} = $meshnode->{verts}[$ie];
      }
    }
    my $ie_sort = [ sort { $b1_inner_edge->{$a}[2] <=> $b1_inner_edge->{$b}[2] } keys %{$b1_inner_edge} ];
    if ($blade_key eq 'blade2') {
      $blades->[$blade_index][0][0] = $ie_sort->[0];
      $blades->[$blade_index][1][0] = $ie_sort->[1];
      $blades->[$blade_index][3][0] = $ie_sort->[2];
    } else {
      $blades->[$blade_index][0][0] = $ie_sort->[0];
      $blades->[$blade_index][2][0] = $ie_sort->[1];
      $blades->[$blade_index][3][0] = $ie_sort->[2];
    }

    # then row two
    my $b1_row_two = {};
    for my $row2 (@{$row_two}) {
      if (defined($verts_by_blade->{$blade_key}{$row2})) {
        $b1_row_two->{$row2} = $meshnode->{verts}[$row2];
      }
    }
    my $r2_sort = [ sort { $b1_row_two->{$a}[0] <=> $b1_row_two->{$b}[0] } keys %{$b1_row_two} ];
    if ($meshnode->{verts}[$blades->[$blade_index][0][0]]->[0] > $meshnode->{verts}[$blades->[$blade_index][0][1]]->[0]) {
      $r2_sort = [ reverse @{$r2_sort} ];
    }
    if ($blade_key eq 'blade2') {
      $blades->[$blade_index][2][0] = $r2_sort->[0];
      $blades->[$blade_index][2][1] = $r2_sort->[1];
    } else {
      $blades->[$blade_index][1][0] = $r2_sort->[0];
      $blades->[$blade_index][1][1] = $r2_sort->[1];
    }
    #print Dumper($b1_corners);
    #print Dumper($b1_inner_edge);
    #print Dumper($b1_row_two);
  }
  #print Dumper($blades);

  my $index_pattern = [ 0, 1, (0) x 20, 2, 3, (2) x 20 ];
  # vertices:
  # blade1 0,0 1,0 2,0 3,0; blade1 0,1 1,1 2,1 3,1;
  # blade1 0,0 1,0 2,0 3,0 x 20;
  # blade2 0,0 1,0 2,0 3,0; blade2 0,1 1,1 2,1 3,1;
  # blade2 0,0 1,0 2,0 3,0 x 20;
  my $vert_indices = [
    [ $blades->[0][0][0], $blades->[0][1][0], $blades->[0][2][0], $blades->[0][3][0] ],
    [ $blades->[0][0][1], $blades->[0][1][1], $blades->[0][2][1], $blades->[0][3][1] ],
    [ $blades->[1][0][0], $blades->[1][1][0], $blades->[1][2][0], $blades->[1][3][0] ],
    [ $blades->[1][0][1], $blades->[1][1][1], $blades->[1][2][1], $blades->[1][3][1] ],
  ];
  my $verts = [];
  foreach (@{$vert_indices}) {
    $verts = [ @{$verts}, [ map {$meshnode->{verts}[$_]} @{$_} ] ];
  }
  #print Dumper($verts);

  #print Dumper($index_pattern);
  #my $verts_final = [ map { @{$verts->[$_]} } @{$index_pattern} ];
  #print Dumper($verts_final);
  #die;

  # tverts:
  # blade1 0,0 1,0 2,0 3,0, blade1 0,1 1,1 2,1 3,1
  # blade1 0,0 1,0 2,0 3,0 x 20
  # blade2 0,0 1,0 2,0 3,0, blade2 0,1 1,1 2,1 3,1
  # blade2 0,0 1,0 2,0 3,0 x 20
  my $tvert_indices = [
    [ $meshnode->{tverti}{$blades->[0][0][0]}, $meshnode->{tverti}{$blades->[0][1][0]}, $meshnode->{tverti}{$blades->[0][2][0]}, $meshnode->{tverti}{$blades->[0][3][0]} ],
    [ $meshnode->{tverti}{$blades->[0][0][1]}, $meshnode->{tverti}{$blades->[0][1][1]}, $meshnode->{tverti}{$blades->[0][2][1]}, $meshnode->{tverti}{$blades->[0][3][1]} ],
    [ $meshnode->{tverti}{$blades->[1][0][0]}, $meshnode->{tverti}{$blades->[1][1][0]}, $meshnode->{tverti}{$blades->[1][2][0]}, $meshnode->{tverti}{$blades->[1][3][0]} ],
    [ $meshnode->{tverti}{$blades->[1][0][1]}, $meshnode->{tverti}{$blades->[1][1][1]}, $meshnode->{tverti}{$blades->[1][2][1]}, $meshnode->{tverti}{$blades->[1][3][1]} ],
  ];
  my $tverts = [];
  foreach (@{$tvert_indices}) {
    $tverts = [ @{$tverts}, [ map {$meshnode->{tverts}[$_]} @{$_} ] ];
  }
  #print Dumper($tverts);

  # normals:
  # blade 2, bottom outside corner (1,1),(0,1),(0,0)
  # blade 2, bottom inside (0,0),(1,0),(1,1)
  # blade 1, bottom outside corner (0,1),(1,1),(0,0)
  # blade 1, bottom inside (0,0),(1,1),(1,0)
  # repeat 44 times

  # we have to calculate these for all lightsaber mesh, including unconverted,
  # so now this calculation resides directly in readasciimdl,
  # at the call site of this function
#  my $normal_face_indices = [
#    [ $blades->[1][1][1], $blades->[1][0][1], $blades->[1][0][0] ],
#    [ $blades->[1][0][0], $blades->[1][1][0], $blades->[1][1][1] ],
#    [ $blades->[0][0][1], $blades->[0][1][1], $blades->[0][0][0] ],
#    [ $blades->[0][0][0], $blades->[0][1][1], $blades->[0][1][0] ],
#  ];
#  my $face_normals = [];
#  foreach (@{$normal_face_indices}) {
#    my ($v1, $v2, $v3) = map {@{$meshnode->{verts}}[$_]} @{$_};
#    my $normal_vector =
#    [
#      $v1->[1] * ($v2->[2] - $v3->[2]) +
#      $v2->[1] * ($v3->[2] - $v1->[2]) +
#      $v3->[1] * ($v1->[2] - $v2->[2]),
#      $v1->[2] * ($v2->[0] - $v3->[0]) +
#      $v2->[2] * ($v3->[0] - $v1->[0]) +
#      $v3->[2] * ($v1->[0] - $v2->[0]),
#      $v1->[0] * ($v2->[1] - $v3->[1]) +
#      $v2->[0] * ($v3->[1] - $v1->[1]) +
#      $v3->[0] * ($v1->[1] - $v2->[1]),
#    ];
#    $face_normals = [ @{$face_normals}, normalize_vector($normal_vector) ];
#  }
#  print Dumper($face_normals);


  # populate sabernode verts, set vertsnum
  $sabernode->{verts} = [ map { @{$verts->[$_]} } @{$index_pattern} ];
  $sabernode->{saber_verts} = $sabernode->{verts};
  $sabernode->{vertnum} = scalar(@{$sabernode->{verts}});
  $sabernode->{saber_vertsnum} = scalar(@{$sabernode->{verts}});
  # populate sabernode tverts, set tvertsnum
  $sabernode->{tverts} = [ map { @{$tverts->[$_]} } @{$index_pattern} ];
  $sabernode->{tvertsnum} = scalar(@{$sabernode->{tverts}});
  # populate sabernode normals
#  $sabernode->{saber_norms} = [ map { @{$face_normals} } (0..scalar(@{$index_pattern}) - 1) ];
#  $sabernode->{saber_normsnum} = scalar(@{$sabernode->{saber_norms}});
  # zero sabernode MDX bitmap
  $sabernode->{mdxdatabitmap} = 0;
  $sabernode->{texturenum} = 1;
  # set node mesh type
  $sabernode->{nodetype} = NODE_SABER;

  return $sabernode;
}


#########################################################
# write out a model in ascii format
# 
sub writeasciimdl {
  my ($model, $convertskin, $extractanims, $options) = (@_);
  my ($file, $filepath, $node);
  my ($argh1, $argh2, $argh3, $argh4);
  my ($nodetype, $temp, $temp2, %bitmaps);
  my ($controller, $controllername, @args);

  # handle options, fill in default values
  if (!defined($options)) {
    $options = {};
  }
  # convert skin nodes to trimesh
  if (!defined($options->{convert_skin})) {
    #$options->{convert_skin} = 0;
    # once the UI is updated, remove legacy params
    $options->{convert_skin} = $convertskin;
  }
  # write animations in ascii model
  if (!defined($options->{extract_anims})) {
    #$options->{extract_anims} = 1;
    # once the UI is updated, remove legacy params
    $options->{extract_anims} = $extractanims;
  }
  # convert bezier animation controllers to linear
  if (!defined($options->{convert_bezier})) {
    $options->{convert_bezier} = 0;
  }
  # convert lightsaber mesh to trimesh
  if (!defined($options->{convert_saber})) {
    $options->{convert_saber} = 1;
  }
  # use .ascii file extensions, default off
  if (!defined($options->{use_ascii_extension})) {
    $options->{use_ascii_extension} = 0;
  }

  $file = $model->{'filename'};
  $filepath = $model->{'filepath+name'};
  
  my $outfile = sprintf(
    '%s%s.mdl%s',
    $filepath,
    $options->{use_ascii_extension} ? '' : '-ascii',
    $options->{use_ascii_extension} ? '.ascii' : ''
  );

  MDLOpsM::File::open(\*MODELOUT, '>', $outfile) or die "can't open out file\n";
  
  # write out the ascii mdl
  #write out the model header
  print(MODELOUT "# mdlops ver: $VERSION from KOTOR $model->{'source'} source\n");
  print(MODELOUT "# model $model->{'partnames'}[0]\n");
  print(MODELOUT "filedependancy $file NULL.mlk\n");
  print(MODELOUT "newmodel $model->{'partnames'}[0]\n");
  print(MODELOUT "setsupermodel $model->{'partnames'}[0] $model->{'supermodel'}\n");
  print(MODELOUT "classification $model->{'classification'}\n");
  print(MODELOUT "classification_unk1 $model->{'classification_unk1'}\n");
  printf(MODELOUT "ignorefog %u\n", $model->{'ignorefog'});
  if (defined($model->{compress_quaternions})) {
    printf(MODELOUT "compress_quaternions %u\n", $model->{'compress_quaternions'});
  }
  if (defined($model->{'headlink'}) && $model->{'headlink'}) {
    printf(MODELOUT "headlink %u\n", $model->{'headlink'});
  }
  print(MODELOUT "setanimationscale $model->{'animationscale'}\n\n");
  
  # track bumpmapped textures at the model level,
  # this will need to be tested against client software like nwmax
  # this is our only way to know whether a mesh requires tangent space calculations
  #if (defined($model->{'bumpmapped_texture'}) &&
  #    scalar(keys %{$model->{'bumpmapped_texture'}})) {
  #    foreach (keys %{$model->{'bumpmapped_texture'}}) {
  #        printf(MODELOUT "bumpmapped_texture %s\n", $_);
  #    }
  #    print(MODELOUT "\n");
  #}

  print(MODELOUT "beginmodelgeom $model->{'partnames'}[0]\n");
  print(MODELOUT "  bmin $model->{'bmin'}[0] $model->{'bmin'}[1] $model->{'bmin'}[2]\n");
  print(MODELOUT "  bmax $model->{'bmax'}[0] $model->{'bmax'}[1] $model->{'bmax'}[2]\n");
  print(MODELOUT "  radius $model->{'radius'}\n");

  #write out the nodes
  for my $i (@{getnodelist($model, 0)}) {
    print("Node: " . $i . "\n") if $printall;

    if ($options->{convert_saber} &&
        $model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER) {
      $model->{'nodes'}{$i} = convert_saber_to_trimesh($model, $i);
    }

    $nodetype = $model->{'nodes'}{$i}{'nodetype'};
    $temp = $model->{'partnames'}[$i];
    if ($nodetype == NODE_DUMMY) {
      $temp2 = "dummy";
    } elsif ($nodetype == NODE_LIGHT) {
      $temp2 = "light";
    } elsif ($nodetype == NODE_EMITTER) {
      $temp2 = "emitter";
    } elsif ($nodetype == NODE_DANGLYMESH) {
      $temp2 = "danglymesh";
    } elsif ($nodetype == NODE_SKIN && !$options->{convert_skin}) {
      $temp2 = "skin";
    } elsif ($nodetype == NODE_SKIN && $options->{convert_skin}) {
      $temp2 = "trimesh";
    } elsif ($nodetype == NODE_TRIMESH) {
      $temp2 = "trimesh";
    } elsif ($nodetype == NODE_AABB) {
      $temp2 = "aabb";
    } elsif ($nodetype == NODE_REFERENCE) {
      $temp2 = "reference";
    } elsif ($nodetype == NODE_SABER) {
#      $temp2 = "dummy";
#      $temp2 = "trimesh";
      $temp2 = 'lightsaber';
    } else {
      $temp2 = "dummy";
    }

    # name translation happens during conversion now
    #if ( $nodetype == NODE_SABER ) {
    #  print(MODELOUT "node " . $temp2 . " 2081__" . $temp . "\n");
    #} else {
      print(MODELOUT "node " . $temp2 . " " . $temp . "\n");
    #}
    print(MODELOUT "  parent " . $model->{'nodes'}{$i}{'parent'} . "\n");

    print(MODELHINT "$temp,$model->{'nodes'}{$i}{'supernode'}\n");

    # cleanup Acontrollers XXX move this sometime...
    # remove leading and trailing space from all Acontroller 0 entries
    # so that they split correctly
    foreach(keys %{$model->{'nodes'}{$i}{'Acontrollers'}}) {
        # continue if the length of this acontroller array is 0, aka empty
        if (!scalar(@{$model->{'nodes'}{$i}{'Acontrollers'}{$_}})) {
            next;
        }
        $model->{'nodes'}{$i}{'Acontrollers'}{$_}[0] =~ s/^\s+//;
        $model->{'nodes'}{$i}{'Acontrollers'}{$_}[0] =~ s/\s+$//;
    }

    # general controller types
    # position
    (undef, $argh1, $argh2, $argh3) = split(/\s+/,$model->{'nodes'}{$i}{'Acontrollers'}{8}[0]);
    if ($argh1 ne "") {
      printf(MODELOUT "  position % .7g % .7g % .7g\n", $argh1, $argh2, $argh3);
    }
    # orientation
    (undef, $argh1, $argh2, $argh3, $argh4) = split(/\s+/,$model->{'nodes'}{$i}{'Acontrollers'}{20}[0]);
    if ($argh1 ne "") {
      printf(MODELOUT "  orientation % .7g % .7g % .7g % .7g\n", $argh1, $argh2, $argh3, $argh4);
    }
    # scale
    (undef, $argh1) = split(/\s+/,$model->{'nodes'}{$i}{'Acontrollers'}{36}[0]);
    if ($argh1 ne "") {
      printf(MODELOUT "  scale % .7g\n", $argh1);
    }
    
    # alpha i.e. "see through" - controller number overlaps with an emitter controller number.
    if (!($nodetype & NODE_HAS_EMITTER)) {
      (undef, $argh1) = split(/\s+/,$model->{'nodes'}{$i}{'Acontrollers'}{132}[0]);
      if ($argh1 ne "") {
        printf(MODELOUT "  alpha % .7g\n", $argh1);
      }
    }
    
    # mesh node controller types
    if ($nodetype & NODE_HAS_MESH) {
      # self illumination i.e. "glow"    
      (undef, $argh1, $argh2, $argh3) = split(/\s+/,$model->{'nodes'}{$i}{'Acontrollers'}{100}[0]);
      if ($argh1 ne "" && $argh2 ne "") {
        printf(MODELOUT "  selfillumcolor %.7g %.7g %.7g\n", $argh1, $argh2, $argh3);
      }
    }
    
    # diffuse color    
    if ( defined($model->{'nodes'}{$i}{'diffuse'}[0]) ) {
      printf(MODELOUT "  diffuse %.7g %.7g %.7g\n", @{$model->{'nodes'}{$i}{'diffuse'}});
    }
    
    # not light node type
    #if (!($nodetype & NODE_HAS_LIGHT)) {
    # the parts of the following that actually exist are in mesh header
    if ($nodetype & NODE_HAS_MESH) {
      # ambient color    
      if ( defined($model->{'nodes'}{$i}{'ambient'}[0]) ) {
        printf(MODELOUT "  ambient %.7g %.7g %.7g\n", @{$model->{'nodes'}{$i}{'ambient'}});
      }
      # render flag    
      if ( defined($model->{'nodes'}{$i}{'render'}) ) {
        printf(MODELOUT "  render %u\n", $model->{'nodes'}{$i}{'render'});
      }
      # shadow flag    
      if ( defined($model->{'nodes'}{$i}{'shadow'}) ) {
        printf(MODELOUT "  shadow %u\n", $model->{'nodes'}{$i}{'shadow'});
      }
      print(MODELOUT "  specular 0.000000 0.000000 0.000000\n");
      print(MODELOUT "  shininess 0.000000\n");
      print(MODELOUT "  wirecolor 1 1 1\n");
      printf(
        MODELOUT "  tangentspace %u\n",
        ($model->{'nodes'}{$i}{'mdxdatabitmap'} & MDX_TANGENT_SPACE) ? 1 : 0
      );
      if (defined($model->{'nodes'}{$i}{inv_count2})) {
        printf(MODELOUT "  inv_count %u %u\n",
               $model->{'nodes'}{$i}{inv_count1},
               $model->{'nodes'}{$i}{inv_count2});
      } else {
        printf(MODELOUT "  inv_count %u\n", $model->{'nodes'}{$i}{inv_count1});
      }
    }
     
    # light node
    if ( $nodetype == NODE_LIGHT ) {
      # subheader data
      print(MODELOUT "  ambientonly " . $model->{'nodes'}{$i}{'ambientonly'} . "\n");
      print(MODELOUT "  nDynamicType " . $model->{'nodes'}{$i}{'ndynamictype'} . "\n"); #should possibly be isDynamic, but this is what nwmax outputs
      print(MODELOUT "  affectDynamic " . $model->{'nodes'}{$i}{'affectdynamic'} . "\n");
      print(MODELOUT "  shadow " . $model->{'nodes'}{$i}{'shadow'} . "\n");
      print(MODELOUT "  flare " . $model->{'nodes'}{$i}{'flare'} . "\n");
      print(MODELOUT "  lightpriority " . $model->{'nodes'}{$i}{'lightpriority'} . "\n");
      print(MODELOUT "  fadingLight " . $model->{'nodes'}{$i}{'fadinglight'} . "\n");

      my $has_flares = defined($model->{'nodes'}{$i}{'flarepositions'}) &&
                       scalar(@{$model->{'nodes'}{$i}{'flarepositions'}});

      # lens flare properties implementation
      if ($has_flares) {
        # not really planning to use this, but this is how neverblender outputs it ... nwmax?
        printf(MODELOUT "  lensflares %u\n", scalar(@{$model->{'nodes'}{$i}{'flarepositions'}}));
      }
      if ($has_flares && scalar(@{$model->{'nodes'}{$i}{'texturenames'}})) {
        printf(MODELOUT "  texturenames %u\n    %s\n",
               scalar(@{$model->{'nodes'}{$i}{'texturenames'}}),
               join("\n    ", @{$model->{'nodes'}{$i}{'texturenames'}}));
      }
      if ($has_flares && scalar(@{$model->{'nodes'}{$i}{'flarepositions'}})) {
        printf(MODELOUT "  flarepositions %u\n    %s\n",
               scalar(@{$model->{'nodes'}{$i}{'flarepositions'}}),
               join("\n    ", map { sprintf('% .7g', $_); } @{$model->{'nodes'}{$i}{'flarepositions'}}));
      }
      if ($has_flares && scalar(@{$model->{'nodes'}{$i}{'flaresizes'}})) {
        printf(MODELOUT "  flaresizes %u\n    %s\n",
               scalar(@{$model->{'nodes'}{$i}{'flaresizes'}}),
               join("\n    ", map { sprintf('%.7g', $_); } @{$model->{'nodes'}{$i}{'flaresizes'}}));
      }
      if ($has_flares && scalar(@{$model->{'nodes'}{$i}{'flarecolorshifts'}})) {
        printf(MODELOUT "  flarecolorshifts %u\n",
               scalar(@{$model->{'nodes'}{$i}{'flarecolorshifts'}}));
        for my $shift_col (@{$model->{'nodes'}{$i}{'flarecolorshifts'}}) {
          printf(MODELOUT "    %.7g %.7g %.7g\n", @{$shift_col});
        }
      }
      printf(MODELOUT "  flareradius %.7g\n", $model->{'nodes'}{$i}{'flareradius'});

      # controllers
      while(($controller, $controllername) = each %{$controllernames{+NODE_HAS_LIGHT}}) {
        (undef, @args) = split(/\s+/,$model->{'nodes'}{$i}{'Acontrollers'}{$controller}[0]);
        if ($args[0] ne "") {
          printf(MODELOUT "  %s %s\n", $controllername, join(" ", @args));
        }
      }
    }
    
    # emitter node
    if ( $nodetype == NODE_EMITTER ) {
      # subheader data
      print(MODELOUT "  deadspace " . $model->{'nodes'}{$i}{'deadspace'} . "\n");
      print(MODELOUT "  blastRadius " . $model->{'nodes'}{$i}{'blastRadius'} . "\n");
      print(MODELOUT "  blastLength " . $model->{'nodes'}{$i}{'blastLength'} . "\n");
      print(MODELOUT "  numBranches " . $model->{'nodes'}{$i}{'numBranches'} . "\n");
      print(MODELOUT "  controlptsmoothing " . $model->{'nodes'}{$i}{'controlptsmoothing'} . "\n");
      print(MODELOUT "  xgrid " . $model->{'nodes'}{$i}{'xgrid'} . "\n");
      print(MODELOUT "  ygrid " . $model->{'nodes'}{$i}{'ygrid'} . "\n");
      print(MODELOUT "  spawntype " . $model->{'nodes'}{$i}{'spawntype'} . "\n");
      print(MODELOUT "  update " . $model->{'nodes'}{$i}{'update'} . "\n");
      print(MODELOUT "  render " . $model->{'nodes'}{$i}{'render'} . "\n");
      print(MODELOUT "  blend " . $model->{'nodes'}{$i}{'blend'} . "\n");
      print(MODELOUT "  texture " . $model->{'nodes'}{$i}{'texture'} . "\n");
      if ($model->{'nodes'}{$i}{'chunkname'} ne "") {
        print(MODELOUT "  chunkname " . $model->{'nodes'}{$i}{'chunkname'} . "\n");
      }
      print(MODELOUT "  twosidedtex " . $model->{'nodes'}{$i}{'twosidedtex'} . "\n");
      print(MODELOUT "  loop " . $model->{'nodes'}{$i}{'loop'} . "\n");
      print(MODELOUT "  renderorder " . $model->{'nodes'}{$i}{'renderorder'} . "\n");
      print(MODELOUT "  m_bFrameBlending " . $model->{'nodes'}{$i}{'m_bFrameBlending'} . "\n");
      print(MODELOUT "  m_sDepthTextureName " . $model->{'nodes'}{$i}{'m_sDepthTextureName'} . "\n");

      #printf(MODELOUT "\n# DEBUG MODE:\n  m_bUnknown1 %u\nm_lUnknown2 %u\n\n",
      #                $model->{'nodes'}{$i}{'m_bUnknown1'}, $model->{'nodes'}{$i}{'m_lUnknown2'});

      print(MODELOUT "  p2p " . $model->{'nodes'}{$i}{'p2p'} . "\n");
      print(MODELOUT "  p2p_sel " . $model->{'nodes'}{$i}{'p2p_sel'} . "\n");
      print(MODELOUT "  affectedByWind " . $model->{'nodes'}{$i}{'affectedByWind'} . "\n");
      print(MODELOUT "  m_isTinted " . $model->{'nodes'}{$i}{'m_isTinted'} . "\n");
      print(MODELOUT "  bounce " . $model->{'nodes'}{$i}{'bounce'} . "\n");
      print(MODELOUT "  random " . $model->{'nodes'}{$i}{'random'} . "\n");
      print(MODELOUT "  inherit " . $model->{'nodes'}{$i}{'inherit'} . "\n");
      print(MODELOUT "  inheritvel " . $model->{'nodes'}{$i}{'inheritvel'} . "\n");
      print(MODELOUT "  inherit_local " . $model->{'nodes'}{$i}{'inherit_local'} . "\n");
      print(MODELOUT "  splat " . $model->{'nodes'}{$i}{'splat'} . "\n");
      print(MODELOUT "  inherit_part " . $model->{'nodes'}{$i}{'inherit_part'} . "\n");
      print(MODELOUT "  depth_texture " . $model->{'nodes'}{$i}{'depth_texture'} . "\n");
      print(MODELOUT "  emitterflag13 " . $model->{'nodes'}{$i}{'emitterflag13'} . "\n");
    
      # controllers
      while(($controller, $controllername) = each %{$controllernames{+NODE_HAS_EMITTER}}) {
        (undef, @args) = split(/\s+/,$model->{'nodes'}{$i}{'Acontrollers'}{$controller}[0]);
        if ($args[0] ne "") {
          printf(MODELOUT "  %s %s\n", $controllername, join(" ", @args));
        }
      }
    }

    if ( $nodetype == NODE_REFERENCE ) {
      printf(MODELOUT "  refModel %s\n", length($model->{nodes}{$i}{refModel}) ? $model->{nodes}{$i}{refModel} : 'NULL');
      printf(MODELOUT "  reattachable %u\n", $model->{nodes}{$i}{reattachable});
    }
    
    # mesh nodes
    if ( $nodetype == NODE_TRIMESH || $nodetype == NODE_SKIN || $nodetype == NODE_DANGLYMESH || $nodetype == NODE_AABB || $nodetype == NODE_SABER ) {
      printf(MODELOUT "  bmin % .7g % .7g % .7g\n", @{$model->{'nodes'}{$i}{'bboxmin'}}[0..2]);
      printf(MODELOUT "  bmax % .7g % .7g % .7g\n", @{$model->{'nodes'}{$i}{'bboxmax'}}[0..2]);
      printf(MODELOUT "  radius % .7g\n", $model->{'nodes'}{$i}{'radius'});
      printf(MODELOUT "  average % .7g % .7g % .7g\n", @{$model->{'nodes'}{$i}{'average'}}[0..2]);

      # render, shadow, ambient, and diffuse should all be in here, they are not actually general
      printf(MODELOUT "  lightmapped %u\n", $model->{'nodes'}{$i}{'lightmapped'});
      printf(MODELOUT "  rotatetexture %u\n", $model->{'nodes'}{$i}{'rotatetexture'});
      printf(MODELOUT "  m_bIsBackgroundGeometry %u\n", $model->{'nodes'}{$i}{'m_bIsBackgroundGeometry'});
      printf(MODELOUT "  beaming %u\n", $model->{'nodes'}{$i}{'beaming'});
      printf(MODELOUT "  transparencyhint %u\n", $model->{'nodes'}{$i}{'transparencyhint'});

      # test for presence of k2 specific flags
      if (defined($model->{'nodes'}{$i}{'dirt_enabled'})) {
          printf(MODELOUT "  dirt_enabled %u\n", $model->{'nodes'}{$i}{'dirt_enabled'});
          printf(MODELOUT "  dirt_texture %u\n", $model->{'nodes'}{$i}{'dirt_texture'});
          printf(MODELOUT "  dirt_worldspace %u\n", $model->{'nodes'}{$i}{'dirt_worldspace'});
          printf(MODELOUT "  hologram_donotdraw %u\n", $model->{'nodes'}{$i}{'hologram_donotdraw'});
      }

      # this is the property magnusII classified as 'shininess'
      # my current understanding is that this is actually animated uv maps,
      # used, for example, to show the 'current' of a river, or a moving cloud,
      # that is the theory, definitely unconfirmed at this time
      printf(MODELOUT "  animateuv %u\n", $model->{'nodes'}{$i}{'animateuv'});
      printf(MODELOUT "  uvdirectionx % .7g\n", $model->{'nodes'}{$i}{'uvdirectionx'});
      printf(MODELOUT "  uvdirectiony % .7g\n", $model->{'nodes'}{$i}{'uvdirectiony'});
      printf(MODELOUT "  uvjitter % .7g\n", $model->{'nodes'}{$i}{'uvjitter'});
      printf(MODELOUT "  uvjitterspeed % .7g\n", $model->{'nodes'}{$i}{'uvjitterspeed'});

      printf(MODELOUT "  bitmap %s\n", $model->{'nodes'}{$i}{'bitmap'});
      if (length($model->{'nodes'}{$i}{'bitmap2'})) {
          printf(MODELOUT "  bitmap2 %s\n", $model->{'nodes'}{$i}{'bitmap2'});
      }
      if (length($model->{'nodes'}{$i}{'texture0'})) {
          printf(MODELOUT "  texture0 %s\n", $model->{'nodes'}{$i}{'texture0'});
      }
      if (length($model->{'nodes'}{$i}{'texture1'})) {
          printf(MODELOUT "  texture1 %s\n", $model->{'nodes'}{$i}{'texture1'});
      }
      $bitmaps{ lc($model->{'nodes'}{$i}{'bitmap'}) } += 1;
      printf(MODELOUT "  verts %u\n", $model->{'nodes'}{$i}{'vertcoordnum'});
      foreach ( @{$model->{'nodes'}{$i}{'verts'}} ) {
        printf(MODELOUT "    % .7g % .7g % .7g\n", @{$_});
      }
      printf(MODELOUT "  faces %u\n", $model->{'nodes'}{$i}{'facesnum'});
      foreach ( @{$model->{'nodes'}{$i}{'Afaces'}} ) {
        print (MODELOUT "    $_\n");
      }
      # properly use the mdx bitmap here
      # there are nodes that contain only slot 2 textures,
      # for example: m12aa_01p in K1
      # saber mesh does not use MDX, so bypass this check if it claims to be textured
      # TODO: repeat this for texture slots 2-4
      if ($model->{'nodes'}{$i}{'texturenum'} != 0 &&
          ($model->{'nodes'}{$i}{'mdxdatabitmap'} & MDX_TEX0_VERTICES ||
           $nodetype & NODE_HAS_SABER)) {
        # write out tverts, nwmax requires these to be 3 coordinate numbers
        #printf(MODELOUT "  tverts %u\n", $model->{'nodes'}{$i}{'vertcoordnum'});
        printf(MODELOUT "  tverts %u\n", scalar(@{$model->{'nodes'}{$i}{'tverts'}}));
        foreach ( @{$model->{'nodes'}{$i}{'tverts'}} ) {
          printf(MODELOUT "    % .7g % .7g\n", $_->[0], $_->[1]);
        }
      }
      if (length($model->{'nodes'}{$i}{'bitmap2'}) &&
          scalar(@{$model->{'nodes'}{$i}{'tverts1'}})) {
        # write out tverts1, nwmax would require these to be 3 coordinate numbers
        printf(MODELOUT "  tverts1 %u\n", scalar(@{$model->{'nodes'}{$i}{'tverts1'}}));
        foreach ( @{$model->{'nodes'}{$i}{'tverts1'}} ) {
          printf(MODELOUT "    % .7g % .7g\n", $_->[0], $_->[1]);
        }
        printf(MODELOUT "  texindices1 %u\n", scalar(@{$model->{'nodes'}{$i}{'texindices'}}));
        foreach ( @{$model->{'nodes'}{$i}{'texindices'}} ) {
          printf(MODELOUT "    %u %u %u\n", @{$_});
        }
      }
      if (length($model->{'nodes'}{$i}{'texture0'}) &&
          scalar(@{$model->{'nodes'}{$i}{'tverts2'}})) {
        # write out tverts2, nwmax would require these to be 3 coordinate numbers
        printf(MODELOUT "  tverts2 %u\n", scalar(@{$model->{'nodes'}{$i}{'tverts2'}}));
        foreach ( @{$model->{'nodes'}{$i}{'tverts2'}} ) {
          printf(MODELOUT "    % .7g % .7g\n", $_->[0], $_->[1]);
        }
        printf(MODELOUT "  texindices2 %u\n", scalar(@{$model->{'nodes'}{$i}{'texindices'}}));
        foreach ( @{$model->{'nodes'}{$i}{'texindices'}} ) {
          printf(MODELOUT "    %u %u %u\n", @{$_});
        }
      }
      if (length($model->{'nodes'}{$i}{'texture1'}) &&
          scalar(@{$model->{'nodes'}{$i}{'tverts3'}})) {
        # write out tverts3, nwmax would require these to be 3 coordinate numbers
        printf(MODELOUT "  tverts3 %u\n", scalar(@{$model->{'nodes'}{$i}{'tverts3'}}));
        foreach ( @{$model->{'nodes'}{$i}{'tverts3'}} ) {
          printf(MODELOUT "    % .7g % .7g\n", $_->[0], $_->[1]);
        }
        printf(MODELOUT "  texindices3 %u\n", scalar(@{$model->{'nodes'}{$i}{'texindices'}}));
        foreach ( @{$model->{'nodes'}{$i}{'texindices'}} ) {
          printf(MODELOUT "    %u %u %u\n", @{$_});
        }
      }
      if ($nodetype & NODE_HAS_SABER) {
        # copy of vertices and the weird face normals, we don't need to export these
        # leaving the code here though, in case someone wants to see them,
        # as I do, during verifications.
        #printf(MODELOUT "  saber_verts %u\n", scalar(@{$model->{'nodes'}{$i}{'saber_verts'}}));
        #foreach ( @{$model->{'nodes'}{$i}{'saber_verts'}} ) {
        #  printf(MODELOUT "    % .7g % .7g % .7g\n", @{$_});
        #}
        #printf(MODELOUT "  saber_norms %u\n", scalar(@{$model->{'nodes'}{$i}{'saber_norms'}}));
        #foreach ( @{$model->{'nodes'}{$i}{'saber_norms'}} ) {
        #  printf(MODELOUT "    % .7g % .7g % .7g\n", @{$_});
        #}
      }
      if ($nodetype == NODE_SKIN && !$options->{convert_skin}) {
        printf(MODELOUT "  weights %u\n", scalar(@{$model->{'nodes'}{$i}{'Abones'}}));
        foreach ( @{$model->{'nodes'}{$i}{'Abones'}} ) {
          printf(MODELOUT "    %s\n", $_);
        }
      }
      if ($nodetype == NODE_DANGLYMESH) {
        printf(MODELOUT "  displacement % .7g\n", $model->{'nodes'}{$i}{'displacement'});
        printf(MODELOUT "  tightness % .7g\n", $model->{'nodes'}{$i}{'tightness'});
        printf(MODELOUT "  period % .7g\n", $model->{'nodes'}{$i}{'period'});
        #printf(MODELOUT "  constraints %u\n", $model->{'nodes'}{$i}{'vertcoordnum'});
        printf(MODELOUT "  constraints %u\n", scalar(@{$model->{'nodes'}{$i}{'constraints'}}));
        foreach ( @{$model->{'nodes'}{$i}{'constraints'}} ) {
          printf(MODELOUT "    % .7g\n", $_);
        }
      }
      if ($nodetype == NODE_AABB) {
        #print (MODELOUT "  aabb\n");
        # i read somewhere that nwmax crashes if aabb does not start on same line...
        print (MODELOUT "  aabb");
        foreach ( @{$model->{'nodes'}{$i}{'aabbnodes'}} ) {
          printf(MODELOUT "      % .7g % .7g % .7g % .7g % .7g % .7g %d\n", @{$_}[0..6]);
        }
      }
    }
    print (MODELOUT "endnode\n");
  }

  # test for unused part names, usually refering to parts of walkmesh file
  # add dummies for them unless the user does not want them
  if (!$options->{skip_extra_partnames}) {
    foreach (@{$model->{partnames}}) {
      if (!defined($model->{nodes}{$model->{nodeindex}{lc $_}})) {
        # no node by this name, print a dummy
        # parent name will be model root unless better candidate exists
        my $parent_name = $model->{partnames}[0];
        if (/_DWK_/ && defined($model->{nodeindex}{lc ($parent_name . '_DWK')})) {
          $parent_name = $parent_name . '_DWK';
        }
        if (/_pwk_/ && defined($model->{nodeindex}{lc ($parent_name . '_pwk')})) {
          $parent_name = $parent_name . '_pwk';
        }
        printf(MODELOUT "node dummy %s\n  parent %s\nendnode\n", $_, $parent_name);
      }
    }
  }

  printf(MODELOUT "endmodelgeom %s\n", $model->{'partnames'}[0]);

    
  # write out the animations if there are any and we are told to do so
  if ($model->{'numanims'} != 0 && $options->{extract_anims}) {
    # loop through the animations
    for (my $i = 0; $i < $model->{'numanims'}; $i++) {
      printf(MODELOUT "\nnewanim %s %s\n", $model->{'anims'}{$i}{'name'}, $model->{'partnames'}[0]);
      printf(MODELOUT "  length %.7g\n", $model->{'anims'}{$i}{'length'});
      printf(MODELOUT "  transtime %.7g\n", $model->{'anims'}{$i}{'transtime'});
      printf(MODELOUT "  animroot %s\n", $model->{'anims'}{$i}{'animroot'});
      if ($model->{'anims'}{$i}{'eventsnum'} != 0) {
        #print(MODELOUT "  eventlist\n");
        foreach ( @{$model->{'anims'}{$i}{'animevents'}{'ascii'}} ) {
          #printf(MODELOUT "    %s\n", $_);
          printf(MODELOUT "  event %s\n", $_);
        }
        #print(MODELOUT "  endlist\n");
      }
      # loop through this animations nodes
      foreach $node (sort {$a <=> $b} keys(%{$model->{'anims'}{$i}{'nodes'}}) ) {
        if ($node eq "truenodenum") {next;}
        print(MODELOUT "  node dummy $model->{'partnames'}[$node]\n");
        print(MODELOUT "    parent $model->{'anims'}{$i}{'nodes'}{$node}{'parent'}\n");

        # loop though this animations controllers
        foreach $temp (keys %{$model->{'anims'}{$i}{'nodes'}{$node}{'Acontrollers'}} ) {
          if ($temp == 42) {
            # can't imagine what the point of this was...
            next;
          }
          my $controllername = getcontrollername($model, $temp, $node);

          my $keytype = '';
          if (defined($model->{'anims'}{$i}{'nodes'}{$node}{'controllers'}{'bezier'}{$temp})) {
            $keytype = 'bezier';
          }

          if ($controllername ne "") {
            printf(MODELOUT "    %s%skey\n", $controllername, !$options->{convert_bezier} ? $keytype : '');
          } else {
            if ($temp != 0) {
              print "didn't find controller $temp in node type $model->{'nodes'}{$node}{'nodetype'} \n";
            } else {
              # temp == 0, this is controller data whose controller has been deleted,
              # the vanilla compiler seems to have created this situation
              # relatively frequently, we are skipping such data
              next;
            }
            printf(MODELOUT "    controller%u%skey\n", $temp, $keytype);
          }
          foreach ( @{$model->{'anims'}{$i}{'nodes'}{$node}{'Acontrollers'}{$temp}} ) {
            # convert bezier controller data to linear, not a true conversion,
            # we are just dropping the control points, as has been done historically
            if ($options->{convert_bezier} && $keytype eq 'bezier') {
              # split into an array
              $_ = [ split(/\s+/, $_) ];
              if (scalar(@{$_}) > 8) {
                # remove last 6 items from array, which are the bezier control points
                $_ = join(' ', @{$_}[0..scalar(@{$_}) - 7]);
              } else {
                # malformed data, should have had 1 time, 1+ data, and 6 control point
                $_ = join(' ', @{$_});
              }
            }
            printf(MODELOUT "      %s\n", $_);
          }
          print(MODELOUT "    endlist\n");
        } # foreach $temp
        print(MODELOUT "  endnode\n");
      } # foreach $node
      
      $temp = $i;
      printf(MODELOUT "\ndoneanim %s %s\n", $model->{'anims'}{$i}{'name'}, $model->{'partnames'}[0]);
    } # for $i
  } # if to do animations
  
  printf(MODELOUT "\ndonemodel %s\n", $model->{'partnames'}[0]);

  MDLOpsM::File::close(*MODELOUT);
}


###########################################################
# Used by writeasciimodel.
# Given a node type and controller number, return the name.
# 
sub getcontrollername {
  my ($model, $controllernum, $node) = (@_);
  my $nodetype = (defined($model->{'nodes'}{$node}) && $model->{'nodes'}{$node}{'nodetype'}
                    ? $model->{'nodes'}{$node}{'nodetype'} : NODE_DUMMY);
  my @nodeheaders = (NODE_HAS_MESH, NODE_HAS_EMITTER, NODE_HAS_LIGHT, NODE_HAS_HEADER);
  
  foreach (@nodeheaders) {
    if (($nodetype & $_) && ($controllernames{$_}{$controllernum} ne '')) {
      return $controllernames{$_}{$controllernum};
    }
  }
  
  return '';
}


#########################################################
# Used by readasciimdl.
# Determine if 2 vectors/vertices are equivalent
# Allows caller to specify precision for matching
# Now safe for comparing any two same-sized numeric lists
#
sub vertex_equals {
  my ($vert1, $vert2, $precision) = @_;

  if (!defined($precision)) {
    $precision = 6;
  }
  my $max_diff = 10 ** (0 - $precision);
  $max_diff *= 5.0;

  my $size = scalar(@{$vert1});

  my $matches = 0;
  for my $index (0..$size - 1) {
    if ($vert1->[$index] == $vert2->[$index] ||
        abs($vert1->[$index] - $vert2->[$index]) < $max_diff) {
      $matches += 1;
    }
  }
  if ($matches == $size) {
    return 1;
  }

  return 0;
}


#########################################################
# Normalize vector passed in as listref, return normalized listref
#
sub normalize_vector {
  my ($vec) = @_;

  my $norm_vec = [ 0, 0, 0 ];

  # tested this extra-accurate version but it does not help
  #use Math::BigFloat;
  #my ($v1, $v2, $v3) = (
  #  Math::BigFloat->new($vec->[0]),
  #  Math::BigFloat->new($vec->[1]),
  #  Math::BigFloat->new($vec->[2]),
  #);
  #my $norm = Math::BigFloat->new(
  #  $v1->bpow(2)->badd($v2->bpow(2))->badd($v3->bpow(2))
  #);
  #$norm = $norm->bsqrt();
  #if (!$norm->is_zero()) {
  #  $norm_vec = [ map { $_->bdiv($norm)->bround(7)->numify() } (
  #    Math::BigFloat->new($vec->[0]),
  #    Math::BigFloat->new($vec->[1]),
  #    Math::BigFloat->new($vec->[2]),
  #  ) ];
  #}

  my $norm = sqrt($vec->[0]**2 + $vec->[1]**2 + $vec->[2]**2);
  if ($norm) {
    $norm_vec = [ map { $_ / $norm } @{$vec} ];
  }

  return $norm_vec;
}


#########################################################
# Used by readasciimdl.
# compute angle as radians between vectors vec1 and vec2
#
sub compute_vector_angle {
  my ($v1, $v2) = @_;
  my $angle = 0.0;

  my $dot_product = $v1->[0] * $v2->[0] + $v1->[1] * $v2->[1] + $v1->[2] * $v2->[2];
  my $vector_lengths = (
    sqrt($v1->[0]**2 + $v1->[1]**2 + $v1->[2]**2) *
    sqrt($v2->[0]**2 + $v2->[1]**2 + $v2->[2]**2)
  );
  # v1 and v2 are normalized, so angle = acos(v1 dot v2)
  #$angle = acos(
  #  ($v1[0] * $v2[0] + $v1[1] * $v2[1] + $v1[2] * $v2[2]) /
  #  (sqrt($v1[0]**2 + $v1[1]**2 + $v1[2]**2) *
  #   sqrt($v2[0]**2 + $v2[1]**2 + $v2[2]**2))
  #);
  #$angle = acos($dot_product);
  if ($vector_lengths > 0.0) {
    $angle = acos(
      $dot_product / $vector_lengths
    );
  }
  #if ($dot_product < 0) {
    # obtuse angle
  #  $angle = (2 * pi) - $angle;
  #} elsif ($dot_product == 0) {
    # same angle, pointing in same direction or opposite?
  #  if (vertex_equals(\@v1, \@v2)) {
  #    return 0;
  #  } else {
  #    return pi / 2;
  #  }
  #}
  # acute angle
  #print Dumper($angle);
  return $angle;
}


#########################################################
# Used by readasciimdl.
# compute angle as radians between face edges at vertex lp
# uses edges lp <-> rp1 and lp <-> rp2
#
sub compute_vertex_angle {
  my ($lp, $rp1, $rp2) = @_;
  my (@v1, @v2);

  @v1 = map { $rp1->[$_] - $lp->[$_] } (0..2);
  @v2 = map { $rp2->[$_] - $lp->[$_] } (0..2);

  return compute_vector_angle(\@v1, \@v2);
}


###########################################################
# Used by readsinglecontroller and readkeyedcontroller.
# Convert angle-axis to quaternion. Outputs as (x,y,z,w).
# 
sub aatoquaternion {
  my ($aaref) = (@_);

  # 2016 updated method to produce closer matching results
  my $sin_a = sin($aaref->[3] / 2);

  $aaref->[0] = $aaref->[0] * $sin_a;
  $aaref->[1] = $aaref->[1] * $sin_a;
  $aaref->[2] = $aaref->[2] * $sin_a;
  $aaref->[3] = cos($aaref->[3] / 2);
}

###########################################################
# Used by readasciicontroller.
# Parse a single controller (single line of data).
# 
sub readsinglecontroller {
  my ($line, $modelref, $nodenum, $controller, $controllername) = (@_);
  my @controllerdata;
  my $temp;

  if ($line =~ /^\s*$controllername(\s+(\S*))+/i) {
    $line =~ s/\s*$controllername//i;
    @controllerdata = ($line =~ /\s+(\S+)/g);
    $modelref->{'nodes'}{$nodenum}{'controllernum'}++;
    $modelref->{'nodes'}{$nodenum}{'controllerdatanum'} += (scalar(@controllerdata) + 1); # add 1 for the time value
    $modelref->{'nodes'}{$nodenum}{'Acontrollers'}{$controller}[0] = "0 " . join(' ', @controllerdata);
    $modelref->{'nodes'}{$nodenum}{'Bcontrollers'}{$controller}{'rows'} = 1;
    $modelref->{'nodes'}{$nodenum}{'Bcontrollers'}{$controller}{'times'}[0] = 0;
    if ($controller == 20) {
      aatoquaternion(\@controllerdata);
    }
    $modelref->{'nodes'}{$nodenum}{'Bcontrollers'}{$controller}{'values'}[0] = \@controllerdata;
    return 1;
  }
  return 0;
}

###########################################################
# Used by readasciicontroller.
# Parse a keyed controller (multiple lines of data).
# 
sub readkeyedcontroller {
  my ($line, $modelref, $nodenum, $animnum, $ASCIIFILE, $controller, $controllername) = (@_);
  my $count;

  if ($line =~ /^\s*${controllername}(bezier)?key/i) {
    my $total;
    my $bezier = 0;
    if (defined($1) && lc($1) eq 'bezier') {
      $bezier = 1;
      $modelref->{'anims'}{$animnum}{'nodes'}{$nodenum}{'controllers'}{'bezier'}{$controller} = 1;
    }
    if ($line =~ /key\s+(\d+)$/i) {
      # old versions of mdlops did not use endlist, instead had 'positionkey 4' for 4 keyframes
      $total = int $1;
    }
    $modelref->{'anims'}{$animnum}{'nodes'}{$nodenum}{'controllernum'}++;
    $count = 0;
    while ((!$total || $count < $total) && ($line = <$ASCIIFILE>) && $line !~ /endlist/) {
      my @controllerdata = ($line =~ /\s+(\S+)/g); # "my" here makes sure it's a new array each time; without it, earlier values are clobbered
      $modelref->{'anims'}{$animnum}{'nodes'}{$nodenum}{'controllerdatanum'} += scalar(@controllerdata); # time value included already
      $modelref->{'anims'}{$animnum}{'nodes'}{$nodenum}{'Acontrollers'}{$controller}[$count] = join(' ', @controllerdata);
      $modelref->{'anims'}{$animnum}{'nodes'}{$nodenum}{'Bcontrollers'}{$controller}{'rows'}++;
      $modelref->{'anims'}{$animnum}{'nodes'}{$nodenum}{'Bcontrollers'}{$controller}{'times'}[$count] = shift (@controllerdata);
      
      # special cases:
      if ($controller == 20) {
      # orientation: convert to quaternions
        aatoquaternion(\@controllerdata);
      } elsif ($controller == 8) {
      # position: take delta from geometry node
        $controllerdata[0] -= $modelref->{'nodes'}{$nodenum}{'Bcontrollers'}{8}{'values'}[0][0];
        $controllerdata[1] -= $modelref->{'nodes'}{$nodenum}{'Bcontrollers'}{8}{'values'}[0][1];
        $controllerdata[2] -= $modelref->{'nodes'}{$nodenum}{'Bcontrollers'}{8}{'values'}[0][2];
      }
      
      $modelref->{'anims'}{$animnum}{'nodes'}{$nodenum}{'Bcontrollers'}{$controller}{'values'}[$count] = \@controllerdata;
      $count++;
    }
    return 1;
  }

  return 0;  
}


###########################################################
# For use by readasciimodel.
# Parse controller out of the input file.
# 
sub readasciicontroller {
# parsing controllers one at a time was fine when there were 5, but sucks when there are, like, 40.
# hopefully this'll work a bit better and won't have too many special cases.
  my ($line, $nodetype, $innode, $isanimation, $modelref, $nodenum, $animnum, $ASCIIFILE) = (@_);
  my ($controller, $controllername, $nodetype);
  
  $nodetype = $modelref->{'nodes'}{$nodenum}{'nodetype'};
  # go through each of the types that have controllers (last is essentially "any node")
  for my $type_test (NODE_HAS_LIGHT, NODE_HAS_EMITTER, NODE_HAS_MESH, NODE_HAS_HEADER) {
      # if this node has this type
      if ($nodetype & $type_test) {
          # this was being done with a while & each before, but that didn't seem to be resetting some kind of iterator??
          # this for loop is more reliable for some reason...
          for $controller (keys %{$controllernames{$type_test}}) {
              $controllername = $controllernames{$type_test}{$controller};
              if ($isanimation) {
                  if (readkeyedcontroller($line, $modelref, $nodenum, $animnum, $ASCIIFILE, $controller, $controllername)) {
                      return 1;
                  }
              } elsif (readsinglecontroller($line, $modelref, $nodenum, $controller, $controllername)) {
                  return 1;
              }
          }
      }
  }
  return 0;
}


###########################################################
# For use by readasciimodel.
# Assign supernode numbers to all nodes, bead-v's algorithm.
# Returns the maximum node number, since it is not passed by ref, but must be updated
sub get_super_nodes {
  my ($model, $supermodel, $max, $supertotal, $currentpart, $superpart) = @_;

  # initialize recursion tracking numbers, set initial model node total
  if (!defined($max)) {
    # compute initial values
    $model->{totalnumnodes} = $model->{truenodenum};
    $supertotal = $supermodel->{totalnumnodes};
    if ($supertotal) {
      $model->{totalnumnodes} += $supertotal + 1;
    }
    my $supermax = 0;
    foreach (values %{$supermodel->{nodes}}) {
      if (ref $_ eq 'HASH' && defined($_->{supernode}) &&
          $_->{supernode} > $supermax) {
        $supermax = $_->{supernode};
      }
    }
    $max = $supermax + 1;
  }

  if ($currentpart < 0 || !defined($model->{nodes}{$currentpart})) {
    return $max;
  }

  # get the node under consideration
  my $node = $model->{nodes}{$currentpart};

  if ($superpart < 0) {
    # parent or node does not match a supernode
    $node->{supernode} = (
      $superpart == -1
        # parent matched, child missed
        ? $max++
        # parent missed, child cannot match
        : $node->{nodenum} + $supertotal + 1
    );
    for my $child (@{$node->{'children'}}) {
      # this node misses, children will miss
      $max = get_super_nodes($model, $supermodel, $max, $supertotal, $child, -2);
    }
  } else {
    # node matched a supernode
    my $supernode = $supermodel->{nodes}{$superpart};

    $node->{supernode} = $supernode->{supernode};

    # test children for matches
    for my $child (@{$node->{'children'}}) {
      my $name = lc $model->{partnames}[$child];
      # make sure supernode's child list exists, otherwise use empty
      my $superchildren = (
        defined($supernode->{'childindexes'})
          ? $supernode->{'childindexes'}{'nums'} : []
      );
      # search by name for a matching supernode
      my $supermatch = -1;
      for my $superchild (@{$superchildren}) {
        if ($name eq lc $supermodel->{partnames}[$superchild]) {
          # matching supernode is found
          $supermatch = $superchild;
          last;
        }
      }
      $max = get_super_nodes($model, $supermodel, $max, $supertotal, $child, $supermatch);
    }
  }
  return $max;
}


###########################################################
# Read in an ascii model
# 
sub readasciimdl {
  my ($buffer, $supercheck, $options) = (@_);
  my ($file, $extension, $filepath);
  my %model={};
  my $supermodel;
  my ($nodenum, $nodename, $work, $work2, $count, $nodestart, $ref);
  my $isgeometry = 0;  # true if we are in model geometry, false if in animations
  my $isanimation = 0; # true if we are in animations, false if in geometry
  my $innode = 0;  # true if we are currently processing a node
  my $animnum = 0;
  my $task = "";
  my %nodeindex = (null => -1);
  my ($temp1, $temp2, $temp3, $temp4, $temp5, $f1matches, $f2matches, $pathonly);
  my $t;
  my $ASCIIMDL;

  # set up default options for functionality
  if (!defined($options)) {
    $options = {};
  }
  # use area and angle weighted vertex normal averaging
  if (!defined($options->{weight_by_angle})) {
    $options->{weight_by_angle} = 0;
  }
  if (!defined($options->{weight_by_area})) {
    $options->{weight_by_area} = 1;
  }
  if (!defined($options->{use_weights})) {
    $options->{use_weights} = $options->{weight_by_angle} || $options->{weight_by_area};
  }
  if (!$options->{use_weights}) {
    $options->{weight_by_angle} = 0;
    $options->{weight_by_area} = 0;
  }
  # use crease angle test for vertex normal averaging
  if (!defined($options->{use_crease_angle})) {
    $options->{use_crease_angle} = 0;
  }
  # specific crease angle to test for in vertex normal averaging
  if (!defined($options->{crease_angle}) ||
      $options->{crease_angle} < 0 ||
      $options->{crease_angle} > 2 * pi) {
    # 45 degrees
    #$options->{crease_angle} = pi / 4.0;
    # 60 degrees
    $options->{crease_angle} = pi / 3.0;
  }
  # produce vertex data required by the engine based on the faces layout,
  # undo unnecessary doubling of vertices, add required doubling of vertices,
  # force all vertex data to be 1:1 as required by MDX format
  # this option is a 50%+ performance hit, but fixes most model geometry issues
  if (!defined($options->{validate_vertex_data})) {
    $options->{validate_vertex_data} = 1;
  }
  # recalculate the aabb tree or use the one provided?
  if (!defined($options->{recalculate_aabb_tree})) {
    $options->{recalculate_aabb_tree} = 1;
  }


  #extract just the name
  $buffer =~ /(.*[\\\/])*([^\\\/]+)\.(mdl.*)$/i;
  $file = $2;
  $extension = $3;
  $model{'filename'} = $2;
  
  $buffer =~ /(.*)\.mdl/i;
  $filepath = $1;
  MDLOpsM::File::open(\$ASCIIMDL, '<', "$filepath.$extension") or die "can't open MDL file $filepath.$extension\n";
  $model{'source'} = "ascii";
  $model{'filepath+name'} = $filepath;
  $pathonly = substr($filepath, 0, length($filepath)-length($model{'filename'}));
  print("$pathonly\n") if $printall;

  # emitter properties
  my $emitter_properties = [
    'deadspace', 'blastRadius', 'blastLength',
    'numBranches', 'controlptsmoothing', 'xgrid', 'ygrid', 'spawntype',
    'update', 'render', 'blend', 'texture', 'chunkname',
    'twosidedtex', 'loop', 'renderorder', 'm_bFrameBlending', 'm_sDepthTextureName',
  ];
  # emitter flags
  my $emitter_flags = {
    p2p                 => 0x0001,
    p2p_sel             => 0x0002,
    affectedByWind      => 0x0004,
    m_isTinted          => 0x0008,
    bounce              => 0x0010,
    random              => 0x0020,
    inherit             => 0x0040,
    inheritvel          => 0x0080,
    inherit_local       => 0x0100,
    splat               => 0x0200,
    inherit_part        => 0x0400,
    depth_texture       => 0x0800,
    emitterflag13       => 0x1000
  };
  # prepare emitter regex matches, all properties and flags are handled alike
  my $emitter_prop_match = join('|', @{$emitter_properties});
  my $emitter_flag_match = join('|', keys %{$emitter_flags});
  
  #set some default values
  $model{'bmin'} = [-5, -5, -1];
  $model{'bmax'} = [5, 5, 10];
  $model{'radius'} = 7;
  $model{'numanims'} = 0;
  $model{'ignorefog'} = 0;
  $model{'animationscale'} = 0.971;
  $model{'compress_quaternions'} = 0;
  
  # these values are for the trimesh counter sequence,
  # an odd inverted count the purpose of which is unknown to me
  #$model{'meshsequence'} = 98;
  #$model{'meshsequencebasis'} = { start => 99, end => 0 };
  $model{'meshsequence'} = 1;

  # counter for MDLedit-style 'names' entries
  $model{'fakenodes'} = 0;

  # read in the ascii mdl
  while (<$ASCIIMDL>) {
    my $line = $_;
    if ($line =~ /beginmodelgeom/i) { # look for the start of the model
      #print("begin model\n");
      $nodenum = 0;
      $isgeometry = 1;
    } elsif ($line =~ /endmodelgeom/i) { # look for the end of the model
      #print("end model\n");
      $isgeometry = 0;
      $nodenum = 0;
    } elsif ($line =~ /\s*bumpmapped_texture\s+(\S*)/i) { # look for a model-wide bumpmapped texture
      $model{'bumpmapped_texture'}{lc $1} = 1;
    } elsif ($line =~ /^\s*headlink\s+(\S*)/i) { # look for model-wide headfix
      $model{'headlink'} = $1;
    } elsif ($line =~ /\s*compress_quaternions\s+(\S*)/i) { # look for model-wide quaternion compression
      $model{'compress_quaternions'} = $1;
    } elsif ($line =~ /\s*newanim\s+(\S*)\s+(\S*)/i) { # look for the start of an animation
      $isanimation = 1; 
      $model{'anims'}{$animnum}{'name'} = $1;
      $model{'numanims'}++;
      $model{'anims'}{$animnum}{'nodelist'} = [];
      $model{'anims'}{$animnum}{'eventtimes'} = [];
      $model{'anims'}{$animnum}{'eventnames'} = [];
      # copy model-wide compress setting to animation, which acts as 'root'
      # during animation post-processing
      $model{'anims'}{$animnum}{'compress_quaternions'} = $model{'compress_quaternions'};
    } elsif ($line =~ /doneanim/i && $isanimation) { # look for the end of an animation
      $isanimation = 0;
      $animnum++;
    } elsif ($line =~ /\s*length\s+(\S*)/i && $isanimation) {
      $model{'anims'}{$animnum}{'length'} = $1;
    } elsif ($line =~ /\s*animroot\s+(\S*)/i && $isanimation) {
      $model{'anims'}{$animnum}{'animroot'} = $1;
    } elsif ($line =~ /\s*transtime\s+(\S*)/i && $isanimation) {
      $model{'anims'}{$animnum}{'transtime'} = $1; 
    } elsif ($line =~ /\s*newmodel\s+(\S*)/i) { # look for the model name
      $model{'name'} = $1;
    } elsif ($line =~ /\s*setsupermodel\s+(\S*)\s+(\S*)/i) { #look for the super model
      $model{'supermodel'} = $2;
    } elsif (!$innode && $line =~ /\s*bmin\s+(\S*)\s+(\S*)\s+(\S*)/i) { #look for the bounding box min
      $model{'bmin'} = [$1,$2,$3];
    } elsif (!$innode && $line =~ /\s*bmax\s+(\S*)\s+(\S*)\s+(\S*)/i) { #look for the bounding box max
      $model{'bmax'} = [$1,$2,$3];
    } elsif ($innode && $line =~ /\s*bmin\s+(\S*)\s+(\S*)\s+(\S*)/i) { #look for the mesh bounding box min
      $model{nodes}{$nodenum}{'bboxmin'} = [$1,$2,$3];
    } elsif ($innode && $line =~ /\s*bmax\s+(\S*)\s+(\S*)\s+(\S*)/i) { #look for the mesh bounding box max
      $model{nodes}{$nodenum}{'bboxmax'} = [$1,$2,$3];
    } elsif ($innode && ($model{'nodes'}{$nodenum}{'nodetype'} & NODE_HAS_MESH) && $line =~ /^\s*radius\s+(\S+)/i) { #look for the mesh radius
      $model{nodes}{$nodenum}{'radius'} = $1;
    } elsif ($innode && $line =~ /\s*average\s+(\S*)\s+(\S*)\s+(\S*)/i) { #look for the mesh average point
      $model{nodes}{$nodenum}{'average'} = [$1,$2,$3];
    } elsif ($line =~ /\s*classification\s+(\S*)/i) { # look for the model type
      # using this as a key into the classifications hash, so format the string
      $model{'classification'} = ucfirst lc $1;
    } elsif ($line =~ /^\s*classification_unk1\s+(\S+)/i) { # look for the unknown classification byte
      $model{'classification_unk1'} = $1;
    } elsif ($line =~ /^\s*ignorefog\s+(\S+)/i) { # look for the model fog interaction
      $model{'ignorefog'} = $1;
    } elsif (!$innode && $line =~ /\s*radius\s+(\S*)/i) {
      $model{'radius'} = $1;
    } elsif ($line =~ /\s*setanimationscale\s+(\S*)/i) {
      $model{'animationscale'} = $1;
    } elsif ($innode && $line =~ /^\s*($emitter_prop_match)\s+(\S+)\s*$/i) {
      $model{'nodes'}{$nodenum}{$1} = $2;
    } elsif ($innode && $line =~ /^\s*($emitter_flag_match)\s+(\S+)\s*$/i) {
      if (!defined($model{'nodes'}{$nodenum}{'emitterflags'})) {
        $model{'nodes'}{$nodenum}{'emitterflags'} = 0;
      }
      if ($2 == 1) {
        $model{'nodes'}{$nodenum}{'emitterflags'} |= $emitter_flags->{$1};
      }
      $model{'nodes'}{$nodenum}{$1} = int $2;
      next;
    } elsif (!$innode && $line =~ /\s*node\s+(\S*)\s+(\S*)/i && $isanimation) { # look for the start of an animation node
      $innode = 1;
      my $nname = lc($2);
      # handle saber, currently tracked as a name prefix rather than a type
      if ($nname =~ /^2081__/) {
        $nname =~ s/^2081__//;
      }
      $nodenum = $nodeindex{$nname};
      push @{$model{'anims'}{$animnum}{'nodelist'}}, $nodenum;
      $model{'anims'}{$animnum}{'nodes'}{'numnodes'}++;
      $model{'anims'}{$animnum}{'nodes'}{$nodenum}{'nodenum'} = $nodenum;
      $model{'anims'}{$animnum}{'nodes'}{$nodenum}{'nodetype'} = $nodelookup{'dummy'};
      $model{'anims'}{$animnum}{'nodes'}{$nodenum}{'controllernum'} = 0;
      $model{'anims'}{$animnum}{'nodes'}{$nodenum}{'controllerdatanum'} = 0;
      $model{'anims'}{$animnum}{'nodes'}{$nodenum}{'childcount'} = 0;
      $model{'anims'}{$animnum}{'nodes'}{$nodenum}{'children'} = [];
    } elsif ($innode && $line =~ /endnode/i && $isanimation) { # look for the end of an animation node
      $innode = 0;
    } elsif ($innode && $line =~ /endnode/i && $isgeometry) { # look for the end of a geometry node
      $nodenum++;
      $innode = 0;
      $task = "";
      $model{'nodes'}{$nodenum}{'header'} = {};
    } elsif (!$innode && $line =~ /\s*node\s+(\S*)\s+(\S*)/i && $isgeometry) { # look for the start of a geometry node
      my ($ntype, $nname) = (lc($1), $2);
      # handle saber, currently tracked as a name prefix rather than a type
      if ($nname =~ /^2081__/) {
        # type should have been 'trimesh', make it 'saber'
        $ntype = 'lightsaber';
        $nname =~ s/^2081__//;
        $model{'nodes'}{$nodenum}{convert_saber} = 1;
      }
      my $nname_key = lc($nname);
      $model{'nodes'}{'truenodenum'}++;
      $innode = 1;
      $model{'nodes'}{$nodenum}{'nodenum'} = $nodenum;
      $model{'nodes'}{$nodenum}{'render'} = 1;
      $model{'nodes'}{$nodenum}{'shadow'} = 0;
      $model{'nodes'}{$nodenum}{'nodetype'} = $nodelookup{$ntype};
      # determine the MDX data size from the node type
      # we will recalculate this more accurately based on known data later
      if ($model{'nodes'}{$nodenum}{'nodetype'} & NODE_HAS_SKIN) { # skin mesh
        $model{'nodes'}{$nodenum}{'mdxdatasize'} = 64;
        $model{'nodes'}{$nodenum}{'texturenum'} = 1;
      } elsif ($model{'nodes'}{$nodenum}{'nodetype'} & NODE_HAS_DANGLY) { # dangly mesh
        $model{'nodes'}{$nodenum}{'mdxdatasize'} = 32;
        $model{'nodes'}{$nodenum}{'texturenum'} = 1;
      } else {
        $model{'nodes'}{$nodenum}{'mdxdatasize'} = 24; # tri mesh with no texture map
        $model{'nodes'}{$nodenum}{'texturenum'} = 0;
      }
      # handle mesh sequence counter
      if ($model{'nodes'}{$nodenum}{'nodetype'} & NODE_HAS_MESH) {
        # assign mesh sequence counter
        #$model{'nodes'}{$nodenum}{'array3'} = $model{'meshsequence'};
        # prepare next mesh sequence counter number
        # modeling a strange sequence... 98..0, 100,199..101, 200,299..201
        # if anyone ever reads the following lines of code ... sorry.
        #if ($model{'meshsequence'} > $model{'meshsequencebasis'}->{start}) {
          # set end of next range to current value + 1
        #  $model{'meshsequencebasis'}->{end} = $model{'meshsequence'} + 1;
          # set current value to start of previous range + 100
        #  $model{'meshsequence'} = $model{'meshsequencebasis'}->{start} + 100;
          # set start of next range to current range start + 100
        #  $model{'meshsequencebasis'}->{start} += 100;
        #}
        # decrement the counter
        #$model{'meshsequence'} -= 1;
        #if ($model{'meshsequence'} < $model{'meshsequencebasis'}->{end}) {
          # if we decrement past our range basis, set next value to upper limit + 1
        #  $model{'meshsequence'} = $model{'meshsequencebasis'}->{start} + 1
        #}

        # use bead-v inverted sequence counter method, slightly easier to understand
        # some chance these should be based on part numbers, which are computed later,
        # and this is an even more wrong place to do lightsaber mesh counter number...
        my $quo = int($model{'meshsequence'} / 100);
        my $mod = $model{'meshsequence'} % 100;
        $model{'nodes'}{$nodenum}{'array3'} = ((2 ** $quo) * 100) - ($t - ($mod ? $quo * 100 : 0)) - ($quo ? 0 : 1);
        $model{'nodes'}{$nodenum}{'inv_count1'} = $model{'nodes'}{$nodenum}{'array3'};
        $model{'meshsequence'} += 1;
      }
      # number of textures will be added to as they are found in parsing
      $model{'nodes'}{$nodenum}{'texturenum'} = 0;
      $model{'nodes'}{$nodenum}{'mdxdatabitmap'} = 0;
      # set to 1 if node's smooth group numbers are all powers of 2, otherwise 0
      $model{'nodes'}{$nodenum}{'sg_base2'} = 1;
      $model{'nodes'}{$nodenum}{'bboxmin'} = [-5, -5, -5];
      $model{'nodes'}{$nodenum}{'bboxmax'} = [5, 5, 5];
      $model{'nodes'}{$nodenum}{'radius'} = 10;
      $model{'nodes'}{$nodenum}{'average'} = [0, 0, 0];
      $model{'nodes'}{$nodenum}{'diffuse'} = [0.8, 0.8, 0.8];
      $model{'nodes'}{$nodenum}{'ambient'} = [0.2, 0.2, 0.2];
      $model{'nodes'}{$nodenum}{'controllernum'} = 0;
      $model{'nodes'}{$nodenum}{'controllerdatanum'} = 0;
      $model{'nodes'}{$nodenum}{'childcount'} = 0;
      $model{'nodes'}{$nodenum}{'children'} = [];
      #$model{'nodes'}{$nodenum}{'nodetype'} = $nodelookup{$ntype};
      $model{'partnames'}[$nodenum] = $nname;
      #node index has the text node name (in lower case) as keys and node number as values
      $nodeindex{$nname_key} = $nodenum;
      $model{'nodeindex'}{$nname_key} = $nodenum;
    } elsif ($innode && $line =~ /^\s*inv_count\s+(\S+)(?:\s+(\S+))?/i) { # inverted mesh sequence counter
      $model{'nodes'}{$nodenum}{'array3'} = $1;
      $model{'nodes'}{$nodenum}{'inv_count1'} = $1;
      if (defined($2)) {
        $model{'nodes'}{$nodenum}{'inv_count2'} = $2;
      }
    } elsif ($innode && $line =~ /^\s*radius\s+(\S*)/i && $model{'nodes'}{$nodenum}{'nodetype'} != $nodelookup{'light'}) {
      $model{'radius'} = $1;

    } elsif (readasciicontroller($line, $model{'nodes'}{$nodenum}{'nodetype'}, $innode, $isanimation, \%model, $nodenum, $animnum, $ASCIIMDL)) {

    } elsif ($innode && $line =~ /\s*parent\s*(\S*)/i) { # if in a node look for the parent property
      if ($isgeometry) {
        $ref = $model{'nodes'};
      } else {
        $ref = $model{'anims'}{$animnum}{'nodes'};
      }
      $ref->{$nodenum}{'parent'} = $1;
      #translate the parents text name into the parents node number
      $ref->{$nodenum}{'parentnodenum'} = defined($nodeindex{lc($1)}) ? $nodeindex{lc($1)} : -1;
      if ($ref->{$nodenum}{'parentnodenum'} != -1) {
        #record what position in the parents child list this node is in
        $ref->{$nodenum}{'childposition'} = $ref->{ $ref->{$nodenum}{'parentnodenum'} }{'childcount'};
        #increment the parents child list
        $ref->{ $ref->{$nodenum}{'parentnodenum'} }{'children'}[$ref->{$nodenum}{'childposition'}] = $nodenum;
        $ref->{ $ref->{$nodenum}{'parentnodenum'} }{'childcount'}++;
      }
    } elsif ($innode && $line =~ /\s*flareradius\s+(\S*)/i) { # if in a node look for the flareradius property
      $model{'nodes'}{$nodenum}{'flareradius'} = $1;
    } elsif ($innode && $line =~ /\s*(flarepositions|flaresizes|flarecolorshifts|texturenames)\s+(\S*)/i) {
      $task = '';
      $count = 0;
      if ($2 > 0) {
        # there are flare data to read, initialize task list:
        $model{'nodes'}{$nodenum}{$1} = [];
        # set flarepositionsnum, flaresizesnum, flarecolorshiftsnum, or texturenamesnum
        $model{'nodes'}{$nodenum}{$1 . 'num'} = int $2;
        $task = $1;
      }
    } elsif ($innode && $line =~ /\s*ambientonly\s+(\S*)/i) { # if in a node look for the ambientonly property
      $model{'nodes'}{$nodenum}{'ambientonly'} = $1;
    } elsif ($innode && $line =~ /\s*ndynamictype\s+(\S*)/i) { # if in a node look for the ndynamictype property
      $model{'nodes'}{$nodenum}{'ndynamictype'} = $1;
    } elsif ($innode && $line =~ /\s*affectdynamic\s+(\S*)/i) { # if in a node look for the affectDynamic property
      $model{'nodes'}{$nodenum}{'affectdynamic'} = $1;
    } elsif ($innode && $line =~ /\s*flare\s+(\S*)/i) { # if in a node look for the flare property
      $model{'nodes'}{$nodenum}{'flare'} = $1;
    } elsif ($innode && $line =~ /\s*lightpriority\s+(\S*)/i) { # if in a node look for the lightpriority property
      $model{'nodes'}{$nodenum}{'lightpriority'} = $1;
    } elsif ($innode && $line =~ /\s*fadinglight\s+(\S*)/i) { # if in a node look for the fadinglight property
      $model{'nodes'}{$nodenum}{'fadinglight'} = $1;
    } elsif ($innode && $line =~ /\s*refmodel\s+(\S+)/i) { # if in a node look for the refModel property
      $model{'nodes'}{$nodenum}{'refModel'} = $1;
    } elsif ($innode && $line =~ /\s*reattachable\s+(\S+)/i) { # if in a node look for the reattachable property
      $model{'nodes'}{$nodenum}{'reattachable'} = $1;
    } elsif ($innode && $line =~ /\s*render\s+(\S*)/i) { # if in a node look for the render property
      $model{'nodes'}{$nodenum}{'render'} = $1;
    } elsif ($innode && $line =~ /\s*shadow\s+(\S*)/i) { # if in a node look for the shadow property
      $model{'nodes'}{$nodenum}{'shadow'} = $1;
    } elsif ($innode && $line =~ /\s*lightmapped\s+(\S*)/i) { # if in a node look for the lightmapped property
      $model{'nodes'}{$nodenum}{'lightmapped'} = $1;
    } elsif ($innode && $line =~ /\s*rotatetexture\s+(\S*)/i) { # if in a node look for the rotatetexture property
      $model{'nodes'}{$nodenum}{'rotatetexture'} = $1;
    } elsif ($innode && $line =~ /\s*m_bIsBackgroundGeometry\s+(\S*)/i) { # if in a node look for the BackgroundGeometry property
      $model{'nodes'}{$nodenum}{'m_bIsBackgroundGeometry'} = $1;
    } elsif ($innode && $line =~ /\s*tangentspace\s+(\S*)/i) { # if in a node look for the tangentspace property
      $model{'nodes'}{$nodenum}{'tangentspace'} = $1;
      if (defined($model{'nodes'}{$nodenum}{'bitmap'}) &&
          !($model{'nodes'}{$nodenum}{'bitmap'} =~ /^null$/i)) {
        $model{'nodes'}{$nodenum}{'mdxdatabitmap'} |= MDX_TANGENT_SPACE;
      }
    } elsif ($innode && $line =~ /\s*beaming\s+(\S*)/i) { # if in a node look for the beaming property
      $model{'nodes'}{$nodenum}{'beaming'} = $1;
    } elsif ($innode && $line =~ /\s*transparencyhint\s+(\S*)/i) { # if in a node look for the transparencyhint property
      $model{'nodes'}{$nodenum}{'transparencyhint'} = $1;
    } elsif ($innode && $line =~ /\s*dirt_enabled\s+(\S*)/i) { # if in a node look for the k2 dirt_enabled property
      $model{'nodes'}{$nodenum}{'dirt_enabled'} = $1;
    } elsif ($innode && $line =~ /\s*dirt_texture\s+(\S*)/i) { # if in a node look for the k2 dirt_texture property
      $model{'nodes'}{$nodenum}{'dirt_texture'} = $1;
    } elsif ($innode && $line =~ /\s*dirt_worldspace\s+(\S*)/i) { # if in a node look for the k2 dirt_worldspace property
      $model{'nodes'}{$nodenum}{'dirt_worldspace'} = $1;
    } elsif ($innode && $line =~ /\s*hologram_donotdraw\s+(\S*)/i) { # if in a node look for the k2 hologram_donotdraw property
      $model{'nodes'}{$nodenum}{'hologram_donotdraw'} = $1;
    } elsif ($innode && $line =~ /\s*animateuv\s+(\S*)/i) { # if in a node look for the animateuv property
      $model{'nodes'}{$nodenum}{'animateuv'} = $1;
    } elsif ($innode && $line =~ /\s*uvdirectionx\s+(\S*)/i) { # if in a node look for the uvdirectionx property
      $model{'nodes'}{$nodenum}{'uvdirectionx'} = $1;
    } elsif ($innode && $line =~ /\s*uvdirectiony\s+(\S*)/i) { # if in a node look for the uvdirectiony property
      $model{'nodes'}{$nodenum}{'uvdirectiony'} = $1;
    } elsif ($innode && $line =~ /\s*uvjitter\s+(\S*)/i) { # if in a node look for the uvjitter property
      $model{'nodes'}{$nodenum}{'uvjitter'} = $1;
    } elsif ($innode && $line =~ /\s*uvjitterspeed\s+(\S*)/i) { # if in a node look for the uvjitterspeed property
      $model{'nodes'}{$nodenum}{'uvjitterspeed'} = $1;
    } elsif ($innode && $line =~ /\s*diffuse\s+(\S*)\s+(\S*)\s+(\S*)/i) { # if in a node look for the diffuse property
      $model{'nodes'}{$nodenum}{'diffuse'} = [$1, $2, $3];
    } elsif ($innode && $line =~ /\s*ambient\s+(\S*)\s+(\S*)\s+(\S*)/i) {  # if in a node look for the ambient property
      $model{'nodes'}{$nodenum}{'ambient'} = [$1, $2, $3];
    } elsif ($innode && $line =~ /\s*specular\s+(\S*)\s+(\S*)\s+(\S*)/i) {  # if in a node look for the specular property
      # specular numbers are not used, have no place in binary models
      $model{'nodes'}{$nodenum}{'specular'} = [$1, $2, $3];
    } elsif ($innode && $line =~ /\s*shininess\s+(\S*)/i) {  # if in a node look for the shininess property
      # shininess numbers are not used, have no place in binary models
      $model{'nodes'}{$nodenum}{'shininess'} = $1;
    } elsif ($line =~ /^\s*name\s+(\S+)/i) {
      # this is the MDLedit approach to walkmesh nodes that get removed,
      # for now, try just inserting them into the names list,
      # it's not going to help with part number mapping, but we'll see
      $model{'partnames'}[$nodenum + ++$model{'fakenodes'}] = $1;
    } elsif ($innode && $line =~ /\s*bitmap\s+(\S*)/i) {  # if in a node look for the bitmap property
      $model{'nodes'}{$nodenum}{'bitmap'} = $1;
      # if this is a bump mapped texture, indicate that we need tangent space calculations
      if ((defined($model{'bumpmapped_texture'}) &&
           defined($model{'bumpmapped_texture'}{lc $1})) ||
          (defined($model{'nodes'}{$nodenum}{'tangentspace'}) &&
           $model{'nodes'}{$nodenum}{'tangentspace'})) {
        $model{'nodes'}{$nodenum}{'mdxdatabitmap'} |= MDX_TANGENT_SPACE;
      }
      $model{'nodes'}{$nodenum}{'bitmap2'} = "";
      $model{'nodes'}{$nodenum}{'texture0'} = "";
      $model{'nodes'}{$nodenum}{'texture1'} = "";
    } elsif ($innode && $line =~ /\s*lightmap\s+(\S*)/i) {  # if in a node look for the bitmap2 property
      # magnusll export compatibility - lightmap
      $model{'nodes'}{$nodenum}{'bitmap2'} = $1;
      # magnusll export does not include lightmapped flag, set it now
      $model{'nodes'}{$nodenum}{'lightmapped'} = 1;
    } elsif ($innode && $line =~ /\s*bitmap2\s+(\S*)/i) {  # if in a node look for the bitmap2 property
      $model{'nodes'}{$nodenum}{'bitmap2'} = $1;
    } elsif ($innode && $line =~ /\s*texture0\s+(\S*)/i) {  # if in a node look for the texture0 property
      $model{'nodes'}{$nodenum}{'texture0'} = $1;
    } elsif ($innode && $line =~ /\s*texture1\s+(\S*)/i) {  # if in a node look for the texture1 property
      $model{'nodes'}{$nodenum}{'texture1'} = $1;
    } elsif ($innode && $line =~ /\s*displacement\s+(\S*)/i) { # if in a node look for the displacement property
      $model{'nodes'}{$nodenum}{'displacement'} = $1;
    } elsif ($innode && $line =~ /\s*tightness\s+(\S*)/i) { # if in a node look for the tightness property
      $model{'nodes'}{$nodenum}{'tightness'} = $1;
    } elsif ($innode && $line =~ /\s*period\s+(\S*)/i) { # if in a node look for the period property
      $model{'nodes'}{$nodenum}{'period'} = $1;
    } elsif (!$innode && $line =~ /^\s*event\s+(\S+)\s+(\S+)/i && $isanimation) { # if in an animation look for the events
      $model{'anims'}{$animnum}{'eventtimes'} = [
        @{$model{'anims'}{$animnum}{'eventtimes'}}, $1
      ];
      $model{'anims'}{$animnum}{'eventnames'} = [
        @{$model{'anims'}{$animnum}{'eventnames'}}, $2
      ];
      $model{'anims'}{$animnum}{'numevents'} = scalar(
        @{$model{'anims'}{$animnum}{'eventtimes'}}
      );
    } elsif (!$innode && $line =~ /eventlist/i && $isanimation) { # if in an animation look for the start of the event list
      $task = "events";
      $model{'anims'}{$animnum}{'numevents'} = 0;
      $count = 0;      
    } elsif (!$innode && $line =~ /endlist/i && $isanimation) { # if in an animation look for the end of the event list
      $task = "";
      $count = 0;
    } elsif ($innode && $line =~ /\s*[^t]verts\s+(\S*)/i) {  # if in a node look for the start of the verts
      $model{'nodes'}{$nodenum}{'vertnum'} = $1;
      $model{'nodes'}{$nodenum}{'mdxdatabitmap'} |= MDX_VERTICES | MDX_VERTEX_NORMALS;
      $task = "verts";
      $count = 0;
    } elsif ($innode && $line =~ /\s*faces\s+(\S*)/i) { # if in a node look for the start of the faces
      $model{'nodes'}{$nodenum}{'facesnum'} = $1;
      $model{'nodes'}{$nodenum}{'vertfaces'} = {};
      $task = "faces";
      $count = 0;
    } elsif ($innode && $line =~ /\s*tverts\s+(\S*)/i) { # if in a node look for the start of the tverts
      $model{'nodes'}{$nodenum}{'tvertsnum'} = $1;
      # if this is a tri mesh with tverts then adjust the MDX data size
      if ($model{'nodes'}{$nodenum}{'nodetype'} == NODE_TRIMESH) {
        $model{'nodes'}{$nodenum}{'mdxdatasize'} = 32;
      }
      $model{'nodes'}{$nodenum}{'texturenum'} += 1;
      $model{'nodes'}{$nodenum}{'mdxdatabitmap'} |= MDX_TEX0_VERTICES;
      #print($task . "|" . $count . "\n");
      $task = "tverts";
      $count = 0;
    } elsif ($innode && ($line =~ /\s*tverts1\s+(\S*)/i ||
                         $line =~ /\s*lightmaptverts\s+(\S*)/i)) { # if in a node look for the start of the tverts for 2nd texture
      # magnusll export compatibility - lightmaptverts
      $model{'nodes'}{$nodenum}{'tverts1num'} = $1;
      $model{'nodes'}{$nodenum}{'texturenum'} += 1;
      $model{'nodes'}{$nodenum}{'mdxdatabitmap'} |= MDX_TEX1_VERTICES;
      #print($task . "|" . $count . "\n");
      $task = "tverts1";
      $count = 0;
    } elsif ($innode && $line =~ /\s*tverts2\s+(\S*)/i) { # if in a node look for the start of the tverts for 3rd texture
      $model{'nodes'}{$nodenum}{'tverts2num'} = $1;
      $model{'nodes'}{$nodenum}{'texturenum'} += 1;
      $model{'nodes'}{$nodenum}{'mdxdatabitmap'} |= MDX_TEX2_VERTICES;
      #print($task . "|" . $count . "\n");
      $task = "tverts2";
      $count = 0;
    } elsif ($innode && $line =~ /\s*tverts3\s+(\S*)/i) { # if in a node look for the start of the tverts for 4th texture
      $model{'nodes'}{$nodenum}{'tverts3num'} = $1;
      $model{'nodes'}{$nodenum}{'texturenum'} += 1;
      $model{'nodes'}{$nodenum}{'mdxdatabitmap'} |= MDX_TEX3_VERTICES;
      #print($task . "|" . $count . "\n");
      $task = "tverts3";
      $count = 0;
    } elsif ($innode && $line =~ /\s*texindices([123])\s+(\S*)/i) { # if in a node look for start of the extra texture vert indices
      $model{'nodes'}{$nodenum}{"texindices$1num"} = $2;
      $model{'nodes'}{$nodenum}{"texindices$1"} = {};
      $task = "texindices$1";
      $count = 0;
    } elsif ($innode && $line =~ /\s*colors\s+(\S*)/i) { # if in a node look for start of the extra texture vert indices
      $model{'nodes'}{$nodenum}{"colorsnum"} = $1;
      $model{'nodes'}{$nodenum}{"colors"} = [];
      $model{'nodes'}{$nodenum}{'mdxdatabitmap'} |= MDX_VERTEX_COLORS;
      $task = "colors";
      $count = 0;
    } elsif ($innode && $line =~ /\s*colorindices\s+(\S*)/i) { # if in a node look for start of the extra texture vert indices
      $model{'nodes'}{$nodenum}{"colorindicesnum"} = $1;
      $model{'nodes'}{$nodenum}{"colorindices"} = {};
      $task = "colorindices";
      $count = 0;
    } elsif ($innode && $line =~ /\s*[^t]saber_verts\s+(\S*)/i) {  # if in a node look for the start of the saber verts
      $model{'nodes'}{$nodenum}{'saber_vertsnum'} = $1;
      $task = "saber_verts";
      $count = 0;
    } elsif ($innode && $line =~ /\s*[^t]saber_norms\s+(\S*)/i) {  # if in a node look for the start of the saber normals
      $model{'nodes'}{$nodenum}{'saber_normsnum'} = $1;
      $task = "saber_norms";
      $count = 0;
    } elsif ($innode && $line =~ /\s*weights\s+(\S*)/i) { # if in a node look for the start of the weights
      $model{'nodes'}{$nodenum}{'weightsnum'} = $1;
      #print($task . "|" . $count . "\n");
      $task = "weights";
      $count = 0;
    } elsif ($innode && $line =~ /\s*constraints\s+(\S*)/i) { # if in a node look for the start of the constraints
      $model{'nodes'}{$nodenum}{'constraintnum'} = $1;
      #print($task . "|" . $count . "\n");
      $task = "constraints";
      $count = 0;
    } elsif ($innode && $line =~ /\s*aabb/i) { # if in a node look for the start of the constraints
      #print("Found aabb\n");
      #print($task . "|" . $count . "\n");
      $task = "aabb";
      $count = 0;
      if($line =~ /\s*aabb\s*(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)/i) {
        $model{'nodes'}{$nodenum}{'aabbnodes'}[$count] = [$1, $2, $3, $4, $5, $6, $7];
        $count++;
      }
    } elsif (!$innode && $isanimation && $task eq "events") { # if in an animation read in events
      $line =~ /\s+(\S*)\s+(\S*)/;
      $model{'anims'}{$animnum}{'eventtimes'}[$count] = $1;
      $model{'anims'}{$animnum}{'eventnames'}[$count] = $2;
      $model{'anims'}{$animnum}{'numevents'}++;
      $count++;      
    } elsif ($innode && $isanimation) { # if in an animation node read in controllers
    } elsif ($innode && $isgeometry && $task ne '') {  # if in a node and in verts, faces, tverts or constraints read them in
      if (defined($model{'nodes'}{$nodenum}{$task . 'num'}) &&
          $count >= $model{'nodes'}{$nodenum}{$task . 'num'}) {
        # this isn't going to end all of the numbered data gathering tasks
        # that are currently implemented, but it will end the ones that use
        # the normal naming conventions...
        $task = '';
        $count = 0;
      }
      if ($task eq "verts" ) { # read in the verts
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'verts'}[$count] = [$1, $2, $3];
        $count++;
      } elsif ($task eq "faces") { # read in the faces
        $line =~ /^\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(?:(\S+)\s+(\S+)\s+(\S+)|$)/;
        #print Dumper([ $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11 ]);
        # magnusll export compatibility - relocated matID
        if (defined($11)) {
          # magnusll's faces structure w/ the extra tvert indices but no extra matID
          $model{'nodes'}{$nodenum}{'Afaces'}[$count] = "$1 $2 $3 $4 $5 $6 $7 $11";
          $model{'nodes'}{$nodenum}{'Bfaces'}[$count] = [0, 0, 0, 0, $11, -1, -1, -1, $1, $2, $3, $4 ];
        } else {
          # normal/usual faces structure
          $model{'nodes'}{$nodenum}{'Afaces'}[$count] = "$1 $2 $3 $4 $5 $6 $7 $8";
          $model{'nodes'}{$nodenum}{'Bfaces'}[$count] = [0, 0, 0, 0, $8, -1, -1, -1, $1, $2, $3, $4 ];
        }

        # temporary list of uvs associated with each face, deleted after vertex validation
        if (!defined($model{'nodes'}{$nodenum}{'faceuvs'})) {
          $model{'nodes'}{$nodenum}{'faceuvs'} = [];
        }
        $model{'nodes'}{$nodenum}{'faceuvs'}->[$count] = [ int($5), int($6), int($7) ];
        if ( defined($model{'nodes'}{$nodenum}{'vertfaces'}{$1}[0]) )
        {
          push @{$model{'nodes'}{$nodenum}{'vertfaces'}{$1}}, $count;
        }
        else
        {
          $model{'nodes'}{$nodenum}{'vertfaces'}{$1} = [$count];
        }

        if ( defined($model{'nodes'}{$nodenum}{'vertfaces'}{$2}[0]) )
        {
          push @{$model{'nodes'}{$nodenum}{'vertfaces'}{$2}}, $count;
        }
        else
        {
          $model{'nodes'}{$nodenum}{'vertfaces'}{$2} = [$count];
        }

        if ( defined($model{'nodes'}{$nodenum}{'vertfaces'}{$3}[0]) )
        {
          push @{$model{'nodes'}{$nodenum}{'vertfaces'}{$3}}, $count;
        }
        else
        {
          $model{'nodes'}{$nodenum}{'vertfaces'}{$3} = [$count];
        }

        if (!defined($model{'nodes'}{$nodenum}{'tverti'}{$1}))
        {
          $model{'nodes'}{$nodenum}{'tverti'}{$1} = $5;
        }

        if (!defined($model{'nodes'}{$nodenum}{'tverti'}{$2}))
        {
          $model{'nodes'}{$nodenum}{'tverti'}{$2} = $6;
        }

        if (!defined($model{'nodes'}{$nodenum}{'tverti'}{$3}))
        {
          $model{'nodes'}{$nodenum}{'tverti'}{$3} = $7;
        }

        # magnusll export compatibility - texindices1 in faces
        # record magnusll style lightmap tverts in our texindices1 structure
        if (defined($11)) {
          $model{'nodes'}{$nodenum}{texindices1}{$count} = [ $8, $9, $10 ];
        }

        # test whether smooth group number is base 2
        # if ALL smooth group numbers in the node ARE a power of 2,
        # they will be reduced to log base 2 before being written to binary.
        # otherwise smooth group numbers will be left as is.
        #if ($4 > 0 && (log($4) / log(2)) =~ /\D/)
        #{
          # logarithm contained a non-digit (.) so not a clean power of 2
        #  $model{'nodes'}{$nodenum}{'sg_base2'} = 0;
        #}

        $count++;

      } elsif ($task eq "tverts") { # read in the tverts
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'tverts'}[$count] = [$1, $2];
        $count++;
      } elsif ($task eq "tverts1") { # read in the tverts for 2nd texture
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'tverts1'}[$count] = [$1, $2];
        $count++;
      } elsif ($task eq "tverts2") { # read in the tverts for 3rd texture
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'tverts2'}[$count] = [$1, $2];
        $count++;
      } elsif ($task eq "tverts3") { # read in the tverts for 4th texture
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'tverts3'}[$count] = [$1, $2];
        $count++;
      } elsif ($task eq "texindices1") { # read in the tvert indices for 2nd texture
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'texindices1'}{$count}  = [ $1, $2, $3 ];
        $count++;
      } elsif ($task eq "texindices2") { # read in the tvert indices for 3rd texture
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'texindices2'}{$count}  = [ $1, $2, $3 ];
        $count++;
      } elsif ($task eq "texindices3") { # read in the tvert indices for 4th texture
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'texindices3'}{$count}  = [ $1, $2, $3 ];
        $count++;
      } elsif ($task eq "colors") { # read in the vertex colors
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'colors'}[$count]  = [ $1, $2, $3 ];
        $count++;
      } elsif ($task eq "colorindices") { # read in the vertex color indices
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'colorindices'}{$count}  = [ $1, $2, $3 ];
        $count++;
      } elsif ($task eq "saber_verts" ) { # read in the verts1 saber data
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'saber_verts'}[$count] = [$1, $2, $3];
        $count++;
      } elsif ($task eq "saber_norms" ) { # read in the saber_norms saber data
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'saber_norms'}[$count] = [$1, $2, $3];
        $count++;
      } elsif ($task eq "weights") { # read in the bone weights
        $line =~ /\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)/;
        # use a temporary hash to ease some of the following sorted classification
        my $bone_hash = {};
        $bone_hash->{$1} = $2;
        if ($3 ne '') {
          $bone_hash->{$3} = $4;
          if ($5 ne "") {
            $bone_hash->{$5} = $6;
            if ($7 ne "") {
              $bone_hash->{$7} = $8;
            }
          }
        }
        # putting the weights into sorted order here makes validation easier
        $model{'nodes'}{$nodenum}{'Abones'}[$count] = join(
          ' ', map { $_, $bone_hash->{$_} } sort keys %{$bone_hash}
        );
        $model{'nodes'}{$nodenum}{'bones'}[$count] = [
          sort keys %{$bone_hash}
        ];
        $model{'nodes'}{$nodenum}{'weights'}[$count] = [
          map { $bone_hash->{$_} } sort keys %{$bone_hash}
        ];
        $count++;
      } elsif ($task eq "constraints") { # read in the constraints
        $line =~ /\s*(\S*)/;
        $model{'nodes'}{$nodenum}{'constraints'}[$count] = $1;
        $count++;
      } elsif ($task eq "aabb") { # read in the aabb stuff
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{'aabbnodes'}[$count] = [$1, $2, $3, $4, $5, $6, $7];
        $count++;
      } elsif ($task eq 'flarepositions' ||
               $task eq 'flaresizes' ||
               $task eq 'texturenames') {
        $line =~ /\s*(\S*)/;
        $model{'nodes'}{$nodenum}{$task} = [
          @{$model{'nodes'}{$nodenum}{$task}}, $1
        ];
        $count++;
      } elsif ($task eq 'flarecolorshifts') {
        $line =~ /\s*(\S*)\s+(\S*)\s+(\S*)/;
        $model{'nodes'}{$nodenum}{$task} = [
          @{$model{'nodes'}{$nodenum}{$task}}, [ $1, $2, $3 ]
        ];
        $count++;
      } # if ($task eq "verts" )
    } # the big IF
  } # while (<$ASCIIMDL>)

  #$model{'nodes'}{'truenodenum'} = $nodenum;
  
  # set the supernodes on the working model
  print ( lc($model{'supermodel'}) . "|" . $supercheck . "\n") if $printall;
  if (lc($model{'supermodel'}) ne "null" && $supercheck == 1 &&
      MDLOpsM::File::exists($pathonly . $model{'supermodel'} . '.mdl')) {
    # if this model has a super model then open the super model
    print("Loading binary supermodel: " . $pathonly . $model{'supermodel'} . ".mdl\n");
    $supermodel = &readbinarymdl(
      $pathonly . $model{'supermodel'} . ".mdl",
      0, modelversion($pathonly . $model{'supermodel'} . ".mdl"),
      { extract_anims => 0, compute_smoothgroups => 0, weld_model => 0, use_mdx => 0 }
    );
    &get_super_nodes(\%model, $supermodel, undef, undef, 0, 0);
    $model{totalnumnodes} += $model{'nodes'}{'truenodenum'};
    if ($printall) {
      print "\nmaximum parts:$model{totalnumnodes} this model parts:$model{'nodes'}{'truenodenum'}\n";
      for (my $i = 0; $i < $model{'nodes'}{'truenodenum'}; $i++)
      {
        printf(
          "super: %s %d %d\n",
          $model{'partnames'}[$i], $model{nodes}{$i}{nodenum}, $model{nodes}{$i}{supernode}
        );
      }
    }
    $supermodel = undef;
    print("super model is version: " . modelversion($pathonly . $model{'supermodel'} . ".mdl") . "\n");
  }
  elsif (lc($model{'supermodel'}) ne "null" && $supercheck == 1) {
    # if this model has a super model then open the original model
    printf("Supermodel not found: %s%s.mdl\n", $pathonly, $model{'supermodel'});
    print("Loading original binary model: " . $pathonly . $model{'name'} . ".mdl\n");
    #$supermodel = &readbinarymdl($pathonly . $model{'supermodel'} . ".mdl", 0);
    #$supermodel = &readbinarymdl($pathonly . $model{'name'} . ".mdl", 0, modelversion($pathonly . $model{'name'} . ".mdl"));
    $supermodel = &readbinarymdl(
      $pathonly . $model{'name'} . ".mdl",
      0, modelversion($pathonly . $model{'name'} . ".mdl"),
      { extract_anims => 0, compute_smoothgroups => 0, weld_model => 0, use_mdx => 0 }
    );
    foreach (keys %{$supermodel->{'nodes'}} ) {
      if ($_ eq "truenodenum") {next;}
      if ( defined( $nodeindex{ lc( $supermodel->{'partnames'}[$_] ) } ) ) {
        #if ($supermodel->{'nodes'}{$_}{'nodetype'} == NODE_SKIN) {
        #  $model{'nodes'}{$nodeindex{lc($supermodel->{'partnames'}[$_])}}{'qbones'}{'unpacked'} = [ @{$supermodel->{'nodes'}{$_}{'qbones'}{'unpacked'}} ];
        #  $model{'nodes'}{$nodeindex{lc($supermodel->{'partnames'}[$_])}}{'tbones'}{'unpacked'} = [ @{$supermodel->{'nodes'}{$_}{'tbones'}{'unpacked'}} ];
        #  $model{'nodes'}{$nodeindex{lc($supermodel->{'partnames'}[$_])}}{'array8'}{'unpacked'} = [ @{$supermodel->{'nodes'}{$_}{'array8'}{'unpacked'}} ];
        #}
        $model{'nodes'}{$nodeindex{lc($supermodel->{'partnames'}[$_])}}{'supernode'} = $supermodel->{'nodes'}{$_}{'supernode'};
      }
    }
    $supermodel = undef;
    print("original model is version: " . modelversion($pathonly . $model{'name'} . ".mdl") . "\n");
  }


  # pwk and dwk nodes can reside in the model, and even be animated therein,
  # however, we don't want to write them out in geometry,
  # remove them now, letting the pwk/dwk files handle their positions etc.
  if ($model{classification} eq 'Placeable' ||
      $model{classification} eq 'Door') {
    # remove any walkmesh nodes now (preserving them in our names list)
    foreach (keys %nodeindex) {
      if (/_dwk$/i || /_pwk$/i) {
        my $wkm_root_index = $nodeindex{$_};
        # remove the root node from its parent
        $model{nodes}{$model{nodes}{$wkm_root_index}->{parentnodenum}}->{children} = [
          grep {
            $_ != $wkm_root_index
          } @{$model{nodes}{$model{nodes}{$wkm_root_index}->{parentnodenum}}->{children}}
        ];
        # update the parent's child count
        $model{nodes}{$model{nodes}{$wkm_root_index}->{parentnodenum}}->{childcount} = scalar(
          @{$model{nodes}{$model{nodes}{$wkm_root_index}->{parentnodenum}}->{children}}
        );
        # delete the root node and its children
        my $walkmesh_nodes = [ @{$model{nodes}{$wkm_root_index}{children}}, $wkm_root_index ];
        for my $wkm_index (@{$walkmesh_nodes}) {
          delete $model{nodes}{$wkm_index};
          # decrease the total
          $model{nodes}{truenodenum} -= 1;
          # decrease the total that includes any supermodel nodes
          if (defined($model{totalnumnodes})) {
            $model{totalnumnodes} -= 1;
          }
        }
        last;
      }
    }
  }

  # make sure we have the right node number - we weren't processing a bunch of the nodes at the end!
  $nodenum = $model{'nodes'}{'truenodenum'};

  for (my $i = 0; $i < $nodenum; $i++)
  {
    if (!($model{nodes}{$i}{nodetype} & NODE_HAS_SABER)) {
      next;
    }
    if (defined($model{nodes}{$i}{verts}) &&
        scalar(@{$model{nodes}{$i}{verts}}) == 16) {
      $model{nodes}{$i}{convert_saber} = 1;
    }
    if ($model{nodes}{$i}{convert_saber}) {
      $model{nodes}{$i} = convert_trimesh_to_saber(\%model, $i);
      #print "converted\n";
    }
    # these are mesh node indices
    #my $normal_face_indices = [ [ 13, 12,  8 ],
    #                            [  8,  9, 13 ],
    #                            [  4,  5,  0 ],
    #                            [  0,  5,  1 ] ];
    my $normal_face_indices = [ [ 93, 92, 88 ],
                                [ 88, 89, 93 ],
                                [  4,  5,  0 ],
                                [  0,  5,  1 ] ];
    my $face_normals = [];
    foreach (@{$normal_face_indices}) {
      my ($v1, $v2, $v3) = @{$model{nodes}{$i}{verts}}[@{$_}];
      my $normal_vector =
      [
        $v1->[1] * ($v2->[2] - $v3->[2]) +
        $v2->[1] * ($v3->[2] - $v1->[2]) +
        $v3->[1] * ($v1->[2] - $v2->[2]),
        $v1->[2] * ($v2->[0] - $v3->[0]) +
        $v2->[2] * ($v3->[0] - $v1->[0]) +
        $v3->[2] * ($v1->[0] - $v2->[0]),
        $v1->[0] * ($v2->[1] - $v3->[1]) +
        $v2->[0] * ($v3->[1] - $v1->[1]) +
        $v3->[0] * ($v1->[1] - $v2->[1]),
      ];
      #$face_normals = [ @{$face_normals}, normalize_vector($normal_vector) ];
      push @{$face_normals}, normalize_vector($normal_vector);
    }
    my $index_pattern = [ 0, 1, (0) x 20, 2, 3, (2) x 20 ];
    #print Dumper($face_normals);
    #print Dumper($model{nodes}{$i}{saber_norms});
    $model{nodes}{$i}->{saber_norms} = [ map { @{$face_normals} } (0..scalar(@{$index_pattern}) - 1) ];
    $model{nodes}{$i}->{saber_normsnum} = scalar(@{$model{nodes}{$i}->{saber_norms}});
    #print Dumper($model{nodes}{$i}{saber_norms});
  }

  # rework node geometry according to the requirements of the MDX data format,
  # making all of the per-vertex data correlated, as if we had vertex objects
  if ($options->{validate_vertex_data}) {
    for (my $i = 0; $i < $nodenum; $i++)
    {
      if (!($model{nodes}{$i}{nodetype} & NODE_HAS_MESH) ||
          $model{nodes}{$i}{nodetype} & NODE_HAS_SABER ||
          $model{nodes}{$i}{nodetype} & NODE_HAS_AABB) {
        next;
      }
      # temporary data structures for this node's new data
      my $verts       = [];
      my $Afaces      = [];
      my $Bfaces      = [];
      my $vertfaces   = {};
      my $sgroups     = [];
      my $tverts      = [];
      my $tverts1     = [];
      my $tverts2     = [];
      my $tverts3     = [];
      my $tvertsi     = {};
      my $colors      = [];
      my $colorsi     = {};
      my $Abones      = [];
      my $bones       = [];
      my $weights     = [];
      my $constraints = [];
      # precompute the types of optional vertex data in use by this node
      my $use_skin    = ($model{nodes}{$i}{nodetype} & NODE_HAS_SKIN);
      my $use_dangly  = ($model{nodes}{$i}{nodetype} & NODE_HAS_DANGLY);
      my $use_tverts  = ($model{nodes}{$i}{'mdxdatabitmap'} & MDX_TEX0_VERTICES);
      my $use_tverts1 = ($model{nodes}{$i}{'mdxdatabitmap'} & MDX_TEX1_VERTICES);
      my $use_tverts2 = ($model{nodes}{$i}{'mdxdatabitmap'} & MDX_TEX2_VERTICES);
      my $use_tverts3 = ($model{nodes}{$i}{'mdxdatabitmap'} & MDX_TEX3_VERTICES);
      my $use_colors  = ($model{nodes}{$i}{'mdxdatabitmap'} & MDX_VERTEX_COLORS);
      # go through all faces, by face index
      for my $face_index (keys @{$model{'nodes'}{$i}{'Afaces'}}) {
        # construct a face structure that contains all the original ascii data,
        # this construction saves a half second on my 7.3s reference character compile
        # versus splitting the ascii face:
        #my $face = [ split(/\s+/, $model{'nodes'}{$i}{'Afaces'}[$face_index]) ];
        my $face = [
          @{$model{'nodes'}{$i}{'Bfaces'}[$face_index]}[8..10],
          $model{'nodes'}{$i}{'Bfaces'}[$face_index][11],
          0, 0, 0, 0, # texture 1
          0, 0, 0, 0, # texture 2
          0, 0, 0, 0, # texture 3
          0, 0, 0, 0, # texture 4
          0, 0, 0     # vertex colors
        ];
        if ($use_tverts || $use_tverts1 || $use_tverts2 || $use_tverts3) {
          # doesn't work because tverti is only accurate when geometry is already correct
          #$face->[4] = $model{'nodes'}{$i}{'tverti'}{$face->[0]};
          #$face->[5] = $model{'nodes'}{$i}{'tverti'}{$face->[1]};
          #$face->[6] = $model{'nodes'}{$i}{'tverti'}{$face->[2]};
          # instead, we made a new structure to track these, it will be deleted!
          $face->[4] = $model{'nodes'}{$i}{'faceuvs'}->[$face_index][0];
          $face->[5] = $model{'nodes'}{$i}{'faceuvs'}->[$face_index][1];
          $face->[6] = $model{'nodes'}{$i}{'faceuvs'}->[$face_index][2];
          $face->[8] = $model{'nodes'}{$i}{'faceuvs'}->[$face_index][0];
          $face->[9] = $model{'nodes'}{$i}{'faceuvs'}->[$face_index][1];
          $face->[10] = $model{'nodes'}{$i}{'faceuvs'}->[$face_index][2];
          $face->[12] = $model{'nodes'}{$i}{'faceuvs'}->[$face_index][0];
          $face->[13] = $model{'nodes'}{$i}{'faceuvs'}->[$face_index][1];
          $face->[14] = $model{'nodes'}{$i}{'faceuvs'}->[$face_index][2];
          $face->[16] = $model{'nodes'}{$i}{'faceuvs'}->[$face_index][0];
          $face->[17] = $model{'nodes'}{$i}{'faceuvs'}->[$face_index][1];
          $face->[18] = $model{'nodes'}{$i}{'faceuvs'}->[$face_index][2];
          if ($use_tverts1 && defined($model{'nodes'}{$i}{'texindices1'})) {
            $face->[8] = $model{'nodes'}{$i}{'texindices1'}{$face_index}->[0];
            $face->[9] = $model{'nodes'}{$i}{'texindices1'}{$face_index}->[1];
            $face->[10] = $model{'nodes'}{$i}{'texindices1'}{$face_index}->[2];
          }
          if ($use_tverts2 && defined($model{'nodes'}{$i}{'texindices2'})) {
            $face->[12] = $model{'nodes'}{$i}{'texindices2'}{$face_index}->[0];
            $face->[13] = $model{'nodes'}{$i}{'texindices2'}{$face_index}->[1];
            $face->[14] = $model{'nodes'}{$i}{'texindices2'}{$face_index}->[2];
          }
          if ($use_tverts3 && defined($model{'nodes'}{$i}{'texindices3'})) {
            $face->[16] = $model{'nodes'}{$i}{'texindices3'}{$face_index}->[0];
            $face->[17] = $model{'nodes'}{$i}{'texindices3'}{$face_index}->[1];
            $face->[18] = $model{'nodes'}{$i}{'texindices3'}{$face_index}->[2];
          }
        }
        if ($use_colors && defined($model{'nodes'}{$i}{'colorindices'})) {
          $face->[20] = $model{'nodes'}{$i}{'colorindices'}{$face_index}->[0];
          $face->[21] = $model{'nodes'}{$i}{'colorindices'}{$face_index}->[1];
          $face->[22] = $model{'nodes'}{$i}{'colorindices'}{$face_index}->[2];
        }
        # empty templates for this face's data
        my $new_Aface = '';
        my $new_Bface = [ 0, 0, 0, 0, int($face->[3]), -1, -1, -1, 0, 0, 0, int($face->[3]) ];
        # retain the face's vertex positions in easier to use structure
        my $face_verts = [
          @{$model{'nodes'}{$i}{verts}}[@{$face}[0..2]]
        ];
        # retain the face's texture vertex positions (if used) in convenient structure
        my $face_tverts = [];
        my $face_tverts1 = [];
        my $face_tverts2 = [];
        my $face_tverts3 = [];
        my $face_colors = [];
        if ($use_tverts) {
          $face_tverts = [
            @{$model{'nodes'}{$i}{tverts}}[@{$face}[4..6]]
          ];
        }
        if ($use_tverts1) {
          $face_tverts1 = [
            @{$model{'nodes'}{$i}{tverts1}}[@{$face}[8..10]]
          ];
        }
        if ($use_tverts2) {
          $face_tverts2 = [
            @{$model{'nodes'}{$i}{tverts2}}[@{$face}[12..14]]
          ];
        }
        if ($use_tverts3) {
          $face_tverts3 = [
            @{$model{'nodes'}{$i}{tverts3}}[@{$face}[16..18]]
          ];
        }
        if ($use_colors) {
          $face_colors = [
            @{$model{'nodes'}{$i}{colors}}[@{$face}[20..22]]
          ];
        }
        # go through the 3 vertices of this face, by face vertex index
        for my $fv_index (0..2) {
          my $match_found = 0;
          # attempt to find matching existing vertex we can use,
          # starting from list end here yields ~50% performance gain
          for my $index (reverse keys @{$verts}) {
            if ((!$use_tverts  || vertex_equals($tverts->[$index],  $face_tverts->[$fv_index],  4)) &&
                (!$use_tverts1 || vertex_equals($tverts1->[$index], $face_tverts1->[$fv_index], 4)) &&
                (!$use_tverts2 || vertex_equals($tverts2->[$index], $face_tverts2->[$fv_index], 4)) &&
                (!$use_tverts3 || vertex_equals($tverts3->[$index], $face_tverts3->[$fv_index], 4)) &&
                (!$use_colors  || vertex_equals($colors->[$index], $face_colors->[$fv_index], 4)) &&
                ($sgroups->[$index] & int($face->[3])) &&
                # having different weights/constraints at the same location is
                # pretty close to an error, but we let people make that mistake...
                # removing the following 2 tests will prevent any weight/constraint mismatches
                (!$use_skin || $Abones->[$index] eq $model{'nodes'}{$i}{Abones}[$face->[$fv_index]]) &&
                (!$use_dangly || $constraints->[$index] == $model{'nodes'}{$i}{constraints}[$face->[$fv_index]]) &&
                vertex_equals($verts->[$index], $face_verts->[$fv_index], 4)) {
              # existing vertex matches on all criteria, use it
              $new_Aface .= $index . ' ';
              $new_Bface->[8 + $fv_index] = $index;
              if (!defined($vertfaces->{$index})) {
                $vertfaces->{$index} = [];
              }
              $vertfaces->{$index} = [ @{$vertfaces->{$index}}, $face_index ];
              if ($use_tverts || $use_tverts1 || $use_tverts2 || $use_tverts3) {
                $tvertsi->{$index} = $index;
              }
              if ($use_colors) {
                $colorsi->{$index} = $index;
              }
              $match_found = 1;
              last;
            }
          }
          if ($match_found) {
            # match was found, proceed to next face vertex
            next;
          }
          # no match, use a new vertex
          my $new_index = scalar(@{$verts});
          # vertex position
          $verts->[$new_index] = [ @{$face_verts->[$fv_index]} ];
          # vertex texture UVs
          if ($use_tverts) {
            $tverts->[$new_index] = [ @{$face_tverts->[$fv_index]} ];
          }
          if ($use_tverts1) {
            $tverts1->[$new_index] = [ @{$face_tverts1->[$fv_index]} ];
          }
          if ($use_tverts2) {
            $tverts2->[$new_index] = [ @{$face_tverts2->[$fv_index]} ];
          }
          if ($use_tverts3) {
            $tverts3->[$new_index] = [ @{$face_tverts3->[$fv_index]} ];
          }
          if ($use_tverts || $use_tverts1 || $use_tverts2 || $use_tverts3) {
            $tvertsi->{$new_index} = $new_index;
          }
          if ($use_colors) {
            $colors->[$new_index] = [ @{$face_colors->[$fv_index]} ];
            $colorsi->{$new_index} = $new_index;
          }
          # vertex smooth group (used for comparison only, not in MDX)
          $sgroups->[$new_index] = int($face->[3]);
          # vertex index in new face structure
          $new_Aface .= $new_index . ' ';
          $new_Bface->[8 + $fv_index] = $new_index;
          # update new map of vertex to connected face indices
          if (!defined($vertfaces->{$new_index})) {
            $vertfaces->{$new_index} = [];
          }
          #$vertfaces->{$new_index} = [ @{$vertfaces->{$new_index}}, $face_index ];
          push @{$vertfaces->{$new_index}}, $face_index;
          # vertex dangly deformation data
          if ($use_dangly) {
            $constraints->[$new_index] = $model{'nodes'}{$i}{constraints}[$face->[$fv_index]];
          }
          # vertex skin deformation data
          if ($use_skin) {
            $Abones->[$new_index] = $model{'nodes'}{$i}{Abones}[$face->[$fv_index]];
            $bones->[$new_index] = [ @{$model{'nodes'}{$i}{bones}[$face->[$fv_index]]} ];
            $weights->[$new_index] = [ @{$model{'nodes'}{$i}{weights}[$face->[$fv_index]]} ];
          }
        }
        # all vertices are now set for this face,
        # add the smoothgroup, tvert indices, and material ID
        $new_Aface = sprintf(
          '%s%s %s%s',
          $new_Aface,
          $face->[3],
          ($use_tverts || $use_tverts1 || $use_tverts2 || $use_tverts3)
            ? $new_Aface : '0 0 0 ',
          $face->[7]
        );
        # add the temporary face data to node's new faces structures
        #$Afaces = [ @{$Afaces}, $new_Aface ];
        push @{$Afaces}, $new_Aface;
        #$Bfaces = [ @{$Bfaces}, $new_Bface ];
        push @{$Bfaces}, $new_Bface;
      }
      #print Dumper($verts);
      #print Dumper(@{$Bfaces});
      #print scalar(@{$verts}) . ' ' . scalar(@{$tverts}) . ' '. scalar(keys %{$tvertsi})."\n";
      # assign the new face and per-vertex data into original node.
      # we can assign because the loop will 'my' new references on the next iteration,
      # rather than reusing these references.
      # make sure all of the updated totals are stored!
      #XXX kill all use of precomputed totals eventually
      #$model{'nodes'}{$i}{Afaces} = [ @{$Afaces} ];
      #$model{'nodes'}{$i}{Bfaces} = [ @{$Bfaces} ];
      $model{'nodes'}{$i}{Afaces} = $Afaces;
      $model{'nodes'}{$i}{Bfaces} = $Bfaces;
      #$model{'nodes'}{$i}{verts} = [ @{$verts} ];
      $model{'nodes'}{$i}{verts} = $verts;
      $model{'nodes'}{$i}{vertnum} = scalar(@{$verts});
      #$model{'nodes'}{$i}{vertfaces} = { %{$vertfaces} };
      $model{'nodes'}{$i}{vertfaces} = $vertfaces;
      if ($use_tverts) {
        #$model{'nodes'}{$i}{tverts} = [ @{$tverts} ];
        $model{'nodes'}{$i}{tverts} = $tverts;
        $model{'nodes'}{$i}{tvertsnum} = scalar(@{$tverts});
      }
      if ($use_tverts1) {
        #$model{'nodes'}{$i}{tverts1} = [ @{$tverts1} ];
        $model{'nodes'}{$i}{tverts1} = $tverts1;
        $model{'nodes'}{$i}{tverts1num} = scalar(@{$tverts1});
      }
      if ($use_tverts2) {
        #$model{'nodes'}{$i}{tverts2} = [ @{$tverts2} ];
        $model{'nodes'}{$i}{tverts2} = $tverts2;
        $model{'nodes'}{$i}{tverts2num} = scalar(@{$tverts2});
      }
      if ($use_tverts3) {
        #$model{'nodes'}{$i}{tverts3} = [ @{$tverts3} ];
        $model{'nodes'}{$i}{tverts3} = $tverts3;
        $model{'nodes'}{$i}{tverts3num} = scalar(@{$tverts3});
      }
      if ($use_tverts || $use_tverts1 || $use_tverts2 || $use_tverts3) {
        #$model{'nodes'}{$i}{tverti} = { %{$tvertsi} };
        $model{'nodes'}{$i}{tverti} = $tvertsi;
        if ($use_tverts1 && defined($model{'nodes'}{$i}{texindices1})) {
          $model{'nodes'}{$i}{texindices1} = $tvertsi;
        }
        if ($use_tverts2 && defined($model{'nodes'}{$i}{texindices2})) {
          $model{'nodes'}{$i}{texindices2} = $tvertsi;
        }
        if ($use_tverts3 && defined($model{'nodes'}{$i}{texindices3})) {
          $model{'nodes'}{$i}{texindices3} = $tvertsi;
        }
        # remove the now-inaccurate list of uv indices per face
        delete $model{'nodes'}{$i}{'faceuvs'};
      }
      if ($use_colors) {
        $model{'nodes'}{$i}{colors} = $colors;
        $model{'nodes'}{$i}{colorindices} = $colorsi;
      }
      if ($use_dangly) {
        $model{'nodes'}{$i}{constraints} = $constraints;
      }
      if ($use_skin) {
        #$model{'nodes'}{$i}{Abones} = [ @{$Abones} ];
        $model{'nodes'}{$i}{Abones} = $Abones;
        $model{'nodes'}{$i}{bones} = $bones;
        #$model{'nodes'}{$i}{weights} = [ @{$weights} ];
        $model{'nodes'}{$i}{weights} = $weights;
        $model{'nodes'}{$i}{weightsnum} = scalar(@{$weights});
      }
    }
  } else {
    # validation not requested, so we need to translate texindices now...
    for (my $i = 0; $i < $nodenum; $i++)
    {
      if (!($model{nodes}{$i}{nodetype} & NODE_HAS_MESH) ||
          $model{nodes}{$i}{nodetype} & NODE_HAS_SABER ||
          $model{nodes}{$i}{nodetype} & NODE_HAS_AABB) {
        next;
      }
      for my $idx_num (1..3) {
        if (defined($model{'nodes'}{$i}{'texindices' . $idx_num})) {
          # has face index => tvert1 index, needs to be vert index => tvert1
          my $tex_idxs = {};
          for my $fidx (keys %{$model{'nodes'}{$i}{'texindices' . $idx_num}}) {
            $tex_idxs->{$model{'nodes'}{$i}{Bfaces}[$fidx][8]} = $model{'nodes'}{$i}{'texindices' . $idx_num}{$fidx}->[0];
            $tex_idxs->{$model{'nodes'}{$i}{Bfaces}[$fidx][9]} = $model{'nodes'}{$i}{'texindices' . $idx_num}{$fidx}->[1];
            $tex_idxs->{$model{'nodes'}{$i}{Bfaces}[$fidx][10]} = $model{'nodes'}{$i}{'texindices' . $idx_num}{$fidx}->[2];
          }
          $model{'nodes'}{$i}{'texindices' . $idx_num} = $tex_idxs;
        }
      }
    }
  }


    # Define the hash (C Array?) to hold the normals,
    # As well as the hash for the surface areas
    # And the flattened vertex list

    my %faceareas    = ();
    my $face_by_pos  = {};


#    open LOG, ">", "log.txt";

    # compute what goes into the MDX data rows for this node, and the offsets for each type of data
    for (my $i = 0; $i < $nodenum; $i++)
    {
        $model{'nodes'}{$i}{'mdxdatasize'} = 0;
        $model{'nodes'}{$i}{'mdxrowoffsets'} = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1];
        # this is the right time to do any override tests for MDX contents
        if ($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER) {
            # mesh of type lightsaber does not use MDX data, make sure size is 0 and offsets are -1
            # also clear the mdx data bitmap so everything is consistent
            $model{'nodes'}{$i}{'mdxdatabitmap'} = 0;
            next;
        }
        foreach (keys @{$structs{'mdxrows'}}) {
            if ($model{'nodes'}{$i}{'mdxdatabitmap'} & $structs{'mdxrows'}->[$_]{bitfield}) {
                # handle row offset in 2 ways, using same keys as readbinary, and a secondary method
                # using a combined array of the 11 possible offsets in common mesh header
                $model{'nodes'}{$i}{$structs{'mdxrows'}->[$_]{offset}} = $model{'nodes'}{$i}{'mdxdatasize'};
                $model{'nodes'}{$i}{'mdxrowoffsets'}->[$structs{'mdxrows'}->[$_]{offset_i}] = $model{'nodes'}{$i}{'mdxdatasize'};
                $model{'nodes'}{$i}{'mdxdatasize'} += $structs{'mdxrows'}->[$_]{num} * 4;
            } else {
                $model{'nodes'}{$i}{$structs{'mdxrows'}->[$_]{offset}} = -1;
            }
        }
        # add in the sub-type MDX row data
        if ($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_SKIN) {
            # add separate offsets for boneweights & boneindices, add their size to overall mdxdatasize
            $model{'nodes'}{$i}{'mdxboneweightsloc'} = $model{'nodes'}{$i}{'mdxdatasize'};
            $model{'nodes'}{$i}{'mdxdatasize'} += 4 * 4; # 4 4-byte floats
            $model{'nodes'}{$i}{'mdxboneindicesloc'} = $model{'nodes'}{$i}{'mdxdatasize'};
            $model{'nodes'}{$i}{'mdxdatasize'} += 4 * 4; # 4 4-byte floats
        }
        printf(
            "$i mdx bitmap %u size %u: offsets %s\n",
            $model{'nodes'}{$i}{'mdxdatabitmap'}, $model{'nodes'}{$i}{'mdxdatasize'},
            join(',', @{$model{'nodes'}{$i}{'mdxrowoffsets'}})
        ) if $printall;
    }

    # calculate new aabb trees if possible
    if ($options->{recalculate_aabb_tree} &&
        eval "defined &MDLOpsM::Walkmesh::detect_format; 1;")
    {
        # advanced walkmesh functions are available, build working aabb trees
        for (my $i = 0; $i < $model{'nodes'}{'truenodenum'}; $i++)
        {
            if (!($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_AABB)) {
                next;
            }
            # prepare enough walkmesh structure for the walkmesh aabb tree calculation
            $model{'nodes'}{$i}{'walkmesh'}{verts} = [
                @{$model{'nodes'}{$i}{'verts'}}
            ];
            $model{'nodes'}{$i}{'walkmesh'}{faces} = [
                map { [ @{$_}[8,9,10] ] } @{$model{'nodes'}{$i}{'Bfaces'}}
            ];
            # this is where the new aabb tree will be:
            $model{'nodes'}{$i}{'walkmesh'}{aabbs} = [];
            MDLOpsM::Walkmesh::aabb(
                $model{'nodes'}{$i}{'walkmesh'},
                [ (0..(scalar(@{$model{'nodes'}{$i}{'walkmesh'}->{faces}}) - 1)) ]
            );
        }
    }

    # Compute bounding box, average, radius
    for (my $i = 0; $i < $nodenum; $i ++)
    {
        # Skip non-mesh nodes
        if (!($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH))
        {
            next;
        }
        my $used_vpos  = {};
        my $used_verts = [ 0, 0, 0 ];
        my $vsum = [ 0.0, 0.0, 0.0 ];
        # note: changed these to 0 values on further study of vanilla models
        # it seems like bmin numbers should never be positive and
        # bmax numbers should never be negative
        $model{'nodes'}{$i}{'bboxmin'} = [ 0.0, 0.0, 0.0 ];
        $model{'nodes'}{$i}{'bboxmax'} = [ 0.0, 0.0, 0.0 ];
        for my $vert (@{$model{'nodes'}{$i}{'verts'}})
        {
            my $vert_key = sprintf('%.4g,%.4g,%.4g', @{$vert});
            foreach (0..2)
            {
                if ($vert->[$_] < $model{'nodes'}{$i}{'bboxmin'}->[$_]) {
                    $model{'nodes'}{$i}{'bboxmin'}->[$_] = $vert->[$_];
                }
                if ($vert->[$_] > $model{'nodes'}{$i}{'bboxmax'}->[$_]) {
                #printf("%g > %g\n", $vert->[$_], $model{'nodes'}{$i}{'bboxmax'}->[$_]);
                    $model{'nodes'}{$i}{'bboxmax'}->[$_] = $vert->[$_];
                }
            }
            if (defined($used_vpos->{$vert_key}))
            {
                next;
            }
            foreach (0..2)
            {
                $used_vpos->{$vert_key} = 1;
                $used_verts->[$_] += 1;
                $vsum->[$_] += $vert->[$_];
            }
        }
        # compute node average from unique vertex positions,
        # no doubles for multiple vertices sharing a position
        $model{'nodes'}{$i}{'average'} = [
            map { $used_verts->[$_] ? $vsum->[$_] / $used_verts->[$_] : 0.0 } (0..2)
        ];
        # compute node radius, it is the longest ray from average point to vertex
        $model{'nodes'}{$i}{'radius'} = 0.0;
        for my $vert (@{$model{'nodes'}{$i}{'verts'}}) {
            my $v_rad = [
                map { $vert->[$_] - $model{'nodes'}{$i}{'average'}->[$_] } (0..2)
            ];
            my $vec_len = sqrt($v_rad->[0]**2 + $v_rad->[1]**2 + $v_rad->[2]**2);
            if ($vec_len > $model{'nodes'}{$i}{'radius'}) {
                $model{'nodes'}{$i}{'radius'} = $vec_len;
            }
        }
    }

    # Compute model-global translations and vertex coordinates for each node
    for (my $i = 0; $i < $nodenum; $i++)
    {
        my $ancestry = [ $i ];
        my $parent = $model{'nodes'}{$i};
        # walk up to the root from the node, prepending each ancestor node number
        # so that we get a flat list of children from root to node
        while ($parent->{'parentnodenum'} != -1) {
            $ancestry = [ $parent->{'parentnodenum'}, @{$ancestry} ];
            $parent = $model{'nodes'}{$parent->{'parentnodenum'}};
        }
        # initialize the node's transform structure which contains
        # the model-global position and orientation, and,
        # a list of transformed vertex positions
        $model{'nodes'}{$i}{transform} = {
            position    => [ 0.0, 0.0, 0.0 ],
            orientation => [ 0.0, 0.0, 0.0, 1.0 ],
            verts       => []
        };
        for my $ancestor (@{$ancestry}) {
            #print Dumper($model{'nodes'}{$ancestor});
            #print Dumper($model{'nodes'}{$ancestor}{'Bcontrollers'});
            if (defined($model{'nodes'}{$ancestor}{'Bcontrollers'}) &&
                defined($model{'nodes'}{$ancestor}{'Bcontrollers'}{8})) {
                # node has a position, add it to current value
                map { $model{'nodes'}{$i}{transform}{position}->[$_] +=
                      $model{'nodes'}{$ancestor}{Bcontrollers}{8}{values}->[0][$_] } (0..2);
            }
            if (defined($model{'nodes'}{$ancestor}{'Bcontrollers'}) &&
                defined($model{'nodes'}{$ancestor}{'Bcontrollers'}{20})) {
                # node has an orientation, multiply quaternions to combine orientations
                $model{'nodes'}{$i}{transform}{orientation} = &quaternion_multiply(
                    $model{'nodes'}{$i}{transform}{orientation},
                    $model{'nodes'}{$ancestor}{'Bcontrollers'}{20}{values}->[0]
                );
            }
#            print Dumper($model{'nodes'}{$i}{transform});
        }
    }

    # Create a position-indexed structure containing all vertices in all meshes
    for (my $i = 0; $i < $nodenum; $i++)
    {
        if (!($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH) ||
            ($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER))
        {
            next;
        }
        # step through the vertices, storing the index in $work
        for $work (keys @{$model{'nodes'}{$i}{'verts'}})
        {
            # apply rotation to the vertex position
            my $vert_pos = &quaternion_apply($model{'nodes'}{$i}{transform}{orientation},
                                             $model{'nodes'}{$i}{'verts'}[$work]);
            # add position (this effectively makes the previous rotation around this point)
            $vert_pos = [
                map { $model{'nodes'}{$i}{transform}{position}->[$_] + $vert_pos->[$_] } (0..2)
            ];
            # store translated vertex position
            $model{'nodes'}{$i}{transform}{verts}->[$work] = $vert_pos;
            # generate string key based on translated vertex position
            my $vert_key = sprintf('%.4g,%.4g,%.4g', @{$vert_pos});
            if (!defined($face_by_pos->{$vert_key})) {
                $face_by_pos->{$vert_key} = [];
            }
            # append this vertex's data to the data list for this position
            #$face_by_pos->{$vert_key} = [
            push
                @{$face_by_pos->{$vert_key}},
                {
                    mesh  => $i,
                    meshname => $model{partnames}[$i],
                    #faces => [ @{$model{'nodes'}{$i}{'vertfaces'}{$work}} ],
                    faces => $model{'nodes'}{$i}{'vertfaces'}{$work},
                    vertex => $work
                };
            #];
        }
    }

    # Total surface area for each smooth group defined in the model,
    # smooth groups can be used as cross-mesh objects,
    # so we don't want this structure to be under a specific node
    # THIS IS NOW UNUSED, COMMENTED OUT
    #$model{'surfacearea_by_group'} = {};

    # Calculate face surface areas and record surface area totals
    # Loop through all of the model's nodes
    for (my $i = 0; $i < $nodenum; $i ++)
    {
        # these calculations are only for mesh nodes
        if (!($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH)) {
            # skip non-mesh nodes
            next;
        }

        # initialize new value for total surface area of faces in this mesh
        $model{'nodes'}{$i}{'surfacearea'} = 0;
        # initialize new hash for total surface areas of faces in this mesh,
        # per smooth-group (this is recorded but unused so far)
        $model{'nodes'}{$i}{'surfacearea_by_group'} = {};

        # Loop through all the node's faces
        foreach (keys @{$model{'nodes'}{$i}{'Bfaces'}}) {
            # store the face data in a hash reference, $face
            my $face = $model{'nodes'}{$i}{'Bfaces'}->[$_];
            # calculate the face's surface area
            my $area = facearea(
                $model{'nodes'}{$i}{'verts'}[$face->[8]],
                $model{'nodes'}{$i}{'verts'}[$face->[9]],
                $model{'nodes'}{$i}{'verts'}[$face->[10]]
            );

            #print "Area: $area in $face->[11]\n";

            # record the face area in the faceareas hash
            $faceareas{$i}{$_} = $area;

            # update the node-level total surface area, this might be a mesh header field
            $model{'nodes'}{$i}{'surfacearea'} += $area;

            # THIS IS NOW UNUSED, COMMENTED OUT
            # initialize node-level smoothgroup surface area to 0 if first face in group
            #if (!defined($model{'nodes'}{$i}{'surfacearea_by_group'}->{$face->[11]})) {
            #    $model{'nodes'}{$i}{'surfacearea_by_group'}->{$face->[11]} = 0;
            #}
            # increase node-level total surface area for smoothgroup
            #$model{'nodes'}{$i}{'surfacearea_by_group'}->{$face->[11]} += $area;

            # initialize total surface area for smoothgroup to 0 if first face in group
            #if (!defined($model{'surfacearea_by_group'}->{$face->[11]})) {
            #    $model{'surfacearea_by_group'}->{$face->[11]} = 0;
            #}
            # increase total surface area for smoothgroup
            #$model{'surfacearea_by_group'}->{$face->[11]} += $area;
        }
    }

    # Calculate face surface normals
    # Calculate face tangent and bitangent vectors if bumpmapping
    # Loop through all of the model's nodes
    for (my $i = 0; $i < $nodenum; $i ++)
    {
        # these calculations are only for mesh nodes
        if (!($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH) ||
            ($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER)) {
            # skip non-mesh nodes
            # skip saber mesh nodes
            next;
        }
        $model{nodes}{$i}{rawfacenormals} = [];
        $model{nodes}{$i}{worldfacenormals} = [];

        # If the node has a mesh and isn't a saber, calculate the face plane normals and plane distances
        if (($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH) && !($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER))
        {
            print ("calculating plane normals for node $i\n") if $printall;

            $count = 0; 

            # Loop through each of the node's faces and calculate the normals
            foreach (@{$model{'nodes'}{$i}{'Bfaces'}})
            {
                my ($p1x, $p1y, $p1z, $p2x, $p2y, $p2z, $p3x, $p3y, $p3z);
                my ($xpx, $xpy, $xpz, $pd, $norm);

                $p1x = $model{'nodes'}{$i}{'verts'}[$_->[8]][0];  # Vertex 1's X
                $p1y = $model{'nodes'}{$i}{'verts'}[$_->[8]][1];  # Vertex 1's Y
                $p1z = $model{'nodes'}{$i}{'verts'}[$_->[8]][2];  # Vertex 1's Z

                $p2x = $model{'nodes'}{$i}{'verts'}[$_->[9]][0];  # Vertex 2's X
                $p2y = $model{'nodes'}{$i}{'verts'}[$_->[9]][1];  # Vertex 2's Y
                $p2z = $model{'nodes'}{$i}{'verts'}[$_->[9]][2];  # Vertex 2's Z

                $p3x = $model{'nodes'}{$i}{'verts'}[$_->[10]][0]; # Vertex 3's X
                $p3y = $model{'nodes'}{$i}{'verts'}[$_->[10]][1]; # Vertex 3's Y
                $p3z = $model{'nodes'}{$i}{'verts'}[$_->[10]][2]; # Vertex 3's Z

                # Old MDLOps code
                #calculate the un-normalized cross product and un-normalized plane distance
                $xpx = $p1y * ($p2z - $p3z) + $p2y * ($p3z - $p1z) + $p3y * ($p1z - $p2z);
                $xpy = $p1z * ($p2x - $p3x) + $p2z * ($p3x - $p1x) + $p3z * ($p1x - $p2x);
                $xpz = $p1x * ($p2y - $p3y) + $p2x * ($p3y - $p1y) + $p3x * ($p1y - $p2y);
                $pd  = -$p1x * ($p2y * $p3z - $p3y * $p2z) -
                        $p2x * ($p3y * $p1z - $p1y * $p3z) -
                        $p3x * ($p1y * $p2z - $p2y * $p1z);


                #calculate the normalizing factor
                $norm = sqrt($xpx**2 + $xpy**2 + $xpz**2);

#               print "Normalizing calculated: $norm\n";

                # Check for $norm being 0 to prevent illegal division by 0...
                $model{'nodes'}{$i}{'rawfacenormals'}[$count] = [ $xpx, $xpy, $xpz ];
                $model{'nodes'}{$i}{'facenormals'}[$count] = normalize_vector([ $xpx, $xpy, $xpz ]);
                $model{'nodes'}{$i}{'worldfacenormals'}[$count] = &quaternion_apply(
                  $model{'nodes'}{$i}{transform}{orientation},
                  $model{'nodes'}{$i}{'facenormals'}[$count]
                );

                if ($norm != 0)
                {
                    # also normalize the plane distance, critical for aabb
                    # not really normalization, just pretending to have been constructed from
                    # normalized vectors
                    $pd /= $norm;
                } else {
                    printf(
                        "Overlapping vertices in node: %s face: %u\n" .
                        "x: % .5g, y: % .5g, z: % .5g\n" .
                        "x: % .5g, y: % .5g, z: % .5g\n" .
                        "x: % .5g, y: % .5g, z: % .5g\n",
                        $model{'partnames'}[$i], $count,
                        $p1x, $p1y, $p1z,
                        $p2x, $p2y, $p2z,
                        $p3x, $p3y, $p3z
                    );
                }
                # store the normalized values;
                $_->[0] = $model{'nodes'}{$i}{'facenormals'}[$count][0];
                $_->[1] = $model{'nodes'}{$i}{'facenormals'}[$count][1];
                $_->[2] = $model{'nodes'}{$i}{'facenormals'}[$count][2];
                $_->[3] = $pd;
#                if($i == 87) { print LOG "Normals for Face $count: " . $Nx/$norm . " " . $Ny/$norm . " " . $Nz/$norm . "\n"; }

                $count++;
#                print "Count increasing\n";

                # print ("$i " . $_->[0] . " " . $_->[1] . " " . $_->[2] . " " . $_->[3] . "\n");

                # determine whether this node uses normal/bump mapping requiring tangent space calculations
                if ($model{'nodes'}{$i}{'bitmap'} =~ /null/i ||
                    !($model{'nodes'}{$i}{'mdxdatabitmap'} & MDX_TANGENT_SPACE)) {
                    # skip tangent/bitangent calculations for non-bump-mapped textures
                    next;
                }
                # compute face tangent and bitangent vectors for bump-mapped textures
                # based on (with key differences for what bioware wants) technique from:
                # http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-13-normal-mapping/
                my ($v0, $v1, $v2) = (
                    $model{'nodes'}{$i}{'verts'}[$_->[8]],
                    $model{'nodes'}{$i}{'verts'}[$_->[9]],
                    $model{'nodes'}{$i}{'verts'}[$_->[10]]
                );
                my ($uv0, $uv1, $uv2) = (
                    $model{'nodes'}{$i}{'tverts'}[$model{'nodes'}{$i}{'tverti'}{$_->[8]}],
                    $model{'nodes'}{$i}{'tverts'}[$model{'nodes'}{$i}{'tverti'}{$_->[9]}],
                    $model{'nodes'}{$i}{'tverts'}[$model{'nodes'}{$i}{'tverti'}{$_->[10]}]
                );
                my ($deltaPos1, $deltaPos2, $deltaUV1, $deltaUV2);
                $deltaPos1 = [ $v1->[0] - $v0->[0], $v1->[1] - $v0->[1], $v1->[2] - $v0->[2] ];
                $deltaPos2 = [ $v2->[0] - $v0->[0], $v2->[1] - $v0->[1], $v2->[2] - $v0->[2] ];
                $deltaUV1  = [ $uv1->[0] - $uv0->[0], $uv1->[1] - $uv0->[1] ];
                $deltaUV2  = [ $uv2->[0] - $uv0->[0], $uv2->[1] - $uv0->[1] ];
                # this is the texture normal's Z component, used to detect texture mirroring
                # it was originally a = uv0 - uv1, b = uv2 - uv1, N=cross(a,b),
                # but since we're talking about a 2d triangle, there's never any XY vector component,
                # so it reduces to just calculating the Z (or w) component of the cross product
                my $tNz = (
                    ($uv0->[0] - $uv1->[0]) * ($uv2->[1] - $uv1->[1]) -
                    ($uv0->[1] - $uv1->[1]) * ($uv2->[0] - $uv1->[0])
                );

                my $r = ($deltaUV1->[0] * $deltaUV2->[1] - $deltaUV1->[1] * $deltaUV2->[0]);
                if ($r == 0.000000) {
                    # prevent a divide-by-zero, this doesn't usually happen for actually-textured objects
                    printf("Overlapping texture vertices in node: %s\n" .
                           "x: % .7g, y: % .7g\nx: % .7g, y: % .7g\nx: % .7g, y: % .7g\n",
                           $model{'partnames'}[$i], @{$uv0}, @{$uv1}, @{$uv2});
                    # this is a weird magic factor determined algebraically from analyzing how p_g0t0.mdl copes
                    # with all the overlapping tex vertices
                    $r = 2406.6388;
                } else {
                    $r = 1.0 / $r;
                }
                # compute face tangent vector
                my $tangent = [
                    ($deltaPos1->[0] * $deltaUV2->[1] - $deltaPos2->[0] * $deltaUV1->[1]) * $r,
                    ($deltaPos1->[1] * $deltaUV2->[1] - $deltaPos2->[1] * $deltaUV1->[1]) * $r,
                    ($deltaPos1->[2] * $deltaUV2->[1] - $deltaPos2->[2] * $deltaUV1->[1]) * $r
                ];
                # compute normalizing factor for tangent vector
                my $bnormalizing_factor = sqrt(
                    ($tangent->[0] ** 2) +
                    ($tangent->[1] ** 2) +
                    ($tangent->[2] ** 2)
                );
                # normalize the face tangent vector by applying the computed factor
                if ($bnormalizing_factor) {
                    # divide each component by normalizing factor
                    $tangent = [
                        map { $_ / $bnormalizing_factor } @{$tangent}
                    ];
                }
                # fix 0-vectors arising from overlapping texture vertices
                if ($tangent->[0] == 0.0000 && $tangent->[1] == 0.0000 && $tangent->[2] == 0.0000) {
                    # it seems incredibly unlikely that these should both just be set to 1,0,0 unconditionally.
                    # my guess here is that there is some criteria for determining whether X,Y, or Z should be 1
                    $tangent = [ 1.0, 0.0, 0.0 ];
                }
                $model{'nodes'}{$i}{'facetangents'}[$count - 1] = $tangent;

                # compute face bitangent vector
                my $bitangent = [
                    ($deltaPos2->[0] * $deltaUV1->[0] - $deltaPos1->[0] * $deltaUV2->[0]) * $r,
                    ($deltaPos2->[1] * $deltaUV1->[0] - $deltaPos1->[1] * $deltaUV2->[0]) * $r,
                    ($deltaPos2->[2] * $deltaUV1->[0] - $deltaPos1->[2] * $deltaUV2->[0]) * $r
                ];
                # compute normalizing factor for bitangent vector
                my $bnormalizing_factor = sqrt(
                    ($bitangent->[0] ** 2) +
                    ($bitangent->[1] ** 2) +
                    ($bitangent->[2] ** 2)
                );
                # normalize the face bitangent vector by applying the computed factor
                if ($bnormalizing_factor) {
                    # divide each component by normalizing factor
                    $bitangent = [
                        map { $_ / $bnormalizing_factor } @{$bitangent}
                    ];
                }
                # fix 0-vectors arising from overlapping texture vertices
                if ($bitangent->[0] == 0.0000 && $bitangent->[1] == 0.0000 && $bitangent->[2] == 0.0000) {
                    # it seems incredibly unlikely that these should both just be set to 1,0,0 unconditionally.
                    # my guess here is that there is some criteria for determining whether X,Y, or Z should be 1
                    $bitangent = [ 1.0, 0.0, 0.0 ];
                }
                $model{'nodes'}{$i}{'facebitangents'}[$count - 1] = $bitangent;

                # fix tangent space handedness: make this true: dot(cross(n,t),b) < 0
                # the game seems to want TBN NOT to form a right-handed coordinate system
                # or, cross(n,t) must have a different orientation from vector b
                my $cross_nt = [
                    $model{'nodes'}{$i}{'facenormals'}[$count - 1][1] * $model{'nodes'}{$i}{'facetangents'}[$count - 1]->[2] -
                    $model{'nodes'}{$i}{'facenormals'}[$count - 1][2] * $model{'nodes'}{$i}{'facetangents'}[$count - 1]->[1],
                    $model{'nodes'}{$i}{'facenormals'}[$count - 1][2] * $model{'nodes'}{$i}{'facetangents'}[$count - 1]->[0] -
                    $model{'nodes'}{$i}{'facenormals'}[$count - 1][0] * $model{'nodes'}{$i}{'facetangents'}[$count - 1]->[2],
                    $model{'nodes'}{$i}{'facenormals'}[$count - 1][0] * $model{'nodes'}{$i}{'facetangents'}[$count - 1]->[1] -
                    $model{'nodes'}{$i}{'facenormals'}[$count - 1][1] * $model{'nodes'}{$i}{'facetangents'}[$count - 1]->[0]
                ];
                if (($cross_nt->[0] * $model{'nodes'}{$i}{'facebitangents'}[$count - 1]->[0] +
                     $cross_nt->[1] * $model{'nodes'}{$i}{'facebitangents'}[$count - 1]->[1] +
                     $cross_nt->[2] * $model{'nodes'}{$i}{'facebitangents'}[$count - 1]->[2]) > 0.0) {
                    $model{'nodes'}{$i}{'facetangents'}[$count - 1] = [
                        map { $_ * -1.0 } @{$model{'nodes'}{$i}{'facetangents'}[$count - 1]}
                    ];
                }
                # if texture is mirrored, we need to invert both tangent and bitangent now
                if ($tNz > 0.0) {
                    $model{'nodes'}{$i}{'facetangents'}[$count - 1] = [
                        map { $_ * -1.0 } @{$model{'nodes'}{$i}{'facetangents'}[$count - 1]}
                    ];
                    $model{'nodes'}{$i}{'facebitangents'}[$count - 1] = [
                        map { $_ * -1.0 } @{$model{'nodes'}{$i}{'facebitangents'}[$count - 1]}
                    ];
                }
                #XXX there is some condition where the tangent space vertex normals differ greatly from the usual vertex normals,
                # it seems to have something to do with the overlapping texture vertex situation, but i'm not sure how yet.
            }
        }
    }

    # Calculate vertex normals and tangent space basis
    # Loop through all of the model's nodes
    for (my $i = 0; $i < $nodenum; $i ++)
    {

        # these calculations are only for mesh nodes
        if (!($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH) ||
            ($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER)) {
            # skip non-mesh nodes
            # skip saber mesh nodes
            next;
        }

#        print $i . ' ' . scalar @{$model{'nodes'}{$i}{'Bfaces'}} . "\n";
#        print LOG "\n";

        # step through the vertices in this mesh
        foreach $work (keys @{$model{'nodes'}{$i}{'verts'}})
        {
            my $vert_key = sprintf(
                '%.4g,%.4g,%.4g',
                @{$model{'nodes'}{$i}{transform}{verts}->[$work]}
            );
            my $position_data = [ @{$face_by_pos->{$vert_key}} ];
            my $meshA = $i;
            my $faceA = -1;
            my $sgA   = -1;
            if (defined($model{'nodes'}{$i}{vertfaces}{$work})) {
                $faceA = (
                    map { @{$_->{faces}} }
                    grep { $_->{mesh} == $i && $_->{vertex} == $work }
                    @{$position_data}
                )[0];
            }
            if ($faceA == -1) {
                $model{'nodes'}{$i}{'vertexnormals'}{$work} = [ 1, 0, 0 ];
                next;
            }
            $sgA = $model{'nodes'}{$i}{'Bfaces'}[$faceA]->[11];
            $model{'nodes'}{$i}{'vertexnormals'}{$work} = [ 0.0, 0.0, 0.0 ];
            if ($model{'nodes'}{$i}{'mdxdatabitmap'} & MDX_TANGENT_SPACE) {
                $model{'nodes'}{$i}{'vertextangents'}[$work] = [ 0.0, 0.0, 0.0 ];
                $model{'nodes'}{$i}{'vertexbitangents'}[$work] = [ 0.0, 0.0, 0.0 ];
            }
            # set to true when vertex normal gets a non-zero value
            my $vertnorm_initialized = 0;
            for my $pos_data (@{$position_data}) {
                my $meshB = $pos_data->{mesh};
                for my $faceB (@{$pos_data->{faces}}) {
                    my $is_self = ($meshA == $meshB && $faceA == $faceB);
                    # don't let rendering geometry influence non-rendering, and vice versa
                    if ($model{'nodes'}{$meshA}{'render'} != $model{'nodes'}{$meshB}{'render'}) {
                        $printall and print "skip visibility mismatch\n";
                        next;
                    }
                    if (($model{'nodes'}{$meshA}{'nodetype'} & NODE_HAS_AABB) &&
                        $meshA != $meshB) {
                        # prevent cross-mesh vertex normal accumulation for AABB nodes
                        $printall and printf(
                            "skip non-AABB for vertex normals in AABB %s %s\n",
                            $model{partnames}[$meshA], $model{partnames}[$meshB]
                        );
                        next;
                    }
                    # don't let influence of geometry from different smooth groups accumulate into the vertex normal
                    # TODO resolve smooth group numbers vs. surface IDs...
                    if (!($model{'nodes'}{$meshB}{'Bfaces'}[$faceB]->[11] & $sgA) && !$is_self) {
                        $printall and printf("skip sg %u != %u\n", $model{'nodes'}{$meshB}{'Bfaces'}[$faceB]->[11], $sgA);
                        next;
                    }
                    if ($options->{use_crease_angle} && $vertnorm_initialized &&
                        #compute_vector_angle($model{'nodes'}{$meshA}{'facenormals'}[$faceA],
                        compute_vector_angle($model{'nodes'}{$i}{'vertexnormals'}{$work},
                                             $model{'nodes'}{$meshB}{'worldfacenormals'}[$faceB]) > $options->{crease_angle}) {
                        if ($model{'nodes'}{$meshA}{'render'}) {
                            # crease angle to use can vary per-model,
                            # when it is even desireable
                            $printall and printf(
                                "skipped %s accumulation \@%.4g,%.4g,%.4g with crease angle: % .7g\n",
                                $model{'partnames'}[$meshA], @{$model{'nodes'}{$i}{'verts'}[$work]},
                                compute_vector_angle($model{'nodes'}{$i}{'vertexnormals'}{$work},
                                                     $model{'nodes'}{$meshB}{'worldfacenormals'}[$faceB])
                            );
                            next;
                        }
                    }
                    my $area = $options->{weight_by_area} ? $faceareas{$meshB}{$faceB} : 1;
                    # initialize angle to 1 in case no vertices match somehow
                    my $angle = $options->{weight_by_angle} ? -1 : 1;

                    # store faceB vertices in listrefs $bv1-3
                    my ($bv1, $bv2, $bv3) = (
                        $model{'nodes'}{$meshB}{transform}{'verts'}[$model{'nodes'}{$meshB}{'Bfaces'}[$faceB]->[8]],
                        $model{'nodes'}{$meshB}{transform}{'verts'}[$model{'nodes'}{$meshB}{'Bfaces'}[$faceB]->[9]],
                        $model{'nodes'}{$meshB}{transform}{'verts'}[$model{'nodes'}{$meshB}{'Bfaces'}[$faceB]->[10]]
                    );

                    if ($options->{weight_by_angle} &&
                        vertex_equals($model{'nodes'}{$i}{transform}{'verts'}[$work], $bv1, 4))
                    {
                        $angle = compute_vertex_angle($bv1, $bv2, $bv3);
                        printf(
                          "mesh %s face %u vert %u (%.3f,%.3f,%.3f) angle %f\n",
                          $model{'partnames'}[$meshB], $faceB, $model{'nodes'}{$meshB}{'Bfaces'}[$faceB]->[8],
                          @{$bv1}, $angle
                        ) if $printall;
                    }
                    elsif ($options->{weight_by_angle} &&
                           vertex_equals($model{'nodes'}{$i}{transform}{'verts'}[$work], $bv2, 4))
                    {
                        $angle = compute_vertex_angle($bv2, $bv1, $bv3);
                        printf(
                          "mesh %s face %u vert %u (%.3f,%.3f,%.3f) angle %f\n",
                          $model{'partnames'}[$meshB], $faceB, $model{'nodes'}{$meshB}{'Bfaces'}[$faceB]->[9],
                          @{$bv2}, $angle
                        ) if $printall;
                    }
                    elsif ($options->{weight_by_angle} &&
                           vertex_equals($model{'nodes'}{$i}{transform}{'verts'}[$work], $bv3, 4))
                    {
                        $angle = compute_vertex_angle($bv3, $bv1, $bv2);
                        printf(
                          "mesh %s face %u vert %u (%.3f,%.3f,%.3f) angle %f\n",
                          $model{'partnames'}[$meshB], $faceB, $model{'nodes'}{$meshB}{'Bfaces'}[$faceB]->[10],
                          @{$bv3}, $angle
                        ) if $printall;
                    }
                    if ($options->{weight_by_angle} && $angle == -1) {
                        # if angle does not get computed, this is usually a miss
                        # due to vertex comparison precision. in a perfect world
                        # we would lower precision and retry.
                        printf "skip %u bad %u face: %u\n", $meshA, $meshB, $faceB;
                        next;
                    }
                    # about to populate the vertex normal (maybe initially)
                    $vertnorm_initialized = 1;
                    # apply angle & area weight to faceB surface normal and
                    # accumulate the x, y, and z components of the vertex normal vector
                    $model{'nodes'}{$i}{'vertexnormals'}{$work}->[0] += (
                        $model{'nodes'}{$meshB}{'worldfacenormals'}[$faceB]->[0] * $area * $angle
                        #$model{'nodes'}{$meshB}{'rawfacenormals'}[$faceB]->[0] * $area * $angle
                    );
                    $model{'nodes'}{$i}{'vertexnormals'}{$work}->[1] += (
                        $model{'nodes'}{$meshB}{'worldfacenormals'}[$faceB]->[1] * $area * $angle
                        #$model{'nodes'}{$meshB}{'rawfacenormals'}[$faceB]->[1] * $area * $angle
                    );
                    $model{'nodes'}{$i}{'vertexnormals'}{$work}->[2] += (
                        $model{'nodes'}{$meshB}{'worldfacenormals'}[$faceB]->[2] * $area * $angle
                        #$model{'nodes'}{$meshB}{'rawfacenormals'}[$faceB]->[2] * $area * $angle
                    );
                    # accumulate the x, y, and z components of the face tangent and bitangent vectors for tangent space
                    if (defined($model{'nodes'}{$meshB}{'facetangents'}[$faceB])) {
                        $model{'nodes'}{$i}{'vertextangents'}[$work]->[0] += (
                            $model{'nodes'}{$meshB}{'facetangents'}[$faceB]->[0] * $area * $angle
                        );
                        $model{'nodes'}{$i}{'vertextangents'}[$work]->[1] += (
                            $model{'nodes'}{$meshB}{'facetangents'}[$faceB]->[1] * $area * $angle
                        );
                        $model{'nodes'}{$i}{'vertextangents'}[$work]->[2] += (
                            $model{'nodes'}{$meshB}{'facetangents'}[$faceB]->[2] * $area * $angle
                        );
                        $model{'nodes'}{$i}{'vertexbitangents'}[$work]->[0] += (
                            $model{'nodes'}{$meshB}{'facebitangents'}[$faceB]->[0] * $area * $angle
                        );
                        $model{'nodes'}{$i}{'vertexbitangents'}[$work]->[1] += (
                            $model{'nodes'}{$meshB}{'facebitangents'}[$faceB]->[1] * $area * $angle
                        );
                        $model{'nodes'}{$i}{'vertexbitangents'}[$work]->[2] += (
                            $model{'nodes'}{$meshB}{'facebitangents'}[$faceB]->[2] * $area * $angle
                        );
                    }
                }
            }
            # vertex normals are now computed, normalize the vector and store
            $model{'nodes'}{$i}{'vertexnormals'}{$work} = normalize_vector(
                $model{'nodes'}{$i}{'vertexnormals'}{$work}
            );
            # convert normal vector from world space to object space,
            # if this node has a 'non-zero' world orientation
            if ($model{'nodes'}{$i}{transform}{orientation}[0] != 0.0 ||
                $model{'nodes'}{$i}{transform}{orientation}[1] != 0.0 ||
                $model{'nodes'}{$i}{transform}{orientation}[2] != 0.0) {
              $model{'nodes'}{$i}{'vertexnormals'}{$work} = &quaternion_apply(
                  [ map { -1.0 * $_ } @{$model{'nodes'}{$i}{transform}{orientation}}[0..2],
                    $model{'nodes'}{$i}{transform}{orientation}[3] ],
                  $model{'nodes'}{$i}{'vertexnormals'}{$work}
              );
            }
            if (defined($model{'nodes'}{$i}{'vertextangents'}) &&
                defined($model{'nodes'}{$i}{'vertextangents'}[$work])) {
                # construct the MDX-ready representation of the tangent space data
                $model{'nodes'}{$i}{'Btangentspace'}[$work] = [
                    @{normalize_vector($model{'nodes'}{$i}{'vertexbitangents'}[$work])},
                    @{normalize_vector($model{'nodes'}{$i}{'vertextangents'}[$work])},
                    @{$model{'nodes'}{$i}{'vertexnormals'}{$work}}
                ];
            }
        }
        if ($printall && defined($model{'nodes'}{$i}{'vertextangents'})) {
            foreach (keys @{$model{'nodes'}{$i}{'vertextangents'}}) {
                printf("$i %u (%.7f, %.7f, %.7f) (%.7f, %.7f, %.7f) (%.7f, %.7f, %.7f)\n",
                       $_,
                       @{$model{'nodes'}{$i}{'Btangentspace'}[$_]});
                       #@{$model{'nodes'}{$i}{'vertexbitangents'}[$_]},
                       #@{$model{'nodes'}{$i}{'vertextangents'}[$_]},
                       #@{$model{'nodes'}{$i}{'vertexnormals'}{$_}});
            }
        }
    }

    # Calculate adjacent faces using the face-by-position map
    # Loop through all of the model's nodes
    for (my $i = 0; $i < $nodenum; $i ++)
    {
        # these calculations are only for mesh nodes
        if (!($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH) ||
            ($model{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER)) {
            # skip non-mesh nodes
            # skip saber mesh nodes
            next;
        }
        my $results = {};
        my $consider_all = 1;
        # step through all faces for this node, store face index in $j
        for my $j (keys @{$model{'nodes'}{$i}{'Bfaces'}})
        {
            # get the position data for each of face $j's 3 vertex positions
            my $position_data = [
                $face_by_pos->{sprintf('%.4g,%.4g,%.4g', @{
                    $model{'nodes'}{$i}{transform}{verts}->[$model{'nodes'}{$i}{'Bfaces'}[$j][8]]
                })},
                $face_by_pos->{sprintf('%.4g,%.4g,%.4g', @{
                    $model{'nodes'}{$i}{transform}{verts}->[$model{'nodes'}{$i}{'Bfaces'}[$j][9]]
                })},
                $face_by_pos->{sprintf('%.4g,%.4g,%.4g', @{
                    $model{'nodes'}{$i}{transform}{verts}->[$model{'nodes'}{$i}{'Bfaces'}[$j][10]]
                })},
            ];
#printf(
#"(%.4g,%.4g,%.4g),(%.4g,%.4g,%.4g),(%.4g,%.4g,%.4g)\n",
#@{$model{'nodes'}{$i}{transform}{verts}->[$model{'nodes'}{$i}{'Bfaces'}[$j][8]]},
#@{$model{'nodes'}{$i}{transform}{verts}->[$model{'nodes'}{$i}{'Bfaces'}[$j][9]]},
#@{$model{'nodes'}{$i}{transform}{verts}->[$model{'nodes'}{$i}{'Bfaces'}[$j][10]]},
#);
#print Dumper($position_data);
            # place vertface maps for each of face $j's 3 vertices into $vfs listref
            my $vfs = [ [], [], [] ];
            for my $facevert (0..2) {
                for my $pos_data (@{$position_data->[$facevert]}) {
                    if ($pos_data->{mesh} == $i &&
                        $pos_data->{vertex} == $model{'nodes'}{$i}{'Bfaces'}[$j][8 + $facevert]) {
                        # the connected faces for this vert
                        #$vfs->[$facevert] = [ @{$vfs->[$facevert]}, @{$pos_data->{faces}} ];
                        push @{$vfs->[$facevert]}, @{$pos_data->{faces}};
                        last;
                    }
                }
                if ($consider_all) {
                    for my $pos_data (@{$position_data->[$facevert]}) {
                        if ($pos_data->{mesh} == $i &&
                            $pos_data->{vertex} != $model{'nodes'}{$i}{'Bfaces'}[$j][8 + $facevert]) {
                            # the connected faces for this vert
                            #$vfs->[$facevert] = [ @{$vfs->[$facevert]}, @{$pos_data->{faces}} ];
                            push @{$vfs->[$facevert]}, @{$pos_data->{faces}};
                        }
                    }
                }
            }
            # we know that vfs[0] has all faces adjacent to 1,
            # vfs[1] all adjacent to 2, vfs[2] all adjacent to 3
            # initialize matches hash with one hash per face vertex
            my $matches = {
                0 => { map { $_ => 1 } grep { $_ != $j } @{$vfs->[0]} },
                1 => { map { $_ => 1 } grep { $_ != $j } @{$vfs->[1]} },
                2 => { map { $_ => 1 } grep { $_ != $j } @{$vfs->[2]} }
            };
            # step through 0,1,2 for 3 vertices of face $j
            for my $l (0..2) {
                # step through all faces adjacent to vertex $l
                foreach(keys %{$matches->{$l}}) {
                    # testing for 2 vertex match (aka, an edge match)
                    # so use $l and $l + 1, unless we are on 2,
                    # when we use $l and $l - 2.
                    my $next = $l == 2 ? -2 : 1;
                    # if $l + $next entry is set, we have found an edge,
                    # and this is an adjacent face, record it in results
                    if ($matches->{$l + $next}{$_}) {
                        $results->{$j}[$l] = $_;
                    }
                }
                if ((defined($results->{$j}[$l]) &&
                     $results->{$j}[$l] != $model{'nodes'}{$i}{'Bfaces'}[$j][5 + $l]) ||
                    (!defined($results->{$j}[$l]) &&
                     $model{'nodes'}{$i}{'Bfaces'}[$j][5 + $l] != -1)) {
                    # this block was for testing against the old method's results
                    # testing showed that the new method works better, because
                    # it has a better understanding of overlapping geometry
                    # (the old method required exact matches, the new uses a set tolerance)
#printf( "mismatch %s $j $l\n", $model{'partnames'}[$i] );
#print Dumper($model{'nodes'}{$i}{'Bfaces'}[$j]);
#print Dumper($results->{$j});
#print Dumper($vfs);
#print Dumper($matches);
                }
                # record the adjacent face result in Bfaces entry
                if (defined($results->{$j}[$l])) {
                    $model{'nodes'}{$i}{'Bfaces'}[$j][5 + $l] = $results->{$j}[$l];
                }
            }
            delete $results->{$j};
        }
    }

#    close LOG;

  # post-process the geometry nodes
  postprocessnodes($model{'nodes'}{0}, \%model, 0);
  # post-process the animation nodes
  for (my $i = 0; $i < $model{'numanims'}; $i++) {
    # need to pass in model{anims}{i} instead of \%model in order to keep
    # the post processing happening on animation node entries instead of geometry
    # when it recurses
    postprocessnodes($model{'anims'}{$i}{'nodes'}{0}, $model{'anims'}{$i}, 1);
  }
  
  print (" nodenum: " . $nodenum . " true: " . $model{'nodes'}{'truenodenum'} . "\n") if $printall;
  $nodenum = $model{'nodes'}{'truenodenum'};
  #cook the bone weights and prepare the bone map
  for (my $i = 0; $i < $nodenum; $i++) {
    $work = 0;
    if ($model{'nodes'}{$i}{'nodetype'} == NODE_SKIN) {
      #fill the bone map with -1
      for (my $j = 0; $j < $nodenum; $j++) {
        $model{'nodes'}{$i}{'node2index'}[$j] = -1;
      }
      # loop through the bones+weights
      for (my $j = 0; $j < $model{'nodes'}{$i}{'weightsnum'}; $j++) {
        #print( " $#{$model{'nodes'}{$i}{'bones'}[$j]} \n");
        $temp1 = "";
        $temp2 = "";
        my $total = 0.0;
        my $extra = 0.0;
        map { $total += $_ } @{$model{'nodes'}{$i}{'weights'}[$j]};
        if (abs(1.0 - $total) > 0.0001) {
          $extra = (1.0 - $total) / scalar(@{$model{'nodes'}{$i}{'weights'}[$j]});
          printf(
            "Node: %s Vertex: %u has weights == %.4g but must be 1.0, ".
            "%.4g will be added to each weight to make the total == 1.0\n",
            $model{'partnames'}[$i], $j, $total, $extra
          );
        }
        for (my $k = 0; $k < 4; $k++) {
          if ($model{'nodes'}{$i}{'bones'}[$j][$k] ne "") {
            if ($model{'nodes'}{$i}{'node2index'}[$nodeindex{ lc($model{'nodes'}{$i}{'bones'}[$j][$k]) }] == -1) {
              $model{'nodes'}{$i}{'index2node'}[$work] = $nodeindex{ lc($model{'nodes'}{$i}{'bones'}[$j][$k]) };
              $model{'nodes'}{$i}{'node2index'}[$nodeindex{ lc($model{'nodes'}{$i}{'bones'}[$j][$k]) }] = $work++;
            }
            $model{'nodes'}{$i}{'Bbones'}[$j][$k] = $model{'nodes'}{$i}{'weights'}[$j][$k] + $extra;
            $model{'nodes'}{$i}{'Bbones'}[$j][$k+4] = $model{'nodes'}{$i}{'node2index'}[$nodeindex{ lc($model{'nodes'}{$i}{'bones'}[$j][$k]) }];
          } else {
            $model{'nodes'}{$i}{'Bbones'}[$j][$k] = 0;
            $model{'nodes'}{$i}{'Bbones'}[$j][$k+4] = -1;
          }   
        }
      }
    }
  }
  print("\nDone reading ascii model: $file\n");
  MDLOpsM::File::close($ASCIIMDL);
  return \%model;
}

##################################################
# Write out a binary model
# 
sub writebinarymdl {
  my ($model, $version, $options) = (@_);
  my ($buffer, $mdxsize, $totalbytes, $nodenum, $work, $nodestart, $animstart);
  my ($file, $filepath, $timestart, $valuestart, $count);
  my ($temp1, $temp2, $temp3, $temp4);

  if ($version ne 'k1' && $version ne 'k2') {
    return;
  }

  # set up option default values
  if (!defined($options)) {
    $options = {};
  }
  if (!defined($options->{headfix})) {
    $options->{headfix} = 0;
  }

  $file = $model->{'filename'};
  $filepath = $model->{'filepath+name'};

  $nodenum = $model->{'nodes'}{'truenodenum'};
  MDLOpsM::File::open(\*BMDLOUT, ">", "$filepath-$version-bin.mdl") or die "can't open MDL file $filepath-$version-bin.mdl\n";
  binmode(BMDLOUT);
  MDLOpsM::File::open(\*BMDXOUT, ">", "$filepath-$version-bin.mdx") or die "can't open MDX file $filepath-$version-bin.mdx\n";
  binmode(BMDXOUT);
 
  #write out MDX
  seek (BMDXOUT, 0, 0);
  for (my $i = 0; $i < $model->{'nodes'}{'truenodenum'}; $i++) {
    #print ("MDX: $i\n");
    if (($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH) &&
        $model->{'nodes'}{$i}{'mdxdatasize'} > 0 &&
        $model->{'nodes'}{$i}{'mdxdatabitmap'} != 0) {
      $model->{'nodes'}{$i}{'mdxstart'} = tell(BMDXOUT);
      #print($model->{'nodes'}{$i}{'vertnum'} . "|writing MDX data for node $i at starting location $model->{'nodes'}{$i}{'mdxstart'} datasize: $model->{'nodes'}{$i}{'mdxdatasize'}\n");
      for (my $j = 0; $j < $model->{'nodes'}{$i}{'vertnum'}; $j++) {
        if ($model->{'nodes'}{$i}{'mdxdatabitmap'} & MDX_VERTICES) {
          $buffer = pack("f",$model->{'nodes'}{$i}{'verts'}[$j][0]);
          $buffer .= pack("f",$model->{'nodes'}{$i}{'verts'}[$j][1]);
          $buffer .= pack("f",$model->{'nodes'}{$i}{'verts'}[$j][2]);
        }
        if ($model->{'nodes'}{$i}{'mdxdatabitmap'} & MDX_VERTEX_NORMALS) {
          $buffer .= pack("f",$model->{'nodes'}{$i}{'vertexnormals'}{$j}[0]);
          $buffer .= pack("f",$model->{'nodes'}{$i}{'vertexnormals'}{$j}[1]);
          $buffer .= pack("f",$model->{'nodes'}{$i}{'vertexnormals'}{$j}[2]);
        }
        # if this mesh has uv coordinates add them in
        if ($model->{'nodes'}{$i}{'mdxdatabitmap'} & MDX_TEX0_VERTICES) {
          $buffer .= pack("f",$model->{'nodes'}{$i}{'tverts'}[$model->{'nodes'}{$i}{'tverti'}{$j}][0]);
          $buffer .= pack("f",$model->{'nodes'}{$i}{'tverts'}[$model->{'nodes'}{$i}{'tverti'}{$j}][1]);
        }
        if ($model->{'nodes'}{$i}{'mdxdatabitmap'} & MDX_TEX1_VERTICES) {
          my $tv_ind = defined($model->{'nodes'}{$i}{'texindices1'})
                         ? $model->{'nodes'}{$i}{'texindices1'}{$j}
                         : $model->{'nodes'}{$i}{'tverti'}{$j};
          $buffer .= pack("f",$model->{'nodes'}{$i}{'tverts1'}[$tv_ind][0]);
          $buffer .= pack("f",$model->{'nodes'}{$i}{'tverts1'}[$tv_ind][1]);
        }
        if ($model->{'nodes'}{$i}{'mdxdatabitmap'} & MDX_TEX2_VERTICES) {
          my $tv_ind = defined($model->{'nodes'}{$i}{'texindices2'})
                         ? $model->{'nodes'}{$i}{'texindices2'}{$j}
                         : $model->{'nodes'}{$i}{'tverti'}{$j};
          $buffer .= pack("f",$model->{'nodes'}{$i}{'tverts2'}[$tv_ind][0]);
          $buffer .= pack("f",$model->{'nodes'}{$i}{'tverts2'}[$tv_ind][1]);
        }
        if ($model->{'nodes'}{$i}{'mdxdatabitmap'} & MDX_TEX3_VERTICES) {
          my $tv_ind = defined($model->{'nodes'}{$i}{'texindices3'})
                         ? $model->{'nodes'}{$i}{'texindices3'}{$j}
                         : $model->{'nodes'}{$i}{'tverti'}{$j};
          $buffer .= pack("f",$model->{'nodes'}{$i}{'tverts3'}[$tv_ind][0]);
          $buffer .= pack("f",$model->{'nodes'}{$i}{'tverts3'}[$tv_ind][1]);
        }
        if ($model->{'nodes'}{$i}{'mdxdatabitmap'} & MDX_VERTEX_COLORS) {
          $buffer .= pack('f*', @{$model->{'nodes'}{$i}{'colors'}[
            defined($model->{'nodes'}{$i}{'colorindices'})
              ? $model->{'nodes'}{$i}{'colorindices'}{$j} : $j
          ]});
        }
        # if this mesh has normal mapping, include the tangent space data
        if ($model->{'nodes'}{$i}{'mdxdatabitmap'} & MDX_TANGENT_SPACE) {
          $buffer .= pack('f[9]', @{$model->{'nodes'}{$i}{'Btangentspace'}[$j]});
        }
        # if this is a skin mesh node then add in the bone weights
        if ($model->{'nodes'}{$i}{'nodetype'} == NODE_SKIN) {
          $buffer .= pack("f*", @{$model->{'nodes'}{$i}{'Bbones'}[$j]} );
        }
        $mdxsize += length($buffer);
        print (BMDXOUT $buffer);
      }
      # add on the end padding
      # 3 1x10^7 floats followed by enough 0's to make one row
      my $terminator = ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_SKIN) ? 1000000 : 10000000;
      $buffer = pack(
        "f*", $terminator, $terminator, $terminator,
        (0) x ( # using repetition operator to get the correct # of 0's
          ($model->{'nodes'}{$i}{'mdxdatasize'} / 4) - # floats in a row
          3 - # subtract the 3 1x10^7s
          (($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_SKIN) ? 8 : 0) # subtract 8 skin floats
        )
      );
      # this is the old mdlops way based on implicit assumption of 24-byte rows
      #$buffer = pack("f*",10000000, 10000000, 10000000, 0, 0, 0, 0, 0);
      if ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_SKIN) {
        # more mysterious padding, this one for skin nodes only
        $buffer .= pack("f*", 1, 0, 0, 0, 0, 0, 0, 0);
      }
      # after padding to one row, we may need to pad further to maintain 16-byte alignment,
      # this is why MDX starting positions always end in 0 in vanilla models
      my $alignment_padding = (
        (($model->{'nodes'}{$i}{'mdxdatasize'} % 16) + ($mdxsize % 16)) % 16
      );
      if (length($alignment_padding)) {
        # the interior mod operation tells us how many bytes into a 16-byte row we are in
        # subtracting from 16 gives us the number of bytes we need to add,
        # divide by 4 to get the number of 4-byte floats we need
        $buffer .= pack(
          'f*', (0) x ($alignment_padding / 4)
        );
      }
      $mdxsize += length($buffer);
      print (BMDXOUT $buffer);
    }
  }
  MDLOpsM::File::close(*BMDXOUT);
  #build the part names array
  #for (my $i = 0; $i < $nodenum; $i++) {
  # ignore nodenum here because we may have names without nodes
  for my $i (keys @{$model->{partnames}}) {
    $model->{'names'}{'raw'} .= pack("Z*", $model->{'partnames'}[$i]);
  }  

  #write out binary MDL
  #write out the file header
  seek (BMDLOUT, 0, 0);
  $buffer = pack("LLL", 0, 0, $mdxsize);
  $totalbytes += length($buffer);
  print (BMDLOUT $buffer);

  #write out the geometry header
  # seek (BMDLOUT, 12, 0);
  if($version eq 'k1') {
    $buffer =  pack("LLZ[32]", 4273776, 4216096, $model->{'name'});  # for kotor 1
  } else {
    $buffer =  pack("LLZ[32]", 4285200, 4216320, $model->{'name'});  # for kotor 2
  }
  $totalbytes += length($buffer);
  print (BMDLOUT $buffer);
  # write out placeholder for root node start location
  $model->{'rootnode'}{'start'} = tell(BMDLOUT);
  $buffer = pack("L", 0);
  $totalbytes += length($buffer);
  print (BMDLOUT $buffer);
  $buffer = pack("L", defined($model->{totalnumnodes}) ? $model->{totalnumnodes} : $nodenum);
  $buffer .= pack("L[7]C[4]", 0,0,0,0,0,0,0,2,49,150,189);
  $totalbytes += length($buffer);
  print (BMDLOUT $buffer);
  
  #write out the model header
  # seek (BMDLOUT, 92, 0);
  $buffer =  pack("C[4]L", $classification{$model->{'classification'}},
    # this is always 4 for placeables ...
    # it is sometimes 2 for characters, but no idea why yet
    # it is 0 for all other classifications of models
    defined($model->{classification_unk1}) ? $model->{classification_unk1} : (
      $classification{$model->{'classification'}} == $classification{Placeable} ? 4 : 0
    ),
    0,
    # actually more like affectedByFog, so invert the value
    $model->{'ignorefog'} ? 0 : 1,
    0
  );
  $totalbytes += length($buffer);
  print (BMDLOUT $buffer);
  $model->{'animroot'}{'start'} = tell(BMDLOUT);
  $buffer =  pack("L*", 0, $model->{'numanims'}, $model->{'numanims'}, 0);
  $buffer .= pack("f*", $model->{'bmin'}[0], $model->{'bmin'}[1], $model->{'bmin'}[2]);
  $buffer .= pack("f*", $model->{'bmax'}[0], $model->{'bmax'}[1], $model->{'bmax'}[2]);
  if ( $model->{'supermodel'} eq "mdlops" ) {
    $buffer .= pack("ffZ[32]", $model->{'radius'}, $model->{'animationscale'}, "NULL");
  } else {
    $buffer .= pack("ffZ[32]", $model->{'radius'}, $model->{'animationscale'}, $model->{'supermodel'});
  }
  $totalbytes += length($buffer);
  print (BMDLOUT $buffer);

  #write out the name array header
  # seek (BMDLOUT, 180, 0);
  $model->{'nameheader'}{'start'} = tell(BMDLOUT);
  $buffer =  pack("LLLL", 0, 0, $mdxsize, 0);
  #$buffer .= pack("LLL", 80+88+28, $nodenum, $nodenum);
  $buffer .= pack("LLL", 80+88+28, scalar(@{$model->{'partnames'}}), scalar(@{$model->{'partnames'}}));
  $totalbytes += length($buffer);
  print (BMDLOUT $buffer);
  #write out the name indexes
  #$buffer = pack("L", 80+88+28+(4*$nodenum));
  $buffer = pack("L", 80+88+28+(4*scalar(@{$model->{'partnames'}})));
  $work = 0;
  for (my $i = 1; $i < scalar(@{$model->{'partnames'}}); $i++) {
  #for (my $i = 1; $i < $nodenum; $i++) {
  #foreach (@{$model->{'partnames'}}) {
    $work += length( $model->{'partnames'}[$i-1] )+1;
    #$work += length($_)+1;
    #$work += length($partname[$i-1])+1;
    $buffer .= pack("L", 80+88+28+(4*scalar(@{$model->{'partnames'}}))+$work);
  }
  $totalbytes += length($buffer);
  print (BMDLOUT $buffer);
  #write out the part names
  $totalbytes += length($model->{'names'}{'raw'});
  print (BMDLOUT $model->{'names'}{'raw'});

  $animstart = tell(BMDLOUT);

  if ($model->{'numanims'} > 0) {
    # animations
    # write out placeholders for the animation indexes
    $buffer = "l" x $model->{'numanims'};
    $buffer = pack($buffer);
    $totalbytes += length($buffer);
    print (BMDLOUT $buffer);  
  
    # write out the actual animations
    for (my $i = 0; $i < $model->{'numanims'}; $i++) {
      seek(BMDLOUT, $totalbytes, 0);
      $model->{'anims'}{$i}{'start'} = tell(BMDLOUT);
      #write out the animation geometry header
      if($version eq 'k1') {
        $buffer =  pack("LLZ[32]", 4273392, 4451552, $model->{'anims'}{$i}{'name'});  # for kotor 1
      } else {
        $buffer =  pack("LLZ[32]", 4284816, 4522928, $model->{'anims'}{$i}{'name'});  # for kotor 2
      }
      $totalbytes += length($buffer);
      print (BMDLOUT $buffer);    
      # write out placeholder for anim node start location
      $model->{'anims'}{$i}{'nodes'}{'startloc'} = tell(BMDLOUT);
      $buffer = pack("L", 0);
      $totalbytes += length($buffer);
      print (BMDLOUT $buffer);
#      $buffer = pack("L", $model->{'anims'}{$i}{'nodes'}{'numnodes'});
      $buffer = pack("L", $nodenum);
      $buffer .= pack("L[8]", 0,0,0,0,0,0,0,5);
      $totalbytes += length($buffer);
      print (BMDLOUT $buffer);

      # write out the animation header
      $buffer  = pack("f", $model->{'anims'}{$i}{'length'} );
      $buffer .= pack("f", $model->{'anims'}{$i}{'transtime'} );
      $buffer .= pack("Z[32]", $model->{'anims'}{$i}{'animroot'} );
      $totalbytes += length($buffer);
      print (BMDLOUT $buffer);
      $model->{'anims'}{$i}{'eventsloc'} = tell(BMDLOUT);
      $buffer  = pack("LLLL", 0, $model->{'anims'}{$i}{'numevents'}, $model->{'anims'}{$i}{'numevents'}, 0);
      $totalbytes += length($buffer);
      print (BMDLOUT $buffer);    

      # write out the animation events (ifany)
      if ( $model->{'anims'}{$i}{'numevents'} > 0 ) {
        $buffer = "";
        $model->{'anims'}{$i}{'eventsstart'} = tell(BMDLOUT);
        foreach ( 0..($model->{'anims'}{$i}{'numevents'} - 1) ) {
          $buffer .= pack("fZ[32]", $model->{'anims'}{$i}{'eventtimes'}[$_], $model->{'anims'}{$i}{'eventnames'}[$_]);
        }
        $totalbytes += length($buffer);
        print (BMDLOUT $buffer);
      }
      $model->{'anims'}{$i}{'nodes'}{'start'} = tell(BMDLOUT);
      # fill in some blanks
      # the start of this animations nodes
      seek(BMDLOUT, $model->{'anims'}{$i}{'nodes'}{'startloc'}, 0);
      print (BMDLOUT pack("L", ($model->{'anims'}{$i}{'nodes'}{'start'} - 12) ) );
      if ($model->{'anims'}{$i}{'numevents'} > 0) {
        # the start of this animations events
         seek(BMDLOUT, $model->{'anims'}{$i}{'eventsloc'}, 0);
        print(BMDLOUT pack("L", ($model->{'anims'}{$i}{'eventsstart'} - 12) ) );
      }
    
      # write out animation nodes recursively
      $totalbytes = writebinarynode($model, $model->{'anims'}{$i}{'nodelist'}->[0], $totalbytes, $version, $i);

    } # for (my $i = 0; $i < $model->{'numanims'}; $i++) {

    # fill in the animation indexes blanks
    $buffer = "";
    for (my $i = 0; $i < $model->{'numanims'}; $i++) {
      $buffer .= pack("L", ($model->{'anims'}{$i}{'start'} - 12) );
    }
    if ($animstart < 20) {die;}
    seek(BMDLOUT, $animstart, 0);
    print(BMDLOUT $buffer);
    # fill in the animation start location
    if ($model->{'animroot'}{'start'} < 20) {die;}
    seek(BMDLOUT, $model->{'animroot'}{'start'}, 0);
    print(BMDLOUT pack("L", ($animstart - 12) ));
    
  } # if ($model->{'numanims'} > 0) {
  
  #$nodestart = tell(BMDLOUT);
  $nodestart = $totalbytes;
  my $nh_nodestart = $nodestart;
  
  # write out the nodes
    
  # now recursive because doing side-by-side comparisons of binary mdls was a real PITA before
  $totalbytes = writebinarynode($model, 0, $totalbytes, $version, "geometry");

  # VarsityPuppet's headfixer method:
  if ($options->{headfix} ||
      (defined($model->{headlink}) && $model->{headlink})) {
      # head models want the root node pointer in the names header to point at neck_g,
      # not the actual root node, so adjust the nh_nodestart value here w/
      # the location of neck_g
      for my $id (keys @{$model->{partnames}}) {
          if ($model->{partnames}[$id] eq 'neck_g') {
              $nh_nodestart = $model->{nodes}{$id}{'header'}{'start'};
              last;
          }
      }
  }

  #fill in some blanks
  #the size of the mdl (minus the file header)
  seek(BMDLOUT, 4, 0);
  print(BMDLOUT pack("L", $totalbytes - 12));
  # the start of the geomtrey nodes
  if ($model->{'rootnode'}{'start'} < 20) {die;}
  seek(BMDLOUT, $model->{'rootnode'}{'start'}, 0);
  print(BMDLOUT pack("L", ($nodestart - 12) ));
  # the start of the animations
  if ($model->{'animroot'}{'start'} < 20) {die;}
  seek(BMDLOUT, $model->{'animroot'}{'start'}, 0);
  print(BMDLOUT pack("L", $animstart - 12));  
  # fill in the node start location in the names header
  seek(BMDLOUT, $model->{'nameheader'}{'start'}, 0);
  print(BMDLOUT pack("L", ($nh_nodestart - 12) ));

  print("done with: $filepath\n");

  MDLOpsM::File::close(*BMDLOUT);
}

#####################################################################
# called only by readasciimdl
# a recursive sub to post-process mesh information in nodes
# code shamelessly cribbed from Torlack's C++ de/compiler
sub postprocessnodes {
  my ($node, $model, $anim) = (@_);
    
  if ($node->{'nodetype'} & NODE_HAS_MESH) {
    # zomg lots to do
    
    if ($node->{'nodetype'} & NODE_HAS_SKIN) {
    
      if (!$anim) {
        # QBones and TBones for model geometry only
        if (! exists($node->{'TBones'}) ) {
          # QBones: will store the orientations (direction) from every other node to this node
          # QBones: will store the positions (length) from every other node to this node
          $node->{'TBones'} = [];
          $node->{'QBones'} = [];

          # Start by getting the distance/length from this node to the root node.
          # Get current position/orientation, then reverse it.
          my (@position, @orientation, @parentposition, @parentorientation, $parent);
          getreversedpositionorientation(\@position, \@orientation, $node);

          # Combine with reversed parent orientations / positions, right up to the root
          $parent = $node;
          while ($parent->{'parentnodenum'} != -1) {
            $parent = $model->{'nodes'}{$parent->{'parentnodenum'}};
            getreversedpositionorientation(\@parentposition, \@parentorientation, $parent); # The rotation's done in here
            addvectors(\@position, \@parentposition, \@position);
            multiplyquaternions(\@orientation, \@parentorientation, \@orientation);
          }

          # okay, now we build the tbone and qbone arrays
          my $count = buildtqbonearrays($model->{'nodes'}{0}, $model, \@position, \@orientation, $node->{'TBones'}, $node->{'QBones'}, 0);

          # You think you're done.  But no, now every element needs to get reversed, and rotated.
          # I believe this changes from (distance/length from this node to other node) to
          # (distance/length from other node to this node).  But I'm too lazy to work out the math to see if that's correct.
          # Also, we will now adjust our orientation quaternions to be in the w,x,y,z format
          # The TBone value for node[nodenum] <=> node[nodenum] should be 0,0,0.
          # We enforce this before inverting, adjusting all other TBones by same
          my $base = $node->{TBones}[$node->{nodenum}];
          for (my $i = 0; $i < $count; $i++) {
            $node->{'QBones'}[$i][3] = - $node->{'QBones'}[$i][3];
            
            # apply base correction to TBone
            $node->{'TBones'}[$i] = [
              map { $node->{'TBones'}[$i][$_] - $base->[$_] } (0..2)
            ];
            # invert TBone
            $node->{'TBones'}[$i][0] = - $node->{'TBones'}[$i][0];
            $node->{'TBones'}[$i][1] = - $node->{'TBones'}[$i][1];
            $node->{'TBones'}[$i][2] = - $node->{'TBones'}[$i][2];

            rotatevector($node->{'TBones'}[$i], @{$node->{'QBones'}[$i]});
            my $temp = $node->{'QBones'}[$i][3];
            $node->{'QBones'}[$i][3] = $node->{'QBones'}[$i][2];
            $node->{'QBones'}[$i][2] = $node->{'QBones'}[$i][1];
            $node->{'QBones'}[$i][1] = $node->{'QBones'}[$i][0];
            $node->{'QBones'}[$i][0] = $temp;
          }

          # apparently now our T and Q bones are good to go.  yay.
          # now prepare 'array8' w/ 0's (runtime array)
          $node->{array8} = [ ([0, 0]) x $count ];
        }
      }
    }
  }
  # DISABLED (i thought this might be needed for sabers, but it wasn't, it will work if used)
  # for orientation keyed controllers in animation,
  # compress and encode quaternions as 3 10-bit floats
  # into a single 32-bit float
  if ($model->{'compress_quaternions'} && $anim &&
      defined($node->{'Bcontrollers'}{20}) &&
      scalar(@{$node->{'Bcontrollers'}{20}{'values'}[0]}) == 4) {
      # encode compressed quaternions
      # decompress algorithm:
      #   leave first value alone completely
      #   generate 4 values from 2nd value
      #   1 = q.x = 1 - ((v1 & 7ff) / 1023)
      #   2 = q.y = 1 - ((v1 >> 11 & 7ff) / 1023)
      #   3 = q.z = 1 - ((v1 >> 22) / 511)
      #   0.5, 0.6, 0.7
      #   0x3f000000, 0x3f19999a, 0x3f333333
      #   1 - 0.7 = (v1 >> 22) / 511
      #   (1 - 0.7) * 511 = v1 >> 22
      # so, to generate, take v3 * 511
      #   y = 1 - x
      #   (1 - v3) * 511 << 11
      #   (1 - v2) * 1023 << 11
      #   (1 - v1) * 1023
      #
      # this loop is going to take each unit quaternion and compress it into
      # a single floating point number. so that is 4 floats down to 1.
      # how does it work? i have *sort of* a clue about that?
      # this guy def does: http://physicsforgames.blogspot.com/2010/03/quaternion-tricks.html
      # basically one of the nums, w, is deriveable from the other 3, so it goes away
      # the trick for x,y,z relies on the fact that they are all in the range of -1,1
      foreach (@{$node->{'Bcontrollers'}{20}{'values'}}) {
          # it seems like we already have unit quaternions,
          # so no normalization necessary
          #my $f = ($_->[0] ** 2) + ($_->[1] ** 2) + ($_->[2] ** 2);
          #print Dumper($_);
          #print "FACTOR: $f\n";
          #if ($f > 0) {
          #    $_ = [ map {
          #      $_ * $f;
          #    } @{$_} ];
          #}
          # odyssey engine wants positive scalar component
          if ($_->[3] < 0.0) {
            # invert scalar and vector components
            $_ = [
              map { -1.0 * $_ } @{$_}
            ];
          }

          my ($qx, $qy, $qz) = @{$_}[0..2];
          my ($cx, $cy, $cz);
          $cz = int(((1.0 + $qz) * 1022.0) * 0.5);
          $cy = int(((1.0 + $qy) * 2046.0) * 0.5);
          $cx = int(((1.0 + $qx) * 2046.0) * 0.5);
          $_->[0] = $cx | ($cy << 11) | ($cz << 22);

          # remove elements 2,3,4 and reduce the total quantity of controller data on the node
          delete $_->[1];
          delete $_->[2];
          delete $_->[3];
          $node->{'controllerdatanum'} -= 3;

          #print Dumper($_);
          #my $temp = $_->[0];
          #print Dumper((
          #  (1.0 - (($temp & 0x7ff) / 1023.0)),
          #  (1.0 - ((($temp >> 11) & 0x7ff) / 1023.0)),
          #  (1.0 - ((($temp >> 22) & 0x7ff) / 511.0))
          #));
      }
  }

  # recursify!
  foreach my $child ( 1..$node->{'childcount'} ) {
    postprocessnodes($model->{'nodes'}{$node->{'children'}[($child - 1)]}, $model, $anim);
  }
}

###########################################################
# Used by postprocessnodes.  Recursive.
# Initialize tbone and qbone arrays.
# 
sub buildtqbonearrays {
  my ($node, $model, $position, $orientation, $tbones, $qbones, $i) = (@_);
  
  my (@currentposition, @currentorientation);
  # get position and orientation
  getpositionorientation(\@currentposition, \@currentorientation, $node);
    
  # rotate position and add it, then store
  rotatevector(\@currentposition, @{$orientation});
  addvectors($position, \@currentposition, $position);
  $tbones->[$i][0] = $position->[0];
  $tbones->[$i][1] = $position->[1];
  $tbones->[$i][2] = $position->[2];
  
  # combine orientations and store
  multiplyquaternions($orientation, \@currentorientation, $orientation);
  $qbones->[$i][0] = $orientation->[0];
  $qbones->[$i][1] = $orientation->[1];
  $qbones->[$i][2] = $orientation->[2];
  $qbones->[$i][3] = $orientation->[3];
  
  $i++;
  
  # recurse on children
  my (@newposition, @neworientation);
  foreach my $child ( 1..$node->{'childcount'} ) {
    @newposition = @$position;
    @neworientation = @$orientation;
    $i = buildtqbonearrays($model->{'nodes'}{$node->{'children'}[($child - 1)]}, $model, \@newposition, \@neworientation, $tbones, $qbones, $i);
  }
  
  return $i;
}

###########################################################
# Get the position and orientation of the given node
# 
sub getpositionorientation {
  my ($position, $orientation, $node) = (@_);

  if (exists($node->{'Acontrollers'}{8})) { #pos
    $position->[0] = $node->{'Bcontrollers'}{8}{'values'}[0][0];
    $position->[1] = $node->{'Bcontrollers'}{8}{'values'}[0][1];
    $position->[2] = $node->{'Bcontrollers'}{8}{'values'}[0][2];
  } else {
    @{$position} = (0.0, 0.0, 0.0);
  }
  if (exists($node->{'Acontrollers'}{20})) { #orient. x, y, z, w
    $orientation->[0] = $node->{'Bcontrollers'}{20}{'values'}[0][0];
    $orientation->[1] = $node->{'Bcontrollers'}{20}{'values'}[0][1];
    $orientation->[2] = $node->{'Bcontrollers'}{20}{'values'}[0][2];
    $orientation->[3] = $node->{'Bcontrollers'}{20}{'values'}[0][3]; 
  } else {
    @{$orientation} = (0.0, 0.0, 0.0, 1.0);
  }
}

###########################################################
# Get the flipped position and orientation of the given node.
# 
sub getreversedpositionorientation {
# get and flip position and orientation
  my ($position, $orientation, $node) = (@_);
  getpositionorientation($position, $orientation, $node);
  @{$position} = ( - $position->[0],
                   - $position->[1],
                   - $position->[2]);
  $orientation->[3] = - $orientation->[3];
  rotatevector($position, @{$orientation});
}

###########################################################
# Rotate vector v about quaternion q
# All quaternions here are x,y,z,w.
# 
sub rotatevector {

  my ($v, @q) = (@_);
             # v: 0 x, 1 y, 2 z
  my @qtemp; # 0 x, 1 y, 2 z, 3 w
  
  if ($v->[0] == 0 && $v->[1] == 0 && $v->[2] == 0) {
    #null vector
    return;
  }

# Here's how it looks by using straight multiplications
#  my (@vm, @qm, @qv, @qbar, @qout);
#  @vm = ($v->[0], $v->[1], $v->[2], 0);
#  @qv = [];
#  
#  multiplyquaternions(\@q, \@vm, \@qv);
# 
#  @qbar = (-$q[0], -$q[1], -$q[2], $q[3]);
#  
#  multiplyquaternions(\@qv, \@qbar, \@qout);
#
#  $v->[0] = $qout[0];
#  $v->[1] = $qout[1];
#  $v->[2] = $qout[2];

# But I went and worked it out.  Matrix algebra, what fun.
  my ($x, $y, $z);
  
  $x =  $v->[0] * ($q[3] * $q[3] + $q[0] * $q[0] - $q[1] * $q[1] - $q[2] * $q[2]) +
        $v->[1] * 2 * ($q[0] * $q[1] - $q[3] * $q[2]) +
        $v->[2] * 2 * ($q[1] * $q[3] + $q[0] * $q[2]);
        
  $y =  $v->[0] * 2 * ($q[0] * $q[1] + $q[3] * $q[2]) +
        $v->[1] * ($q[3] * $q[3] - $q[0] * $q[0] + $q[1] * $q[1] - $q[2] * $q[2]) +
        $v->[2] * 2 * ( - $q[3] * $q[0] + $q[1] * $q[2]);
  
  $z =  $v->[0] * 2 * ( - $q[3] * $q[1] + $q[0] * $q[2]) +
        $v->[1] * 2 * ($q[3] * $q[0] + $q[1] * $q[2]) +
        $v->[2] * ($q[3] * $q[3] - $q[0] * $q[0] - $q[1] * $q[1] + $q[2] * $q[2]);
  
  $v->[0] = $x;
  $v->[1] = $y;
  $v->[2] = $z;

}

###########################################################
# Add vectors v1 and v2 and put result in v3.
# 3-vectors only.  Pass in as refs.
# 
sub addvectors {
  my ($v1, $v2, $v3) = (@_);
  $v3->[0] = $v1->[0] + $v2->[0];
  $v3->[1] = $v1->[1] + $v2->[1];
  $v3->[2] = $v1->[2] + $v2->[2];
}

###########################################################
# Multiply q1 and q2 and put the result in q3.
# All quaternions of the form (x, y, z, w). Pass as refs.
sub multiplyquaternions {
  my ($q1, $q2, $q3) = (@_);
  my @qtemp;

  $qtemp[0] =   $q1->[3] * $q2->[0] - $q1->[2] * $q2->[1] + $q1->[1] * $q2->[2] + $q1->[0] * $q2->[3];
  $qtemp[1] =   $q1->[2] * $q2->[0] + $q1->[3] * $q2->[1] - $q1->[0] * $q2->[2] + $q1->[1] * $q2->[3];
  $qtemp[2] = - $q1->[1] * $q2->[0] + $q1->[0] * $q2->[1] + $q1->[3] * $q2->[2] + $q1->[2] * $q2->[3];
  $qtemp[3] = - $q1->[0] * $q2->[0] - $q1->[1] * $q2->[1] - $q1->[2] * $q2->[2] + $q1->[3] * $q2->[3];
  
  @{$q3} = @qtemp;
}

###########################################################
# Multiply q1 and q2 and return the result.
# All quaternions of the form (x, y, z, w). Pass as refs.
sub quaternion_multiply {
  my ($quat1, $quat2) = @_;
  my @q1 = @{$quat1};
  my @q2 = @{$quat2};
  # if either is only 3 coordinates, assume this is a point that we are rotating,
  # which is done by making it into a w = 0 quaternion
  if (scalar(@q1) == 3) {
    $q1[3] = 0.0;
  }
  if (scalar(@q2) == 3) {
    $q2[3] = 0.0;
  }
  return [
      $q1[3] * $q2[0] - $q1[2] * $q2[1] + $q1[1] * $q2[2] + $q1[0] * $q2[3],
      $q1[2] * $q2[0] + $q1[3] * $q2[1] - $q1[0] * $q2[2] + $q1[1] * $q2[3],
    - $q1[1] * $q2[0] + $q1[0] * $q2[1] + $q1[3] * $q2[2] + $q1[2] * $q2[3],
    - $q1[0] * $q2[0] - $q1[1] * $q2[1] - $q1[2] * $q2[2] + $q1[3] * $q2[3]
  ];
}

###########################################################
# Apply quaternion rotation to vector/point position
# This is an application of the 'sandwich product' method of rotating
# vectors using quaternions: v' = q * v * q^-1
# The vector is made into a quaternion by adding a 0 scalar (w) value
sub quaternion_apply {
  my ($quat, $vertex) = @_;
  return quaternion_multiply(
    quaternion_multiply($quat, [ @{$vertex}, 0.0 ]),
    [ -1.0 * $quat->[0],
      -1.0 * $quat->[1],
      -1.0 * $quat->[2],
      $quat->[3] ]
  );
}

#####################################################################
sub writebinarynode
{
    my ($ref, $i, $totalbytes, $version, $type) = (@_);
    my ($buffer, $count, $work, $timestart, $valuestart, $model);
    my ($temp1, $temp2, $temp3, $temp4, $ga, $controller);
    my $nodenum = $ref->{'nodes'}{'truenodenum'};
    my $nodestart = $totalbytes;

    if ($type eq "geometry")
    {
        $model = $ref;
        $ga = "geo";
    }
    else
    {
        #$model{'anims'}{$animnum}{'nodes'}{$nodenum}
        $model = $ref->{'anims'}{$type};
        $ga = "ani";
    }
  
    #print "writing node $i type $type \n";
    seek (BMDLOUT, $nodestart, 0);

    #write out the node header
    $model->{'nodes'}{$i}{'header'}{'start'} = tell(BMDLOUT);
    if ( defined( $ref->{'nodes'}{$i}{'supernode'} ) )
    {
        $work = $ref->{'nodes'}{$i}{'supernode'};
    }
    else
    {
        $work = $i;
    }
    $buffer = pack("SSSS", $model->{'nodes'}{$i}{'nodetype'}, $work, $i, 0);

    if ( $ga eq "ani" )
    {
        $buffer .= pack("L", ($model->{'start'} - 12) );
    }
    else
    {
        $buffer .= pack("L", 0);
    }
    
    if ($model->{'nodes'}{$i}{'parentnodenum'} != -1)
    {
        $buffer.= pack("L", $model->{'nodes'}{ $model->{'nodes'}{$i}{'parentnodenum'} }{'header'}{'start'} - 12);
    }
    else
    {
        $buffer.= pack("L", 0);
    }

    if ( defined( $ref->{'nodes'}{$i}{'Bcontrollers'}{8} ) && $ga eq "geo")
    {
        $buffer .= pack("f[3]", @{$ref->{'nodes'}{$i}{'Bcontrollers'}{8}{'values'}[0]});
    }
    else
    {
        $buffer .= pack("f[3]",  0, 0, 0);
    }

    if ( defined($ref->{'nodes'}{$i}{'Bcontrollers'}{20}) && $ga eq "geo")
    {
        $temp1 = $ref->{'nodes'}{$i}{'Bcontrollers'}{20}{'values'}[0][3]; # w
        $temp2 = $ref->{'nodes'}{$i}{'Bcontrollers'}{20}{'values'}[0][0]; # x
        $temp3 = $ref->{'nodes'}{$i}{'Bcontrollers'}{20}{'values'}[0][1]; # y
        $temp4 = $ref->{'nodes'}{$i}{'Bcontrollers'}{20}{'values'}[0][2]; # z
        $buffer .= pack("f[4]", $temp1, $temp2, $temp3, $temp4);
    }
    else
    {
        $buffer .= pack("f[4]", 1, 0, 0, 0);
    }
    $totalbytes += length($buffer);
    print(BMDLOUT $buffer);

    #prepare the child array pointer
    $model->{'nodes'}{$i}{'childarraypointer'} = tell(BMDLOUT);
    $buffer = pack("LLL", 0, $model->{'nodes'}{$i}{'childcount'}, $model->{'nodes'}{$i}{'childcount'});
    $totalbytes += length($buffer);
    print(BMDLOUT $buffer);

    #prepare the controller array pointer and controller data array pointer
    if ($model->{'nodes'}{$i}{'controllernum'} != 0 || $model->{'nodes'}{$i}{'controllerdatanum'} != 0)
    {
        # we have controllers, so write the place holder data
        $model->{'nodes'}{$i}{'controllerpointer'} = tell(BMDLOUT);
        $buffer = pack("LLL", 0, $model->{'nodes'}{$i}{'controllernum'}, $model->{'nodes'}{$i}{'controllernum'});
        $totalbytes += length($buffer);
        print(BMDLOUT $buffer);

        $model->{'nodes'}{$i}{'controllerdatapointer'} = tell(BMDLOUT);
        $buffer = pack("LLL", 0, $model->{'nodes'}{$i}{'controllerdatanum'}, $model->{'nodes'}{$i}{'controllerdatanum'});
        $totalbytes += length($buffer);
        print(BMDLOUT $buffer);
    }
    else
    {
        # we have no controllers, so fill with zeroes
        $buffer = pack("LLL", 0, 0, 0);
        $buffer .= pack("LLL", 0, 0, 0);
        $totalbytes += length($buffer);
        print (BMDLOUT $buffer);
    }  

    #write out the light sub header and data (if any)
    if ($model->{'nodes'}{$i}{'nodetype'} == 3)
    {
        #$buffer  = pack("fLLLLLLLLLLLLLLL", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
        # make our lives a little easier by assuring that these lists at least exist
        foreach ('flaresizes', 'flarepositions', 'flarecolorshifts', 'texturenames') {
          if (!defined($model->{'nodes'}{$i}{$_})) {
            $model->{'nodes'}{$i}{$_} = [];
          }
        }
        $buffer  = pack("fLLL", $model->{'nodes'}{$i}{'flareradius'}, 0, 0, 0);
        $totalbytes += length($buffer);
        print (BMDLOUT $buffer);
        $model->{'nodes'}{$i}{'flaresizespointer'} = tell(BMDLOUT);
        $buffer  = pack('LLL', 0, scalar(@{$model->{'nodes'}{$i}{'flaresizes'}}), scalar(@{$model->{'nodes'}{$i}{'flaresizes'}}));
        $totalbytes += length($buffer);
        print (BMDLOUT $buffer);
        $model->{'nodes'}{$i}{'flarepositionspointer'} = tell(BMDLOUT);
        $buffer  = pack('LLL', 0, scalar(@{$model->{'nodes'}{$i}{'flarepositions'}}), scalar(@{$model->{'nodes'}{$i}{'flarepositions'}}));
        $totalbytes += length($buffer);
        print (BMDLOUT $buffer);
        $model->{'nodes'}{$i}{'flarecolorshiftspointer'} = tell(BMDLOUT);
        $buffer  = pack('LLL', 0, scalar(@{$model->{'nodes'}{$i}{'flarecolorshifts'}}), scalar(@{$model->{'nodes'}{$i}{'flarecolorshifts'}}));
        $totalbytes += length($buffer);
        print (BMDLOUT $buffer);
        $model->{'nodes'}{$i}{'texturenamespointer'} = tell(BMDLOUT);
        $buffer  = pack('LLL', 0, scalar(@{$model->{'nodes'}{$i}{'texturenames'}}), scalar(@{$model->{'nodes'}{$i}{'texturenames'}}));
        $totalbytes += length($buffer);
        print (BMDLOUT $buffer);

        $buffer  = pack("L", $model->{'nodes'}{$i}{'lightpriority'});
        $buffer .= pack("L", $model->{'nodes'}{$i}{'ambientonly'});
        $buffer .= pack("L", $model->{'nodes'}{$i}{'ndynamictype'});
        $buffer .= pack("L", $model->{'nodes'}{$i}{'affectdynamic'});
        $buffer .= pack("L", $model->{'nodes'}{$i}{'shadow'});
        $buffer .= pack("L", $model->{'nodes'}{$i}{'flare'});
        $buffer .= pack("L", $model->{'nodes'}{$i}{'fadinglight'});
        $totalbytes += length($buffer);
        print (BMDLOUT $buffer);

        # write out flare data: texture names, sizes, positions, colorshifts
        if (scalar(@{$model->{'nodes'}{$i}{'flarepositions'}})) {
            # write out placeholders for the pointers to the texture names
            $model->{'nodes'}{$i}{'texturenamespointerlocation'} = tell(BMDLOUT);
            $model->{'nodes'}{$i}{'texturenameslocation'} = tell(BMDLOUT);
            my $name_pointers = [];
            foreach (1..scalar(@{$model->{'nodes'}{$i}{'texturenames'}})) {
                $name_pointers = [ @{$name_pointers}, 0 ];
            }
            $buffer  = pack('L' x scalar(@{$model->{'nodes'}{$i}{'texturenames'}}), @{$name_pointers});
            $totalbytes += (scalar(@{$model->{'nodes'}{$i}{'texturenames'}}) * 4);
            print (BMDLOUT $buffer);

            # write out the texture name strings
            $model->{'nodes'}{$i}{'texturenameslocations'} = [];
            for my $texname (@{$model->{'nodes'}{$i}{'texturenames'}}) {
                $model->{'nodes'}{$i}{'texturenameslocations'} = [
                    @{$model->{'nodes'}{$i}{'texturenameslocations'}},
                    # subtract 12 (file header length) from offsets now
                    tell(BMDLOUT) - 12
                ];
                $buffer = pack('Z*', $texname);
                #print "TEX: $buffer\n";
                $totalbytes += length($buffer);
                print (BMDLOUT $buffer);
            }

            # go back and write out the name pointers
            seek(BMDLOUT, $model->{'nodes'}{$i}{'texturenamespointerlocation'}, 0);
            print (BMDLOUT pack('L' x scalar(@{$model->{'nodes'}{$i}{'texturenameslocations'}}),
                                 @{$model->{'nodes'}{$i}{'texturenameslocations'}}));

            # return file position to head
            seek(BMDLOUT, $totalbytes, 0);

            # note offset and write flaresizes
            $model->{'nodes'}{$i}{'flaresizeslocation'} = tell(BMDLOUT);
            $buffer = pack('f' x scalar(@{$model->{'nodes'}{$i}{'flaresizes'}}), @{$model->{'nodes'}{$i}{'flaresizes'}});
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            # note offset and write flarepositions
            $model->{'nodes'}{$i}{'flarepositionslocation'} = tell(BMDLOUT);
            $buffer = pack('f' x scalar(@{$model->{'nodes'}{$i}{'flarepositions'}}), @{$model->{'nodes'}{$i}{'flarepositions'}});
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            # note offset and write flarecolorshifts
            $buffer = '';
            $model->{'nodes'}{$i}{'flarecolorshiftslocation'} = tell(BMDLOUT);
            for my $col_shift (@{$model->{'nodes'}{$i}{'flarecolorshifts'}}) {
                $buffer .= pack('fff', @{$col_shift});
            }
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            # go back and write out the other pointers
            seek(BMDLOUT, $model->{'nodes'}{$i}{'flaresizespointer'}, 0);
            print(BMDLOUT pack('L', $model->{'nodes'}{$i}{'flaresizeslocation'} - 12));
            seek(BMDLOUT, $model->{'nodes'}{$i}{'flarepositionspointer'}, 0);
            print(BMDLOUT pack('L', $model->{'nodes'}{$i}{'flarepositionslocation'} - 12));
            seek(BMDLOUT, $model->{'nodes'}{$i}{'flarecolorshiftspointer'}, 0);
            print(BMDLOUT pack('L', $model->{'nodes'}{$i}{'flarecolorshiftslocation'} - 12));
            seek(BMDLOUT, $model->{'nodes'}{$i}{'texturenamespointer'}, 0);
            print(BMDLOUT pack('L', $model->{'nodes'}{$i}{'texturenameslocation'} - 12));

            # return file position to head
            seek(BMDLOUT, $totalbytes, 0);
        }
    }

    #write out the emitter sub header and data (if any)
    if ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_REFERENCE)
    {
        $buffer = pack(
            'Z[32]L',
            $model->{'nodes'}{$i}{'refModel'},
            $model->{'nodes'}{$i}{'reattachable'}
        );
        print (BMDLOUT $buffer);
        $totalbytes += length($buffer);
    }

    if ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_EMITTER)
    {
        # size 224: 32 + 32 + 32 + 32 + 32 + 16 + 8 + 2 + 1 + 32 + 1 + 4
        $buffer = pack(
            #'l[2]f[3]l[3]Z[32]Z[32]Z[32]Z[64]Z[16]l[2]S[2]l', 0, 0,
            'f[3]L[5]Z[32]Z[32]Z[32]Z[32]Z[16]L[2]SCZ[32]CL',
            $model->{'nodes'}{$i}{'deadspace'},           # 0
            $model->{'nodes'}{$i}{'blastRadius'},         # 1
            $model->{'nodes'}{$i}{'blastLength'},         # 2
            $model->{'nodes'}{$i}{'numBranches'},         # 3
            $model->{'nodes'}{$i}{'controlptsmoothing'},  # 4
            $model->{'nodes'}{$i}{'xgrid'},               # 5
            $model->{'nodes'}{$i}{'ygrid'},               # 6
            $model->{'nodes'}{$i}{'spawntype'},           # 7
            $model->{'nodes'}{$i}{'update'},              # 8
            $model->{'nodes'}{$i}{'render'},              # 9
            $model->{'nodes'}{$i}{'blend'},               # 10
            $model->{'nodes'}{$i}{'texture'},             # 11
            $model->{'nodes'}{$i}{'chunkname'},           # 12
            $model->{'nodes'}{$i}{'twosidedtex'},         # 13
            $model->{'nodes'}{$i}{'loop'},                # 14
            $model->{'nodes'}{$i}{'renderorder'},         # 15
            $model->{'nodes'}{$i}{'m_bFrameBlending'},    # 16
            $model->{'nodes'}{$i}{'m_sDepthTextureName'}, # 17
            0, #$model->{'nodes'}{$i}{'m_bUnknown1'},         # 18
            $model->{'nodes'}{$i}{'emitterflags'},        # 19
        );
        print (BMDLOUT $buffer);
        $totalbytes += length($buffer);
    }

    #write out the mesh sub header and data (if any)
    if ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH)
    {
        #print "mesh node type " . $model->{'nodes'}{$i}{'nodetype'} . "\n";
        # write out function pointers
        if ($version eq 'k1')
        {
            if ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_DANGLY)  #289
            {
                $buffer =  pack("LL", 4216640, 4216624); # for kotor 1
            }
            elsif ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_SKIN)  #97
            {
                $buffer =  pack("LL", 4216592, 4216608); # for kotor 1
            }
            else
            {
                $buffer =  pack("LL", 4216656, 4216672); # for kotor 1
            }
        }
        else
        {
            if ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_DANGLY)  #289
            {
                $buffer =  pack("LL", 4216864, 4216848); # for kotor 2
            }
            elsif ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_SKIN)  #97
            {
                $buffer =  pack("LL", 4216816, 4216832); # for kotor 2
            }
            else
            {
                $buffer =  pack("LL", 4216880, 4216896); # for kotor 2
            } 
        }
        $totalbytes += length($buffer);
        print(BMDLOUT $buffer);
        $model->{'nodes'}{$i}{'faceslocpointer'} = tell(BMDLOUT);
        $buffer =  pack("LLL", 0, $model->{'nodes'}{$i}{'facesnum'}, $model->{'nodes'}{$i}{'facesnum'});

        # set bounding box min, max, radius, average
        $buffer .= pack("f[3]", @{$model->{'nodes'}{$i}{'bboxmin'}});
        $buffer .= pack("f[3]", @{$model->{'nodes'}{$i}{'bboxmax'}});
        $buffer .= pack("f", $model->{'nodes'}{$i}{'radius'});
        $buffer .= pack("f[3]", @{$model->{'nodes'}{$i}{'average'}});
        $buffer .= pack("f[3]", @{$model->{'nodes'}{$i}{'diffuse'}} );
        $buffer .= pack("f[3]", @{$model->{'nodes'}{$i}{'ambient'}} );
        $buffer .= pack("L", $model->{'nodes'}{$i}{'transparencyhint'} );
        $buffer .= pack("Z[32]", $model->{'nodes'}{$i}{'bitmap'} );
        $buffer .= pack("Z[32]", $model->{'nodes'}{$i}{'bitmap2'} );
        $buffer .= pack("Z[12]", $model->{'nodes'}{$i}{'texture0'} );
        $buffer .= pack("Z[12]", $model->{'nodes'}{$i}{'texture1'} );
        #$buffer .= pack("f[14]", 0,0,0,0,0,0,0,0,0,0,0,0,0,0);
        #$buffer .= pack("f[6]", 0,0,0,0,0,0); #compile time vertex indices, left over faces
        $totalbytes += length($buffer);
        print(BMDLOUT $buffer);

        $model->{'nodes'}{$i}{'vertnumpointer'} = tell(BMDLOUT);      
        $buffer = pack("L*", 0, 1, 1);
        $totalbytes += length($buffer);
        print(BMDLOUT $buffer);

        $model->{'nodes'}{$i}{'vertlocpointer'} = tell(BMDLOUT);      
        $buffer = pack("L*", 0, 1, 1);
        $totalbytes += length($buffer);
        print(BMDLOUT $buffer);

        $model->{'nodes'}{$i}{'unknownpointer'} = tell(BMDLOUT);      
        $buffer = pack("L*", 0, 1, 1);
        $buffer .= pack("l*", -1, -1, 0);
        # the following 8 bytes are not well understood yet and probably wrong
        if ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER) {
          #$buffer .= pack("C*", 0, 0, 0, 0, 0, 0, 0, 17);
          $buffer .= pack("C*", 171, 91, 237, 62, 120, 144, 188, 1);
          #shortsbr1,6 1st lightsaber mesh plane:
          #$buffer .= pack("C*", 171, 91, 237, 62, 120, 144, 188, 1);
          #$buffer .= pack("C*", -85, 91, -19, 62, 120, -112, -68, 1);
          #shortsbr1,6 2nd lightsaber mesh plane:
          #$buffer .= pack("C*", 0, 0, 0, 0, 0, 145, 6, 2);
          #$buffer .= pack("C*", 0, 0, 0, 0, 0, -111, 6, 2);
          #lghtsbr1,2,3 1st lightsaber mesh plane:
          #$buffer .= pack("C*", 171, 91, 237, 62, 104, 176, 207, 1);
          #$buffer .= pack("C*", -85, 91, -19, 62, 104, -80, -49, 1);
          #lghtsbr1,2,3 2nd lightsaber mesh plane:
          #$buffer .= pack("C*", 0, 0, 0, 0, 232, 210, 6, 2);
          #$buffer .= pack("C*", 0, 0, 0, 0, -24, -46, 6, 2);
          #dblsbr1 1st lightsaber mesh plane:
          #$buffer .= pack("C*", 171, 91, 237, 64, 206, 192, 207, 1);
          #$buffer .= pack("C*", -85, 91, -19, 64, -50, -64, -49, 1);
          #dblsbr1 2nd lightsaber mesh plane:
          #$buffer .= pack("C*", 0, 0, 0, 0, 112, 35, 193, 1);
          #$buffer .= pack("C*", 0, 0, 0, 0, 112, 35, -63, 1);
          #dblsbr1 3rd lightsaber mesh plane:
          #$buffer .= pack("C*", 29, 133, 171, 56, 232, 45, 54, 0);
          #$buffer .= pack("C*", 29, -123, -85, 56, -24, 45, 54, 0);
          #dblsbr1 4th lightsaber mesh plane:
          #$buffer .= pack("C*", 184, 166, 239, 1, 120, 6, 232, 1);
          #$buffer .= pack("C*", -72, -90, -17, 1, 120, 6, -24, 1);
        } else {
          $buffer .= pack("C*", 3, 0, 0, 0, 0, 0, 0, 0);
        }
        $buffer .= pack('Lffff', $model->{'nodes'}{$i}{'animateuv'}, # sparkle? .lmt? might actually be animateuv
                                 $model->{'nodes'}{$i}{'uvdirectionx'},
                                 $model->{'nodes'}{$i}{'uvdirectiony'},
                                 $model->{'nodes'}{$i}{'uvjitter'},
                                 $model->{'nodes'}{$i}{'uvjitterspeed'});

        $buffer .= pack("l", $model->{'nodes'}{$i}{'mdxdatasize'});

        # don't know what this is, but is definately has something to do with textures
        # MDXDataBitmap, bitfield describing what mesh info is found in the MDX row
        # 35 = 1, 2, 32 = (i believe) verts, uv verts, normals
        #if ($model->{'nodes'}{$i}{'texturenum'} == 1)
        #{
        #    $buffer .= pack("l", 35 );
        #}
        #else
        #{
        #    $buffer .= pack("l", 33 );
        #}
        #$buffer .= pack("l*", 0, 12, -1);

        #if ($model->{'nodes'}{$i}{'mdxdatasize'} > 24)
        #{
        #    $buffer .= pack("l*", 24);
        #}
        #else
        #{
        #    $buffer .= pack("l*", -1);
        #}
        #$buffer .= pack("l*", -1, -1, -1, -1, -1, -1, -1);
        $buffer .= pack('L', $model->{'nodes'}{$i}{'mdxdatabitmap'});
        $buffer .= pack('l[11]', @{$model->{'nodes'}{$i}{'mdxrowoffsets'}});

        $buffer .= pack("ss", $model->{'nodes'}{$i}{'vertnum'}, $model->{'nodes'}{$i}{'texturenum'} );

        $buffer .= pack('C*', $model->{'nodes'}{$i}{'lightmapped'},
                              $model->{'nodes'}{$i}{'rotatetexture'},
                              $model->{'nodes'}{$i}{'m_bIsBackgroundGeometry'},
                              $model->{'nodes'}{$i}{'shadow'},
                              $model->{'nodes'}{$i}{'beaming'},
                              $model->{'nodes'}{$i}{'render'});

        if ($version eq 'k2')
        {
            $buffer .= pack("CCssL", $model->{'nodes'}{$i}{'dirt_enabled'} ? 1 : 0, 0,
                                     $model->{'nodes'}{$i}{'dirt_texture'} ? $model->{'nodes'}{$i}{'dirt_texture'} : 1,
                                     $model->{'nodes'}{$i}{'dirt_worldspace'} ? $model->{'nodes'}{$i}{'dirt_worldspace'} : 1,
                                     $model->{'nodes'}{$i}{'hologram_donotdraw'} ? 1 : 0);
        } else {
            $buffer .= pack('s', 0);
        }

        # not sure this surface area hypothesis is actually correct,
        # i have not seen it with a value that makes sense in any models...
        $buffer .= pack('fL', $model->{'nodes'}{$i}{'surfacearea'}, 0);

        if ($version eq 'k2')
        {
            # this is not placed correctly at all
            #$buffer .= pack("l*", 0, 0);
        }

        $buffer .= pack("l", $model->{'nodes'}{$i}{'mdxstart'});
        $totalbytes += length($buffer);
        print(BMDLOUT $buffer);
        $model->{'nodes'}{$i}{'vertfloatpointer'} = tell(BMDLOUT);
        $buffer = pack("l", 0);
        $totalbytes += length($buffer);
        print(BMDLOUT $buffer);

        # end of mesh subheader

        # write out the mesh sub-sub-header and data (if there is any)
        if ($model->{'nodes'}{$i}{'nodetype'} == NODE_SKIN)  # skin mesh sub-sub-header
        {
            # compile-time only array, then ptr to skin weights in mdx, then ptr to skin bone refs in mdx
            $buffer = pack("l*", 0, 0, 0, $model->{'nodes'}{$i}{'mdxboneweightsloc'},
                                          $model->{'nodes'}{$i}{'mdxboneindicesloc'});
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            # write out the bone map location place holder
            $model->{'nodes'}{$i}{'bonemaplocpointer'} = tell(BMDLOUT);
            $buffer = pack("l*", 0, $nodenum);
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            # write out qbones location place holder  (Torlack -> "QBone Ref Inv")
            $model->{'nodes'}{$i}{'qboneslocpointer'} = tell(BMDLOUT);
            $buffer = pack("l*", 0, $nodenum, $nodenum);
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            # write out unknown array2 location place holder  (Torlack -> "TBone Ref Inv")
            $model->{'nodes'}{$i}{'tboneslocpointer'} = tell(BMDLOUT);
            $buffer = pack("l*", 0, $nodenum, $nodenum);
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            # write out unknown array3 location place holder  (Torlack -> "Bone constant indices")
            $model->{'nodes'}{$i}{'skinarray3locpointer'} = tell(BMDLOUT);
            $buffer = pack("l*", 0, $nodenum, $nodenum);
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            # write out bone index (Torlack -> "Bone part numbers")
            $buffer = "";
            foreach (0 .. 17)
            {
                if(defined($model->{'nodes'}{$i}{'index2node'}[$_]))
                {
                    $buffer .= pack("s", $model->{'nodes'}{$i}{'index2node'}[$_]);
                }
                else
                {
                    $buffer .= pack("s", 0);
                }
            }
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            #write out bone map
            $model->{'nodes'}{$i}{'bonemaplocation'} = tell(BMDLOUT);
            $buffer = pack("f*", @{$model->{'nodes'}{$i}{'node2index'}} );
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            #write out QBones
            $buffer = "";
            $model->{'nodes'}{$i}{'qboneslocation'} = tell(BMDLOUT);
            foreach (0..$nodenum - 1)
            {
                $buffer .= pack("f", $model->{'nodes'}{$i}{'QBones'}[$_][0] );
                $buffer .= pack("f", $model->{'nodes'}{$i}{'QBones'}[$_][1] );
                $buffer .= pack("f", $model->{'nodes'}{$i}{'QBones'}[$_][2] );
                $buffer .= pack("f", $model->{'nodes'}{$i}{'QBones'}[$_][3] );
            }
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            #write out TBones
            $buffer = "";
            $model->{'nodes'}{$i}{'tboneslocation'} = tell(BMDLOUT);
            foreach (0..$nodenum - 1)
            {
                $buffer .= pack("f", $model->{'nodes'}{$i}{'TBones'}[$_][0] );
                $buffer .= pack("f", $model->{'nodes'}{$i}{'TBones'}[$_][1] );
                $buffer .= pack("f", $model->{'nodes'}{$i}{'TBones'}[$_][2] );
                #$buffer .= pack("f*", 0,0,0,0,0,0,0,0,0 );
            }
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            #write out unknown array3
            $buffer = "";
            $model->{'nodes'}{$i}{'skinarray3location'} = tell(BMDLOUT);
            foreach (0..$nodenum - 1)
            {
                $buffer .= pack('SS', @{$model->{'nodes'}{$i}{'array8'}[$_]});
                #$buffer .= pack("S", $model->{'nodes'}{$i}{'array8'}{'unpacked'}[($_ * 2)] );
                #$buffer .= pack("S", $model->{'nodes'}{$i}{'array8'}{'unpacked'}[($_ * 2) + 1] );
                #$buffer .= pack("f*", 0,0 );
            }
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);
        }
        elsif ($model->{'nodes'}{$i}{'nodetype'} == NODE_SABER) # lightsaber mesh sub-sub-header
        {
            $model->{'nodes'}{$i}{'saber_vertspointer'} = tell(BMDLOUT);
            $buffer = pack('L', 0); # offset into data
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            $model->{'nodes'}{$i}{'tvertspointer'} = tell(BMDLOUT);
            $buffer = pack('L', 0); # offset into data
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            $model->{'nodes'}{$i}{'saber_normspointer'} = tell(BMDLOUT);
            $buffer = pack('L', 0); # offset into data
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            $buffer = pack(
              'LL',
              (defined($model->{'nodes'}{$i}{inv_count1}) ? $model->{'nodes'}{$i}{inv_count1} : 98),
              (defined($model->{'nodes'}{$i}{inv_count2}) ? $model->{'nodes'}{$i}{inv_count2} : 97)
            ); # 87 - 98, 2 values between 1 and 4 apart
            #$buffer .= pack('C[4]', 0, 0, 0, 0); # for lghtsbr and dblsbr
            #$buffer .= pack('C[4]', 235, 219, 57, 185); # for shrtsbr
            #$buffer .= pack('C[4]', -21, -37, 57, -71); # for shrtsbr (signed)
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            # data arrays to write out:
            # vertcoords2 (loc 2)
            $buffer = '';
            $model->{'nodes'}{$i}{'saber_vertslocation'} = tell(BMDLOUT);
            foreach(@{$model->{'nodes'}{$i}{'verts'}}) {
                $buffer .= pack('fff', @{$_});
            }
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

             # data2081-3 (loc 4)
             # face/vertex normals
            $buffer = '';
            $model->{'nodes'}{$i}{'saber_normslocation'} = tell(BMDLOUT);
            foreach(@{$model->{'nodes'}{$i}{'saber_norms'}}) {
                $buffer .= pack('fff', @{$_});
            }
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

             # tverts (loc 3)
            $buffer = '';
            $model->{'nodes'}{$i}{'tvertslocation'} = tell(BMDLOUT);
            foreach(@{$model->{'nodes'}{$i}{'tverts'}}) {
                $buffer .= pack('ff', @{$_});
            }
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);
        }
        elsif ($model->{'nodes'}{$i}{'nodetype'} == NODE_DANGLYMESH)  # dangly mesh sub-sub-header
        {
            $model->{'nodes'}{$i}{'constraintspointer'} = tell(BMDLOUT);
            $buffer = pack("lll", 0, $model->{'nodes'}{$i}{'vertnum'}, $model->{'nodes'}{$i}{'vertnum'} );
            $buffer .= pack("f", $model->{'nodes'}{$i}{'displacement'} );
            $buffer .= pack("f", $model->{'nodes'}{$i}{'tightness'} );
            $buffer .= pack("f", $model->{'nodes'}{$i}{'period'} );
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            $model->{'nodes'}{$i}{'danglyvertspointer'} = tell(BMDLOUT);
            $buffer = pack("l", 0 );
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            # write out dangly mesh constraints
            $buffer = "";
            $model->{'nodes'}{$i}{'constraintslocation'} = tell(BMDLOUT);
            foreach ( @{$model->{'nodes'}{$i}{'constraints'}} )
            {
                $buffer .= pack("f", $_ );
            }
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            # for some reason we now have to write out a duplicate of the vert coords
            $model->{'nodes'}{$i}{'danglyvertslocation'} = tell(BMDLOUT);
            $buffer = "";
            foreach ( @{$model->{'nodes'}{$i}{'verts'}} )
            {
                $buffer .= pack("f*", @{$_} );
            }
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);
        }
        elsif ($model->{'nodes'}{$i}{'nodetype'} == NODE_AABB)  # walk mesh sub-sub-header
        {
            # aabb tree location pointer, (tree immediately following so + 4)
            $buffer = pack("L", ((tell(BMDLOUT) - 12) + 4) );
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);

            # write out advanced aabb tree if it exists
            if (defined($model->{'nodes'}{$i}{'walkmesh'}) &&
                defined($model->{'nodes'}{$i}{'walkmesh'}{aabbs}) &&
                scalar(@{$model->{'nodes'}{$i}{'walkmesh'}{aabbs}}))
            {
                # aabb_start = $totalbytes - 12;
                $buffer = '';
                for my $aabb (@{$model->{'nodes'}{$i}{'walkmesh'}{aabbs}}) {
                    # convert aabb left/right tree indices to offsets using:
                    # start location, index, aabb node size (40)
                    $buffer .= pack(
                        'f[6]LLll', @{$aabb}[0..5],
                        ($aabb->[6] != -1 ? 0 : ($totalbytes - 12) + ($aabb->[9] * 40)),
                        ($aabb->[6] != -1 ? 0 : ($totalbytes - 12) + ($aabb->[10] * 40)),
                        $aabb->[6], $aabb->[8]
                    );
                }
                $totalbytes += length($buffer);
                print (BMDLOUT $buffer);
            }
            # fall back to legacy aabb tree
            else
            {
                $temp1 = tell(BMDLOUT);
                (undef, $buffer) = writeaabb($model, $i, 0, $temp1 );
                seek(BMDLOUT, $buffer, 0);
                $totalbytes += $buffer - $temp1;
            }
        } # end of nodetype == NODE_SKIN sub-sub-header

        # write out the mesh data

        # write out the faces
        $buffer = "";
        $model->{'nodes'}{$i}{'faceslocation'} = tell(BMDLOUT);
        foreach ( @{$model->{'nodes'}{$i}{'Bfaces'}} )
        {
            $buffer .= pack("fffflssssss", @{$_}[0..10] );
        }
        $totalbytes += length($buffer);
        print (BMDLOUT $buffer);

        # write out the number of vertex indices
        $model->{'nodes'}{$i}{'vertnumlocation'} = tell(BMDLOUT);
        if ($model->{'nodes'}{$i}{'nodetype'} != NODE_SABER) {
            $totalbytes += 4;
            print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'facesnum'} * 3));
        }

        # write out the vert floats
        $buffer = "";
        $model->{'nodes'}{$i}{'vertfloatlocation'} = tell(BMDLOUT);
        if ($model->{'nodes'}{$i}{'nodetype'} != NODE_SABER) {
            foreach ( @{$model->{'nodes'}{$i}{'verts'}} )
            {
                $buffer .= pack("f*", @{$_} );
            }
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);
        }

        # write out the vertex indicies location placeholder
        $model->{'nodes'}{$i}{'vertloclocation'} = tell(BMDLOUT);
        if ($model->{'nodes'}{$i}{'nodetype'} != NODE_SABER) {
            $totalbytes += 4;
            print(BMDLOUT pack("l", 0));
        }

        # write out mesh sequence counter number
        $model->{'nodes'}{$i}{'unknownlocation'} = tell(BMDLOUT);
        if ($model->{'nodes'}{$i}{'nodetype'} != NODE_SABER) {
            $totalbytes += 4;
            print(BMDLOUT pack("L", $model->{'nodes'}{$i}{'inv_count1'}));
        }

        # write out the vert indices
        $buffer = "";
        $model->{'nodes'}{$i}{'vertindicieslocation'} = tell(BMDLOUT);
        if ($model->{'nodes'}{$i}{'nodetype'} != NODE_SABER) {
            foreach ( @{$model->{'nodes'}{$i}{'Bfaces'}} )
            {
                $buffer .= pack("sss", $_->[8], $_->[9], $_->[10] );
            }
            $totalbytes += length($buffer);
            print (BMDLOUT $buffer);
        }
    } # write mesh subheader and data if

    #write out place holders for the child node indexes (if any)
    $model->{'nodes'}{$i}{'childarraylocation'} = tell(BMDLOUT);
    foreach ( 1..$model->{'nodes'}{$i}{'childcount'} )
    {
        print (BMDLOUT pack("L", 0));
        $totalbytes += 4;
    }
    
    #recurse on children, if any
    for my $child ( @{$model->{'nodes'}{$i}{'children'}} )
    {
        $totalbytes = writebinarynode($ref, $child, $totalbytes, $version, $type);
    }


    # $model{'anims'}{$animnum}{'nodes'}{$nodenum}{'Bcontrollers'}{20}{'times'}[$count]
    # $model{'anims'}{$animnum}{'nodes'}{$nodenum}{'Bcontrollers'}{8}{'times'}[$count] = $1;
    # $model{'anims'}{$animnum}{'nodes'}{$nodenum}{'Bcontrollers'}{8}{'values'}[$count] = [$2,$3,$4];

    #write out the controllers and their data (if any)
    $model->{'nodes'}{$i}{'controllerdata'}{'unpacked'} = [];
    my $raw_values = {};
    $count = 0;
    $buffer = "";

    if ( $model->{'nodes'}{$i}{'controllernum'} > 0 )
    {
        # loop through the controllers and make the controller data list
        foreach $controller (sort {$a <=> $b} keys %{$model->{'nodes'}{$i}{'Bcontrollers'}} )
        {
            # first the time keys
            $timestart = $count;
            foreach ( @{$model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'times'}} )
            {
                push @{$model->{'nodes'}{$i}{'controllerdata'}{'unpacked'}}, $_;
                $count++;
            }

            # now the values BACK HERE
            $valuestart = $count;
            foreach my $blah ( @{$model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'values'}} )
            {
                foreach ( @{$blah} )
                {
                    push @{$model->{'nodes'}{$i}{'controllerdata'}{'unpacked'}}, $_;
                    $count++;
                }
            }

            my $ccol = scalar(@{$model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'values'}[0]});

            # bezier keyed conroller support
            if ($ga eq 'ani' && defined($model->{'nodes'}{$i}{'controllers'}{'bezier'}{$controller}))
            {
                # alter number of columns for bezier keyed controllers now
                $ccol = ($ccol / 3) + 16;
            }

            # Write out controller data, like the chart below:
            #
            # $controller can be one of the following:
            # ========================================
            #
            # 8		Position		All
            # 20	Orientation		All
            # 36	Scaling			All
            #
            # 100	SelfIllumColor		All meshes
            # 128	Alpha			All meshes
            #
            # 76	Color			Light
            # 88	Radius			Light
            # 96	ShadowRadius		Light
            # 100	VerticalDisplacement	Light
            # 140	Multiplier		Light
            #
            # 80	AlphaEnd		Emitter
            # 84	AlphaStart		Emitter
            # 88	BirthRate		Emitter
            # 92	Bounce_Co (-efficient)	Emitter
            # 96	ColorEnd		Emitter
            # 108	ColorStart		Emitter
            # 120	CombineTime		Emitter
            # 124	Drag			Emitter
            # 128	FPS			Emitter
            # 132	FrameEnd		Emitter
            # 136	FrameStart		Emitter
            # 140	Grav			Emitter
            # 144	LifeExp			Emitter
            # 148	Mass			Emitter
            # 152	P2P_Bezier2		Emitter
            # 156	P2P_Bezier3		Emitter
            # 160	ParticleRot (-ation)	Emitter
            # 164	RandVel (-om -ocity)	Emitter
            # 168	SizeStart		Emitter
            # 172	SizeEnd			Emitter
            # 176	SizeStart_Y		Emitter
            # 180	SizeStart_X		Emitter
            # 184	Spread			Emitter
            # 188	Threshold		Emitter
            # 192	Velocity		Emitter
            # 196	XSize			Emitter
            # 200	YSize			Emitter
            # 204	BlurLength		Emitter
            # 208	LightningDelay		Emitter
            # 212	LightningRadius		Emitter
            # 216	LightningScale		Emitter
            # 228	Detonate		Emitter
            # 464	AlphaMid		Emitter
            # 468	ColorMid		Emitter
            # 480	PercentStart		Emitter
            # 481	PercentMid		Emitter
            # 482	PercentEnd		Emitter
            # 484	SizeMid			Emitter
            # 488	SizeMid_Y		Emitter

            if ( $controller == 8 && $ga eq "ani")
            {
                $buffer .= pack("LSSSSCCCC", $controller, 16, $model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'rows'},
                $timestart, $valuestart, $ccol, 0, 0, 0);
            }
            elsif ( $controller == 20 && $ga eq "ani" )
            {
                if ($ccol == 1) {
                    # this is a compressed quaternion encoded in a single float case.
                    # record controller data indices that will be treated as 'raw'
                    # they cannot be treated as usual floats,
                    # because compressed quaternions are not numbers in float range,
                    # and encoding them as such later will produce incorrect bytes
                    $raw_values = {
                        %{$raw_values},
                        map { $_ => 1 } (
                            $valuestart..(
                                $valuestart +
                                ($model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'rows'} *
                                 $ccol) - 1
                            )
                        )
                    };
                    # the game engine wants to see '2' for number of columns,
                    # it is not accurate, just a signal
                    $ccol = 2;
                }
                $buffer .= pack("LSSSSCCCC", $controller, 28, $model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'rows'},
                $timestart, $valuestart, $ccol, 0, 0, 0);
            }
            elsif ( $controller == 8 && $ga eq "geo" )
            {
                $buffer .= pack("LSSSSCCCC", $controller, -1, $model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'rows'},
                $timestart, $valuestart, $ccol, 87, 73, 0);
            }
            elsif ( $controller == 20 && $ga eq "geo" )
            {
                $buffer .= pack("LSSSSCCCC", $controller, -1, $model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'rows'},
                $timestart, $valuestart, $ccol, 57, 71, 0);
            }
            elsif ( ($controller == 132 || $controller == 100) && $ga eq "geo" )
            {
                $buffer .= pack("LSSSSCCCC", $controller, -1, $model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'rows'},
                $timestart, $valuestart, $ccol, 227, 119, 17);
            }
            elsif ( $controller == 36 )
            {
                $buffer .= pack("LSSSSCCCC", $controller, -1, $model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'rows'},
                $timestart, $valuestart, $ccol, 50, 18, 0); #245, 245, 17);
                # some models have 50, 17, 0... important? TBD
            }
            elsif ( ($model->{'nodes'}{$i}{'nodetype'} == NODE_LIGHT || $ga eq 'geo') &&
                    ($controller == 88 || $controller == 140 || $controller == 76)) # radius, multiplier, color
            {
                $buffer .= pack("LSSSSCCCC", $controller, -1, $model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'rows'},
                $timestart, $valuestart, $ccol, 255, 114, 17);
            }
            elsif ( $model->{'nodes'}{$i}{'nodetype'} == NODE_EMITTER ) {
                # these numbers are still bad ... need to figure them out for real sometime soon
                $buffer .= pack("LSSSSCCCC", $controller, -1, $model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'rows'},
                $timestart, $valuestart, $ccol, 99, 121, 17);
            }
            else
            {
                $buffer .= pack("LSSSSCCCC", $controller, -1, $model->{'nodes'}{$i}{'Bcontrollers'}{$controller}{'rows'},
                $timestart, $valuestart, $ccol, 0, 0, 0);
            }
        } # foreach $controller (sort {$a <=> $b} keys %{$model->{'nodes'}{$i}{'Bcontrollers'}} ) {

    # write out the controllers
    $model->{'nodes'}{$i}{'controllerlocation'} = tell(BMDLOUT);
    $totalbytes += length($buffer);
    print (BMDLOUT $buffer);
    # write out the controllers data
    $model->{'nodes'}{$i}{'controllerdatalocation'} = tell(BMDLOUT);
    $buffer = '';
    #$buffer = pack("f*", @{$model->{'nodes'}{$i}{'controllerdata'}{'unpacked'}} );
    #print Dumper($raw_values);
    for my $data_index (keys @{$model->{'nodes'}{$i}{'controllerdata'}{'unpacked'}}) {
      # using compressed quaternions in animation makes the following test necessary.
      # basically, the compressed quaternion fits into 4 bytes, but it's not actually a float
      # number. writing it out as a float _will_ cause it to be wrong.
      if (!defined($raw_values->{$data_index})) {
        $buffer .= pack('f', $model->{'nodes'}{$i}{'controllerdata'}{'unpacked'}[$data_index]);
      } else {
        $buffer .= pack('L', $model->{'nodes'}{$i}{'controllerdata'}{'unpacked'}[$data_index]);
      }
    }
    $totalbytes += length($buffer);
    print (BMDLOUT $buffer);
  } elsif ($model->{'nodes'}{$i}{'controllerdatanum'} > 0 ) {
    $model->{'nodes'}{$i}{'controllerdatalocation'} = tell(BMDLOUT);
    foreach my $blah ( @{$model->{'nodes'}{$i}{'Bcontrollers'}{0}{'values'}} ) {
      push @{$model->{'nodes'}{$i}{'controllerdata'}{'unpacked'}}, $blah;
      $count++;
    }
    $buffer = pack("f*", @{$model->{'nodes'}{$i}{'controllerdata'}{'unpacked'}} );
    $totalbytes += length($buffer);
    print (BMDLOUT $buffer);
  }

  $nodestart = tell(BMDLOUT);

  #fill in all the blanks we left behind
  # fill in header blanks
  seek(BMDLOUT, $model->{'nodes'}{$i}{'childarraypointer'}, 0);
  print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'childarraylocation'} - 12));

  # fill in common mesh stuff blanks
  if ($model->{'nodes'}{$i}{'nodetype'} == NODE_TRIMESH || $model->{'nodes'}{$i}{'nodetype'} == NODE_SKIN || $model->{'nodes'}{$i}{'nodetype'} == NODE_DANGLYMESH || $model->{'nodes'}{$i}{'nodetype'} == NODE_AABB) {
    seek(BMDLOUT, $model->{'nodes'}{$i}{'faceslocpointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'faceslocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'vertnumpointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'vertnumlocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'vertlocpointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'vertloclocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'unknownpointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'unknownlocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'vertfloatpointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'vertfloatlocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'vertloclocation'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'vertindicieslocation'} - 12));
  }
  # fill in mesh sub-sub-header blanks
  if ($model->{'nodes'}{$i}{'nodetype'} == NODE_SKIN) {  # skin mesh
    seek(BMDLOUT, $model->{'nodes'}{$i}{'bonemaplocpointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'bonemaplocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'qboneslocpointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'qboneslocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'tboneslocpointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'tboneslocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'skinarray3locpointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'skinarray3location'} - 12));
  } elsif ($model->{'nodes'}{$i}{'nodetype'} == NODE_DANGLYMESH) { # dangly mesh
    seek(BMDLOUT, $model->{'nodes'}{$i}{'constraintspointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'constraintslocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'danglyvertspointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'danglyvertslocation'} - 12));
  } elsif ($model->{'nodes'}{$i}{'nodetype'} == NODE_SABER) { # saber mesh
    seek(BMDLOUT, $model->{'nodes'}{$i}{'faceslocpointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'faceslocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'vertnumpointer'}, 0);
    print(BMDLOUT pack("L[3]", $model->{'nodes'}{$i}{'vertnumlocation'} - 12, 0, 0));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'vertlocpointer'}, 0);
    print(BMDLOUT pack("L[3]", $model->{'nodes'}{$i}{'vertloclocation'} - 12, 0, 0));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'unknownpointer'}, 0);
    print(BMDLOUT pack("L[3]", $model->{'nodes'}{$i}{'unknownlocation'} - 12, 0, 0));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'vertfloatpointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'vertfloatlocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'saber_vertspointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'saber_vertslocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'saber_normspointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'saber_normslocation'} - 12));
    seek(BMDLOUT, $model->{'nodes'}{$i}{'tvertspointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'tvertslocation'} - 12));
  }
  # fill in the controller blanks
  if ( $model->{'nodes'}{$i}{'controllernum'} != 0) {
    seek(BMDLOUT, $model->{'nodes'}{$i}{'controllerpointer'}, 0);
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'controllerlocation'} - 12));
  }
  if ( $model->{'nodes'}{$i}{'controllerdatanum'} != 0) {
    seek(BMDLOUT, $model->{'nodes'}{$i}{'controllerdatapointer'}, 0);    
    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'controllerdatalocation'} - 12));
  }
  #if this is a child of another node fill in the child list for the parent
  if (lc($model->{'nodes'}{$i}{'parent'}) ne "null") {  
    seek(BMDLOUT, $model->{'nodes'}{$model->{'nodes'}{$i}{'parentnodenum'}}{'childarraylocation'} + ($model->{'nodes'}{$i}{'childposition'} * 4), 0);
    if (tell(BMDLOUT) == 0) {
      print("$model->{'nodes'}{$i}{'parent'}\n");
      print("$model->{'nodes'}{$i}{'parentnodenum'}\n");
    }

    print(BMDLOUT pack("l", $model->{'nodes'}{$i}{'header'}{'start'} - 12));
  }
  #print("start+bytes: " . $nodestart . "|" . $totalbytes . "\n");
  seek(BMDLOUT, $nodestart, 0);
    
  return $totalbytes;
}

##################################################
# Write out a raw binary model
# 
sub writerawbinarymdl {
  my ($model, $version) = (@_);
  my ($buffer, $mdxsize, $totalbytes, $nodenum, $work, $nodestart);
  my ($file, $filepath, $timestart, $valuestart, $count);
  my $BMDLOUT;
  my ($temp1, $temp2, $temp3, $temp4, $roffset);
  my $tempref;

  if ($version eq 'k1') {
    # a kotor 1 model
    #$uoffset = -2;  # offset for unpacked values
    $roffset = -8;  # offset for raw bytes
  } elsif ($version eq 'k2') {
    # a kotor 2 model
    #$uoffset = 0;
    $roffset = 0;
  } else {
    return;
  }
  
  $file = $model->{'filename'};
  $filepath = $model->{'filepath+name'};

  $nodenum = $model->{'nodes'}{'truenodenum'};
  MDLOpsM::File::open(\$BMDLOUT, ">", $filepath."-$version-r-bin.mdl") or die "can't open MDL file $filepath-$version-r-bin.mdl\n";
  binmode($BMDLOUT);
  MDLOpsM::File::open(\*BMDXOUT, ">", $filepath."-$version-r-bin.mdx") or die "can't open MDX file $filepath-$version-r-bin.mdx\n";
  binmode(BMDXOUT);
 
  #write out MDX
  seek (BMDXOUT, 0, 0);
  for (my $i = 0; $i < $model->{'nodes'}{'truenodenum'}; $i++) {
    if ( defined($model->{'nodes'}{$i}{'mdxdata'}{'raw'}) ) {
      $model->{'nodes'}{$i}{'mdxstart'} = tell(BMDXOUT);
      print("writing MDX data for node $i at starting location $model->{'nodes'}{$i}{'mdxstart'}\n") if $printall;
      $buffer = $model->{'nodes'}{$i}{'mdxdata'}{'raw'};
      $mdxsize += length($buffer);
      print (BMDXOUT $buffer);
    }
  }
  MDLOpsM::File::close(*BMDXOUT);

  #write out binary MDL
  #write out the file header
  seek ($BMDLOUT, 0, 0);
  $buffer = pack("LLL", 0, 0, $mdxsize);
  $totalbytes += length($buffer);
  print ($BMDLOUT $buffer);

  #write out the geometry header
  $model->{'geoheader'}{'start'} = tell($BMDLOUT);
  $buffer = $model->{'geoheader'}{'raw'};
  $totalbytes += length($buffer);
  print ($BMDLOUT $buffer);
  
  #write out the model header
  $model->{'modelheader'}{'start'} = tell($BMDLOUT);
  $buffer = $model->{'modelheader'}{'raw'};
  $totalbytes += length($buffer);
  print ($BMDLOUT $buffer);

  #write out the name array header
  $model->{'nameheader'}{'start'} = tell($BMDLOUT);
  $buffer = $model->{'nameheader'}{'raw'};
  substr($buffer,  8,  4, pack("l", $mdxsize) );  #replace mdx size with new mdx size
  $totalbytes += length($buffer);
  print ($BMDLOUT $buffer);
  #write out the name array indexes
  $model->{'nameindexes'}{'start'} = tell($BMDLOUT);
  $buffer = $model->{'nameindexes'}{'raw'};
  $totalbytes += length($buffer);
  print ($BMDLOUT $buffer);
  #write out the part names
  $model->{'names'}{'start'} = tell($BMDLOUT);
  $buffer = $model->{'names'}{'raw'};
  $totalbytes += length($buffer);
  print ($BMDLOUT $buffer);

  #write out the animation indexes
  $model->{'anims'}{'indexes'}{'start'} = tell($BMDLOUT);
  $buffer = $model->{'anims'}{'indexes'}{'raw'};
  $totalbytes += length($buffer);
  print ($BMDLOUT $buffer);
  
  #write out the animations (if any)
  for (my $i = 0; $i < $model->{'numanims'}; $i++) {
    #write out the animation geoheader
    $model->{'anims'}{$i}{'geoheader'}{'start'} = tell($BMDLOUT);
    $buffer = $model->{'anims'}{$i}{'geoheader'}{'raw'};
    $totalbytes += length($buffer);
    print ($BMDLOUT $buffer);
    #write out the animation header
    $model->{'anims'}{$i}{'animheader'}{'start'} = tell($BMDLOUT);
    $buffer = $model->{'anims'}{$i}{'animheader'}{'raw'};
    $totalbytes += length($buffer);
    print ($BMDLOUT $buffer);
    #write out the animation events (if any)
    if ( defined($model->{'anims'}{$i}{'animevents'}{'raw'}) ) {
      $model->{'anims'}{$i}{'animevents'}{'start'} = tell($BMDLOUT);
      $buffer = $model->{'anims'}{$i}{'animevents'}{'raw'};
      $totalbytes += length($buffer);
      print ($BMDLOUT $buffer);
    }

    #write out the animation nodes
    #$tempref = $model->{'anims'}{$i}{'nodes'};
    foreach ( sort {$a <=> $b} keys %{$model->{'nodesort'}{$i}} ) {
      #$model->{'nodesort'}{$animnum}{$startnode+12} = $node . "-header";
      ($temp1, $temp2) = split( /-/,$model->{'nodesort'}{$i}{$_} );
      $buffer = $model->{'anims'}{$i}{'nodes'}{$temp1}{$temp2}{'raw'};
      $totalbytes += length($buffer);
      print ($BMDLOUT $buffer);
    }
  } #write out animations for loop

  # write out the nodes
  # in a bioware binary mdl I think they use a recursive function to write
  # the data.  You can tell by how the node controllers and controller data
  # come after the children of the node.  This procedure writes out the
  # data linearly.  Because of this you will never get an exact binary
  # match with a bioware model.  But it seems to work, so I'm gonna leave
  # it as it is.
  #
  # 2016 update: above spells out what was wrong here. now implemented
  #   recursively for closer to exact binary matches.
  $totalbytes += &writerawnodes($BMDLOUT, $model, $roffset);

  #fill in the last blank, the size of the mdl (minus the file header)
  seek($BMDLOUT, 4, 0);
  print($BMDLOUT pack("l", $totalbytes - 12));

  print("$file\n");
  print("done with: $filepath\n");

  MDLOpsM::File::close($BMDLOUT);
}


##########################################################
# This is a recursive method to write raw nodes for the replacer.
# Produces more exact binary matches than previous flat iterative approach.
#
sub writerawnodes {
  my ($BMDLOUT, $model, $roffset, $node_index) = @_;

  my ($buffer, $totalbytes);

  $buffer = '';
  $totalbytes = 0;

  if (!defined($node_index)) {
    # root node is nodenum 0 ... not a *great* assumption
    #XXX we can get the rootnode location, maybe search for it by start location
    $node_index = 0;
  }

  # assume caller has left the file seeked to where we should write the node
  my $nodestart = tell($BMDLOUT);

  #write out the node header
  $model->{'nodes'}{$node_index}{'header'}{'start'} = $nodestart;
  $buffer = $model->{'nodes'}{$node_index}{'header'}{'raw'};
  $totalbytes += length($buffer);
  print($BMDLOUT $buffer);

  #write out the sub header, sub-sub-header, and data (if any)
  if ( defined( $model->{'nodes'}{$node_index}{'subhead'}{'raw'} ) ) {
    # write out the node header
    $model->{'nodes'}{$node_index}{'subhead'}{'start'} = tell($BMDLOUT);
    $buffer = $model->{'nodes'}{$node_index}{'subhead'}{'raw'};
    $totalbytes += length($buffer);
    print($BMDLOUT $buffer);

    # write out node specific data for mesh nodes
    if ($model->{'nodes'}{$node_index}{'nodetype'} & NODE_HAS_MESH) {
      # write out mesh type specific data
      if ($model->{'nodes'}{$node_index}{'nodetype'} & NODE_HAS_SABER) { # node type 2081 I call it saber mesh
        # write out a copy of the vertex coordinates
        $model->{'nodes'}{$node_index}{'vertcoords2'}{'start'} = tell($BMDLOUT);
        print("$node_index-vertcoords2: $model->{'nodes'}{$node_index}{'vertcoords2'}{'start'}\n") if $printall;
        $buffer = $model->{'nodes'}{$node_index}{'vertcoords2'}{'raw'};
        $totalbytes += length($buffer);
        print ($BMDLOUT $buffer);

        # write out the node type 2081 data (what is this?)
        $model->{'nodes'}{$node_index}{'data2081-3'}{'start'} = tell($BMDLOUT);
        print("$node_index-data2081-3: $model->{'nodes'}{$node_index}{'data2081-3'}{'start'}\n") if $printall;
        $buffer = $model->{'nodes'}{$node_index}{'data2081-3'}{'raw'};
        $totalbytes += length($buffer);
        print ($BMDLOUT $buffer);

        # write out the tverts+
        $model->{'nodes'}{$node_index}{'tverts+'}{'start'} = tell($BMDLOUT);
        print("$node_index-tverts+: $model->{'nodes'}{$node_index}{'tverts+'}{'start'}\n") if $printall;
        $buffer = $model->{'nodes'}{$node_index}{'tverts+'}{'raw'};
        $totalbytes += length($buffer);
        print ($BMDLOUT $buffer);
      } elsif ($model->{'nodes'}{$node_index}{'nodetype'} & NODE_HAS_SKIN) { # skin mesh
        # write out the bone map
        $model->{'nodes'}{$node_index}{'bonemap'}{'start'} = tell($BMDLOUT);
        $buffer = $model->{'nodes'}{$node_index}{'bonemap'}{'raw'};
        $totalbytes += length($buffer);
        print ($BMDLOUT $buffer);

        # write out the qbones
        $model->{'nodes'}{$node_index}{'qbones'}{'start'} = tell($BMDLOUT);
        $buffer = $model->{'nodes'}{$node_index}{'qbones'}{'raw'};
        $totalbytes += length($buffer);
        print ($BMDLOUT $buffer);

        # write out the tbones
        $model->{'nodes'}{$node_index}{'tbones'}{'start'} = tell($BMDLOUT);
        $buffer = $model->{'nodes'}{$node_index}{'tbones'}{'raw'};
        $totalbytes += length($buffer);
        print ($BMDLOUT $buffer);

        # write out unknown array 8
        $model->{'nodes'}{$node_index}{'array8'}{'start'} = tell($BMDLOUT);
        $buffer = $model->{'nodes'}{$node_index}{'array8'}{'raw'};
        $totalbytes += length($buffer);
        print ($BMDLOUT $buffer);
      } elsif ($model->{'nodes'}{$node_index}{'nodetype'} & NODE_HAS_DANGLY) { # dangly mesh
        # write out dangly constraints
        $model->{'nodes'}{$node_index}{'constraints+'}{'start'} = tell($BMDLOUT);
        $buffer = $model->{'nodes'}{$node_index}{'constraints+'}{'raw'};
        $totalbytes += length($buffer);
        print ($BMDLOUT $buffer);
      }

      # write out the faces
      $model->{'nodes'}{$node_index}{'faces'}{'start'} = tell($BMDLOUT);
      $buffer = $model->{'nodes'}{$node_index}{'faces'}{'raw'};
      $totalbytes += length($buffer);
      print ($BMDLOUT $buffer);

      if (!($model->{'nodes'}{$node_index}{'nodetype'} & NODE_HAS_SABER)) {
        # write out the pointer to the array that holds the number of vert indices
        $model->{'nodes'}{$node_index}{'pntr_to_vert_num'}{'start'} = tell($BMDLOUT);
        $buffer = $model->{'nodes'}{$node_index}{'pntr_to_vert_num'}{'raw'};
        $totalbytes += length($buffer);
        print ($BMDLOUT $buffer);
      }

      # write out the vertex coordinates
      $model->{'nodes'}{$node_index}{'vertcoords'}{'start'} = tell($BMDLOUT);
      $buffer = $model->{'nodes'}{$node_index}{'vertcoords'}{'raw'};
      $totalbytes += length($buffer);
      print ($BMDLOUT $buffer);

      if (!($model->{'nodes'}{$node_index}{'nodetype'} & NODE_HAS_SABER)) {
        # write out the pointer to the array that holds the location of the vert indices
        $model->{'nodes'}{$node_index}{'pntr_to_vert_loc'}{'start'} = tell($BMDLOUT);
        $buffer = pack("l", (tell($BMDLOUT) + 8) - 12);
        $totalbytes += length($buffer);
        print ($BMDLOUT $buffer);

        # write out mesh sequence counter array that always has 1 element
        $model->{'nodes'}{$node_index}{'array3'}{'start'} = tell($BMDLOUT);
        $buffer = $model->{'nodes'}{$node_index}{'array3'}{'raw'};
        $totalbytes += length($buffer);
        print ($BMDLOUT $buffer);

        # write out the vert indices
        $model->{'nodes'}{$node_index}{'vertindexes'}{'start'} = tell($BMDLOUT);
        $buffer = $model->{'nodes'}{$node_index}{'vertindexes'}{'raw'};
        $totalbytes += length($buffer);
        print ($BMDLOUT $buffer);
      } # {'nodetype'} != 2081
    } # ($nodetype & NODE_HAS_MESH) if
  } # write subheader, sub-subheader, and data if

  #write out child node indexes (if any)
  if ( $model->{'nodes'}{$node_index}{'childcount'} != 0 ) {
    $model->{'nodes'}{$node_index}{'childcounter'} = 0;
    $model->{'nodes'}{$node_index}{'childindexes'}{'start'} = tell($BMDLOUT);
    $buffer = $model->{'nodes'}{$node_index}{'childindexes'}{'raw'};
    $totalbytes += length($buffer);
    print ($BMDLOUT $buffer);

    #write out child nodes
    my $childbytes = 0;
    # record position where child(ren) begin
    $nodestart = tell($BMDLOUT);
    for my $child_index (@{$model->{'nodes'}{$node_index}{'childindexes'}{'nums'}}) {
      # record size of child and maybe its children
      $childbytes += &writerawnodes($BMDLOUT, $model, $roffset, $child_index);
      # every child that is written seeks to its pointers as last activity,
      # therefore we seek to just after the written child(ren) after write
      seek($BMDLOUT, $nodestart + $childbytes, 0);
    }
    $totalbytes += $childbytes;
  }

  # write out the controllers
  $model->{'nodes'}{$node_index}{'controllers'}{'start'} = tell($BMDLOUT);
  $buffer = $model->{'nodes'}{$node_index}{'controllers'}{'raw'};
  $totalbytes += length($buffer);
  print ($BMDLOUT $buffer);

  # write out the controllers data
  $model->{'nodes'}{$node_index}{'controllerdata'}{'start'} = tell($BMDLOUT);
  $buffer = $model->{'nodes'}{$node_index}{'controllerdata'}{'raw'};
  $totalbytes += length($buffer);
  print ($BMDLOUT $buffer);

  # go back and change all the pointers
  # write in the header blanks
  # location of this nodes parent
  if ($node_index != 0) {
    seek($BMDLOUT, $model->{'nodes'}{$node_index}{'header'}{'start'} + 12, 0);
    print($BMDLOUT pack("l", $model->{'nodes'}{ $model->{'nodes'}{$node_index}{'parentnodenum'} }{'header'}{'start'} - 12));
  } else {
    seek($BMDLOUT, $model->{'nodes'}{$node_index}{'header'}{'start'} + 12, 0);
    print($BMDLOUT pack("l", 0));
  }
  if ($model->{'nodes'}{$node_index}{'childcount'} != 0) {
    # pointer to the child array
    seek($BMDLOUT, $model->{'nodes'}{$node_index}{'header'}{'start'} + 44, 0);
    print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'childindexes'}{'start'} - 12));
  }
  # fill in mesh stuff blanks
  if ($model->{'nodes'}{$node_index}{'nodetype'} & NODE_HAS_MESH) {
    if ($model->{'nodes'}{$node_index}{'nodetype'} & NODE_HAS_SABER) {
      seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 340 + $roffset, 0); #
      print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'vertcoords2'}{'start'} - 12));
      seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 344 + $roffset, 0); #
      print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'tverts+'}{'start'} - 12));
      seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 348 + $roffset, 0); #
      print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'data2081-3'}{'start'} - 12));
    } elsif ($model->{'nodes'}{$node_index}{'nodetype'} & NODE_HAS_SKIN) {
      seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 360 + $roffset, 0); #
      print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'bonemap'}{'start'} - 12));
      seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 368 + $roffset, 0); #
      print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'qbones'}{'start'} - 12));
      seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 380 + $roffset, 0); #
      print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'tbones'}{'start'} - 12));
      seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 392 + $roffset, 0); #
      print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'array8'}{'start'} - 12));
    } elsif ($model->{'nodes'}{$node_index}{'nodetype'} & NODE_HAS_DANGLY) {
      seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 340 + $roffset, 0); #
      print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'constraints+'}{'start'} - 12));
    }

    seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 8, 0);
    print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'faces'}{'start'} - 12));

    if (!($model->{'nodes'}{$node_index}{'nodetype'} & NODE_HAS_SABER)) {
      seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 176, 0);
      print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'pntr_to_vert_num'}{'start'} - 12));
      seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 188, 0);
      print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'pntr_to_vert_loc'}{'start'} - 12));
      seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 200, 0);
      print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'array3'}{'start'} - 12));
      seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 332 + $roffset, 0); #
      print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'mdxstart'}));
    }

    seek($BMDLOUT, $model->{'nodes'}{$node_index}{'subhead'}{'start'} + 336 + $roffset, 0); #
    print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'vertcoords'}{'start'} - 12));
  } # ($model->{'nodes'}{$node_index}{'nodetype'} & NODE_HAS_MESH)

  # fill in the controller blanks
  if ( $model->{'nodes'}{$node_index}{'controllernum'} != 0) {
    seek($BMDLOUT, $model->{'nodes'}{$node_index}{'header'}{'start'} + 56, 0);
    print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'controllers'}{'start'} - 12));
    seek($BMDLOUT, $model->{'nodes'}{$node_index}{'header'}{'start'} + 68, 0);
    print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'controllerdata'}{'start'} - 12));
  }

  #if this is a child of another node fill in the child list for the parent
  if (lc($model->{'nodes'}{$node_index}{'parent'}) ne "null") {
    my $temp1;
    $temp1 =  $model->{'nodes'}{ $model->{'nodes'}{$node_index}{'parentnodenum'} }{'childindexes'}{'start'};
    $temp1 += $model->{'nodes'}{ $model->{'nodes'}{$node_index}{'parentnodenum'} }{'childcounter'} * 4;
    seek($BMDLOUT, $temp1, 0);
    $model->{'nodes'}{ $model->{'nodes'}{$node_index}{'parentnodenum'} }{'childcounter'}++;
    if (tell($BMDLOUT) == 0) {
      print("$model->{'nodes'}{$node_index}{'parentnodenum'}\n");
      print("$model->{'nodes'}{ $model->{'nodes'}{$node_index}{'parentnodenum'} }{'childindexes'}{'start'}\n");
      print("$model->{'nodes'}{ $model->{'nodes'}{$node_index}{'parentnodenum'} }{'childcounter'}\n");
      print("$model->{'nodes'}{$node_index}{'parent'}\n");
    }
    print($BMDLOUT pack("l", $model->{'nodes'}{$node_index}{'header'}{'start'} - 12));
  }

  return $totalbytes;
}


##########################################################
# This takes data from an ascii source and makes it look
# like it is from a binary source (as best as we can at the moment).
#
sub replaceraw {
  my ($binarymodel, $asciimodel, $binarynodename, $asciinodename) = (@_);
  my ($buffer, $binarynode, $asciinode, $item);  
  my ($count, $timestart, $valuestart, $work);

  $binarynode = $binarymodel->{'nodeindex'}{lc($binarynodename)};
  $asciinode = $asciimodel->{'nodeindex'}{lc($asciinodename)};

  print("$binarynode - $binarynodename\n");
  print("$asciinode - $asciinodename\n");

  print("$asciimodel->{'nodes'}{$asciinode}{'mdxdatasize'}\n") if $printall;
  # replace the MDX data
  $buffer = "";
  # build the raw mdx data from the ascii model
  for (my $j = 0; $j < $asciimodel->{'nodes'}{$asciinode}{'vertnum'}; $j++) {
    $buffer .= pack("f",$asciimodel->{'nodes'}{$asciinode}{'verts'}[$j][0]);
    $buffer .= pack("f",$asciimodel->{'nodes'}{$asciinode}{'verts'}[$j][1]);
    $buffer .= pack("f",$asciimodel->{'nodes'}{$asciinode}{'verts'}[$j][2]);
    $buffer .= pack("f",$asciimodel->{'nodes'}{$asciinode}{'vertexnormals'}{$j}[0]);
    $buffer .= pack("f",$asciimodel->{'nodes'}{$asciinode}{'vertexnormals'}{$j}[1]);
    $buffer .= pack("f",$asciimodel->{'nodes'}{$asciinode}{'vertexnormals'}{$j}[2]);
    # if this mesh has uv coordinates add them in
    if ($asciimodel->{'nodes'}{$asciinode}{'mdxdatasize'} > 24) {
      $buffer .= pack("f",$asciimodel->{'nodes'}{$asciinode}{'tverts'}[$asciimodel->{'nodes'}{$asciinode}{'tverti'}{$j}][0]);
      $buffer .= pack("f",$asciimodel->{'nodes'}{$asciinode}{'tverts'}[$asciimodel->{'nodes'}{$asciinode}{'tverti'}{$j}][1]);
    }
    # if this is a skin mesh node then add in the bone weights
    if ($asciimodel->{'nodes'}{$asciinode}{'nodetype'} == NODE_SKIN) {
      $buffer .= pack("f*", @{$asciimodel->{'nodes'}{$asciinode}{'Bbones'}[$j]} );
    }
  }
  # add on the end padding
  # this should actually be enforcing 32-byte alignment i think, but it isn't.
  # it gets lucky most of the time though (wouldn't work replacing untextured mesh probably)
  if ($asciimodel->{'nodes'}{$asciinode}{'nodetype'} == NODE_SKIN) {
    # padding for skin nodes seems to be different, more like this:
    $buffer .= pack("f*", 1000000, 1000000, 1000000, 0,
                          0, 0, 0, 0,  1, 0, 0, 0,  0, 0, 0, 0);
  } else {
    $buffer .= pack("f*", 10000000, 10000000, 10000000, 0,
                          0, 0, 0, 0);
  }
  # write the mdx data to the binary model
  $binarymodel->{'nodes'}{$binarynode}{'mdxdata'}{'raw'} = $buffer;
  
  # replace the node header
  # get the raw data from the binary model
  $buffer = $binarymodel->{'nodes'}{$binarynode}{'header'}{'raw'};
  # replace parts of the raw data from the binary model with data from the ascii model

  substr($buffer, 16, 4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'Bcontrollers'}{8}{'values'}[0][0]) ); # x
  substr($buffer, 20, 4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'Bcontrollers'}{8}{'values'}[0][1]) ); # y
  substr($buffer, 24, 4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'Bcontrollers'}{8}{'values'}[0][2]) ); # z
  substr($buffer, 28, 4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'Bcontrollers'}{20}{'values'}[0][3]) ); # w
  substr($buffer, 32, 4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'Bcontrollers'}{20}{'values'}[0][0]) ); # x
  substr($buffer, 36, 4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'Bcontrollers'}{20}{'values'}[0][1]) ); # y
  substr($buffer, 40, 4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'Bcontrollers'}{20}{'values'}[0][2]) ); # z

  substr($buffer, 60, 4, pack("l", $asciimodel->{'nodes'}{$asciinode}{'controllernum'}) );
  substr($buffer, 64, 4, pack("l", $asciimodel->{'nodes'}{$asciinode}{'controllernum'}) );
   
  substr($buffer, 72, 4, pack("l", $asciimodel->{'nodes'}{$asciinode}{'controllerdatanum'}) );
  substr($buffer, 76, 4, pack("l", $asciimodel->{'nodes'}{$asciinode}{'controllerdatanum'}) );
  # write the raw data back to the binary model
  $binarymodel->{'nodes'}{$binarynode}{'header'}{'raw'} = $buffer;

  # replace controllers and their data
  $binarymodel->{'nodes'}{$binarynode}{'controllerdata'}{'unpacked'} = [];
  $count = 0;
  $buffer = "";
  # loop through the controllers and make the controller data list
  foreach $work (sort {$a <=> $b} keys %{$asciimodel->{'nodes'}{$asciinode}{'Bcontrollers'}} ) {
    # first the time keys
    $timestart = $count;
    foreach ( @{$asciimodel->{'nodes'}{$asciinode}{'Bcontrollers'}{$work}{'times'}} ) {
      push @{$binarymodel->{'nodes'}{$binarynode}{'controllerdata'}{'unpacked'}}, $_;
      $count++;
    }
    # now the values FIXING
    $valuestart = $count;
    foreach my $blah ( @{$asciimodel->{'nodes'}{$asciinode}{'Bcontrollers'}{$work}{'values'}} ) {
      foreach ( @{$blah} ) {
        push @{$binarymodel->{'nodes'}{$binarynode}{'controllerdata'}{'unpacked'}}, $_;
        $count++;
      }
    }
    $buffer .= pack("LSSSSCCCC", $work, -1, 1, $timestart, $valuestart, scalar(@{$asciimodel->{'nodes'}{$asciinode}{'Bcontrollers'}{$work}{'values'}[0]}), 0, 0, 0);
  }

  # write out the controllers
  $binarymodel->{'nodes'}{$binarynode}{'controllers'}{'raw'} = $buffer;
  # write out the controllers data
  $buffer = pack("f*", @{$binarymodel->{'nodes'}{$binarynode}{'controllerdata'}{'unpacked'}} );
  $binarymodel->{'nodes'}{$binarynode}{'controllerdata'}{'raw'} = $buffer;

  # replace mesh header
  # get the raw data from the binary model
  $buffer = $binarymodel->{'nodes'}{$binarynode}{'subhead'}{'raw'};
  # replace parts of the raw data from the binary model with data from the ascii model
  substr($buffer,  12,  4, pack("l", $asciimodel->{'nodes'}{$asciinode}{'facesnum'}) );
  substr($buffer,  16,  4, pack("l", $asciimodel->{'nodes'}{$asciinode}{'facesnum'}) );
  substr($buffer,  60,  4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'diffuse'}[0]) );
  substr($buffer,  64,  4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'diffuse'}[1]) );
  substr($buffer,  68,  4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'diffuse'}[2]) );
  substr($buffer,  72,  4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'ambient'}[0]) );
  substr($buffer,  76,  4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'ambient'}[1]) );
  substr($buffer,  80,  4, pack("f", $asciimodel->{'nodes'}{$asciinode}{'ambient'}[2]) );
  substr($buffer,  88, 32, pack("Z[32]", $asciimodel->{'nodes'}{$asciinode}{'bitmap'}) );
  substr($buffer, 120, 32, pack("Z[32]", $asciimodel->{'nodes'}{$asciinode}{'bitmap2'}) );
  substr($buffer, 252,  4, pack("l", $asciimodel->{'nodes'}{$asciinode}{'mdxdatasize'}) );
  if ($asciimodel->{'nodes'}{$asciinode}{'mdxdatasize'} > 24) {
    substr($buffer, 272, 4, pack("l", 24) );  # texture data offset
    substr($buffer, 306, 2, pack("s", 1) );   # number of textures
  } else {
    substr($buffer, 272, 4, pack("l", -1) );  # texture data offset
    substr($buffer, 306, 2, pack("s", 0) );   # number of textures
  }
  substr($buffer, 304, 2, pack("s", $asciimodel->{'nodes'}{$asciinode}{'vertnum'}) );
  if ($asciimodel->{'nodes'}{$asciinode}{'shadow'} == 1) {
    substr($buffer, 310, 2, pack("s", 256) );
  } else {
    substr($buffer, 310, 2, pack("s", 0) );
  }
  if ($asciimodel->{'nodes'}{$asciinode}{'render'} == 1) {
    substr($buffer, 312, 2, pack("s", 256) );
  } else {
    substr($buffer, 312, 2, pack("s", 0) );
  }
  # write the raw data back to the binary model
  $binarymodel->{'nodes'}{$binarynode}{'subhead'}{'raw'} = $buffer;

  # replace the face array
  $buffer = "";
  foreach ( @{$asciimodel->{'nodes'}{$asciinode}{'Bfaces'}} ) {
    $buffer .= pack("fffflssssss", @{$_}[0..10] );
  }
  $binarymodel->{'nodes'}{$binarynode}{'faces'}{'raw'} = $buffer;

  # replace vertex coordinates
  $buffer = "";
  foreach ( @{$asciimodel->{'nodes'}{$asciinode}{'verts'}} ) {
    $buffer .= pack("f*", @{$_} );
  }
  $binarymodel->{'nodes'}{$binarynode}{'vertcoords'}{'raw'} = $buffer;
  
  # replace vertex indexes
  $buffer = "";
  foreach ( @{$asciimodel->{'nodes'}{$asciinode}{'Bfaces'}} ) {
    $buffer .= pack("sss", $_->[8], $_->[9], $_->[10] );
  }
  $binarymodel->{'nodes'}{$binarynode}{'vertindexes'}{'raw'} = $buffer;
  $binarymodel->{'nodes'}{$binarynode}{'pntr_to_vert_num'}{'raw'} = pack("l", $asciimodel->{'nodes'}{$asciinode}{'facesnum'} * 3);
}

##########################################################
# This builds a tree list with the model data.
# Only works for models from binary source right now
# 
sub buildtree {
  my ($tree, $model) = (@_);
  my $temp;

  if ($model->{'source'} eq "ascii") {
    print("Model from ascii source\n");
    return;
  }

  #empty out the tree list
  $tree->delete('all');

  $tree->add('.', 
       -text => $model->{'filename'},
             -data => $model);
  
  # add the basic stuff that is in every model
  $tree->add('.geoheader', 
             -text => "geo_header ($model->{'geoheader'}{'start'})",
             -data => 1);
  $tree->add('.modelheader', 
             -text => "model_header ($model->{'modelheader'}{'start'})",
             -data => 1);
  $tree->add('.namearray', 
             -text => 'Name_array',
             -data => 1);
  $tree->add('.namearray.nameheader', 
             -text => "name_header ($model->{'nameheader'}{'start'})",
             -data => 1);
  $tree->add('.namearray.nameindexes', 
             -text => "name_indexes ($model->{'nameindexes'}{'start'})",
             -data => 1);
  $tree->add('.namearray.partnames', 
             -text => "names ($model->{'names'}{'start'})",
             -data => 1);
  $tree->setmode(".namearray", "close");
  $tree->close(".namearray");
  
  # add the animations (if any)
  if ($model->{'numanims'} != 0) {
    # make the animation root
    $tree->add('.anims', -text => "Animations");
    $tree->add('.anims.indexes', 
               -text => "anim_indexes ($model->{'anims'}{'indexes'}{'start'})",
               -data => 1);
    # loop through the animations
    for (my $i = 0; $i < $model->{'numanims'}; $i++) {
      $tree->add(".anims.$i", 
                 -text => $model->{'anims'}{$i}{'name'},
                 -data => 1);
      $tree->add(".anims.$i.geoheader", 
                 -text => "anim_geoheader ($model->{'anims'}{$i}{'geoheader'}{'start'})",
                 -data => 1);
      $tree->add(".anims.$i.animheader", 
                 -text => "anim_header ($model->{'anims'}{$i}{'animheader'}{'start'})",
                 -data => 1);
      # if this animation has events then add an entry for them
      if ($model->{'anims'}{$i}{'eventsnum'} != 0) {
        $tree->add(".anims.$i.animevents", 
                   -text => "anim_events ($model->{'anims'}{$i}{'animevents'}{'start'})",
                   -data => 1);
      }
      # loop through the nodes for this animation
      $tree->add(".anims.$i.nodes", 
                 -text => "nodes",
                 -data => 1);
      foreach (sort {$a <=> $b} keys(%{$model->{'anims'}{$i}{'nodes'}}) ) {
  if ($_ eq 'truenodenum') {next;};
        $tree->add(".anims.$i.nodes.$_", 
                   -text => "<$model->{'anims'}{$i}{'nodes'}{$_}{'nodetype'}> $_-$model->{'partnames'}[$_] <$model->{'anims'}{$i}{'nodes'}{$_}{'parent'}>",
                   -data => 1);
        $tree->add(".anims.$i.nodes.$_.header", 
                   -text => "header ($model->{'anims'}{$i}{'nodes'}{$_}{'header'}{'start'})",
                   -data => 1);
  # if the node has children make an entry
        if ($model->{'anims'}{$i}{'nodes'}{$_}{'childcount'} != 0) {
          $tree->add(".anims.$i.nodes.$_.childindexes", 
                     -text => "children ($model->{'anims'}{$i}{'nodes'}{$_}{'childindexes'}{'start'})",
                     -data => 9);
        }
  # if the node has controllers make entries for them and their data
        if ($model->{'anims'}{$i}{'nodes'}{$_}{'controllernum'} != 0) {
          $tree->add(".anims.$i.nodes.$_.controllers", 
                     -text => "controllers ($model->{'anims'}{$i}{'nodes'}{$_}{'controllers'}{'start'})",
                     -data => 9);
          $tree->add(".anims.$i.nodes.$_.controllerdata", 
                     -text => "controllerdata ($model->{'anims'}{$i}{'nodes'}{$_}{'controllerdata'}{'start'})",
                     -data => 1);
  }
  # make the branch closeable and close it
        $tree->setmode(".anims.$i.nodes.$_", "close");
        $tree->close(".anims.$i.nodes.$_");
      } # for each loop
      # make the branch closeable and close it
      $tree->setmode(".anims.$i.nodes", "close");
      $tree->close(".anims.$i.nodes");
      
      # make the branch closeable and close it
      $tree->setmode(".anims.$i", "close");
      $tree->close(".anims.$i");
    } # for loop
    # make the branch closeable and close it
    $tree->setmode(".anims", "close");
    $tree->close(".anims");
  } # animations if

  # create the node root
  $tree->add('.nodes', 
             -text => "nodes",
             -data => 1);
  # loop through the geometry nodes
  for (my $i = 0; $i < $model->{'nodes'}{'truenodenum'}; $i++) {
    $tree->add(".nodes.$i", 
               -text => "<$model->{'nodes'}{$i}{'nodetype'}> $i-$model->{'partnames'}[$i] <$model->{'nodes'}{$i}{'parent'}>",
               -data => 1);
    $tree->add(".nodes.$i.header", 
               -text => "node_header_$model->{'nodes'}{$i}{'nodetype'} ($model->{'nodes'}{$i}{'header'}{'start'})",
               -data => 1);
    # if this node has controllers make entries for them and their data
    if ($model->{'nodes'}{$i}{'controllernum'} != 0) {
      $tree->add(".nodes.$i.header.controllers", 
                 -text => "controllers ($model->{'nodes'}{$i}{'controllers'}{'start'})",
                 -data => 9);
      $tree->add(".nodes.$i.header.controllerdata", 
                 -text => "controller_data  ($model->{'nodes'}{$i}{'controllerdata'}{'start'})",
                 -data => 1);
    }
    # if this node has children make an entry for it
    if ($model->{'nodes'}{$i}{'childcount'} != 0) {
      $tree->add(".nodes.$i.header.childindexes", 
                 -text => "node_children ($model->{'nodes'}{$i}{'childindexes'}{'start'})",
                 -data => 1);
    }
    # if this node has a subheader make an entry for it
    if ($model->{'nodes'}{$i}{'nodetype'} != NODE_DUMMY) {
      $tree->add(".nodes.$i.subhead", 
                 -text => "subhead",
                 -data => 1);
    }
    # now we take care of specific node types
    # nodes with trimesh, nodetypes = 33, 97, 289, 2081
    if ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH) {
      $tree->add(".nodes.$i.subhead.faces", 
                 -text => "faces  ($model->{'nodes'}{$i}{'faces'}{'start'})",
                 -data => 11);
      if (!($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER)) { # unknown node type 2081, I call it saber mesh
        $tree->add(".nodes.$i.subhead.vertcoords", 
                   -text => "vertcoords ($model->{'nodes'}{$i}{'vertcoords'}{'start'})",
                   -data => 3);
        $tree->add(".nodes.$i.subhead.pntr_to_vert_num", 
                   -text => "pntr_to_vert_num ($model->{'nodes'}{$i}{'pntr_to_vert_num'}{'start'})",
                   -data => 1);
        $tree->add(".nodes.$i.subhead.pntr_to_vert_loc", 
                   -text => "pntr_to_vert_loc ($model->{'nodes'}{$i}{'pntr_to_vert_loc'}{'start'})",
                   -data => 1);
        $tree->add(".nodes.$i.subhead.array3", 
                   -text => "array3 ($model->{'nodes'}{$i}{'array3'}{'start'})",
                   -data => 1);
        $tree->add(".nodes.$i.subhead.vertindexes", 
                   -text => "vertindexes ($model->{'nodes'}{$i}{'vertindexes'}{'start'})",
                   -data => 3);
      }
    }    
    if ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_SKIN) { # node type 97 = skin mesh
      $tree->add(".nodes.$i.subhead.bonemap", 
                 -text => "bonemap ($model->{'nodes'}{$i}{'bonemap'}{'start'})",
                 -data => 1);
      $tree->add(".nodes.$i.subhead.qbones", 
                 -text => "qbones ($model->{'nodes'}{$i}{'qbones'}{'start'})",
                 -data => 4);
      $tree->add(".nodes.$i.subhead.tbones", 
                 -text => "tbones ($model->{'nodes'}{$i}{'tbones'}{'start'})",
                 -data => 3);
      $tree->add(".nodes.$i.subhead.array8", 
                 -text => "array8 ($model->{'nodes'}{$i}{'array8'}{'start'})",
                 -data => 2);
    } elsif ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_DANGLY) { # node type 289 = dangly mesh
      $tree->add(".nodes.$i.subhead.constraints+", 
                 -text => "constraints+ ($model->{'nodes'}{$i}{'constraints+'}{'start'})",
                 -data => 1);
    } elsif ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_AABB) { # node type 545 = aabb
      $tree->add(".nodes.$i.subhead.aabb", 
                 -text => "aabb ($model->{'nodes'}{$i}{'aabb'}{'start'})",
                 -data => 10);
    } elsif ($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER) { # unknown node type 2081, I call it saber mesh
      $tree->add(".nodes.$i.subhead.vertcoords", 
                 -text => "vertcoords ($model->{'nodes'}{$i}{'vertcoords'}{'start'})",
                 -data => 3);
      $tree->add(".nodes.$i.subhead.vertcoords2", 
                 -text => "vertcoords2 ($model->{'nodes'}{$i}{'vertcoords2'}{'start'})",
                 -data => 3);
      $tree->add(".nodes.$i.subhead.tverts+", 
                 -text => "tverts+ ($model->{'nodes'}{$i}{'tverts+'}{'start'})",
                 -data => 2);
      $tree->add(".nodes.$i.subhead.data2081-3", 
                 -text => "data2081-3 ($model->{'nodes'}{$i}{'data2081-3'}{'start'})",
                 -data => 2);
    }
    # if node has mdx data add entry for it.  2081 is a mesh, but has no mdx data!
    if (($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_MESH) && !($model->{'nodes'}{$i}{'nodetype'} & NODE_HAS_SABER)) {
      $tree->add(".nodes.$i.subhead.mdxdata", 
                 -text => "mdxdata {$model->{'nodes'}{$i}{'mdxdata'}{'start'}}",
                 -data => $model->{'nodes'}{$i}{'mdxdata'}{'dnum'});
    }
    # if this is not a dummy node then make the branch closeable and close it
    if ($model->{'nodes'}{$i}{'nodetype'} != NODE_DUMMY) {
      $tree->setmode(".nodes.$i.subhead", "close");
      $tree->close(".nodes.$i.subhead");
    }
    $tree->setmode(".nodes.$i.header", "close");
    $tree->close(".nodes.$i.header");
    $tree->setmode(".nodes.$i", "close");
    $tree->close(".nodes.$i");
  } # geometry node loop
        
  $tree->setmode(".nodes", "close");
  $tree->close(".nodes");
}

sub printhex {
  #this sub takes the raw data and outputs hex data for output to the console
  my ($stuff) = @_;
  my $counter = 0;

  $stuff = unpack("H*", $stuff);

  for ($counter = 0; $counter < length($stuff); $counter += 8) {
    if (($counter != 0) && ($counter % 32 == 0)) {print("\n");}
    print(substr($stuff, $counter, 8) . "|");
 }
  print ("\n\n");
}

1;

#^L
package MDLOpsM::Walkmesh;
use strict;
use warnings;

BEGIN {
  require Exporter;
  use vars qw(@ISA @EXPORT @EXPORT_OK %EXPORT_TAGS $VERSION);
  $VERSION = '0.1.0';
  @EXPORT = qw(readbinarywalkmesh writebinarywalkmesh readasciiwalkmesh writeasciiwalkmesh detect_format aabb);
  @ISA = qw(Exporter);
}

use Data::Dumper;

BEGIN {
  use vars qw($info);
  $info = {
    sizes => {
      header => 136,
      vert => 12,
      face => 12,
      type => 4,
      normal => 12,
      plane_distance => 4,
      aabb => 44,
      adjacent_face => 12,
      edge_loop => 8,
      perimeter => 4
    },
    templates => {
      header => 'A[8]L' . ('f' x 15) . 'LL' . 'LL' . 'L' . 'L' . 'L' . 'LLLLLLLLL',
      face => 'LLL',
      type => 'L',
      aabb => 'f[6]l[5]',
      adjacent_face => 'lll',
      edge_loop => 'll',
      perimeter => 'l',
    },
    hooks => {
      pwk => [ 'use01', 'use02' ],
      dwk => [ 'open1_01', 'open2_01', 'closed_01', 'closed_02' ],
    },
    filler => "
  orientation 1.0 0.0 0.0 0.0
  bitmap NULL
",
    filler_old => "
  orientation 1.0 0.0 0.0 0.0
  wirecolor 0.694118 0.580392 0.101961
  multimaterial 20
    Dirt
    Obscuring
    Grass
    Stone
    Wood
    Water
    Nonwalk
    Transparent
    Carpet
    Metal
    Puddles
    Swamp
    Mud
    Leaves
    Lava
    BottomlessPit
    DeepWater
    Door
    Snow
    Sand
  ambient 0.588 0.588 0.588
  diffuse 0.705882 0.0 1.0
  specular 0.0 0.0 0.0
  selfillumcolor 0.0 0.0 0.0
  bitmap NULL
"
  };
}

# walkmesh materials
use constant WOK_DIRT           => 1;
use constant WOK_OBSCURING      => 2;
use constant WOK_GRASS          => 3;
use constant WOK_STONE          => 4;
use constant WOK_WOOD           => 5;
use constant WOK_WATER          => 6;
use constant WOK_NONWALK        => 7;
use constant WOK_TRANSPARENT    => 8;
use constant WOK_CARPET         => 9;
use constant WOK_METAL          => 10;
use constant WOK_PUDDLES        => 11;
use constant WOK_SWAMP          => 12;
use constant WOK_MUD            => 13;
use constant WOK_LEAVES         => 14;
use constant WOK_LAVA           => 15;
use constant WOK_BOTTOMLESSPIT  => 16;
use constant WOK_DEEPWATER      => 17;
use constant WOK_DOOR           => 18;
use constant WOK_SNOW           => 19;
use constant WOK_SAND           => 20;

###############################################################################
#
###############################################################################
sub detect_format {
  my ($file) = @_;

  my ($fh, $test);

  if (!MDLOpsM::File::exists($file) ||
      !MDLOpsM::File::open(\$fh, '<', $file)) {
    return undef;
  }
  my $is_binary = 0;
  read $fh, $test, 8;
  if ($test =~ /^bwm v1.0$/i) {
    $is_binary = 1;
  }
  MDLOpsM::File::close($fh);
  return $is_binary;
}

sub detect_type {
  my ($file) = @_;

  if ($file =~ /wok(?:\.ascii)?$/i) {
    return 'wok';
  } elsif ($file =~ /dwk(?:\.ascii)?$/i) {
    return 'dwk';
  } elsif ($file =~ /pwk(?:\.ascii)?$/i) {
    return 'pwk';
  }

  return undef;
}

###############################################################################
#
###############################################################################
sub non_walk {
  my ($material) = @_;

  if ($material == WOK_NONWALK ||
      $material == WOK_OBSCURING ||
      $material == WOK_SNOW ||
      $material == WOK_TRANSPARENT ||
      $material == WOK_DEEPWATER ||
      # bottomless pit is actually walkable in 104pera.wok
      #$material == WOK_BOTTOMLESSPIT ||
      # following is logical, but unused in vanilla
      $material == WOK_LAVA) {
    return 1;
  }

  return 0;
}

###############################################################################
#
###############################################################################
sub readasciiwalkmesh {
  my ($file, $options) = @_;

  my ($fh, $lines);

  my $walkmesh = {
    header => {},
    verts  => [],
    faces  => [],
    types  => [],
  };

  # the extra data that will make our calculations easier
  my $extra = {
    vertfaces => {}
  };

  if (!MDLOpsM::File::exists($file) ||
      !MDLOpsM::File::open(\$fh, '<', $file)) {
    die sprintf('error: file does not exist or not readable: %s: %s', $file, $!);
  }

  $lines = [ <$fh> ];
  MDLOpsM::File::close($fh);

  my $parsing = {
    node => 0,
    vertices => 0,
    faces => 0,
    roomlinks => 0
  };
  my $face_data = [];
  my $room_links = {};

  if (scalar(grep { /(?:^|\s+)node.*dwk_wg_/i } @{$lines}) > 1 &&
      !defined($options->{walkmesh_name})) {
    #print Dumper([grep { /(?:^|\s+)node.*dwk_wg_/i } @{$lines}]);
    my $walkmeshes = {
      closed => readasciiwalkmesh($file, { walkmesh_name => 'wg_closed' }),
      open1  => readasciiwalkmesh($file, { walkmesh_name => 'wg_open1'  }),
      open2  => readasciiwalkmesh($file, { walkmesh_name => 'wg_open2'  }),
    };
    $walkmeshes->{closed}{header}{dwk_type} = 'closed';
    $walkmeshes->{open1}{header}{dwk_type}  = 'open1';
    $walkmeshes->{open2}{header}{dwk_type}  = 'open2';
    $walkmeshes->{closed}{header}{points} = [
      (map {$walkmeshes->{closed}{header}{position}[$_] +
           $walkmeshes->{closed}{header}{closed_01}[$_]} keys @{$walkmeshes->{closed}{header}{closed_01}}),
      (map {$walkmeshes->{closed}{header}{position}[$_] +
           $walkmeshes->{closed}{header}{closed_02}[$_]} keys @{$walkmeshes->{closed}{header}{closed_02}}),
      @{$walkmeshes->{closed}{header}{closed_01}},
      @{$walkmeshes->{closed}{header}{closed_02}}
    ];
    $walkmeshes->{open1}{header}{points} = [
      (map {$walkmeshes->{open1}{header}{closed_01}[$_] - $walkmeshes->{open1}{header}{position}[$_]} keys @{$walkmeshes->{open1}{header}{closed_01}}),
      @{$walkmeshes->{open1}{header}{open1_01}},
      @{$walkmeshes->{open1}{header}{closed_01}},
      #(map {$walkmeshes->{open1}{header}{position}[$_] - ($walkmeshes->{closed}{header}{position}[$_] +
      #     $walkmeshes->{open1}{header}{closed_01}[$_]) - $walkmeshes->{open1}{header}{position}[$_]} keys @{$walkmeshes->{open1}{header}{closed_01}}),
      (map {$walkmeshes->{open1}{header}{position}[$_] +
           $walkmeshes->{open1}{header}{open1_01}[$_]} keys @{$walkmeshes->{open1}{header}{open1_01}}),
    ];
    $walkmeshes->{open2}{header}{points} = [
      (map {$walkmeshes->{open2}{header}{closed_02}[$_] - $walkmeshes->{open2}{header}{position}[$_]} keys @{$walkmeshes->{open2}{header}{closed_01}}),
      @{$walkmeshes->{open2}{header}{open2_01}},
      @{$walkmeshes->{open2}{header}{closed_02}},
      #(map {$walkmeshes->{open2}{header}{position}[$_] +
      #     $walkmeshes->{open2}{header}{closed_02}[$_]} keys @{$walkmeshes->{open2}{header}{closed_02}}),
      (map {$walkmeshes->{open2}{header}{position}[$_] +
           $walkmeshes->{open2}{header}{open2_01}[$_]} keys @{$walkmeshes->{open2}{header}{open2_01}}),
    ];
    return $walkmeshes;
  }

  # basic parsing of the pertinent ascii walkmesh data
  for my $line (@{$lines}) {
    # get node
    if (!$parsing->{node} &&
        $line =~ /(?:^|\s+)node (?:trimesh|aabb)\s+(\S+)/i) {
      $walkmesh->{header}{name} = $1;
      if (defined($options->{walkmesh_name}) &&
          !($walkmesh->{header}{name} =~ /$options->{walkmesh_name}/i)) {
        next;
      }
      $walkmesh->{header}{format} = 'BWM V1.0';
      $walkmesh->{header}{type_readable} = detect_type($file);
      $walkmesh->{header}{type} = 0;
      if ($walkmesh->{header}{type_readable} eq 'wok') {
        $walkmesh->{header}{type} = 1;
      }
      $parsing->{node} = 1;
      next;
    } elsif (!$parsing->{node}) {
      next;
    }
    # get position
    if ($line =~ /(?:^|\s+)position\s+([-e.\d]+)\s+([-e.\d]+)\s+([-e.\d]+)/i) {
      $walkmesh->{header}{position} = [ $1, $2, $3 ];
      next;
    }
    # get vertices
    if (!$parsing->{vertices} &&
        $line =~ /(?:^|\s+)verts\s+(\d+)/) {
      $parsing->{vertices} = int($1);
      next;
    }
    if ($parsing->{vertices} &&
        $line =~ /([-e.\d]+)\s+([-e.\d]+)\s+([-e.\d]+)/i) {
      # add the vertex to the list
      $walkmesh->{verts} = [
        @{$walkmesh->{verts}}, [ $1, $2, $3 ]
      ];
      $parsing->{vertices} -= 1;
      next;
    }
    # get faces and types (material)
    if (!$parsing->{faces} &&
        $line =~ /(?:^|\s+)faces\s+(\d+)/) {
      $parsing->{faces} = int($1);
      next;
    }
    if ($parsing->{faces} &&
        $line =~ /^\s+?(\d+)\s+(\d+)\s+(\d+)(?:\s+\d+){4}\s+(\d+)/) {
      $face_data = [ @{$face_data}, [ $1, $2, $3, $4 ] ];
      $parsing->{faces} -= 1;
      next;
    }
    if (!$parsing->{roomlinks} &&
        $line =~ /(?:^|\s+)roomlinks\s*(\d+?)?/i) {
      $parsing->{roomlinks} = defined($1) ? int($1) : 'endlist';
      next;
    }
    if ($parsing->{roomlinks} &&
        $line =~ /(?:^|\s+)(\d+)\s+(\d+)/) {
      $room_links->{$1} = int($2);
      if ($parsing->{roomlinks} ne 'endlist') {
        $parsing->{roomlinks} -= 1;
      }
      next;
    }
    if ($parsing->{roomlinks} &&
        $line =~ /(?:^|\s+)endlist/i) {
      $parsing->{roomlinks} = 0;
      next;
    }
    if ($line =~ /(?:^|\s+)endnode/i) {
      $parsing->{node} = 0;
      #$parsing->{vertices} = 0;
      #$parsing->{faces} = 0;
      next;
    }
  }

  if (!defined($walkmesh->{header}{name})) {
    # error, no node was found
    die "no walkmesh name found";
  }
  if (!defined($walkmesh->{header}{position})) {
    # error, no position was found
    die "no walkmesh position found";
  }

  # walkmesh valid enough, parse the ascii hook point dummies for pwk/dwk
  if ($walkmesh->{header}{type_readable} ne 'wok') {
    for my $line (@{$lines}) {
      # read hook position dummy nodes for pwk/dwk
      if (!$parsing->{hook} &&
          $line =~ /(?:^|\s+)node dummy\s+(\S+)/i) {
        # try to match type-specific hook points w/ dummy name
        for my $hook (@{$info->{hooks}{$walkmesh->{header}{type_readable}}}) {
          if ($1 =~ /$hook$/i) {
            $parsing->{hook} = $hook;
            last;
          }
        }
        next;
      }
      # get hook position
      if (defined($parsing->{hook}) &&
          $line =~ /(?:^|\s+)position\s+(-?[.\d]+)\s+(-?[.\d]+)\s+(-?[.\d]+)/i) {
        $walkmesh->{header}{$parsing->{hook}} = [ $1, $2, $3 ];
        next;
      }
      # clear hook parsing state
      if (defined($parsing->{hook}) &&
          $line =~ /(?:^|\s+)endnode/i) {
        delete $parsing->{hook};
      }
    }
  }
  # parsing finished, move face & material data into place

  # weld the mesh
  my $used_keys = {};
  # map original vertex indices => new vertex indices
  my $vert_index_map = {};
  # boolean for whether welding action is needed
  my $weld_needed = 0;
  for my $vert_index (0..scalar(@{$walkmesh->{verts}}) - 1) {
    # get xyz position as a single string for hash key
    my $vert_pos = sprintf(
      '%.4g,%.4g,%.4g',
      @{$walkmesh->{verts}[$vert_index]}
    );
    if (defined($used_keys->{$vert_pos})) {
      # this means there is a location with multiple vertices
      $weld_needed = 1;
      # set original vertex index = the one new vertex at same location
      # also take into account that the new vert might be a redirection
      $vert_index_map->{$vert_index} = $vert_index_map->{$used_keys->{$vert_pos}};
      next;
    }
    $vert_index_map->{$vert_index} = scalar(keys %{$used_keys});
    $extra->{verts_by_pos}{$vert_pos} = [ scalar(keys %{$used_keys}) ];
    $used_keys->{$vert_pos} = $vert_index;
  }
  if ($weld_needed) {
    # take the original vert index => new vert index map,
    # and translate it into a sorted, unique list of new vert indices
    my $vert_index_map_inv = [
      sort { $a <=> $b } values %{{
        map { $vert_index_map->{$_} => $_ }
        sort { $b <=> $a }
        keys %{$vert_index_map}
      }}
    ];
    # rewrite vertex indices in faces
    for my $face_index (0..scalar(@{$face_data}) - 1) {
      $face_data->[$face_index] = [
        (map { $vert_index_map->{$_} } @{$face_data->[$face_index]}[0..2]),
        $face_data->[$face_index][3]
      ];
    }
    # rewrite vertices
    $walkmesh->{verts} = [
      @{$walkmesh->{verts}}[@{$vert_index_map_inv}]
    ];
  }
  undef $used_keys;
  undef $vert_index_map;

  # sort non-walk faces to the end of the list, then split off the types
  $face_data = [
    (grep { !&non_walk($_->[3]) } @{$face_data}),
    (grep { &non_walk($_->[3]) } @{$face_data})
  ];
  #print Dumper($face_data);die;
  for my $face (@{$face_data}) {
    $walkmesh->{faces} = [
      @{$walkmesh->{faces}}, [ @{$face}[0..2] ]
    ];
    $walkmesh->{types} = [
      @{$walkmesh->{types}}, $face->[3]
    ];
    # construct the adjacency map of vert index => face indices
    if (!defined($extra->{vertfaces}{$face->[0]})) {
      $extra->{vertfaces}{$face->[0]} = [];
    }
    if (!defined($extra->{vertfaces}{$face->[1]})) {
      $extra->{vertfaces}{$face->[1]} = [];
    }
    if (!defined($extra->{vertfaces}{$face->[2]})) {
      $extra->{vertfaces}{$face->[2]} = [];
    }
    $extra->{vertfaces}{$face->[0]} = [ @{$extra->{vertfaces}{$face->[0]}},
                                        scalar(@{$walkmesh->{faces}}) - 1 ];
    $extra->{vertfaces}{$face->[1]} = [ @{$extra->{vertfaces}{$face->[1]}},
                                        scalar(@{$walkmesh->{faces}}) - 1 ];
    $extra->{vertfaces}{$face->[2]} = [ @{$extra->{vertfaces}{$face->[2]}},
                                        scalar(@{$walkmesh->{faces}}) - 1 ];
  }
  undef $face_data;

  # calculate the rest of the values

  # calculate the face normals
  $walkmesh->{normals} = [];
  for my $face (@{$walkmesh->{faces}}) {
    my ($v1, $v2, $v3) = (
      $walkmesh->{verts}[$face->[0]],
      $walkmesh->{verts}[$face->[1]],
      $walkmesh->{verts}[$face->[2]]
    );
    my $normal_vector = [
      ($v2->[1] - $v1->[1]) * ($v3->[2] - $v1->[2]) - ($v2->[2] - $v1->[2]) * ($v3->[1] - $v1->[1]),
      ($v2->[2] - $v1->[2]) * ($v3->[0] - $v1->[0]) - ($v2->[0] - $v1->[0]) * ($v3->[2] - $v1->[2]),
      ($v2->[0] - $v1->[0]) * ($v3->[1] - $v1->[1]) - ($v2->[1] - $v1->[1]) * ($v3->[0] - $v1->[0])
    ];
    my $normal_factor = sqrt($normal_vector->[0]**2 +
                             $normal_vector->[1]**2 +
                             $normal_vector->[2]**2);
    if ($normal_factor == 0) {
      $normal_factor = 1;
    }
    $normal_vector = [ map { $_ / $normal_factor } @{$normal_vector} ];
    $walkmesh->{normals} = [
      @{$walkmesh->{normals}},
      [ @{$normal_vector} ]
    ];
  }

  # calculate the face plane coefficients
  $walkmesh->{plane_distances} = [];
  for my $index (0..scalar(@{$walkmesh->{faces}}) - 1) {
    # scalar product: normal vector dot v1
    my ($normal, $v1) = (
      $walkmesh->{normals}[$index],
      $walkmesh->{verts}[$walkmesh->{faces}[$index][0]]
    );
    $walkmesh->{plane_distances} = [
      @{$walkmesh->{plane_distances}},
      -1.0 * ($normal->[0] * $v1->[0] + $normal->[1] * $v1->[1] + $normal->[2] * $v1->[2])
    ];
  }

  # everything below is for wok walkmesh only, not dwk or pwk
  if (!$walkmesh->{header}{type}) {
    return $walkmesh;
  }

  # calculate the face adjacency for walkable faces
  $walkmesh->{adjacent_faces} = [];
  my $adjacency_matrix = {};
  for my $index (0..scalar(@{$walkmesh->{faces}}) - 1) {
    if (&non_walk($walkmesh->{types}[$index])) {
      last;
    }
    # map of global face number/index => adjacency list number/index
    # this structure would be necessary if we had walk faces mixed
    # with non-walk faces, rather than following convention of all
    # non-walk at the end
    $adjacency_matrix->{$index} = scalar(keys(%{$adjacency_matrix}));
  }
  for my $index (0..scalar(@{$walkmesh->{faces}}) - 1) {
    if (&non_walk($walkmesh->{types}[$index])) {
      last;
    }
    # get vertex positions for each face vertex, suitable as keys into verts_by_pos
    my $fv_pos = [
      sprintf('%.4g,%.4g,%.4g', @{$walkmesh->{verts}->[$walkmesh->{faces}[$index][0]]}),
      sprintf('%.4g,%.4g,%.4g', @{$walkmesh->{verts}->[$walkmesh->{faces}[$index][1]]}),
      sprintf('%.4g,%.4g,%.4g', @{$walkmesh->{verts}->[$walkmesh->{faces}[$index][2]]}),
    ];
    # construct a reduced list of faces connected to each vert,
    # constrain list to only walkable faces
    my $vfs = [
      { map { $_ => 1 }
        grep { !&non_walk($walkmesh->{types}[$_]) && $_ != $index }
          map { @{$_} } @{$extra->{vertfaces}}{@{$extra->{verts_by_pos}{$fv_pos->[0]}}} },
      { map { $_ => 1 }
        grep { !&non_walk($walkmesh->{types}[$_]) && $_ != $index }
          map { @{$_} } @{$extra->{vertfaces}}{@{$extra->{verts_by_pos}{$fv_pos->[1]}}} },
      { map { $_ => 1 }
        grep { !&non_walk($walkmesh->{types}[$_]) && $_ != $index }
          map { @{$_} } @{$extra->{vertfaces}}{@{$extra->{verts_by_pos}{$fv_pos->[2]}}} },
    ];
#    my $vfs = [
#      { map { $_ => 1 }
#        grep { $walkmesh->{types}[$_] != WOK_NONWALK && $_ != $index }
#          @{$extra->{vertfaces}{$walkmesh->{faces}[$index][0]}} },
#      { map { $_ => 1 }
#        grep { $walkmesh->{types}[$_] != WOK_NONWALK && $_ != $index }
#          @{$extra->{vertfaces}{$walkmesh->{faces}[$index][1]}} },
#      { map { $_ => 1 }
#        grep { $walkmesh->{types}[$_] != WOK_NONWALK && $_ != $index }
#          @{$extra->{vertfaces}{$walkmesh->{faces}[$index][2]}} }
#    ];
    my $results = [];
    for (my $i = 0; $i < 3; $i++) {
      my $result = -1;
      foreach (keys %{$vfs->[$i]}) {
        my $next = $i == 2 ? -2 : 1;
        if ($vfs->[$i + $next]{$_}) {
          # this is getting us the adjacent face,
          # but we need to know *which* edge in the other face,
          # and then add 3*face# + 0|1|2 to get an edge-in-adjacent-face number
          # $_ is a face number, but we need to know what edge in that face
          my $fv_pos = [
            sprintf('%.4g,%.4g,%.4g', @{$walkmesh->{verts}->[$walkmesh->{faces}[$_][0]]}),
            sprintf('%.4g,%.4g,%.4g', @{$walkmesh->{verts}->[$walkmesh->{faces}[$_][1]]}),
            sprintf('%.4g,%.4g,%.4g', @{$walkmesh->{verts}->[$walkmesh->{faces}[$_][2]]}),
          ];
          my $test = [
#            [ grep { $_ == $index } @{$extra->{vertfaces}{$walkmesh->{faces}[$_][0]}} ],
#            [ grep { $_ == $index } @{$extra->{vertfaces}{$walkmesh->{faces}[$_][1]}} ],
#            [ grep { $_ == $index } @{$extra->{vertfaces}{$walkmesh->{faces}[$_][2]}} ]
            [ grep { $_ == $index } map { @{$_} } @{$extra->{vertfaces}}{@{$extra->{verts_by_pos}{$fv_pos->[0]}}} ],
            [ grep { $_ == $index } map { @{$_} } @{$extra->{vertfaces}}{@{$extra->{verts_by_pos}{$fv_pos->[1]}}} ],
            [ grep { $_ == $index } map { @{$_} } @{$extra->{vertfaces}}{@{$extra->{verts_by_pos}{$fv_pos->[2]}}} ],
          ];
          $result = 3 * $adjacency_matrix->{$_};
          if (scalar(@{$test->[0]}) && scalar(@{$test->[1]})) {
            # edge #1 in adjacent face
            $result += 0;
            #print "$index $i $_ 1\n";
          }
          if (scalar(@{$test->[1]}) && scalar(@{$test->[2]})) {
            # edge #2 in adjacent face
            $result += 1;
            #print "$index $i $_ 2\n";
          }
          if (scalar(@{$test->[2]}) && scalar(@{$test->[0]})) {
            # edge #3 in adjacent face
            $result += 2;
            #print "$index $i $_ 3\n";
          }
        }
      }
      $results = [ @{$results}, $result ];
    }
    $walkmesh->{adjacent_faces} = [
      @{$walkmesh->{adjacent_faces}}, [ @{$results} ]
    ]
  }
  #print scalar(@{$walkmesh->{adjacent_faces}}) , "\n";
  #print Dumper($walkmesh->{adjacent_faces}) , "\n";

  # calculate perimetric walkable edge loops, build out the perimeters at the same time
  # we won't have a way to do room adjacency until we start looking at multiple models
  # and/or module (are/lyt?) files
  $walkmesh->{edge_loops} = [];
  $walkmesh->{perimeters} = [];
  $extra->{edges} = [];
  my $perimeter_count = 0;
  for my $face_index (0..scalar(@{$walkmesh->{adjacent_faces}}) - 1) {
    for my $edge_index (0..scalar(@{$walkmesh->{adjacent_faces}[$face_index]}) - 1) {
      my $next = $edge_index == 2 ? 0 : $edge_index + 1;
      if ($walkmesh->{adjacent_faces}[$face_index][$edge_index] == -1) {
        $extra->{edges} = [
          @{$extra->{edges}},
          {
            face => $face_index,
            enum => $edge_index,
            edge => $face_index * 3 + $edge_index,
            v1   => $walkmesh->{faces}[$face_index][$edge_index],
            v2   => $walkmesh->{faces}[$face_index][$next],
          }
        ];
      }
    }
  }
  my $edge_index = 0;
  my $last_edge_vert = undef;
  while (scalar(@{$extra->{edges}})) {
    if (!defined($last_edge_vert)) {
      # if no last vert, use this one
      $walkmesh->{edge_loops} = [
        @{$walkmesh->{edge_loops}},
        [ $extra->{edges}[$edge_index]{edge},
          (defined($room_links->{$extra->{edges}[$edge_index]{edge}})
             ? $room_links->{$extra->{edges}[$edge_index]{edge}} : -1) ]
      ];
      $last_edge_vert = $extra->{edges}[$edge_index]{v2};
      $perimeter_count += 1;
      splice @{$extra->{edges}}, $edge_index, 1;
      $edge_index = 0;
      next;
    } elsif ($extra->{edges}[$edge_index]{v1} == $last_edge_vert) {
      # if last vert, find next edge on this loop
      $walkmesh->{edge_loops} = [
        @{$walkmesh->{edge_loops}}, [
          $extra->{edges}[$edge_index]{edge},
          # adjacent room (from module .lyt file list)
          (defined($room_links->{$extra->{edges}[$edge_index]{edge}})
             ? $room_links->{$extra->{edges}[$edge_index]{edge}} : -1)
        ]
      ];
      $last_edge_vert = $extra->{edges}[$edge_index]{v2};
      $perimeter_count += 1;
      splice @{$extra->{edges}}, $edge_index, 1;
      $edge_index = 0;
      next;
    } elsif ($edge_index == scalar(@{$extra->{edges}}) - 1) {
      # if last vert and last edge, loop is closed
      $walkmesh->{perimeters} = [
        @{$walkmesh->{perimeters}}, $perimeter_count
      ];
      undef $last_edge_vert;
      $edge_index = 0;
      next;
    }
    $edge_index += 1;
  }
  # write the final perimeter
  $walkmesh->{perimeters} = [
    @{$walkmesh->{perimeters}}, $perimeter_count
  ];

  # calculate the AABB tree
  $walkmesh->{aabbs} = [];
  aabb($walkmesh, [ (0..(scalar(@{$walkmesh->{faces}}) - 1)) ]);
  #printf("aabb: %u\n", scalar(@{$walkmesh->{aabbs}}));

  return $walkmesh;
}

###############################################################################
# Unstable sorting algorithm used by AABB tree construction to produce results
# closer to vanilla.
#
###############################################################################
sub face_shell_sort {
  my ($index, $faces, $centroids) = @_;
  # a is list of indexes we want to sort based on centroids[a][index] value comparison
  my @a = @{$faces};
  my ($h, $i, $j, $k);

  for ($h = @a; $h = int $h / 2;) {
  #for ($h = @a; $h = int $h / 1.5;) {
    #print "$h\n";
    for my $i ($h .. scalar(@a) - 1) {
      my $j = $i;
      my $temp = $a[$i]; # temp is indices h..end
      #while ($j >= $h && $centroids->[$a[$j - $h]][$index] >= $centroids->[$temp][$index]) {
      while ($j >= $h && $centroids->[$a[$j - $h]][$index] > $centroids->[$temp][$index]) {
        $a[$j] = $a[$j - $h];
        $j -= $h;
      }
      $a[$j] = $temp;
    }
  }

  return @a;
}

###############################################################################
# AABB tree construction from face list, for creating binary walkmesh
#
###############################################################################
sub aabb {
  my ($walkmesh, $faces, $centroids, $parent_split) = @_;

  # this is past a leaf, should not happen
  if (!scalar(@{$faces})) {
    return -1;
  }
#  print "\n";

  # 0-base array index of this tree node
  my $tree_index = scalar(@{$walkmesh->{aabbs}});

  if (!defined($centroids)) {
    # generate face centroid list for reuse throughout tree construction
    $centroids = [];
    for my $index (@{$faces}) {
      my $face_centroid = [ 0.0, 0.0, 0.0 ];
      my $face = $walkmesh->{faces}[$index];
      for my $vert (@{$face}) {
        my $vertex = $walkmesh->{verts}[$vert];
        # add values to face centroid
        map { $face_centroid->[$_] += $vertex->[$_] } (0..2);
      }
      $face_centroid = [ map { $_ / 3 } @{$face_centroid} ];
      $centroids = [ @{$centroids}, [ @{$face_centroid} ] ];
    }
  }

  # bounding box calculation structure
  my $bb = {
    min => [  100000.0,  100000.0,  100000.0 ],
    max => [ -100000.0, -100000.0, -100000.0 ],
    #min => [  0,  0,  0 ],
    #max => [ -0, -0, -0 ],
    centroids => $centroids,
  };

  my $norms = {};
  # calculate bounding box min/max/center coordinates
  for my $index (@{$faces}) {
    my $face = $walkmesh->{faces}[$index];
    for my $vert (@{$face}) {
      my $vertex = $walkmesh->{verts}[$vert];
      # get minimum vertex value for x, y, z
      #map { $bb->{min}[$_] = $bb->{min}[$_] > $vertex->[$_] ? $vertex->[$_] + 0.01 : $bb->{min}[$_] } (0..2);
      map { $bb->{min}[$_] = $bb->{min}[$_] > $vertex->[$_] ? $vertex->[$_] : $bb->{min}[$_] } (0..2);
      # get maximum vertex value for x, y, z
      #map { $bb->{max}[$_] = $bb->{max}[$_] < $vertex->[$_] ? $vertex->[$_] + 0.01 : $bb->{max}[$_] } (0..2);
      map { $bb->{max}[$_] = $bb->{max}[$_] < $vertex->[$_] ? $vertex->[$_] : $bb->{max}[$_] } (0..2);
    }
    $norms->{$index} = &face_normal(
      @{$walkmesh->{verts}}[@{$walkmesh->{faces}[$index]}]
    );
  }

  # the aabb node for this point in the tree
  my $node = [ @{$bb->{min}}, @{$bb->{max}}, -1, 4, 0, -1, -1 ];
  $walkmesh->{aabbs} = [ @{$walkmesh->{aabbs}}, $node ];

  # handle a leaf node, the easy case
  if (scalar(@{$faces}) == 1) {
    # set the face index for this tree node
    $node->[6] = $faces->[0];
    return $tree_index;
  }

  # use bounding box size to determine axis upon which to divide the tree
  # also referred to as extents in center-extents representation
  $bb->{size} = [ map { $bb->{max}[$_] - $bb->{min}[$_] } (0..2) ];

  $parent_split = defined($parent_split) ? $parent_split : 0;
  my $split_axis = $parent_split;
  if ($bb->{size}[0] > 0.0) {
    $split_axis = 0;
  }
  if ($bb->{size}[1] > $bb->{size}[0]) {
    $split_axis = 1;
  }
  if ($bb->{size}[2] > $bb->{size}[1] &&
      $bb->{size}[2] > $bb->{size}[0]) {
    $split_axis = 2;
  }

  $printall and print
    "$tree_index " .
    join(', ', @{$bb->{min}}). "  " .
    join(', ', @{$bb->{max}}). "  " .
    join(', ', @{$bb->{size}}). "\n";

  # sort centroids for median selection
  my $sorted = [
    sort {
      #if ($bb->{centroids}[$a][1] + $walkmesh->{plane_distances}[$a] < $bb->{centroids}[$b][1] + $walkmesh->{plane_distances}[$b])
      #{ return -1 }
      #elsif ($bb->{centroids}[$a][1] + $walkmesh->{plane_distances}[$a] > $bb->{centroids}[$b][1] + $walkmesh->{plane_distances}[$b])
      #{ return 1 }
      if ($bb->{centroids}[$a][$split_axis] < $bb->{centroids}[$b][$split_axis])
      { return -1 }
      elsif ($bb->{centroids}[$a][$split_axis] > $bb->{centroids}[$b][$split_axis])
      { return 1 }
#      my $sum_a = 0.0;
#      map { $sum_a += $bb->{centroids}[$a][$_] } (0..2);
#      my $sum_b = 0.0;
#      map { $sum_b += $bb->{centroids}[$b][$_] } (0..2);
#      if ($sum_a > $sum_b) { return -1; }
#      if ($sum_a < $sum_b) { return 1; }
      #if ($bb->{centroids}[$a][$parent_split] < $bb->{centroids}[$b][$parent_split])
      #{ return -1 }
      #elsif ($bb->{centroids}[$a][$parent_split] > $bb->{centroids}[$b][$parent_split])
      #{ return 1 }
      #return $b <=> $a;
      return 0;
    } @{$faces},
  ];

  $printall and print
    "$tree_index " .
    "$split_axis " .
    join(',', @{$sorted}[0..int(scalar(@{$sorted}) / 2) - 1]).
    "  |  ".
    join(',', @{$sorted}[int(scalar(@{$sorted}) / 2)..scalar(@{$sorted}) - 1]).
    "\n";

  #$sorted = [ face_shell_sort($split_axis, $sorted, $bb->{centroids}) ];
  #$sorted = [ face_shell_sort($split_axis, [ sort @{$faces} ], $bb->{centroids}) ];
  $sorted = [ face_shell_sort($split_axis, $faces, $bb->{centroids}) ];

  $printall and print
    "$tree_index " .
    "$split_axis " .
    join(',', @{$sorted}[0..int(scalar(@{$sorted}) / 2) - 1]).
    "  |  ".
    join(',', @{$sorted}[int(scalar(@{$sorted}) / 2)..scalar(@{$sorted}) - 1]).
    "\n";

  print "$tree_index split: $split_axis, parentsplit: $parent_split\n" if $printall;

  my $lists = {
    left  => [],
    right => [],
  };
  my $found_split = 0;
  my $tested_axes = 1;
  my $median_index_pos = int(scalar(@{$sorted}) / 2);
  #print Dumper($sorted);
#  printf "split index: %u\n", $sorted[$median_index_pos];
  my $left_adj = 1;
  my $right_adj = 0;
  my $negative_axis = 0;

  $lists->{left} = [ @{$sorted}[0..$median_index_pos - 1] ];
  $lists->{right} = [ @{$sorted}[$median_index_pos..scalar(@{$sorted}) - 1] ];
  #$lists->{left} = [ @{$sorted}[0..$median_index_pos - $left_adj] ];
  #$lists->{right} = [ @{$sorted}[$median_index_pos+$right_adj..scalar(@{$sorted}) - 1] ];

  my $left_bbmin = [  1000.0,  1000.0,  1000.0 ];
  my $left_bbmax = [ -1000.0, -1000.0, -1000.0 ];
  my $right_bbmin = [  1000.0,  1000.0,  1000.0 ];
  my $right_bbmax = [ -1000.0, -1000.0, -1000.0 ];
  for my $index (@{$lists->{left}}) {
    my $face = $walkmesh->{faces}[$index];
    for my $vert (@{$face}) {
      my $vertex = $walkmesh->{verts}[$vert];
      # get maximum vertex value for x, y, z
      $left_bbmin = [ map { $left_bbmin->[$_] > $vertex->[$_] ? $vertex->[$_] : $left_bbmin->[$_] } (0..2) ];
      $left_bbmax = [ map { $left_bbmax->[$_] < $vertex->[$_] ? $vertex->[$_] : $left_bbmax->[$_] } (0..2) ];
    }
  }
  for my $index (@{$lists->{right}}) {
    my $face = $walkmesh->{faces}[$index];
    for my $vert (@{$face}) {
      my $vertex = $walkmesh->{verts}[$vert];
      # get maximum vertex value for x, y, z
     $right_bbmin = [ map { $right_bbmin->[$_] > $vertex->[$_] ? $vertex->[$_] : $right_bbmin->[$_] } (0..2) ];
     $right_bbmax = [ map { $right_bbmax->[$_] < $vertex->[$_] ? $vertex->[$_] : $right_bbmax->[$_] } (0..2) ];
    }
  }
  my $result = [ map { (($right_bbmax->[$_] + $right_bbmin->[$_]) / 2.0) - (($left_bbmin->[$_] + $left_bbmax->[$_]) / 2.0) } (0..2) ];
  #my $result = [ map { ($right_bbmax->[$_] - $left_bbmax->[$_]) + ($right_bbmin->[$_] - $left_bbmin->[$_]) } (0..2) ];
  #my $result = [ map { $right_bbmax->[$_] - $left_bbmax->[$_] } (0..2) ];
  my $max = 0.0;
  $printall and print "cdiff " . Dumper($result);

  $printall and print
    "$tree_index " .
    "left: " .
    join(', ', @{$left_bbmin}) .
    join(', ', @{$left_bbmax}) .
    join(', ', map {$left_bbmax->[$_] - $left_bbmin->[$_]} (0..2) ) .
    "\n";
  $printall and print
    "$tree_index " .
    "right: " .
    join(', ', @{$right_bbmin}) .
    join(', ', @{$right_bbmax}) .
    join(', ', map {$right_bbmax->[$_] - $right_bbmin->[$_]} (0..2) ) .
    "\n";
  $split_axis = $parent_split;
  $printall and print "$tree_index parent:$parent_split, computed: $node->[8]\n";
  foreach (0..2) {
    if (abs($result->[$_]) > $max) {
      $split_axis = $_;
      $max = abs($result->[$_]);
    }
  }
  $printall and print "$tree_index parent:$parent_split, computed: $node->[8]\n";
#  if ($max == 0.0 && scalar(@{$lists->{left}}) && scalar(@{$lists->{right}})) {
#    $result = [ map { $bb->{centroids}[$lists->{right}[0]][$_] - $bb->{centroids}[$lists->{left}[scalar(@{$lists->{left}}) - 1]][$_] } (0..2) ];
#    foreach (0..2) {
#      if (abs($result->[$_]) > $max) {
#        $split_axis = $_;
#        $max = abs($result->[$_]);
#      }
#    }
#  }
  if ($max > 0.0 && $result->[$split_axis] < 0.0) {
    $negative_axis = $split_axis + 3;
  }
  $node->[8] = 2**($negative_axis ? $negative_axis : $split_axis);
  $printall and print "$tree_index parent:$parent_split, computed: $node->[8]\n";
  #printf "%u %u %u\n", scalar(@{$lists->{left}}), scalar(@{$lists->{right}}), $median_index_pos;
  #print Dumper($lists);
  $found_split = 1;

  my $total_norms = [ 0, 0, 0 ];
  map { $total_norms->[0] += $_->[0]; $total_norms->[1] += $_->[1];$total_norms->[2] += $_->[2]; } values %{$norms};
#  print Dumper($total_norms);

  # recurse left and right, store returned child indices
  $node->[9]  = aabb($walkmesh, [ @{$lists->{left}} ], $centroids, $split_axis);
  $node->[10] = aabb($walkmesh, [ @{$lists->{right}} ], $centroids, $split_axis);

  my $left_idx = $node->[9];
  while ($left_idx != -1) {
    if ($walkmesh->{aabbs}[$left_idx][9] == -1) {
      last;
    }
    $left_idx = $walkmesh->{aabbs}[$left_idx][9];
  }
  my $right_idx = $node->[10];
  while ($right_idx != -1) {
    if ($walkmesh->{aabbs}[$right_idx][10] == -1) {
      last;
    }
    $right_idx = $walkmesh->{aabbs}[$right_idx][10];
  }
  if ($right_idx != -1 && $left_idx != -1) {
    #print "$left_idx $right_idx\n";
    #my $result = [ map { $walkmesh->{aabbs}[$right_idx][$_] - $walkmesh->{aabbs}[$left_idx][$_] } (3..5) ];
    my $result = [ map { ($walkmesh->{aabbs}[$right_idx][$_ + 3] - $walkmesh->{aabbs}[$left_idx][$_ + 3]) +
                         ($walkmesh->{aabbs}[$right_idx][$_] - $walkmesh->{aabbs}[$left_idx][$_]) } (0..2) ];
    my $max = 0.0;
    #print "maxdiff ";
    #print Dumper($result);
    foreach (0..2) {
      if (abs($result->[$_]) > $max) {
        $split_axis = $_;
        $max = abs($result->[$_]);
      }
    }
    if ($result->[$split_axis] < 0.0) {
      $negative_axis = $split_axis + 3;
    }
    $printall and print "$tree_index $node->[8] " . (2**($negative_axis ? $negative_axis : $split_axis))  . "\n";
    #$node->[8] = 2**($negative_axis ? $negative_axis : $split_axis);
    # does not seem to work as hoped... + ~20 wrong planes
  }

  return $tree_index;
}


###############################################################################
#
###############################################################################
sub face_normal {
  my ($v1, $v2, $v3) = @_;
  if (ref $v1 ne 'ARRAY' ||
      ref $v2 ne 'ARRAY' ||
      ref $v3 ne 'ARRAY') {
    # invalid, not enough verts given
    return [ 0.0, 0.0, 0.0 ];
  }
  return [
    $v1->[1] * ($v2->[2] - $v3->[2]) +
    $v2->[1] * ($v3->[2] - $v1->[2]) +
    $v3->[1] * ($v1->[2] - $v2->[2]),
    $v1->[2] * ($v2->[0] - $v3->[0]) +
    $v2->[2] * ($v3->[0] - $v1->[0]) +
    $v3->[2] * ($v1->[0] - $v2->[0]),
    $v1->[0] * ($v2->[1] - $v3->[1]) +
    $v2->[0] * ($v3->[1] - $v1->[1]) +
    $v3->[0] * ($v1->[1] - $v2->[1]),
  ];
}

###############################################################################
#
###############################################################################
sub readbinarywalkmesh {
  my ($file) = @_;

  my ($fh, $buffer, $unpacked);

  my $walkmesh = {
    header => {},
    verts  => [],
    faces  => [],
    types  => [],
  };

  if (!MDLOpsM::File::exists($file) ||
      !MDLOpsM::File::open(\$fh, '<', $file)) {
    die sprintf('error: file does not exist or not readable: %s: %s', $file, $!);
  }

  # set binary read mode and seek 0 just to be sure
  binmode $fh;
  seek($fh, 0, 0);

  # read the header
  read($fh, $buffer, $info->{sizes}{header});
  $unpacked = [ unpack($info->{templates}{header}, $buffer) ];
  # classify the header info
  $walkmesh->{header}{format}           = $unpacked->[0];
  $walkmesh->{header}{type}             = $unpacked->[1];
  $walkmesh->{header}{position}         = [ @{$unpacked}[14..16] ];
  $walkmesh->{header}{vert_num}         = $unpacked->[17];
  $walkmesh->{header}{vert_pos}         = $unpacked->[18];
  $walkmesh->{header}{face_num}         = $unpacked->[19];
  $walkmesh->{header}{face_pos}         = $unpacked->[20];
  $walkmesh->{header}{type_num}         = $unpacked->[19]; # 4B * number of faces
  $walkmesh->{header}{type_pos}         = $unpacked->[21];
  $walkmesh->{header}{normal_num}       = $unpacked->[19]; # 12B * number of faces
  $walkmesh->{header}{normal_pos}       = $unpacked->[22];
  $walkmesh->{header}{plane_distance_num} = $unpacked->[19]; # 4B * number of faces
  $walkmesh->{header}{plane_distance_pos} = $unpacked->[23];
  $walkmesh->{header}{aabb_num}         = $unpacked->[24]; # 2n - 1 (n = number of faces)
  $walkmesh->{header}{aabb_pos}         = $unpacked->[25];
  $walkmesh->{header}{unknown}          = $unpacked->[26];
  $walkmesh->{header}{adjacent_face_num} = $unpacked->[27]; # 12 byte values
  $walkmesh->{header}{adjacent_face_pos} = $unpacked->[28];
  $walkmesh->{header}{edge_loop_num}    = $unpacked->[29]; # 8B values
  $walkmesh->{header}{edge_loop_pos}    = $unpacked->[30];
  $walkmesh->{header}{perimeter_num}    = $unpacked->[31]; # 4B values
  $walkmesh->{header}{perimeter_pos}    = $unpacked->[32];

#print Dumper([ @{$unpacked}[2..13] ]);
  $walkmesh->{header}{type_readable} = detect_type($file);
  if ($walkmesh->{header}{type_readable} eq 'pwk') {
    # read the use01 and use02 points
    $walkmesh->{header}{use01} = [ @{$unpacked}[2..4] ];
    $walkmesh->{header}{use02} = [ @{$unpacked}[5..7] ];
  }
  if ($walkmesh->{header}{type_readable} eq 'dwk') {
    # read the use01 and use02 points
    # find subtype
    if ($file =~ /^.+(\d).*$/) {
      if ($1 == 0) {
        $walkmesh->{header}{dwk_type} = 'closed';
        $walkmesh->{header}{closed_01} = [ @{$unpacked}[8..10] ];
        $walkmesh->{header}{closed_02} = [ @{$unpacked}[11..13] ];
      } elsif ($1 == 1) {
        $walkmesh->{header}{dwk_type} = 'open1';
        $walkmesh->{header}{open1_01} = [ @{$unpacked}[5..7] ];
      } elsif ($1 == 2) {
        $walkmesh->{header}{dwk_type} = 'open2';
        $walkmesh->{header}{open2_01} = [ @{$unpacked}[5..7] ];
      }
    }
  }

  # read each data type
  for my $data_type ('vert', 'face', 'type', 'normal', 'plane_distance', 'aabb', 'adjacent_face', 'edge_loop', 'perimeter') {
    my $num_key         = $data_type . '_num';
    my $pos_key         = $data_type . '_pos';
    my $plural          = $data_type . 's';
    my $numper          = $info->{sizes}{$data_type} / 4;
    my $template        = defined($info->{templates}{$data_type}) ? $info->{templates}{$data_type} x $walkmesh->{header}{$num_key} : 'f*';

    $walkmesh->{$plural} = [];
    if ($walkmesh->{header}{$num_key} < 1) {
      next;
    }
    seek($fh, $walkmesh->{header}{$pos_key}, 0);
    read($fh, $buffer, $walkmesh->{header}{$num_key} * $info->{sizes}{$data_type});
    $unpacked = [ unpack($template, $buffer) ];
    for my $num (0..$walkmesh->{header}{$num_key} - 1) {
      $walkmesh->{$plural} = [
        @{$walkmesh->{$plural}},
        ($numper > 1
           ? [ @{$unpacked}[($num * $numper)..(($num * $numper) + ($numper - 1))] ]
           : $unpacked->[$num])
      ];
    }
  }
  MDLOpsM::File::close($fh);

#print Dumper($walkmesh->{header});
#print Dumper($walkmesh);
#die;
  return $walkmesh;
}


###############################################################################
#
###############################################################################
sub writeasciiwalkmesh {
  my ($file, $walkmesh, $options) = @_;

  my ($fh);

  if (!MDLOpsM::File::open(\$fh, '>', $file)) {
    die sprintf('error: file not writable: %s', $!);
  }

  if (defined($walkmesh->{closed}) && defined($walkmesh->{open1})) {
    # write out combined dwk for 3 inputs
    $options->{model} = sprintf('%s_DWK', uc $options->{model});
    for my $dwk_type ('closed', 'open1', 'open2') {
      printf(
        $fh "node trimesh md_DWK_wg_%s\n" .
        "  parent %s\n  position % .7g % .7g % .7g%s",
        $dwk_type,
        $options->{model},
        @{$walkmesh->{$dwk_type}{header}{position}},
        $info->{filler}
      );
      printf(
        $fh "verts %u\n  %s\n",
        scalar(@{$walkmesh->{$dwk_type}{verts}}),
        join("\n  ", map { sprintf('% .7g % .7g % .7g', @{$_}) } @{$walkmesh->{$dwk_type}{verts}})
      );
      printf(
        $fh "faces %u\n  %s\n",
        scalar(@{$walkmesh->{$dwk_type}{faces}}),
        join("\n  ", map {
          sprintf('%u %u %u 1 0 0 0 %u',
                  @{$walkmesh->{$dwk_type}{faces}[$_]},
                  $walkmesh->{$dwk_type}{types}[$_])
        } (0..scalar(@{$walkmesh->{$dwk_type}{faces}}) - 1))
      );
      print $fh "endnode\n";

      # write out door walkmesh dummies
      for my $hook (@{$info->{hooks}{dwk}}) {
        if (!defined($walkmesh->{$dwk_type}{header}{$hook})) {
          next;
        }
        printf(
          $fh "node dummy %s\n" .
          "  parent %s\n  position % .7g % .7g % .7g\n" .
          "endnode\n",
          'md_DWK_dp_' . $hook, $options->{model},
          @{$walkmesh->{$dwk_type}{header}{$hook}}
        );
      }
    }
  } else {
    # write out wok or pwk
    printf(
      $fh "node trimesh %s_wg\n" .
      "  parent %s%s\n  position % .7g % .7g % .7g%s",
      $options->{model},
      $options->{model},
      ($options->{extension} eq 'pwk' ? '_' . $options->{extension} : ''),
      @{$walkmesh->{header}{position}},
      $info->{filler}
    );
    printf(
      $fh "verts %u\n  %s\n",
      scalar(@{$walkmesh->{verts}}),
      join("\n  ", map { sprintf('% .7g % .7g % .7g', @{$_}) } @{$walkmesh->{verts}})
    );
    printf(
      $fh "faces %u\n  %s\n",
      scalar(@{$walkmesh->{faces}}),
      join("\n  ", map {
        sprintf('%u %u %u 1 0 0 0 %u',
                @{$walkmesh->{faces}[$_]},
                $walkmesh->{types}[$_])
      } (0..scalar(@{$walkmesh->{faces}}) - 1))
    );
    if ($walkmesh->{header}{type}) {
      my $links = [ grep { $_->[1] != -1 } @{$walkmesh->{edge_loops}} ];
      if (scalar(@{$links})) {
        printf(
          $fh "roomlinks %u\n  %s\n",
          scalar(@{$links}),
          join("\n  ", map {
            sprintf('%u %u', @{$_})
          } (@{$links}))
        );
      }
    }
    print $fh "endnode\n";

    # write out placeable walkmesh dummies
    for my $hook (@{$info->{hooks}{pwk}}) {
      if (!defined($walkmesh->{header}{$hook})) {
        next;
      }
      printf(
        $fh "node dummy %s\n" .
        "  parent %s_%s\n  position % .7g % .7g % .7g\n" .
        "endnode\n",
        'pwk_' . $hook,
        $options->{model}, $options->{extension},
        @{$walkmesh->{header}{$hook}}
      );
    }
  }

  MDLOpsM::File::close($fh);
}

###############################################################################
#
###############################################################################
sub writebinarywalkmesh {
  my ($file, $walkmesh) = @_;

  my ($fh);

  if (!MDLOpsM::File::open(\$fh, '>', $file)) {
    die sprintf('error: file not writable: %s', $!);
  }

  # set binary write mode
  binmode $fh;

  # write the header
  print($fh pack('A[8]', $walkmesh->{header}{format}));
  print($fh pack('L', $walkmesh->{header}{type}));
  if ($walkmesh->{header}{type}) {
    # wok file
    print($fh pack('f[12]', 0 x 12));
  } elsif ($walkmesh->{header}{type_readable} eq 'pwk') {
    # pwk file
    print($fh pack('f[12]',
      defined($walkmesh->{header}{use01}) ? @{$walkmesh->{header}{use01}} : (0, 0, 0),
      defined($walkmesh->{header}{use02}) ? @{$walkmesh->{header}{use02}} : (0, 0, 0),
      0 x 6
    ));
  } elsif ($walkmesh->{header}{type_readable} eq 'dwk') {
    # dwk file
    print($fh pack('f[12]',
      defined($walkmesh->{header}{points}) ? @{$walkmesh->{header}{points}} : (0 x 12),
    ));
  }
  print($fh pack('f[3]', @{$walkmesh->{header}{position}}));
  my $data_position = $info->{sizes}{header};
  print($fh pack('LL', scalar(@{$walkmesh->{verts}}), $data_position));
  $data_position += scalar(@{$walkmesh->{verts}}) * $info->{sizes}{vert};
  print($fh pack('LL', scalar(@{$walkmesh->{faces}}), $data_position));
  $data_position += scalar(@{$walkmesh->{faces}}) * $info->{sizes}{face};
  print($fh pack('L', $data_position));
  $data_position += scalar(@{$walkmesh->{faces}}) * $info->{sizes}{type};
  print($fh pack('L', $data_position));
  $data_position += scalar(@{$walkmesh->{faces}}) * $info->{sizes}{normal};
  print($fh pack('L', $data_position));
  $data_position += scalar(@{$walkmesh->{faces}}) * $info->{sizes}{plane_distance};
  if ($walkmesh->{header}{type}) {
    # wok file
    print($fh pack('LL', scalar(@{$walkmesh->{aabbs}}), $data_position));
    $data_position += scalar(@{$walkmesh->{aabbs}}) * $info->{sizes}{aabb};
    print($fh pack('L', 0));
    print($fh pack('LL', scalar(@{$walkmesh->{adjacent_faces}}), $data_position));
    $data_position += scalar(@{$walkmesh->{adjacent_faces}}) * $info->{sizes}{adjacent_face};
    print($fh pack('LL', scalar(@{$walkmesh->{edge_loops}}), $data_position));
    $data_position += scalar(@{$walkmesh->{edge_loops}}) * $info->{sizes}{edge_loop};
    print($fh pack('LL', scalar(@{$walkmesh->{perimeters}}), $data_position));
  } else {
    # pwk or dwk file
    print($fh pack('LLLLLLLLL', 0 x 9));
  }

  # write the vertices
  print($fh pack('f*', map { @{$_} } @{$walkmesh->{verts}}));
  # write the faces
  print($fh pack('L*', map { @{$_} } @{$walkmesh->{faces}}));
  # write the types
  print($fh pack('L*', @{$walkmesh->{types}}));
  # write the face normals
  print($fh pack('f*', map { @{$_} } @{$walkmesh->{normals}}));
  # write the face planar distances
  print($fh pack('f*', @{$walkmesh->{plane_distances}}));

  if (!$walkmesh->{header}{type}) {
    return;
  }

  # write the aabb tree array
  print($fh map { pack($info->{templates}{aabb}, @{$_}) } @{$walkmesh->{aabbs}});
  # write the walkable face adjacency
  print($fh pack('l*', map { @{$_} } @{$walkmesh->{adjacent_faces}}));
  # write the perimetric edge loops
  print($fh pack('l*', map { @{$_} } @{$walkmesh->{edge_loops}}));
  # write the perimeter edge count
  print($fh pack('l*', @{$walkmesh->{perimeters}}));

  MDLOpsM::File::close($fh);
}

1;

#^L
###############################################################################
# MDLOps File Operations,
# exists to handle the funhouse that is perl with Unicode filenames on Windows
###############################################################################
package MDLOpsM::File;
use strict;
use warnings;
# package conditionally includes Win32 constants so we must do this:
no strict 'subs';

BEGIN {
  require Exporter;
  use vars qw(@ISA @EXPORT @EXPORT_OK %EXPORT_TAGS $VERSION $win32);
  $VERSION = '0.1.0';
  @EXPORT = qw(open exists);
  @ISA = qw(Exporter);

  use FileHandle;
  use Encode;
  $win32 = 1;
  #use Win32API::File qw(:ALL);
  eval 'use Win32API::File qw(:ALL);';
  if ($@) {
    $win32 = 0;
  }
}

use Data::Dumper;

our $win32_handles = {};

sub close {
  my ($fh) = @_;

  if ($win32) {
    $fh->flush();
    my $fd = fileno($fh);
    if (defined($win32_handles->{$fd})) {
      CloseHandle($win32_handles->{$fd});
      delete $win32_handles->{$fd};
    }
  }
  return close($fh);
}

sub open {
  my ($fh, $mode, $filename, $noerror) = @_;
  if ($win32) {
    # win32 support for unicode wide characters in file/path names
    # we are only supporting two mode profiles, the ones we use,
    # read (must exist) or write (truncate if exist)
    #my $winmode = FILE_READ_DATA;
    my $winmode = FILE_GENERIC_READ;
    my $svShare = FILE_SHARE_READ;
    my $uCreate = OPEN_EXISTING;
    my $uFlags = 0;
    my $openmode = 'r';
    if ($mode =~ />/) {
      #$winmode = FILE_WRITE_DATA;
      #print "write_dat: $winmode\n";
      $winmode = FILE_GENERIC_WRITE;
      #print "write_generic: $winmode\n";
      $svShare = FILE_SHARE_READ;
      #$uCreate = TRUNCATE_EXISTING();
      #print "trunc_ex: $uCreate\n";
      #$uCreate = OPEN_ALWAYS;
      $uCreate = CREATE_ALWAYS;
      #print "trunc_ex: $uCreate\n";
      # non-buffered IO on the windows native filehandle
      #$uFlags = FILE_FLAG_WRITE_THROUGH;
      $uFlags = 0;
      $openmode = 'w';
    }
    # create windows filehandle
    my $native_fh = Win32API::File::CreateFileW(
      encode('utf16-le', $filename . "\0"),
      $winmode, $svShare, [], $uCreate, $uFlags, []
    );
    if (!$native_fh) {
      !$noerror and print "File Error: $filename $^E\n";
      return 0;
    }
    # get perl filehandle for windows filehandle
    my $perl_fh = FileHandle->new;
    if (OsFHandleOpen($perl_fh, $native_fh, $openmode)) {
      # make write handles autoflush, non-buffered IO
      #if ($openmode =~ /w/i) {
      #  $perl_fh->autoflush(1);
      #}
      # someone has to hold this reference (or the file closes),
      # so why not do that here...
      my $fd = fileno($perl_fh);
      $win32_handles->{$fd} = $native_fh;
      # set filehandle reference that was passed in
      ${$fh} = $perl_fh;
      return 1;
    } else {
      !$noerror and print "File Error: $filename $!\n";
      CloseHandle($native_fh);
    }
  } else {
    #print "not win32: $filename\n";
    return open(${$fh}, $mode, $filename);
  }

  return 0;
}

sub exists {
  my ($filename) = @_;

  if (!$win32) {
    #print "not win32\n";
    return -f $filename;
  }
  #print "$filename\n";
  my $fh = 0;
  if (&open(\$fh, '<', $filename, 1)) {
    &close($fh);
    return 1;
  }
  return 0;
}

1;
