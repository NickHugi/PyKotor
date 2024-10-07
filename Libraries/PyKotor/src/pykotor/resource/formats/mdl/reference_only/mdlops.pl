#!/usr/bin/env perl
#
###########################################################
# mdlops.pl version 1.0.2
# Copyright (C) 2004 Chuck Chargin Jr. (cchargin@comcast.net)
#
# (With some changes by JdNoa (jdnoa@hotmail.com) between
# November 2006 and May 2007.)
#
# (With some more changes by VarsityPuppet and Fair Strides
# (tristongoucher@gmail.com) during January 2016.)
#
# (With a lot more changes by ndix UR during 2016-2018.)
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
#			    Reworked calculations of face, vertex normals, plane distances, adjacent faces
#			    Added tangent space calculations
#			    Added emitter and finished light node support
#			    Added walkmesh support (DWK/PWK/WOK)
#			    Added lightsaber mesh support and conversion
#			    Added bezier controller support and fixed existing controller list
#			    Added normalization of vertex data into MDX form
#			    Added detection of real smoothgroups
#			    Added reference node support
#			    Fixed replacer for many cases
#			    Unicode path/filename support
#			    Many more small fixes and features
#
# January, 2017:        Version 1.0.1
#			    Fixed compression and decompression of quaternions
#			    Fixed axis-angle to quaternion conversion
#			    Fixed walkmesh use point encoding, off-by-one
#			    Fixed ascii walkmesh node naming
#			    Fixed walkmesh compatibility with mdledit/kmax
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
# MUCH MUCH thanks to JdNoa for her cracking of the compressed quaternion format
#
# Thanks to my testers:
#   T7nowhere
#   Svosh
#   Seprithro
#   ChAiNz.2da
#
# file browser dialog added by tk102
#
# Thanks to all at Holowan Laboratories for your input
# and support.
#
# usage:
# command line usage of perl scripts:
# NOTE: you must first copy the MDLOpsM.pm file into your \perl\lib directory
# perl mdlops.pl [-a] [-s] [-k1|-k2] c:\directory\model.mdl
# OR
# perl mdlops.pl [-a] [-s] [-k1|-k2] c:\directory\*.mdl
#
# command line usage of the compiled perl script: 
# mdlops.exe [-a] [-s] [-k1|-k2] c:\directory\model.mdl
# OR
# mdlops.exe [-a] [-s] [-k1|-k2] c:\directory\*.mdl
# 
# For the command line the following switches can be used:
# -a will skip extracting animations
# -s will convert skin to trimesh
# -k1 will output a binary model in kotor 1 format
# -k2 will output a binary model in kotor 2 format
# 
# NOTE: The script automatically detects the type
#       of model.
#
# NOTE: For binary models you must have the .MDL and .MDX
#       in the same directory
#
# NOTE: For importing models with supermodels, the supermodel .MDL 
#       must be in the same directory.
#
# 1) In a command prompt: perl mdlops.pl OR double click mdlops.exe
# 2) click 'select file'
# 3) browse to directory that has your .mdl file.
#    Select the .mdl and click 'open'
# 4) To quickly convert the model click 'Read and write model'
#    NOTE: The script will automatically detect the model type.
# 5) If you started with a binary file (ex. model.mdl) then the
#    resulting ascii model will be model-ascii.mdl
# 6) If you started with an ascii file (ex. model.mdl) then the
#    resulting binary model will be model-bin.mdl
#
# What is this? (see readme for more info)
# 
# This is a Perl script for converting
# Star Wars Knights of the Old Republic (kotor for short)
# binary models to ascii and back again.
#
# Binary models are converted to an ascii format compatible
# with NeverWinter Nights.
# 
# Features:
# -Automatic detection of model type
# -Automatic detection of model version (kotor 1 or kotor 2)
# -works with trimesh models
# -works with dangly mesh models
# -works with skin mesh models
# -works with emitters, lights, reference nodes
# -works with all known node and model types
# -replacer: lets you replace a trimesh in binary model with a trimesh from an ascii model
# -renamer: lets you rename textures in a binary model
# 
# read the "Quick tutorial.txt" for a quick and dirty
# explanation of how to get your models into kotor
#
# Dedicated to Cockatiel
#

# source file contains utf8 characters
use utf8;
# mdlops prints utf8 characters to stdout
binmode STDOUT, ":utf8";

# Command line usage help:
sub usage {
 print sprintf("
MDLOps is a KotOR Model Operations utility providing compile/decompile

usage: %s [options]

compile/decompile options:
  -k1                           Compile binary model for KotOR1
  -k2                           Compile binary model for KotOR2:TSL
  --walkmesh                    Process a walkmesh also if it exists

binary => ascii:
  -a, --no-anim                 Do NOT extract animations from binary model
  --smoothgroups                Compute smoothgroup numbers from binary model
  --weld                        Weld model
  -s, --convert-skin            Convert skin nodes to trimesh
  --no-convert-saber            Disable lightsaber mesh conversion
  --convert-bezier              Convert bezier animation controllers to linear
  --use-ascii-extension         Use ascii file extension instead of filename

ascii => binary:
  --head                        Head model, use head fix
  --no-validate                 Assume vertex object data is consistent
  --weight VALUE                Use weighted averaging for normals
                                Value: 'area', 'angle', 'none', or 'both'
  --crease                      Use crease angle test to add smooth group separation
  --crease-angle                Crease angle to use, in degrees, default: %u\x{00B0}

replacer options:
  --replacer                    Use Taina's replacer mode
  --bmdl MODEL                  Binary MDL file to use
  --bmesh NAME                  Name of mesh to replace in binary model
  --amdl MODEL                  ASCII Text MDL file to replace from
  --amesh NAME                  Name of mesh to inject into binary model

options:
  --help, -h                    Show this information
  --verbose, -v                 Verbose output
", (split /\//, $0)[-1], $mdl_opts->{creaseangle}
  );
  die;
}

use strict;
no strict 'subs';

BEGIN {
  # conditional loading allows us to use this script on
  # non-windows machines w/o Tk installed.
  eval 'use Tk;';
  eval 'use Tk::Tree;';
  eval 'use Tk::Photo;';
  eval 'use Tk::FileDialog;';

  # for file browser added by tk102, thanks tk102!
  eval 'use Win32::FileOp qw(:DIALOGS :_DIALOGS);';
  if ($@) {
    # non-windows, declare this dummy method
    sub OpenDialog {}
  }
  # stupid windows shells don't do globbing!
  eval 'use Win32::Autoglob;';
  #$ENV{PERL_JSON_BACKEND}='JSON::backportPP';
  # non-core Perl package needed for conf file
  eval 'use JSON;';
}

use MDLOpsM;          # special forces? or just a Perl script?
use Getopt::Long;
use Math::Trig;

#eval 'use JSON;';
# required for configuration file, perl-core:
use File::Spec::Functions qw(canonpath);
use File::Basename;

use vars qw($VERSION $APPNAME);
$VERSION = '1.0.2';
$APPNAME = 'MDLOps';

#this holds all of the Tk objects
our %object;
#this holds the binary model
our $model1;
#this holds the ascii model (replacer only)
our $model2;

#our $reqversion = 'k2';
our $curversion = '';
our $mdl_opts = {
  extract_anims => 1, # 1 = yes extract animations, 0 = do not extract animations
  convertskin => 0,   # 1 = convert skin to trimesh, 0 = do not convert skin to trimesh
  convertbezier => 0, # 1 = convert bezier controllers to linear, 0 = export bezier controllers as is
  convertsaber => 1,  # 1 = convert saber to trimesh, 0 = do not convert saber to trimesh
  headfix => 0,       # 1 = link node root to neck_g, fixes head models, 0 = node root is root dummy
  weightarea => 1,
  weightangle => 0,
  usecrease => 0,
  creaseangle => 60,
  smoothgroups => 1,
  weld_model => 0,
  validateverts => 1,
  generateaabb => 1,
  use_asc_ext => 0,
  reqversion => 'k2',
  use_opt_file => 1,
  option_mode => 'readbinary',
};
our ($source, $sourcetext);
our $usegui;

#perl2exe_exclude MacPerl.pm
#perl2exe_include File/Glob
#perl2exe_include Tk
#perl2exe_include Tk/Tree
#perl2exe_include Tk/Photo
#perl2exe_include Tk/Frame
#perl2exe_include Tk/Radiobutton
#perl2exe_include Tk/Checkbutton
#perl2exe_include Tk/Scrollbar
#perl2exe_include Win32/FileOp
#perl2exe_include Win32/Autoglob
#perl2exe_include JSON
#perl2exe_include JSON/PP
#perl2exe_include JSON/Any
#perl2exe_include JSON/PP/Boolean
#perl2exe_include File/Spec
#perl2exe_include File/Basename
#perl2exe_include Encode
#perl2exe_include Win32API/File
#perl2exe_include Win32
#perl2exe_include "unicore/Heavy.pl";
#perl2exe_include "unicore/To/Fold.pl";
#perl2exe_include Carp/Heavy
#perl2exe_include Math/BigInt/Calc
#perl2exe_include Tie/Handle

