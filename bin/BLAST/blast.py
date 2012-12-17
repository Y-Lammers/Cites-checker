#!/usr/bin/python2.7
'''

@author: Thomas Bolderink
@co-author: Alex Hoogkamer

 blast script for blast -barcode pipeline
dependencies:
Bio python
Unix OS


input: fastqfile
output: XML file with blastN search results
'''

from Bio.Blast import NCBIWWW
#import os
import sys
'''

'''
input_handle = sys.stdin.readlines()
'''
the input from the Trim script needs to be converted into 
a format which is usable by NCBIWWW
'''
data_handle = []
fasta       = ''
a           = 0

for line in input_handle:
    if a < 0:
        if line[0] == '>':
            fasta = line
            a = a + 1
        else:
            pass
    else:
        if line[0] == '>':
            fasta = fasta + "\n"
            data_handle.append(fasta)
            fasta = line
        else:
            fasta = fasta + line.strip("\n")

blast_handle = ''
for line in data_handle:
    blast_handle = blast_handle + line
fasta_handle = NCBIWWW.qblast("blastn","nt", blast_handle, megablast = False)  # define blast parameters for blast search
save_file = open("my_blast.xml", "w")                                          # results of the blast search are stored in xml file
save_file.write(fasta_handle.read())
sys.stdout.write(fasta_handle.read())
save_file.close
fasta_handle.close