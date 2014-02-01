#!/usr/bin/perl
# $Id: printenv.pl,v 1.2 2007-10-24 17:41:28 jonrober Exp $
# printenv.pl -- demo perl program that prints out environment variables.

print "Content-type: text/plain\n\n";
foreach $var (sort(keys(%ENV))) {
    $val = $ENV{$var};
    $val =~ s|\n|\\n|g;
    $val =~ s|"|\\"|g;
    print "${var}=\"${val}\"\n";
}