#perl2exe_info ProductName=MDLOps
#perl2exe_info ProductVersion=1.0.2
#perl2exe_info FileDescription=MDLOps
#perl2exe_info FileVersion=1.0.2
#perl2exe_info Comment=MDLOps
#perl2exe_info InternalName=MDLOps
#perl2exe_info OriginalFilename=mldops.exe
#perl2exe_info LegalCopyright=Copyright (C) 2004 Chuck Chargin Jr. (cchargin@comcast.net)

our $help_text = [
  'Compiler / Decompiler:',
  'For binary models you must have the .mdl and .mdx in the same directory.',
  'Output files are written to the same directory as the source files.',
  "Corresponding walkmesh files will also be converted when found in same directory,\nbut only with 'Read and write model' button.",
  "Application state and options are saved in defaults.json file, to reset all settings to default, simply trash defaults.json.",
  'Options are provided primarily for compatibility, generally the defaults are the highest quality settings.',
];

my %opt;

Getopt::Long::Configure('bundling');
GetOptions(
  # cli replacer support
  'replacer'            => \$opt{replacer},
  'bmdl=s'              => \$opt{rep_binary_model},
  'bmesh=s@'            => \$opt{rep_binary_mesh},
  'amdl=s'              => \$opt{rep_ascii_model},
  'amesh=s@'            => \$opt{rep_ascii_mesh},
  # mdlops long-standing options
  'k=s'                 => \$opt{version},
  's|convert-skin'      => \$mdl_opts->{convertskin},
  'a|no-anim'           => \$opt{noanim},
  # mdlops new options
  'head'                => \$mdl_opts->{headfix},
  'weight:s'            => \$opt{weight},
  'crease'              => \$mdl_opts->{usecrease},
  'crease-angle:s'      => \$mdl_opts->{creaseangle},
  'convert-bezier'      => \$mdl_opts->{convertbezier},
  'no-validate'         => \$opt{novalidate},
  'no-convert-saber'    => \$opt{noconvertsaber},
  'use-ascii-extension' => \$mdl_opts->{use_asc_ext},
  'smoothgroups'        => \$opt{smoothgroups},
  'weld'                => \$mdl_opts->{weld_model},
  # basics
  'h|help'              => \$opt{help},
  'v|verbose'           => \$opt{verbose},
);
$opt{help} and usage();

#use Data::Dumper;
#print Dumper({ %opt });
#print Dumper([ @ARGV ]);

