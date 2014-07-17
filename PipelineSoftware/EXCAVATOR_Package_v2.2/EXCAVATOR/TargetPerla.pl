#!/usr/bin/perl

use warnings;
use Pod::Usage;
use Getopt::Long;
use strict;
use Cwd 'abs_path';
	
######################################################################
#
#	Variables initialization with default values
#
######################################################################

our ($record,@words,@unlinkfiles);

our $Assembly="hg19";				# Calling option "--assembly hg18" sets the string variable $Assembly="hg18"

our ($Program_Folder_Path,$Target_File_Path,$Target_Name,$Source_Data);

our ($Path_2_Wig,$Path_2_fasta);

our ($verbose,$help,$man);

######################################################################
#
#	Defining options
#
######################################################################

GetOptions('assembly=s'=>\$Assembly,'verbose|v'=>\$verbose,'help|h'=>\$help,'man|m'=>\$man,) or pod2usage ();

$help and pod2usage (-verbose=>1, -exitval=>1, -output=>\*STDOUT);
$man and pod2usage (-verbose=>2, -exitval=>1, -output=>\*STDOUT);
@ARGV or pod2usage (-verbose=>0, -exitval=>1, -output=>\*STDOUT);
@ARGV == 3 or pod2usage ("Syntax error");
	
######################################################################
#
#	Defining system variables
#
######################################################################

my ($myscriptname,$myscript,$workingfolder,$L1,$L2);

$myscript=abs_path($0);
$L1=length($myscript);
$L2=length("TargetPerla.pl");
$Program_Folder_Path=substr $myscript, 0, ($L1 - $L2 - 1);

print "Program folder is: $Program_Folder_Path\n";

$Source_Data=$ARGV[0];
$Target_File_Path=$ARGV[1];
$Target_Name=$ARGV[2];

our $Target_Filt_Path="$Program_Folder_Path/data/targets/$Assembly/$Target_Name";

######################################################################
#
#	Checking temporary folder for NeoMap.sh
#
######################################################################

if(-e "$Program_Folder_Path/.tmp"){
	print "'Checked temporary folder for NeoMap.sh!\n";
}
else{
	mkdir ("$Program_Folder_Path/.tmp");
	print "Created temporary folder for NeoMap.sh!\n";
}

######################################################################
#
#	Removing empty lines from source file
#	and creating support temporary files
#
######################################################################

my $range=99999;
my $ID=int(rand($range));
my $filename="source.$ID";

if(-e $filename){ 
	$ID=$ID+100000;
}

system qq(awk NF $Source_Data > source.$ID);

######################################################################
#
#	Reading source file
#
######################################################################

open(CHECKBOOK,"source.$ID") || die "Couldn't open the source file!";

while($record=<CHECKBOOK>){
	chomp($record);
	@words=split(' ',$record);
	
	$Path_2_Wig=$words[0];
	$Path_2_fasta=$words[1];
			
######################################################################
#
#	Checking target file format
#
######################################################################

print "Checking target file format...\n";
system qq(rm -f ErrorTarget.out);
system qq(head -1 $Target_File_Path | awk '{if (\$3<\$2) print "Exon #1 end value is smaller than start value. Please check target file format. Exons start (end) must be in column 2 (3)." > "ErrorTarget.out"; else print "Target file seems properly formatted."}');

if(-e "ErrorTarget.out"){
	print "Exiting: target seems to be uncorrectly formatted. Please check ErrorTarget.out!\n";
	exit;
}

######################################################################
#
#	Target initialization
#
######################################################################

print "Filtering target from $Target_File_Path...\n";
system qq(R --slave --args $Target_File_Path,$Program_Folder_Path,$Target_Name,$Assembly < $Program_Folder_Path/lib/R/FilterTarget.R);
print "Calculating mappability...\n";
print "Source file: $Path_2_Wig.";
system qq($Program_Folder_Path/lib/bash/./NeoMap.sh $Path_2_Wig $Program_Folder_Path $Assembly $Target_Name);
print "Calculating GC content...\n";
print "Source file: $Path_2_fasta.";
system qq($Program_Folder_Path/lib/bash/./GC3.sh $Target_Filt_Path/Filtered.txt $Program_Folder_Path $Assembly $Target_Name $Path_2_fasta);
print "...done!\n";

}

close(CHECKBOOK);
@unlinkfiles=("source.$ID");
unlink @unlinkfiles;

######################################################################
#
#	Documentation
#
######################################################################

=head1 SYNOPSIS 

 perl TargetPerla.pl [arguments] [options]

 Options:

       -h, --help                   Print help message.
       -m, --man                    Print complete documentation.
       -v, --verbose                Use verbose output.
           --assembly               Specify assembly for target initialization. Default value is hg19.

 Function:
 
 TargetPerla.pl initialises target file for further data processing with EXCAVATOR package. It requires 3 arguments (one source files - with two paths to source data for mappability and GC-content calculations, path to target file and target name) to run properly. A sub-folder with the specified target name will be created under "EXCAVATOR/data/targets/hgXX" (default assembly is hg19). Target input file (.bed, .txt or any plain text file) must be tab-delimited.

 Example: 
 
 EXCAVATOR> perl TargetPerla.pl  SourceTarget.txt /Users/.../MyTarget.bed TargetName
 
=head1 OPTIONS

=over 8

=item B<--help>

Print a brief usage message and detailed explanation of options.

=item B<--man>

Print the complete manual of the script.

=item B<--verbose>

Use verbose output.

=item B<--assembly>

Sets the assembly for target calculations. If omitted default value is hg19.

=back

=head1 DESCRIPTION

TargetPerla.pl is a Perl script which is part of the EXCAVATOR package. It includes all of the first step operations of the EXCAVATOR package. It filters a target file and calculates, for a specific assembly, GC content and mappability. These data are required by the ReadPerla.pl module of the EXCAVATOR package.

It requires, as arguments, the path to a source file (the default source file is "SourceTarget.txt" and is placed in the main EXCAVATOR folder) containing the paths to source data (for the calculations of mappability and GC-content), the path to the target input file and a "target name". Target input file (.bed, .txt or any plain text file) must be tab-delimited. Setting the target name as "MyTarget", all data calculated will be saved in the "MyTarget" folder in (if you are using the hg19 assembly) EXCAVATOR/data/targets/hg19/MyTarget.

The default assembly, namely hg19, can be substituted with any other with the option --assembly followed by a string specifying the new assembly (e.g. you may run perl /.../EXCAVATOR/TargetPerla.pl SourceTarget.txt /.../Target.bed TargetName --assembly hg18).

EXCAVATOR is freely available to the community for non-commercial use. For questions or comments, please contact "lorenzotattini@gmail.com".

=cut
