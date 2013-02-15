#!/usr/bin/env python

# Create a local database containing the CITES appendices
# Database contains the CITES species names and synonymes based on:
# and the species ncbi species taxon identifier


# import the argparse module to handle the input commands
#import argparse, sys

#parser = argparse.ArgumentParser(description = 'Create a table containing the CITES species')

#parser.add_argument('--download', metavar='', type=str, 
#			help='Enter the 454 sequence fasta file(s)', nargs='+')
#parser.add_argument('--output_dir', metavar='output directory', type=str, 

def download_raw_CITES ():
	
	# import the urllib2 module used to download the Cites appendices
	import urllib2

	# open the url and read the .php webpage
	CITES_url = urllib2.urlopen('http://www.cites.org/eng/app/appendices.php')
	CITES_php = CITES_url.read()

	#print(CITES_php)

	# return the raw .php file
	return CITES_php


def clean_cell (cell):
	
	import re

	cell = str(''.join(cell.findAll(text=True)).encode('ascii','ignore'))
	regex = re.compile(r'[\n\r\t]')
	cell = regex.sub('', cell).strip().replace('&nbsp;',' ')
	
	while '  ' in cell:
		cell = cell.replace('  ', ' ')

	return cell	


def parse_php (php_file):

	# import BeautifulSoup to parse the webpage
	from BeautifulSoup import BeautifulSoup
	
	# fill this dictionary with all species for the 3
	# CITES categories
	CITES_dict = {1:[],2:[],3:[]}
	
	# read the CITES web page	
	CITES_page = BeautifulSoup(php_file)
	
	# extract the tables
	tables = CITES_page.findAll('table')
	
	# parse through the table and find all cites species
	# (in bold / italic) and under which category they fit
	rows = tables[1].findAll('tr')
	for tr in rows[2:]:
		cols = tr.findAll('td')
		count = 1
		for td in cols:
			cell = td.find('b')
			# if the cell is filled, retrieve the
			# species name and add it to the dictionary
			if cell != None:
				cell = clean_cell(cell)
				if ';' in cell:	cell = cell.split(';')[1]
				CITES_dict[count].append([cell,clean_cell(td)])
			count += 1
	
	# return the dictionary containing the species
	return CITES_dict			


def TNRS (name):
	
	# import the request module to connect to the TNRS api
	# and deal with the JSON resuls and the time module
	# to prevent floading of the api
	import requests, time

	# Send the TNRS request
	TNRS_req = requests.get('http://api.phylotastic.org/tnrs/submit',
		params={'query':name},
		allow_redirects=True)

	redirect_url, time_count = TNRS_req.url, 0

	# send retrieve requests at 5 second intervals till
	# the api returns the JSON object with the results
	while redirect_url and time_count < 60:
		retrieve_response = requests.get(redirect_url)
		retrieve_results = retrieve_response.json()
		
		# if the results contains the JSON object
		# retrieve all accepted names for the species
		# and return these
		if u'names' in retrieve_results:
			name_list = [name,[]]
			names = retrieve_results.get(u'names')
			for item in names[0]['matches']:
				if item['sourceId'] == 'NCBI':
					name_list.append(str(item['uri']).split('/')[-1])
				synonym = item['acceptedName']
				if synonym != name and ' ' in synonym and synonym != '':
					name_list[1].append(str(item['acceptedName']))

			# return the list with species names
			return name_list
		
		# time out before sending the new request
		# use a counter to keep track of the time, if there is
		# still no server reply the function will return an empty list
		time.sleep(5)
		time_count += 5

	print('Timeout for species %s' % name)
	return [name,[]]

def get_taxid (species):
	
	# get taxon id based on species name (if not provided by TNRS search)

	# import Entrez module from biopython to connect to the genbank servers
	from Bio import Entrez

	'''
	def get_TaxonomyChild():
	handle = Entrez.esearch(db="Taxonomy", term="Chlamydiales [subtree] AND species[rank]", RetMax="100000")
	record = Entrez.read(handle)
	IdListOrganisms = record["IdList"]
	for organism in IdListOrganisms:
		if organism == "813":
			handle = Entrez.esearch(db="Taxonomy", term="txid"+organism+"[Organism]", RetMax="100000")
			record = Entrez.read(handle)
			StrainList = record["IdList"]
			for Strain in StrainList:
				if Strain == "471472":
					print Strain
'''

	Entrez.email = "s1mpmm41l@npclient.com"
	species = species.replace(" ", "+").strip()
	search = Entrez.esearch(term = species, db = "taxonomy", retmode = "xml")
	record = Entrez.read(search)

	print record
		
	if record['IdList'] != []:
		
		return record['IdList'][0]

	return 'none'

def combine_sets (CITES_dic):
	
	# Expand the CITES information with TNRS synonyms and Taxonomic IDs

	# parse through the different CITES appendixes and
	# and try to retrieve the TNRS synonyms and NCBI Taxonomic IDs
	# for each species

	species_count, ncbi_taxon = 0, 0

	for appendix in CITES_dic:
		for cell in CITES_dic[appendix][:10]:
			TNRS_data = TNRS(cell[0])
			if len(TNRS_data) != 3:
				print TNRS_data
				print cell[1]

				#if TNRS
				for alt in TNRS_data[1]:
					print ('als =  %s, taxon_id = %s' % (alt ,get_taxid(alt)))

			else:
				ncbi_taxon += 1

			species_count += 1
	
	print('Species count: %i, Taxon_ID count: %i' % (species_count, ncbi_taxon))

def main ():
	
	CITES_php = download_raw_CITES()
	CITES_dic = parse_php(CITES_php)
	combine_sets(CITES_dic)



if __name__ == "__main__":
    main()