if ($ARGV[0] ne "" || $opt{replacer}) {
  # we have files given to command line or replacer requested, use CLI mode
  $usegui = "no";

  # translate our options into the values we need
  #$reqversion = $opt{version} == 1 ? 'k1' : 'k2';
  $mdl_opts->{reqversion} = $opt{version} == 1 ? 'k1' : 'k2';
  $mdl_opts->{extract_anims} = !$opt{noanim};
  $mdl_opts->{convertsaber}  = !$opt{noconvertsaber};
  $mdl_opts->{validateverts} = !$opt{novalidate};
  $mdl_opts->{smoothgroups}  = defined($opt{smoothgroups}) ? 1 : 0;
  if (defined($opt{weight})) {
    # area, angle, both, or off/false
    if ($opt{weight} eq '') {
      $opt{weight} = 'both';
    }
    if ($opt{weight} eq 'both') {
      $mdl_opts->{weightarea} = 1;
      $mdl_opts->{weightangle} = 1;
    } elsif ($opt{weight} eq 'area') {
      $mdl_opts->{weightarea} = 1;
      $mdl_opts->{weightangle} = 0;
    } elsif ($opt{weight} eq 'angle') {
      $mdl_opts->{weightarea} = 0;
      $mdl_opts->{weightangle} = 1;
    } elsif ($opt{weight} =~ /off/i ||
             $opt{weight} =~ /^f/i ||
             $opt{weight} =~ /^n/i) {
      $mdl_opts->{weightarea} = 0;
      $mdl_opts->{weightangle} = 0;
    }
  }

  # print summary of settings
  if ($opt{verbose} && !$mdl_opts->{extract_anims}) {
    print("Animations will not be extracted\n");
  }
  if ($opt{verbose} && $mdl_opts->{convertskin}) {
    print("Skins will be converted to trimesh\n");
  }
  if ($opt{verbose}) {
    print("binary will be kotor $opt{version}\n");
  }

  # run the replacer if requested
  if ($opt{replacer}) {
    &replacenodes_cli;
  }

  # process the files
  my $counter = 0;
  foreach (@ARGV) {
    my $fname = $_;
    printf("working on model %u: %s\n", $counter++, $fname);
    &doit($fname);
  }
  print("$counter models processed\n");
} else {
  # no files given to command line, so fire up the GUI
  $usegui = "yes";

  # read saved default settings and state
  my $file_opts = &defaults_read();
  if (defined($file_opts->{use_opt_file})) {
    if ($file_opts->{use_opt_file}) {
      # restore settings is requested
      #$mdl_opts = $file_opts;
      # use a simple merge, in case of version change, options added, etc.
      for my $okey (keys %{$file_opts}) {
        if (!defined($file_opts->{$okey})) {
          next;
        }
        $mdl_opts->{$okey} = $file_opts->{$okey};
      }
    } else {
      # user has saved their desire to not restore settings...
      $mdl_opts->{use_opt_file} = 0;
    }
  }

  $object{'main'} = MainWindow->new;
  $object{'main'}->resizable(0,0);
  $object{'main'}->configure(-title => "$APPNAME $VERSION");
  if (MDLOpsM::File::exists('icon.bmp')) {
    $object{'main'}->iconimage(
      $object{'main'}->Photo(-file => "icon.bmp", -format => 'bmp')
    );
  }
  
  our ($maxwidth, $maxheight) = $object{'main'}->maxsize;

  $object{'helpbutton'} = $object{'main'}->Button(-text => "Help", -command => \&helpview);
  # model file picker
  $object{'browse'}=$object{'main'}->Button(-text=>"Select file", -command=>[\&browse_for_file, 'direntry']);
  $object{'direntry'} = $object{'main'}->Entry();
  # model actions
  $object{'readbutton'} = $object{'main'}->Button(-text=>"Read model", -command => \&readmodel);
  $object{'writebutton'} = $object{'main'}->Button(-text=>"Write model", -command => \&writemodel);
  $object{'readandwrite'} = $object{'main'}->Button(-text=>"Read and write model", -command => \&doit);
  $object{'viewdata'}=$object{'main'}->Button(-text=>"View data", -command=>\&viewdata);
  # extra tools
  $object{'openreplacer'}=$object{'main'}->Button(-text=>"Replacer", -command=>\&openreplacer);
  $object{'openrenamer'}=$object{'main'}->Button(-text=>"Renamer", -command=>\&openrenamer);
  # target game version
  $object{'gameversionlabel'} = $object{'main'}->Label(-text => 'Target Game:');
  $object{'versionk1'}=$object{'main'}->Radiobutton(
    -text=>"Kotor 1", 
    -value => 'k1',
    -indicatoron => 'false', 
    -command => [\&defaults_write, $mdl_opts],
    -variable => \$mdl_opts->{reqversion}
  );
  $object{'versionk2'}=$object{'main'}->Radiobutton(
    -text=>"Kotor 2", 
    -value => 'k2',
    -indicatoron => 'false', 
    -command => [\&defaults_write, $mdl_opts],
    -variable => \$mdl_opts->{reqversion}
  );
  # options frame, contains nav frame and options
  $object{'optionframe'} = $object{'main'}->Frame(
    -label => 'Options:', -labelPack => [ -anchor => 'w', -fill => 'none' ]
  );
  # options types navigation
  $object{'optionnavframe'} = $object{'optionframe'}->Frame();
  $object{'optbutreadbin'} = $object{'optionnavframe'}->Radiobutton(
    -text=>"Read Binary", 
    -command => \&showoptions,
    -value => 'readbinary',
    -indicatoron => 'false', 
    -variable => \$mdl_opts->{option_mode}
  );
  $object{'optbutwritebin'} = $object{'optionnavframe'}->Radiobutton(
    -text=>"Write Binary", 
    -command => \&showoptions,
    -value => 'writebinary',
    -indicatoron => 'false', 
    -variable => \$mdl_opts->{option_mode}
  );
  $object{'optbutreadasc'} = $object{'optionnavframe'}->Radiobutton(
    -text=>"Read ASCII", 
    -command => \&showoptions,
    -value => 'readascii',
    -indicatoron => 'false', 
    -variable => \$mdl_opts->{option_mode}
  );
  $object{'optbutwriteasc'} = $object{'optionnavframe'}->Radiobutton(
    -text=>"Write ASCII", 
    -command => \&showoptions,
    -value => 'writeascii',
    -indicatoron => 'false', 
    -variable => \$mdl_opts->{option_mode}
  );
  # options, by type
  # read binary
  $object{'animcheck'} = $object{'optionframe'}->Checkbutton(
    -text => "Extract animations",
    -command => [\&defaults_write, $mdl_opts],
    -variable => \$mdl_opts->{extract_anims}
  );
  $object{'smoothgroups'} = $object{'optionframe'}->Checkbutton(
    -text => "Compute smoothgroup numbers",
    -command => [\&defaults_write, $mdl_opts],
    -variable => \$mdl_opts->{smoothgroups}
  );
  $object{'weld_model'} = $object{'optionframe'}->Checkbutton(
    -text => "Weld model vertices (Remove doubles)",
    -command => [\&defaults_write, $mdl_opts],
    -variable => \$mdl_opts->{weld_model}
  );
  # write ascii
  # animcheck also here...
  $object{'skincheck'} = $object{'optionframe'}->Checkbutton(
    -text => "Convert skin to trimesh",
    -command => [\&defaults_write, $mdl_opts],
    -variable => \$mdl_opts->{convertskin}
  );
  $object{'convertbezier'} = $object{'optionframe'}->Checkbutton(
    -text => "Convert bezier animation controllers to linear",
    -command => [\&defaults_write, $mdl_opts],
    -variable => \$mdl_opts->{convertbezier}
  );
    $object{'convertsaber'} = $object{'optionframe'}->Checkbutton(
      -text => "Convert lightsaber to trimesh",
      -command => [\&defaults_write, $mdl_opts],
      -variable => \$mdl_opts->{convertsaber}
    );
    $object{'use_asc_ext'} = $object{'optionframe'}->Checkbutton(
      -text => "Use .ascii file extension",
      -command => [\&defaults_write, $mdl_opts],
      -variable => \$mdl_opts->{use_asc_ext}
    );
    # write binary
    $object{'headfix'} = $object{'optionframe'}->Checkbutton(
      -text => "Head model fix link to neck_g",
      -command => [\&defaults_write, $mdl_opts],
      -variable => \$mdl_opts->{headfix}
    );
    # read ascii
    $object{'validate'} = $object{'optionframe'}->Checkbutton(
      -text => "Force MDX-compatible vertex data",
      -command => [\&defaults_write, $mdl_opts],
      -variable => \$mdl_opts->{validateverts}
    );
    $object{'weightarea'} = $object{'optionframe'}->Checkbutton(
      -text => "Use area weighted vertex normal calculations",
      -command => [\&defaults_write, $mdl_opts],
      -variable => \$mdl_opts->{weightarea}
    );
    $object{'weightangle'} = $object{'optionframe'}->Checkbutton(
      -text => "Use angle weighted vertex normal calculations",
      -command => [\&defaults_write, $mdl_opts],
      -variable => \$mdl_opts->{weightangle}
    );
    $object{'generateaabb'} = $object{'optionframe'}->Checkbutton(
      -text => "Generate AABB tree instead of using tree from file",
      -command => [\&defaults_write, $mdl_opts],
      -variable => \$mdl_opts->{generateaabb}
    );
    $object{'usecrease'} = $object{'optionframe'}->Checkbutton(
      -text => "Separate smooth groups across sharp angles",
      -command => [\&defaults_write, $mdl_opts],
      -variable => \$mdl_opts->{usecrease}
    );
    $object{'creaseframe'} = $object{'optionframe'}->Frame();
    $object{'creaseangle'} = $object{'creaseframe'}->Entry(
      -width => 5,
      -validate => 'focusout',
      -validatecommand => \&valid_angle,
      -textvariable => \$mdl_opts->{creaseangle}
    );
    $object{'creaselabel'} = $object{'creaseframe'}->Label(-text => 'degrees, Sharp angle definition to use');
    $object{'creaseangle'}->pack(-side => 'left', -anchor => 'w');
    $object{'creaselabel'}->pack(-side => 'right', -anchor => 'e');

    # Lay out the interface elements into main window
    $object{helpbutton}->form(-r => '%100', -t => '%0', -rp => 10, -tp => 10);

    # target game version
    $object{gameversionlabel}->form(-l => '%0', -t => '%0', -lp => 10, -tp => 10);
    $object{'versionk1'}->form(-l => [$object{gameversionlabel}, 0],
                         -lp => 10,
                         -tp => 10,
                         -t => '%0');
    $object{'versionk2'}->form(-l => [$object{versionk1}, 0],
                         -lp => 20,
                         -tp => 10,
                         -t => '%0');

    # model file picker
    $object{'browse'}->form (-t => [$object{'versionk1'},0],
                           -b => [$object{'readbutton'},0],
                           -tp => 10,
                           -lp => 10,
                           -l => '%0');
    $object{'direntry'}->form(-t => [$object{'versionk1'},0],
                              -r => '%100',
                              -l => [$object{'browse'},0],
                              -b => [$object{'readbutton'},0],
                              -tp => 10,
                              -lp => 10,
                              -rp => 10);
    
    # model actions
    $object{'readbutton'}->form(
      -tp => 10,
      -lp => 10,
      -l => '%0',
      -b => [$object{'optionframe'},0]
    );
    $object{'writebutton'}->form(
      -tp => 10,
      -lp => 20,
      -l => [$object{'readbutton'},0],
      -b => [$object{'optionframe'},0]
    );
    $object{'readandwrite'}->form(
      -tp => 10,
      -lp => 20,
      -l => [$object{'writebutton'},0],
      -b => [$object{'optionframe'},0]
    );
    $object{'viewdata'}->form(
      -tp => 10,
      -lp => 20,
      -rp => 10,
      -l => [$object{'readandwrite'},0],
      -b => [$object{'optionframe'},0]
    );

    # option nav type items
    $object{optbutreadbin}->pack(-side => 'left', -anchor => 'n');
    $object{optbutwritebin}->pack(-side => 'left', -anchor => 'n');
    $object{optbutreadasc}->pack(-side => 'left', -anchor => 'n');
    $object{optbutwriteasc}->pack(-side => 'left', -anchor => 'n');
    # option nav frame
    $object{'optionnavframe'}->pack(-pady => 5);
    # populate options frame for selected type
    &showoptions();
    # option frame
    $object{'optionframe'}->form(-lp => 10,
                                 -bp => 5,
                                 -tp => 5,
                                 -b => '%100',
                                 -l => '%0');

    # extra functions, renamer and replacer
    $object{'openrenamer'}->form(
      -r => '%100',
      -l => [$object{optionframe}, 0],
      -t => [$object{'viewdata'},0],
      -lp => 10,
      -rp => 10,
      -tp => 10,
      -bp => 10
    );
    $object{'openreplacer'}->form(
      -r => '%100',
      -l => [$object{optionframe}, 0],
      -t => [$object{'openrenamer'},0],
      -lp => 10,
      -rp => 10,
      -bp => 10
    );

    # everything is placed, update & compute window size
    $object{'main'}->update;
    $object{'main'}->geometry(sprintf(
      '+%u+%u',
      ($maxwidth / 2) - ($object{'main'}->width / 2),
      ($maxheight / 2) - ($object{'main'}->height / 2)
    )); 

    # create the data viewer window and its objects
    $object{'dataviewwin'} = $object{'main'}->Toplevel('title' => "$APPNAME Data Viewer");

    $object{'thelist'} = $object{'dataviewwin'}->Scrolled('Tree',-itemtype => 'text',
                                                    -browsecmd => \&displaydata,
                                                    -scrollbars => 'se');

    $object{'hexdata'} = $object{'dataviewwin'}->Scrolled('Listbox', 
                                                  -scrollbars => 'e',
                                                  -font => 'systemfixed',
                                                  -width => 37);

    $object{'chardata'} = $object{'dataviewwin'}->Scrolled('Listbox',
                                                   -scrollbars => 'e',
                                                   -font => 'systemfixed',
                                                   -width => 20);

    $object{'cookeddata'} = $object{'dataviewwin'}->Scrolled('Listbox',
                                                     -scrollbars => 'e',
                                                     -font => 'systemfixed',
                                                     -width => 30);

    $object{'cookeddata'}->form(-t => '%0',
                                -r => '%100',
                                -b => '%100');

    $object{'chardata'}->form(-t => '%0',
                              -r => [$object{'cookeddata'},0],
                              -b => '%100');

    $object{'hexdata'}->form(-t => '%0',
                             -r => [$object{'chardata'},0], 
                             -b => '%100');

    $object{'thelist'}->form(-t => '%0', 
                             -l => '%0', 
                             -r => [$object{'hexdata'},0], 
                             -b => '%100');
    # the data viewer window has been built, now hide it
    $object{'dataviewwin'}->withdraw;
    # override the delete command so it hides the data viewer window
    $object{'dataviewwin'}->protocol('WM_DELETE_WINDOW', [\&withdrawwindow, 'dataviewwin']);

    #create the replacer model selection window
    $object{'repmodselwin'} = $object{'main'}->Toplevel('title' => 'Replacer: model select');
    $object{'repmodselwin'}->protocol('WM_DELETE_WINDOW', [\&withdrawwindow, 'repmodselwin']);
    $object{'repmodselwin'}->withdraw;
    $object{'binbrowse'}=$object{'repmodselwin'}->Button(-text=>"Binary model", 
                                                   -command=>[\&browse_for_file, 'binaryentry']);
    $object{'binaryentry'} = $object{'repmodselwin'}->Entry(-width => 40);
    $object{'ascbrowse'}=$object{'repmodselwin'}->Button(-text=>"Ascii model",
                                                   -command=>[\&browse_for_file, 'asciientry']);
    $object{'asciientry'} = $object{'repmodselwin'}->Entry(-width => 40);
    $object{'repread'} = $object{'repmodselwin'}->Button(-text=>"Read models",
                                                   -command => \&repreadmodel);

    $object{'binbrowse'}->form(-t => '%0',
                         -tp => 5,
             -l => '%0',
             -lp => 5);

    $object{'binaryentry'}->form(-t => '%0',
                           -tp => 10,
               -l => [$object{'binbrowse'},0],
               -lp => 10,
                     -r => '%100',
                     -rp => 5);

    $object{'ascbrowse'}->form(-t => [$object{'binbrowse'},0],
                         -tp => 10,
             -l => '%0',
             -lp => 5);

    $object{'asciientry'}->form(-t => [$object{'binbrowse'},0],
                          -tp => 15,
              -l => [$object{'ascbrowse'},0],
              -lp => 17,
                    -r => '%100',
                    -rp => 5);

    $object{'repread'}->form(-l => '%40',
                       -t => [$object{'asciientry'},0],
           -tp => 10,
                 -bp => 10);

    $object{'repmodselwin'}->update;
    $object{'repmodselwin'}->geometry(sprintf(
      '+%u+%u',
      ($maxwidth / 2) - ($object{'repmodselwin'}->width / 2),
      ($maxheight / 2) - ($object{'repmodselwin'}->height / 2)
    )); 

       
    # create replacer node selection window
    $object{'repnodeselwin'} = $object{'main'}->Toplevel('title' => 'Replacer: mesh select');
    $object{'repnodeselwin'}->protocol('WM_DELETE_WINDOW', [\&withdrawwindow, 'repnodeselwin']);
    $object{'repnodeselwin'}->withdraw;
    $object{'repnodebaselabel'}=$object{'repnodeselwin'}->Label(-text => 'Base model name:');
    $object{'repnodebaseentry'}=$object{'repnodeselwin'}->Entry(-width => 30);
    $object{'repnodereplace'}=$object{'repnodeselwin'}->Button(-text=>"Do it!",
                                                         -command=>\&replacenodes);
    $object{'repnodereptarg'}=$object{'repnodeselwin'}->Button(-text=>"Set replace target",
                                                         -command=>\&openreptargwin);
    $object{'replacelist'} = $object{'repnodeselwin'}->Scrolled('Listbox', 
                                                                -scrollbars => 'e',
                            -width => 40);

    $object{'replacelist'}->form (-l => '%0',
                            -lp => 10,
                -t => '%0',
                -tp => 10,
                -r => '%100',
                -rp => 10,
                -b => [$object{'repnodebaselabel'},0],
                      -bp => 10);

    $object{'repnodebaselabel'}->form(-l => '%0',
                                -lp => 10,
              -b => [$object{'repnodereplace'},0],
                                      -bp => 10);

    $object{'repnodebaseentry'}->form(-l => [$object{'repnodebaselabel'},0],
                                -lp => 10,
              -r => '%100',
              -rp => 10,
              -b => [$object{'repnodereplace'},0],
              -bp => 10);

    $object{'repnodereptarg'}->form(-l => '%0',
                              -lp => 10,
            -b => '%100',
            -bp => 10);
            
    $object{'repnodereplace'}-> form ( -l => [$object{'repnodereptarg'},0],
                                 -lp => 10,
                                 -b => '%100',
               -bp => 10);

    $object{'repnodeselwin'}->update;
    $object{'repnodeselwin'}->geometry(sprintf(
      '+%u+%u',
      ($maxwidth / 2) - 285,
      ($maxheight / 2) - ($object{'repnodeselwin'}->height / 2)
    )); 
           
    # create replacer target sub window
    $object{'repnodetargwin'} = $object{'main'}->Toplevel('title' => 'Replacer: target select');
    $object{'repnodetargwin'}->protocol('WM_DELETE_WINDOW', [\&withdrawwindow, 'repnodetargwin']);
    $object{'repnodetargwin'}->withdraw;
    $object{'targetselect'}=$object{'repnodetargwin'}->Button(-text=>"Select target",
                                                        -command=>\&targetselect);
    $object{'targetlist'} = $object{'repnodetargwin'}->Scrolled('Listbox', 
                                                                -scrollbars => 'e');

    $object{'targetselect'}->form(-l => '%35',
                            -b => '%100',
                                  -bp => 10);
                  
    $object{'targetlist'}-> form(-l => '%0',
                           -lp => 10,
               -r => '%100',
               -rp => 10,
               -t => '%0',
               -tp => 10,
                     -b => [$object{'targetselect'},0],
                     -bp => 10);

    $object{'repnodetargwin'}->update;
    $object{'repnodetargwin'}->geometry(sprintf(
      '+%u+%u',
      ($maxwidth / 2) + 15,
      ($maxheight / 2) - ($object{'repnodetargwin'}->height / 2)
    ));

    # create renamer window
    $object{'renamerwin'} = $object{'main'}->Toplevel('title' => 'Renamer');
    $object{'renamerwin'}->protocol('WM_DELETE_WINDOW', [\&withdrawwindow, 'renamerwin']);
    $object{'renamerwin'}->withdraw;
    $object{'renamernewnamelabel'}=$object{'renamerwin'}->Label(-text => 'New name:');
    $object{'renamernewname'}=$object{'renamerwin'}->Entry(-width => 30);
    $object{'renamerdoit'}=$object{'renamerwin'}->Button(-text=>"Change name",
                                                         -command=>\&renameit);
    $object{'renamerwrite'}=$object{'renamerwin'}->Button(-text=>"Write model",
                                                          -command=>\&writeit);
    $object{'renamerlist'} = $object{'renamerwin'}->Scrolled('Listbox', 
                                                             -scrollbars => 'e',
                                                             -width => 40);

    $object{'renamerlist'}->form (-l => '%0',
                            -lp => 10,
                -t => '%0',
                -tp => 10,
                -r => '%100',
                -rp => 10,
                -b => [$object{'renamernewnamelabel'},0],
                -bp => 10);

    $object{'renamernewnamelabel'}->form(-l => '%0',
                                -lp => 10,
              -b => [$object{'renamerdoit'},0],
                                      -bp => 10);

    $object{'renamernewname'}->form(-l => [$object{'renamernewnamelabel'},0],
                                -lp => 10,
              -r => '%100',
              -rp => 10,
              -b => [$object{'renamerdoit'},0],
              -bp => 10);

    $object{'renamerdoit'}->form(-l => '%0',
                              -lp => 10,
            -b => '%100',
            -bp => 10);

    $object{'renamerwrite'}->form(-l => [$object{'renamerdoit'},0],
                              -lp => 10,
            -b => '%100',
            -bp => 10);
          
    $object{'renamerwin'}->update;
    $object{'renamerwin'}->geometry(sprintf(
      '+%u+%u',
      ($maxwidth / 2) - ($object{'renamerwin'}->width / 2),
      ($maxheight / 2) - ($object{'renamerwin'}->height / 2)
    )); 
    
    MainLoop;
  }
  print("$APPNAME exiting!\n");
  exit 0;

  sub Tk::Error {
    # do nothing - get rid of most of the crap printed to stderr by the background error handler
    #use Data::Dumper;
    #print Dumper(@_);
    print "error handler\n";
  }

  # GUI: show the instructions/help window
  sub helpview {
    if ($object{'helpwin'}) {
      # window already exists, focus it
      $object{'helpwin'}->deiconify;
      $object{'helpwin'}->raise;
      return;
    }

    my ($maxwidth, $maxheight) = $object{'main'}->maxsize;

    # create help/usage/instructions window
    $object{'helpwin'} = $object{'main'}->Toplevel('title' => "$APPNAME Help");
    $object{'helpwin'}->protocol('WM_DELETE_WINDOW', [\&nukewindow, 'helpwin']);

    my $prev_obj;
    for my $index (keys @{$help_text}) {
      my $label = sprintf('helplabel%u', $index);
      my $top = '%0';
      my $bottom_padding = 0;
      if ($prev_obj) {
        # all but first text elements use previous element for top alignment
        $top = [$prev_obj, 0];
      }
      if ($index == scalar(@{$help_text}) - 1) {
        # put bottom padding on last text element
        $bottom_padding = 20;
      }
      $object{$label} = $object{'helpwin'}->Label(-text => $help_text->[$index], -justify => 'left');
      $object{$label}->form(
        -t => $top, -l => '%0',
        -lp => 20, -tp => 10, -rp => 20, -bp => $bottom_padding
      );
      $prev_obj = $object{$label};
    }

    $object{'helpwin'}->update;
    $object{'helpwin'}->geometry(sprintf(
      '+%u+%u',
      ($maxwidth / 2) - 285,
      ($maxheight / 2) - $object{'helpwin'}->height
    )); 
    $object{'helpwin'}->deiconify;
    #$object{'helpwin'}->raise;
  }

