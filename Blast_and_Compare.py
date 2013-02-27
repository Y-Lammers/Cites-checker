#!/usr/bin/env python

# descrip


# import the argparse module to handle the input commands
import argparse

# get the commandline arguments that specify the input fastafile and the output file
parser = argparse.ArgumentParser(description = ('retrieve blast and taxonomic information for a fasta file'))

parser.add_argument('-i', '--input_file', metavar='fasta file', dest='i', type=str, 
			help='enter the fasta file')
parser.add_argument('-o', '--output_file', metavar='output file', dest='o', type=str, 
			help='enter the output file')
parser.add_argument('-a', '--BLAST_algorithm', metavar='algorithm', dest='a', type=str, 
			help='Enter the algorithm BLAST wil use (default=blastn)', default='blastn')
parser.add_argument('-d', '--BLAST_database', metavar='database', dest='d', type=str,
			help = 'Enter the database BLAST wil use (default=nt)', default = 'nt')
parser.add_argument('-s', '--hitlist_size', dest='s', type=int,
			help = 'Enter the size of the hitlist BLAST wil return (default=1)', default=1)
parser.add_argument('-m', '--megablast', dest='m', action='store_true', 
			help = 'Use megablast, can only be used in combination with blastn')
parser.add_argument('-mi', '--min_identity', dest='mi', type=int, 
			help = 'Enter the minimal identity for BLAST results', default = 97)
parser.add_argument('-mc', '--min_coverage', dest='mc', type=int, 
			help = 'Enter the minimal coverage for BLAST results', default = 100)
parser.add_argument('-me', '--max_evalue', dest='me', type=float, 
			help = 'Enter the minimal E-value for BLAST results', default = 0.05)
parser.add_argument('-b', '--blacklist', metavar='blacklist file', dest='b', type=str,
			help = 'File containing the blacklisted genbank id\'s')
parser.add_argument('-c', '--CITES_db', metavar='CITES database file', dest='c', type=str,
			help = 'Path to the local copy of the CITES database')

args = parser.parse_args()

def blast_bulk (fasta_file, settings):

	# The blast modules are imported from biopython
	from Bio.Blast import NCBIWWW, NCBIXML
	from Bio import SeqIO
	
	# parse the fasta file
	seq_list = [seq for seq in SeqIO.parse(fasta_file, 'fasta')]

	# open the fasta file
	#fasta_open = open(fasta_file, 'r')
	#fasta_handle = fasta_open.read()
	
	blast_list = []

	for seq in seq_list:
		print seq
		result_handle = NCBIWWW.qblast(settings[0], settings[1], seq.format('fasta'), megablast=settings[3], hitlist_size=settings[2])
		blast_list.append(NCBIXML.read(result_handle))
	# Blast the sequences against the NCBI nucleotide database
	# return a list with the blast results
	#result_handle = NCBIWWW.qblast(settings[0], settings[1], fasta_handle, megablast=settings[3], hitlist_size=settings[2])
	#blast_list = [item for item in NCBIXML.parse(result_handle)]	

	return blast_list


def blacklist (blacklist_file):
	
	# return a list containing the blacklisted genbank id's
	# the blacklist follows the following format:
	# genbank_id, description
	try:
		return [line for line in open(blacklist_file,'r')]
	except:
		return []


def CITES_db (CITES_file):
	
	# open the local CITES database, return a dictionary
	# containing the CITES information with the taxid's as keys

	CITES_dic = {}
	
	for line in open(CITES_file, 'r'):
		line = line.rstrip().split(',')
		if line[0] != 'Date':
			CITES_dic[line[0]] = line[1:]

	return CITES_dic


def parse_blast (blast_list, filter_list, CITES_dic, outpath, mode):
	
	# parse_through the blast results and remove
	# results that do not meet the e-value, coverage,
	# identity and blacklist critera

	from Bio.Blast import NCBIWWW, NCBIXML

	for blast_result in blast_list:
		for alignment in blast_result.alignments:
			for hsp in alignment.hsps:
	            		
				# calculate the %identity
		            	identity = float(hsp.identities/(len(hsp.match)*0.01))

				# grab the genbank number
				gb_num = alignment.title.split('|')[1]
				
				# an alignment needs to meet 3 criteria before 
				# it is an acceptable result: above the minimum 
				# identity, minimum coverage and E-value
			
				# create containing the relevant blast results
				# pass this list to the filter_hits function to
				# filter and write the blast results
				filter_hits([('\"' + blast_result.query + '\"'), ('\"' + alignment.title + '\"'), gb_num, str(identity),
						str(blast_result.query_length), str(hsp.expect), str(hsp.bits)],
						filter_list, CITES_dic, outpath, mode)


def obtain_tax (code):
	
	# a module from Biopython is imported to connect to the Entrez database
	from Bio import Entrez
	from Bio import SeqIO

	taxon = [[],[]]

	try:
		# based on the genbank id the taxon id is retrieved from genbank
		Entrez.email = "quick@test.com"
		handle = Entrez.efetch(db="nucleotide", id= code, rettype="gb",retmode="text")
		record = SeqIO.read(handle, "gb")

		# parse through the features and grap the taxon_id
		sub = record.features
		taxon[0] = sub[0].qualifiers['db_xref'][0].split(':')[1]
		taxon[1] = record.annotations['organism']

	except:
		pass

	return taxon


def filter_hits (blast, filter_list, CITES_dic, outpath, mode):
	
	print blast
	# filter the blast hits, based on the minimum
	# identity, minimum coverage, e-value and the user blacklist
	if float(blast[3]) >= filter_list[0] and int(blast[4]) >= filter_list[1] and float(blast[5]) <= filter_list[2]:
		if blast[2] not in filter_list[3]:
			taxon = obtain_tax(blast[2])
			results = blast+taxon

			# check if the taxon id of the blast hit
			# is present in the CITES_dic
			if taxon[0] in CITES_dic:			
				results+CITES_dic[taxon[0]]
			
			# write the results
			write_results(','.join(results), outpath, mode)
			
			

def write_results (result, outpath, mode):
	
	# write the results to the output file
	out_file = open(outpath, mode)
	out_file.write(result + '\n')
	out_file.close()


def main ():

	# two lists of the desired blast and filter settings
	blast_settings = [args.a, args.d, args.s, args.m]
	filter_list = [args.mi, args.mc, args.me, blacklist(args.b)]
	
	# create a dictionary containing the local CITES set
	CITES_dic = CITES_db(args.c)

	# create a blank result file and write the header
	header = 'query,hit,accession,identity,hit length,e-value,bit-score,taxon id,genbank record species,CITES species,CITES info,NCBI Taxonomy name,appendix'
	write_results(header, args.o, 'w')

	# blast the fasta file
	blast_list = blast_bulk(args.i, blast_settings)

	# parse through the results and write the blast hits + CITES info
	parse_blast(blast_list, filter_list, CITES_dic, args.o, 'a')
	

if __name__ == "__main__":
    main()