# validation for crease angle input
sub valid_angle {
  my ($input) = @_;
  if ($input =~ /[^0-9.]/) {
    return 0;
  }
  if ($input < 0 || $input > 360) {
    return 0;
  }
  return 1;
}

# GUI: handle navigation between option types in options frame
sub showoptions {
  my $opt_keys = [
    'animcheck', 'smoothgroups', 'weld_model',
    'skincheck', 'convertbezier', 'convertsaber', 'use_asc_ext',
    'headfix',
    'validate', 'generateaabb', 'weightarea', 'weightangle', 'usecrease', 'creaseframe'
  ];
  # unmap all options
  for my $key (@{$opt_keys}) {
    $object{$key}->packForget();
  }
  # pack the options corresponding to the selected type
  if ($mdl_opts->{option_mode} eq 'readbinary') {
    $object{animcheck}->pack(-side => 'top',-anchor => 'w');
    $object{smoothgroups}->pack(-side => 'top',-anchor => 'w');
    $object{weld_model}->pack(-side => 'top',-anchor => 'w');
  } elsif ($mdl_opts->{option_mode} eq 'writebinary') {
    $object{headfix}->pack(-side => 'top',-anchor => 'w');
  } elsif ($mdl_opts->{option_mode} eq 'readascii') {
    $object{validate}->pack(-side => 'top',-anchor => 'w');
    $object{generateaabb}->pack(-side => 'top', -anchor => 'w');
    $object{weightarea}->pack(-side => 'top',-anchor => 'w');
    $object{weightangle}->pack(-side => 'top',-anchor => 'w');
    $object{usecrease}->pack(-side => 'top',-anchor => 'w');
    $object{creaseframe}->pack(-side => 'top',-anchor => 'w');
  } elsif ($mdl_opts->{option_mode} eq 'writeascii') {
    $object{animcheck}->pack(-side => 'top',-anchor => 'w');
    $object{skincheck}->pack(-side => 'top',-anchor => 'w');
    $object{convertsaber}->pack(-side => 'top',-anchor => 'w');
    $object{convertbezier}->pack(-side => 'top',-anchor => 'w');
    $object{use_asc_ext}->pack(-side => 'top',-anchor => 'w');
  }
  &defaults_write($mdl_opts);
}

# read in a model
# This routine checks to see if the model is binary or ascii
# then it calls the correct extraction routine
sub readmodel {
  my $option = shift(@_);
  my $filepath = $object{'direntry'}->get;
  $model1 = undef;
  $model2 = undef;
  
  # do a little sanity checking
  if ($filepath eq "") { # the path box is empty!
    return &showerror(-2);
  } elsif (!MDLOpsM::File::exists($filepath)) { # the path does not exist!
    return &showerror(-3, $filepath);
  }

  print("-----------------------------------\n");

  $curversion = &modelversion($filepath);
  print("version: " . $curversion . "\n");

  if (&modeltype($filepath) eq "binary") {
    print ("model is binary\n");
    # load the model
    $model1 = &readbinarymdl($filepath, $mdl_opts->{extract_anims}, $curversion, {
      extract_anims => $mdl_opts->{extract_anims},
      compute_smoothgroups => $mdl_opts->{smoothgroups},
      weld_model => $mdl_opts->{weld_model}
    });
    print("building tree view\n");
    &buildtree($object{'thelist'}, $model1);  # populate the data view with the data
    # change the title of the window to show the model status
    $object{'main'}->configure(-title => "$APPNAME $VERSION $model1->{'name'} ($model1->{'source'} $curversion source)");
    # disable the version buttons
    #$object{'versionk1'}->configure(-state => 'disabled');
    #$object{'versionk2'}->configure(-state => 'disabled');
  } else {
    print("model is ascii\n");
    &cleardisplay;  # clear the data view and hide it, data view does not work with ascii files

    # load the model
    $model1 = &readasciimdl($filepath, 1, {
      validate_vertex_data  => $mdl_opts->{validateverts},
      weight_by_area        => $mdl_opts->{weightarea},
      weight_by_angle       => $mdl_opts->{weightangle},
      recalculate_aabb_tree => $mdl_opts->{generateaabb},
      use_crease_angle      => $mdl_opts->{usecrease},
      crease_angle          => defined($mdl_opts->{creaseangle}) ? deg2rad($mdl_opts->{creaseangle}) : undef
    });
    $object{'main'}->configure(-title => "$APPNAME $VERSION $model1->{'name'} ($model1->{'source'} source)");
    # enable the version buttons
    #$object{'versionk1'}->configure(-state => 'normal');
    #$object{'versionk2'}->configure(-state => 'normal');
  }

  # if the model could not be loaded we get a negative number back
  if ($model1 < 0) {
    return &showerror($model1);
  }

#  $object{'main'}->messageBox(-message => "Model $model1->{'name'} loaded from " . &modeltype($filepath) . " source.", 
#                       -title => "$APPNAME status", 
#           -type => 'OK');
  print("Finished reading model\n");
  print("-----------------------------------\n");
}

# write out a model
# The routine checks where the model came from (ascii or binary) then writes out
# the opposite type.  So, a model from ascii source will be written as a binary model.
sub writemodel {
  my $filepath = $object{'direntry'}->get;
  if (!defined($model1)) {
    return &showerror('You must read a model first!');
  }

  print("-----------------------------------\n");
  if ($model1->{'source'} eq "binary") {
    print ("model is from binary source, writing ascii model\n");
    &writeasciimdl(
      $model1, $mdl_opts->{convertskin}, $mdl_opts->{extract_anims}, {
        extract_anims => $mdl_opts->{extract_anims},
        convert_skin => $mdl_opts->{convertskin},
        convert_saber => $mdl_opts->{convertsaber},
        convert_bezier => $mdl_opts->{convertbezier},
        use_ascii_extension => $mdl_opts->{use_asc_ext},
      }
    );
  } else {
    print ("model is from ascii source, writing binary model\n");
    &writebinarymdl($model1, $mdl_opts->{reqversion}, {
      headfix => $mdl_opts->{headfix}
    });
  }
  print("Finished writing model\n");
  print("-----------------------------------\n");
}

# read in a model then write it out in the opposite format
# This routine checks to see if the model is ascii or binary
# then calls the correct routine to load the model.
# If the load completes then it calls the opposite write
# routine to write out the model.  So, if the selected
# is a binary model it will be loaded then written out
# in ascii format.
sub doit {
  # my $option = shift(@_);
  my $buffer;
  my $filepath;

  if ($usegui eq "yes") {
    $filepath = $object{'direntry'}->get;
  } else {
    $filepath = shift(@_);
  }
  
  $model1 = undef;
  $model2 = undef;
  
  # do some sanity checks
  if ($filepath eq "") { # the file box is empty!
    return &showerror(-2);
  } elsif (!MDLOpsM::File::exists($filepath)) { # the file does not exist!
    return &showerror(-3);
  }

  print("-----------------------------------\n");
  # determine model type and load it, then write out
  # the opposite format
  if (&modeltype($filepath) eq "binary") {
    $curversion = &modelversion($filepath);
    print ("reading binary model\n");
    $model1 = &readbinarymdl($filepath, $mdl_opts->{extract_anims}, $curversion, {
      extract_anims => $mdl_opts->{extract_anims},
      compute_smoothgroups => $mdl_opts->{smoothgroups},
      weld_model => $mdl_opts->{weld_model}
    });
    print ("writing ascii model\n");
    &writeasciimdl($model1, $mdl_opts->{convertskin}, $mdl_opts->{extract_anims}, {
      extract_anims  => $mdl_opts->{extract_anims},
      convert_skin   => $mdl_opts->{convertskin},
      convert_saber  => $mdl_opts->{convertsaber},
      convert_bezier => $mdl_opts->{convertbezier},
      use_ascii_extension => $mdl_opts->{use_asc_ext},
    });
    if ($usegui eq "yes") {
      print ("Building tree view\n");
      &buildtree($object{'thelist'}, $model1);
    }
  } else {
    print ("reading ascii model\n");
    if ($usegui eq "yes") {
      &cleardisplay;
    }
    $model1 = &readasciimdl($filepath, 1, {
      validate_vertex_data  => $mdl_opts->{validateverts},
      weight_by_area        => $mdl_opts->{weightarea},
      weight_by_angle       => $mdl_opts->{weightangle},
      recalculate_aabb_tree => $mdl_opts->{generateaabb},
      use_crease_angle      => $mdl_opts->{usecrease},
      crease_angle          => defined($mdl_opts->{creaseangle}) ? deg2rad($mdl_opts->{creaseangle}) : undef
    });
    if ($model1 < 0) {
      return &showerror($model1);
    }
    print ("writing binary model\n");
    &writebinarymdl($model1, $mdl_opts->{reqversion}, {
      headfix => $mdl_opts->{headfix}
    });
  }
  &dowalkmesh($filepath);
  print("Finished processing model\n");
  print("-----------------------------------\n");
}

sub dowalkmesh {
  my ($filepath) = @_;
  my $walkmesh;
  my $wkm_files = [];
  my $extension = 'wok';
  # filepath contains a model file, first get potential walkmesh names
  my $path = '';
  my $file = $filepath;
  if ($file =~ /^(.+[\/\\])?(.+)$/) {
    $path = $1;
    $file = $2;
  }
  $file =~ /^(.+)(-.+?)?\.(mdl(?:\.ascii)?)$/i;
  my ($model_name, $suffix) = ($1, $2);
  #$file = $path . $file;
  if (!defined($model1) || !defined($model1->{name})) {
    return;
  }
  # if model1 classification is placeable, try pwk
  if (lc $model1->{classification} eq 'placeable') {
    $extension = 'pwk';
    $wkm_files = [
      $path . $model_name . $suffix . '.' . $extension
    ];
  } elsif (lc $model1->{classification} eq 'door') {
    $extension = 'dwk';
    if ($model1->{source} eq 'binary') {
      
    } else {
      $wkm_files = [
        $path . $model_name . $suffix . '.' . $extension
      ];

    }
  } else {
  }
  if (lc $model1->{classification} eq 'door' &&
      $model1->{source} eq 'binary') {
    $wkm_files = [
      $path . $model_name . '0' . $suffix . '.' . $extension,
      $path . $model_name . '1' . $suffix . '.' . $extension,
      $path . $model_name . '2' . $suffix . '.' . $extension,
    ];
  } else {
    $wkm_files = [
      $path . $model_name . $suffix . '.' . $extension
    ];
  }
  # if first file does not exist, or specifically requested,
  # try using .EXT.ascii form instead
  if ($mdl_opts->{use_asc_ext} || !MDLOpsM::File::exists($wkm_files->[0])) {
    $wkm_files = [
      map { if (MDLOpsM::File::exists($_ . '.ascii')) { $_ . '.ascii' } else { $_ } } @{$wkm_files}
    ];
  }
  my $is_binary = MDLOpsM::Walkmesh::detect_format($wkm_files->[0]);
  if (!defined($is_binary)) {
    # error, file probably does not exist
    return;
  } elsif ($is_binary) {
    print ("reading binary walkmesh\n");
    if (scalar(@{$wkm_files}) > 1) {
      $walkmesh = {};
      $walkmesh->{closed} = MDLOpsM::Walkmesh::readbinarywalkmesh($wkm_files->[0]);
      $walkmesh->{open1}  = MDLOpsM::Walkmesh::readbinarywalkmesh($wkm_files->[1]);
      $walkmesh->{open2}  = MDLOpsM::Walkmesh::readbinarywalkmesh($wkm_files->[2]);
    } else {
      #print "Reading walkmesh file for $model1->{name}\n";
      $walkmesh = MDLOpsM::Walkmesh::readbinarywalkmesh($wkm_files->[0]);
      #print Dumper($walkmesh->{header});
      #die;
      #print Dumper($walkmesh->{aabbs});
      #delete $walkmesh->{aabbs};
      #$walkmesh->{aabbs} = [];
      #MDLOpsW::aabb($walkmesh, [ (0..(scalar(@{$walkmesh->{faces}}) - 1)) ]);
      #print Dumper($walkmesh->{aabbs});
      #die;
    }
    my $outfile = sprintf(
      '%s%s%s%s.%s%s',
      $path, $model_name, $suffix,
      $mdl_opts->{use_asc_ext} ? '' : '-ascii',
      $extension,
      $mdl_opts->{use_asc_ext} ? '.ascii' : ''
    );
    if ($walkmesh && length($outfile)) {
      print ("writing ascii walkmesh\n");
      MDLOpsM::Walkmesh::writeasciiwalkmesh($outfile, $walkmesh, {
        model => $model1->{name}, extension => $extension
      });
    }
  } else {
    print ("reading ascii walkmesh\n");
    $walkmesh = MDLOpsM::Walkmesh::readasciiwalkmesh($wkm_files->[0]);
    my $outfile = sprintf('%s%s-bin.%s', $path, $model_name, $extension);
    if ($walkmesh && length($outfile)) {
      print ("writing binary walkmesh\n");
      if (defined($walkmesh->{closed}) &&
          defined($walkmesh->{open1})) {
        MDLOpsM::Walkmesh::writebinarywalkmesh(
          sprintf('%s%s0-bin.%s', $path, $model_name, $extension),
          $walkmesh->{closed}
        );
        MDLOpsM::Walkmesh::writebinarywalkmesh(
          sprintf('%s%s1-bin.%s', $path, $model_name, $extension),
          $walkmesh->{open1}
        );
        MDLOpsM::Walkmesh::writebinarywalkmesh(
          sprintf('%s%s2-bin.%s', $path, $model_name, $extension),
          $walkmesh->{open2}
        );
      } else {
        MDLOpsM::Walkmesh::writebinarywalkmesh($outfile, $walkmesh);
      }
    }
  }
}

# open the renamer window
sub openrenamer {
  # see if there is a loaded model and it is from binary
  if (!defined($model1)) {
    return &showerror(-2);
  }
  if($model1->{'source'} ne "binary") {
    return &showerror('Model must be from binary source!');
  }

  my @meshnodes;
  my @texturenames;
  
  $object{'renamerwin'}->configure(-title => "Renamer: $model1->{'name'}");

  # clear out the list box and entry box
  $object{'renamerlist'}->delete(0, 'end');
  $object{'renamernewname'}->delete(0, 'end');
  # fill the list box with any meshes and their textures found in the binary model
  foreach ( sort {$a <=> $b} keys %{$model1->{'nodes'}} ) {
    if ($_ eq 'truenodenum') {next;}
    if ( $model1->{'nodes'}{$_}{'nodetype'} & 32) {
      if ( ! ($model1->{'nodes'}{$_}{'nodetype'} & 512)) { # skip walk meshes
        $object{'renamerlist'}->insert('end', $model1->{'partnames'}[$_] . "=" . $model1->{'nodes'}{$_}{'bitmap'});
      }
    }
  }
  
  $object{'renamerwin'}->deiconify;
  $object{'renamerwin'}->raise;
}

# rename the texture for the currently selected mesh node
sub renameit {
  my $target;
  my $meshname;
  my $texturename;

  $texturename = $object{'renamernewname'}->get;
  
  # do the sanity checks
  $target = $object{'renamerlist'}->curselection;
  if ($target eq "") {
    #print("You must select a target mesh first!\n");
    return &showerror(-8);
  } elsif ($texturename eq "") {
    #print("You must enter a new name first!\n");
    return &showerror(-10);
  } elsif (length($texturename) > 31) {
    #print("Name must be 31 characters or less!\n");
    return &showerror(-9);
  } elsif ($texturename =~ /\s/) {
    #print("Name can't have white space in it!\n");
    return &showerror(-11);
  } elsif ($texturename =~ /=/) {
    #print("Name can't have = in it!\n");
    return &showerror(-12);
  }

  ($meshname) = split /=/,$object{'renamerlist'}->get($target);

  $object{'renamerlist'}->delete($target);
  $object{'renamerlist'}->insert($target, $meshname . "=" . $texturename);
 
}

# write out a binary model with the textures renamed
sub writeit {
  my $buffer;

  foreach ($object{'renamerlist'}->get(0, 'end')) {
    /(.*)=(.*)/;
    print("mesh=" . $1 . " texture=" . $2 . " " . $model1->{'nodeindex'}{lc($1)} . "\n");
    # get the raw mesh header
    $buffer = $model1->{'nodes'}{ $model1->{'nodeindex'}{lc($1)} }{'subhead'}{'raw'};
    # replace the texture name
    substr($buffer,  88, 32, pack("Z[32]", $2) );
    # write the data back to the model
    $model1->{'nodes'}{ $model1->{'nodeindex'}{lc($1)} }{'subhead'}{'raw'} = $buffer;
  }

  writerawbinarymdl($model1, $curversion);
  $object{'renamerwin'}->withdraw;
  return &showmessage('Done!');
}

# CLI: node replacer entrypoint, easier than modifying replacenodes...
sub replacenodes_cli {
  #my ($model1, $model2, $curversion) = 
  repreadmodel($opt{rep_binary_model}, $opt{rep_ascii_model});

  # do some kind of renaming here...

  if (scalar(@{$opt{rep_binary_mesh}}) != scalar(@{$opt{rep_ascii_mesh}})) {
    return &showerror('number of ascii source nodes and binary target nodes must match');
  }

  foreach (0..(scalar(@{$opt{rep_binary_mesh}}) - 1)) {
    printf("Replacing binary %s with ascii %s\n", $opt{rep_binary_mesh}->[$_], $opt{rep_ascii_mesh}->[$_]);
    replaceraw($model1, $model2, $opt{rep_binary_mesh}->[$_], $opt{rep_ascii_mesh}->[$_]);
  }

  # write out the new model
  writerawbinarymdl($model1, $curversion);
}

# replace the selected nodes
sub replacenodes {
  my @source;
  my @target;
  my $work;
  my $buffer;

  # get the model base name from the entry box
  $work = $object{'repnodebaseentry'}->get;
  # set the model base name 
  if(length($model1->{'name'}) == length($work) ) {
    print("Base model name will be set to: " . $work . "\n");
    # get the raw geoheader
    $buffer = $model1->{'geoheader'}{'raw'};
    # change the model base name
    substr($buffer, 8, 32, pack("Z[32]", $work) );
    # put the changed data back into the raw geoheader
    $model1->{'geoheader'}{'raw'} = $buffer;

    # get the raw part names list
    $buffer = $model1->{'names'}{'raw'};
    # change the aurora base name
    substr($buffer, 0, length($work)+1, pack("Z*", $work) );
    # put the changed data back into the raw part names list
    $model1->{'names'}{'raw'} = $buffer;

    # change the models file name and path
    $work = lc($work);
    $model1->{'filename'} = $work;
    substr($model1->{'filepath+name'}, length($model1->{'filepath+name'}) - length($work), length($work), $work);
  } else {
    #print("Base model name must be " . length($model1->{'name'}) . " characters\n");
    return &showerror(-7, length($model1->{'name'}));
  }

  # build the replace list
  foreach ($object{'replacelist'}->get(0, 'end')) {
    /(\S*)( to be replaced by )?(\S*)?/;
    if ($3 ne "") {
      $source[$work] = $1;
      $target[$work] = $3;
      $work++;
    }
  }

  # replace the nodes
  foreach (0..$#source) {
    print("Replacing binary $source[$_] with ascii $target[$_]\n");
    replaceraw($model1, $model2, $source[$_], $target[$_]);
  }
  # write out the new model
  writerawbinarymdl($model1, $curversion);
  $object{'repnodeselwin'}->withdraw;

  return &showmessage('Done!');
}

sub openreplacer {
  $object{'repmodselwin'}->deiconify;
  $object{'repmodselwin'}->raise;
}

# read the selected binary and ascii models for the replacer
sub repreadmodel {
  my ($binarypath, $asciipath);
  if ($usegui eq 'yes') {
    $binarypath = $object{'binaryentry'}->get;
    $asciipath = $object{'asciientry'}->get;
    $object{'replacelist'}->delete(0, 'end');
    $object{'targetlist'}->delete(0, 'end');
  } else {
    ($binarypath, $asciipath) = @_;
  }
  
  $model1 = undef;
  $model2 = undef;

  # do a little sanity checking
  if ($binarypath eq "") { # the path box is empty!
    return &showerror(-2);
  } elsif (!MDLOpsM::File::exists($binarypath)) { # the path does not exist!
    return &showerror(-3, $binarypath);
  }
  if ($asciipath eq "") { # the path box is empty!
    return &showerror(-2);
  } elsif (!MDLOpsM::File::exists($asciipath)) { # the path does not exist!
    return &showerror(-3, $asciipath);
  }

  # check if binary model is really binary
  if (&modeltype($binarypath) ne "binary") {
    return &showerror(-4, $binarypath);
  }
  # check if ascii model is really ascii
  if (&modeltype($asciipath) ne "ascii") {
    return &showerror(-5, $asciipath);
  }

  #read the models
  $curversion = &modelversion($binarypath);
  $model1 = &readbinarymdl($binarypath, 1, $curversion, {
    extract_anims => $mdl_opts->{extract_anims},
    compute_smoothgroups => 0,
    weld_model => 0
  });
  #&writerawbinarymdl($model1);
  $model2 = &readasciimdl($asciipath, 0, {
    validate_vertex_data  => $mdl_opts->{validateverts},
    weight_by_area        => $mdl_opts->{weightarea},
    weight_by_angle       => $mdl_opts->{weightangle},
    recalculate_aabb_tree => $mdl_opts->{generateaabb},
    use_crease_angle      => $mdl_opts->{usecrease},
    crease_angle          => defined($mdl_opts->{creaseangle}) ? deg2rad($mdl_opts->{creaseangle}) : undef
  });
    
  if ($usegui ne 'yes') {
    return;
  }

  # fill the source list box with any trimeshes found in the binary model
  foreach ( sort {$a <=> $b} keys %{$model1->{'nodes'}} ) {
    if ($_ eq 'truenodenum') {next;}
    if ( $model1->{'nodes'}{$_}{'nodetype'} == 33) {
      $object{'replacelist'}->insert('end', $model1->{'partnames'}[$_]);
    }
  }

  # fill the target list box with any trimeshes found in the ascii model
  $object{'targetlist'}->insert('end', "<none>");
  foreach ( sort {$a <=> $b} keys %{$model2->{'nodes'}} ) {
    if ($_ eq 'truenodenum') {next;}
    if ( $model2->{'nodes'}{$_}{'nodetype'} == 33) {
      $object{'targetlist'}->insert('end', $model2->{'partnames'}[$_]);
    }
  }

  # fill in the base model name entry box
  $object{'repnodebaseentry'}->delete('0','end');
  $object{'repnodebaseentry'}->insert('end',$model1->{'name'});
  
  $object{'repmodselwin'}->withdraw;
  
  $object{'repnodeselwin'}->deiconify;
  $object{'repnodeselwin'}->raise;
  print "final\n";
}

# select the mesh from the ascii model that will replace the mesh in the binary model
sub targetselect {
  if ($object{'targetlist'}->curselection eq "") {
    #print("You must select a target mesh first!\n");
    return &showerror(-8);
  }
  
  if ($object{'targetlist'}->get($object{'targetlist'}->curselection) eq "<none>") {
    $object{'replacelist'}->delete($source);
    $object{'replacelist'}->insert($source, "$sourcetext");
  } else {
    $object{'replacelist'}->delete($source);
    $object{'replacelist'}->insert($source, "$sourcetext to be replaced by " . $object{'targetlist'}->get($object{'targetlist'}->curselection));
  }
  
  $object{'repnodetargwin'}->withdraw;
}

# select the mesh from the binary model that is to be replaced
sub openreptargwin {
  $source = $object{'replacelist'}->curselection;
  
  if ($source eq "") {
    #print("You must select a source mesh first!\n");
    return &showerror(-6);
  }
  
  ($sourcetext) = split / /,$object{'replacelist'}->get($source);
  
  $object{'repnodetargwin'}->deiconify;
  $object{'repnodetargwin'}->raise;
}

# un-hides the data view window
sub viewdata {
  $object{'dataviewwin'}->deiconify;
}

# routine to destroy a window instead of hiding it
sub nukewindow {
  my ($name) = @_;
  $object{$name}->destroy;
  delete $object{$name};
}
# routine to hide a window instead of destroying it
sub withdrawwindow {
  $object{shift(@_)}->withdraw;
}

sub defaults_read {
  my $options = {};
  my $dirname = dirname(__FILE__);
  my $dir_sep = canonpath '/';

  if (open(my $fh, '<', $dirname . $dir_sep . 'defaults.json')) {
    my $str = join('', <$fh>);
    if (length($str) && $str =~ /{/) {
      local $@;
      $options = eval 'decode_json($str);';
      if (ref $options ne 'HASH') {
        printf(
          "invalid settings file will be overwritten: %s\n%s\n",
          $dirname . $dir_sep . 'defaults.json', $@
        );
        $options = {};
      }
      #print Dumper($options);
    }
    close($fh);
  }
  return $options;
}

sub defaults_write {
  my ($options) = @_;

  my $dirname = dirname(__FILE__);
  my $dir_sep = canonpath '/';
  #print to_json($options, {utf8 => 1, pretty=> 1});
  if (!defined &to_json) {
    return;
  }
  if (!$options->{use_opt_file}) {
    $options = { use_opt_file => 0 };
  }

  if (open(my $fh, '>', $dirname . $dir_sep . 'defaults.json')) {
    print $fh to_json($options, {utf8 => 1, pretty=> 1});
    close($fh);
  } else {
    print "cannot write to ${dirname}${$dir_sep}defaults.json. ".
          "option defaults will not be saved.\n";
  }
}

# my simple little user message handler
sub showstatus {
  my ($message) = @_;

  printf("%s\n", $message);
  if($usegui eq "yes") {
    $object{'main'}->messageBox(
      -message => $message, 
      -title => "$APPNAME Status", 
      -type => 'OK'
    );
  }

  return 1;
}

# my simple little error handler
sub showerror {
  my ($error, $path) = @_;
  my $message;

  if ($error =~ /[A-Za-z ]/) {
    $message = $error;
    $error = -50;
  } elsif ($error == -1) {
    $message = "Model has a face with overlapping vertices.";
  } elsif ($error == -2) {
    $message = "You must select a model file first!";
  } elsif ($error == -3) {
    $message = "$path does not exist!";
  } elsif ($error == -4) {
    $message = "$path is not a binary model!";
  } elsif ($error == -5) {
    $message = "$path is not an ascii model!";
  } elsif ($error == -6) {
    $message = "You must select a source mesh first!";
  } elsif ($error == -7) {
    $message = "Name must be $path characters long!";
  } elsif ($error == -8) {
    $message = "You must select a target mesh first!";
  } elsif ($error == -9) {
    $message = "Name must be 31 characters or less!";
  } elsif ($error == -10) {
    $message = "You must enter a new name first!";
  } elsif ($error == -11) {
    $message = "Name can't have white space in it!";
  } elsif ($error == -12) {
    $message = "Name can't have = in it!";
  } elsif ($error == -13) {
    $message = "Done!";
  }
 
  &showstatus('Error: ' . $message);

  return $error;
}

# clear out the data view
sub cleardisplay {
  $object{'dataviewwin'}->withdraw;
  $object{'thelist'}->delete('all');
  $object{'hexdata'}->delete(0,'end');
  $object{'chardata'}->delete(0,'end');
  $object{'cookeddata'}->delete(0,'end');
}

# display the data in the data view window when a tree entry is clicked
sub displaydata {
  my ($loc, $item, $num, $sub1, $sub2, $sub3) = ("","","","","","");
  my (@raw, @chars, @cooked) = ((),(),());
  
  #get the currently selected list item
  $loc = $object{'thelist'}->info('anchor');
  #split the list info at . and stuff it into the variables
  (undef, $item, $num, $sub1, $sub2, $sub3) = split(/\./,$loc);
  #print("$item|$num|$sub1|$sub2|$sub3\n");

  #clear out the list boxes
  $object{'hexdata'}->delete(0,'end');
  $object{'chardata'}->delete(0,'end');
  $object{'cookeddata'}->delete(0,'end');

  
  if ($item eq "nodes" && $sub1 ne "") {
    if ($sub2 eq "") {
      #this is for node headers and node data
      @raw = hexchop($model1->{$item}{$num}{$sub1}{'raw'});
      @chars = charchop($model1->{$item}{$num}{$sub1}{'raw'});
      @cooked = @{$model1->{$item}{$num}{$sub1}{'unpacked'}};
    } else {
      #this is for node arrays and children lists
      @raw = hexchop($model1->{$item}{$num}{$sub2}{'raw'});
      @chars = charchop($model1->{$item}{$num}{$sub2}{'raw'});
      @cooked = @{$model1->{$item}{$num}{$sub2}{'unpacked'}};
    }
  } elsif ($item =~ /^anims/) {
    if ($sub3 ne "") {
      @raw = hexchop($model1->{$item}{$num}{$sub1}{$sub2}{$sub3}{'raw'});
      @chars = charchop($model1->{$item}{$num}{$sub1}{$sub2}{$sub3}{'raw'});
      @cooked = @{$model1->{$item}{$num}{$sub1}{$sub2}{$sub3}{'unpacked'}};
    } elsif ($sub1 eq "geoheader" || $sub1 eq "animheader" || $sub1 eq "animevents") {
      @raw = hexchop($model1->{$item}{$num}{$sub1}{'raw'});
      @chars = charchop($model1->{$item}{$num}{$sub1}{'raw'});
      @cooked = @{$model1->{$item}{$num}{$sub1}{'unpacked'}};
    } elsif ($num eq "indexes") {
      @raw = hexchop($model1->{$item}{$num}{'raw'});
      @chars = charchop($model1->{$item}{$num}{'raw'});
      @cooked = @{$model1->{$item}{$num}{'unpacked'}};
    }
  } elsif ($item eq "namearray" && $num ne "") {
    #this is for the names array and animatios
    if ($num eq "partnames") {
      @raw = hexchop($model1->{'names'}{'raw'});
      @chars = charchop($model1->{'names'}{'raw'});
      @cooked = @{$model1->{'partnames'}};
    } else {
      @raw = hexchop($model1->{$num}{'raw'});
      @chars = charchop($model1->{$num}{'raw'});
      @cooked = @{$model1->{$num}{'unpacked'}};
    }
  } elsif ($item eq "fileheader" || $item eq "geoheader" || $item eq "modelheader") {
    #this is for the simple headers file, geometry and model
    @raw = hexchop($model1->{$item}{'raw'});
    @chars = charchop($model1->{$item}{'raw'});
    @cooked = @{$model1->{$item}{'unpacked'}};
  }

  #tag a number onto the beginning of all the cooked data
  $num = 0;
  $sub2 = 0;
  $sub1 = $object{'thelist'}->info('data', $loc);
  foreach $item (@cooked) {
    if ($sub1 == 1) {
      $item = sprintf("(%03s) %s", $num, $item);
    } else {
      $sub2++;
      if ($sub2 > $sub1) {
        $sub2 = 1;
      }
      $item = sprintf("%03s-%02s %s",$num, $sub2, $item);
    }
    $num++; 
  }

  #fill the listboxes
  $object{'hexdata'}->insert(0, @raw);
  $object{'chardata'}->insert(0, @chars);
  $object{'cookeddata'}->insert(0, @cooked);
}

sub charchop {
  # this sub takes the raw data and outputs text for use in the chardata listbox
  my ($stuff) = @_;
  my ($counter, $work, @lines) = (0,"",());
  my $temp;

  for ($counter = 0; $counter < length($stuff); $counter++) {
    if (($counter != 0) && ($counter % 16 == 0)) {
      push(@lines, $work);
      $work = "";
    } elsif (($counter != 0) && ($counter % 4 == 0)) {
      $work .= "|"
    }
    $temp = substr($stuff, $counter, 1);
    #print($temp);
    if ( ord($temp) > 31 && ord($temp) < 127) {
      $work .= substr($stuff, $counter, 1) ;
    } else {
      $work .= " " ;
    }
  }
  if ($work ne "") {push(@lines, $work)};
  #print("@lines\n");
  return @lines;
}

sub hexchop {
  #this sub takes the raw data and outputs it in hex for use in the hexdata listbox
  my ($stuff) = @_;
  my ($counter, $work, @lines) = (0,"",());

  $stuff = unpack("H*", $stuff);

  for ($counter = 0; $counter < length($stuff); $counter += 8) {
    if (($counter != 0) && ($counter % 32 == 0)) {
      push(@lines, $work);
      $work = "";
    }
    $work .= substr($stuff, $counter, 8) . "|";
  }
  if ($work ne "") {push(@lines, $work)};
  #print("@lines\n");
  return @lines;
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
  print ("\n--> " . tell(MODELMDL));
  print ("\n\n");
}

sub browse_for_file {
  my $target = shift @_;
  # a file dialog that is cross platform, but just unspeakably foul
  #use Tk::JBrowseEntry;
  #use Tk::JFileDialog;
  #my $dialog_name;
  #my $dlg = $object{main}->JFileDialog(-Title => 'Tits', -Create => 0);
  #$dlg->configure(-FPat => '*pl', -ShowAll => 'NO', -Path => '.');
  #$dialog_name = $dlg->Show(-Horiz => 1);
  #unless (-e $dialog_name) { return; }
  #$object{$target}->delete('0','end');
  #$object{$target}->insert('end',$dialog_name);
  #return;

  # Win32::FileOp kind of sucks...
  # I had to modify it to support Unicode, pretty straightforward though,
  # just adding a few encode('utf16-le') and doubling up the "\0" chars in
  # sub OpenOrSaveDialog, also use Encode, and point it at GetOpenFileNameW.
  # Resulting method returns utf8, which is what MDLOpsM::File methods expect.
  my %parms=(
    title => "Open Model File",
    handle => 0,
    filename => "",
    filters => { 'Model Files' => '*.mdl',
                 'ASCII Model Files' => '*.mdl.ascii',
                 'All Files' => '*.*' },
    options => OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST
  );
  $Win32::FileOp::BufferSize = 131072;
  my $dialog_name;
  $dialog_name = OpenDialog \%parms;
  unless (defined($dialog_name) &&
          length($dialog_name)) { return; }
  #my $x = 0;
  #foreach (split //, $dialog_name) {
  #  print "$x $_ " . ord($_) . "\n";
  #  $x++;
  #}
  #print $dialog_name . ' '.length($dialog_name)."\n";
  unless (MDLOpsM::File::exists($dialog_name)) { return; }
  $object{$target}->delete('0','end');
  $object{$target}->insert('end',$dialog_name);
}
