#usr/bin/env python

## useful imports
import time
import io
import os
import re
import subprocess
import sys
from sys import argv
from datetime import datetime
from io import open

## configuration
import configparser
import concurrent.futures

#####################
#### functions ######
#####################

def help_options():
	print ("\n#######################################################################")
	print ("  NAME: fromRaw_to_isomiR")
	print ("  VERSION: 0.4")
	print ("  AUTHORS: Antonio Luna de Haro (v0.1) & Jose F Sanchez-Herrero (v1).")
	print ("           Copyright (C) 2018-2019 Lauro Sumoy Lab, IGTP, Spain")
	print ("#########################################################################")
	print ("\nDESCRIPTION:")
	print ("- This script is a pipeline generated for the analysis of paired-end or single end reads from small RNA-seq data.")
	print ("\n- Available analysis are:")
	print ("\t+ General:")
	print ("\t\t+ Trimming using Cutadapt")
	print ("\t\t+ Merge paired-end reads using FastqJoin")
	print ("\t\t+ RNA Biotype analysis using STAR.")
	print ("\n\t+ Small RNA seq:")
	print ("\t\t+ miRNA-isomiR analysis using sRNAtoolbox ")
	print ("\t\t+ tRFs using MINTmap and MINTbase.")
	print ("")
	print ("USAGE:\npython3", os.path.abspath(argv[0]),"config_file.txt ")
	print ("\nPARAMETERS:")
	print ("A configuration file is necessary that includes general and detailed information for the project.")
	print ("")
	print ("*******************************************************")
	print (" Configuration file details:")
	print ("*******************************************************")
	print ("")
	print ("")
	print ("*******************************************************")
	print ("")
	print ("")
	print ("CITATION:")
	print ("[to add citation]")
	print ("")
	print ("")
	print ("DOCUMENTATION:")
	print ("See [ <http://website/> ] for full documentation")
	print ("")
	print ("")
	print ("LICENSE:")
	print ("This program is free software: you can redistribute it and/or modify")
	print ("it under the terms of the GNU General Public License as published by")
	print ("the Free Software Foundation, either version 3 of the License, or")
	print ("(at your option) any later version.")
	print ("")
	print ("This program is distributed in the hope that it will be useful,")
	print ("but WITHOUT ANY WARRANTY; without even the implied warranty of")
	print ("MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the")
	print ("GNU General Public License for more details.")
	print ("")
	print ("You should have received a copy of the GNU General Public License")
	print ("along with this program.  If not, see <http://www.gnu.org/licenses/>.")
	print ("")
	print ("")
	print ("#################################################\n\n")
###############

###############   
def gettime (start_time):
    total_sec = time.time() - start_time
    m, s = divmod(int(total_sec), 60)
    h, m = divmod(m, 60)
    return h, m, s
###############   
    
###############   
def create_subfolder (name, path):
    ## create subfolder  ##	
	subfolder_path = path + "/" + name
	    
    # define the access rights
	try:
		os.mkdir(subfolder_path, access_rights)
	except OSError:  
	   	print ("\tDirectory %s already exists" % subfolder_path)
	else:  
		print ("\tSuccessfully created the directory %s " % subfolder_path)
	
	print ("")
	return subfolder_path
###############   
    
###############   
def timestamp (start_time_partial):
	h,m,s = gettime(start_time_partial)
	print ('--------------------------------')
	print ('(Time spent: %i h %i min %i s)' %(int(h), int(m), int(s)))
	print ('--------------------------------')
	return time.time()
############### 

###############
def select_samples (samples_prefix, path_to_samples):
    
    #Get all files in the folder "path_to_samples"    
	files = os.listdir(path_to_samples)
	sample_list = []
	for fastq in files:	
		samplename_search = re.search(r"(%s)\_(\d{1,2})\_([a-zA-Z]{6})(.*)" % samples_prefix, fastq)
		if samplename_search:
			if 'merged' not in fastq:
				if fastq.endswith('.gz'):
					sample_list.append(fastq[:-3])
				elif fastq.endswith('fastq'):
					sample_list.append(fastq)
				else:
					print ("** ERROR: ", fastq, 'is a file that is neither in fastq.gz or .fastq format, so it is not included')

	non_duplicate_samples = list(set(sample_list))
	number_samples = len(non_duplicate_samples)
	
	print ("\t\t- ", number_samples," samples selected from ", path_to_samples)
	return sorted(non_duplicate_samples)
	
###############

###############
def command_sender(string2send):
	#print (string2send)
	try:
		subprocess.check_output(string2send, shell = True)
	except subprocess.CalledProcessError as err:
		print ('')
		
###############

###############
def sender(list_cmd):
	
	# We can use a with statement to ensure threads are cleaned up promptly
	with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
		# Start the load operations and mark each future with its URL
		commandsSent = { executor.submit(command_sender, commands): commands for commands in list_cmd }	
		for cmd2 in concurrent.futures.as_completed(commandsSent):
			details = commandsSent[cmd2]
			try:
				data = cmd2.result()
			except Exception as exc:
				print ('***ERROR:')
				print (string2send)
				print('%r generated an exception: %s' % (details, exc))
###############
 
###############    
def one_file_per_sample(final_sample_list, path_to_samples, directory, read, output_file):
	## merge sequencing files for sample, no matter of sector or lane generated.
	grouped_subsamples = []
	bigfile_list = []
	commands2sent = []
	
	output_file = open(output_file, 'a')
	output_file.write("\nMerge samples:\n")
	
	for samplex in final_sample_list:
		if samplex not in grouped_subsamples:
			samplename = []
			subsamples = []
			for prefix in prefix_list:
				samplename_search = re.search(r"(%s)\_(\d{1,2})\_([a-zA-Z]{6})(.*)" % prefix, samplex)
				if samplename_search:			
					name = samplename_search.group(1)
					sample = samplename_search.group(2)
					original_name = name + "_" + sample + "_"
					commonname = name + "_" + sample + "_" + read + ".fastq"
					bigfilepath = directory + "/" + commonname
					bigfile_list.append(commonname)	
					
					for sampley in final_sample_list:
						if original_name in sampley:
							subsamples.append(path_to_samples + "/" + sampley)
							grouped_subsamples.append(sampley)
					if not os.path.isfile(bigfilepath) or os.stat(bigfilepath).st_size == 0:
						partsofsample = ' '.join(sorted(subsamples))
						cmd = 'cat %s >> %s' %(partsofsample, bigfilepath)						
						## DUMP in file					
						output_file.write(cmd)   
						output_file.write('\n')						
						## get command				
						commands2sent.append(cmd)
					else:
						print ('\t + Sample %s is already merged' % commonname)
	
	## close file
	output_file.close()		
	#sent commands on threads
	sender(commands2sent)	
	print ('There are' , len(bigfile_list) , 'samples after merging for read' , read, '\n')
	return bigfile_list
	
###############

###############
def get_symbolic_link (final_sample_list, path_to_samples, directory):
	for samplex in final_sample_list:
		sample_path = path_to_samples + '/' + samplex
		cmd = 'ln -s %s %s' %(sample_path, directory)
		try:
			print ('Symbolic link sample ', samplex)
			subprocess.check_output(cmd, shell = True)
		except subprocess.CalledProcessError as err:
			print (err.output)
			#sys.exit()

	files2return = os.listdir(directory)
	return files2return
###############

###############   
def cutadapt (list_R1, list_R2, path, out_path, file_name):
	trimmed_R1 = []
	trimmed_R2 = []
	command2sent = []	
	output_file = open(file_name, 'a')
	output_file.write("\nTrim samples:\n")
	
	for file_R1 in list_R1:
		file_R1_path = path + "/" + file_R1
		cmd = []
		cutadapt_exe = config['EXECUTABLES']['cutadapt']  	
		adapter_3 = config['PARAMETERS']['adapter_3']		
		for prefix in prefix_list:
			sampleR1_search = re.search(r"(%s)\_(\d{1,2})\_(.*)" % prefix, file_R1)
			if sampleR1_search:
				name = sampleR1_search.group(1) + '_' + sampleR1_search.group(2)
				path_name = out_path + "/" + name
				common = path_name + '_trimmed_'
				o_param = common + "R1.fastq"
				p_param = common + "R2.fastq"
				trimmed_R1.append(o_param)
				logfile = common + 'logfile.txt'

				if paired_end == False:
					## single-end
					cmd = '%s -a %s -o %s %s > %s' %(cutadapt_exe, adapter_3, o_param, file_R1_path, logfile)
				else: ## paired-end
					if list_R2: ## paired-end
						sampleR2 = path + "/" + sampleR1_search.group(1) + '_' + sampleR1_search.group(2) + '_R2.fastq'
						try:
							os.path.isfile(sampleR2)					
						except:
							print ("**ERROR: pair for sample ",o_param," doest not exist")
							print ("Sample will be treated as single end")
							## set cmd for single eng as no R2 file
							cmd = '%s -a %s -o %s %s' %(cutadapt_exe, adapter_3, o_param, file_R1_path)
						else:
							#paired end:
							adapter_5 = config['PARAMETERS']['adapter_5']
							file_R2_path = sampleR2
							cmd = '%s -a %s -A %s -o %s -p %s %s %s > %s' %(cutadapt_exe, adapter_3, adapter_5, o_param, p_param, file_R1_path, file_R2_path, logfile)
							trimmed_R2.append(p_param)
					else:
						## single-end
						cmd = '%s -a %s -o %s %s > %s' %(cutadapt_exe, adapter_3, o_param, file_R1_path, logfile)
	
				if (os.path.isfile(o_param)):
					if (os.path.isfile(p_param)):
						print ('\tSample %s is already trimmed in paired-end mode' % name)
					else:
						print ('\tSample %s is already trimmed in single-end mode' % name)	
				## not trimmed
				else: 
					## DUMP in file					
					output_file.write(cmd)   
					output_file.write('\n')	
					# get command 
					command2sent.append(cmd)
					
	## close file
	output_file.close()
	#sent commands on threads			
	sender(command2sent)

	return trimmed_R1, trimmed_R2
###############

###############     
def fastqjoin (trimmed_R1, trimmed_R2, out_path, file_name):
	joined_files = []
	cmd = []
	command2sent = []
	
	output_file = open(file_name, 'a')
	output_file.write("\nfastqjoin samples:\n")
	
	fastqjoin_exe = config['EXECUTABLES']['fastqjoin']    	
	error_param = config['PARAMETERS']['fastqjoin_percent_difference']
	for file_R1 in trimmed_R1:
	
		for prefix in prefix_list:
			sampleR1_search = re.search(r"(%s)\_(\d{1,2})\_(.*)" % prefix, file_R1)
			if sampleR1_search:
				# names
				name = sampleR1_search.group(1) + '_' + sampleR1_search.group(2)
				path_name = out_path + '/' + name + '_trimmed_join.fastq'
				unjoined_1 = out_path + '/' + name + '_trimmed_unjoin_R1.fastq'
				unjoined_2 = out_path + '/' + name + '_trimmed_unjoin_R2.fastq'
				joined_files.append(path_name)				
				logfile = out_path + '/' + name + '_logfile.txt'
			
				## get read2
				string2search = '.*' + name + '.*'
				regex=re.compile(string2search)			
				sampleR2 = [m.group(0) for l in trimmed_R2 for m in [regex.search(l)] if m]

				##
				if sampleR2[0] in trimmed_R2:
					cmd = fastqjoin_exe + ' -p %s %s %s -o %s -o %s -o %s > %s' %(error_param, file_R1, sampleR2[0], unjoined_1, unjoined_2, path_name, logfile)
				else: ## single-end
					cmd = 'cp %s %s' %(file_R1, path_name)
				if (os.path.isfile(path_name)):
					print ('\tSample %s is already joined' %name)
				else: ## not merged
					## Dump in file
					output_file.write(cmd)
					output_file.write('\n')	
					# get command
					command2sent.append(cmd)

	## close file
	output_file.close()				
	#sent commands on threads			
	sender(command2sent)

	## ToDOs: count and provide statistics for joined reads
	return joined_files
###############       
    
###############       
def sRNAbench (joined_reads, outpath, file_name):
	results = []
	sRNAbench_exe = config['EXECUTABLES']['sRNAbenchtoolbox'] + 'exec/sRNAbench.jar'
	sRNAbench_db = config['EXECUTABLES']['sRNAbenchtoolbox']
	command2sent = []
	## open
	output_file = open(file_name, 'a')

	for jread in joined_reads:
		for prefix in prefix_list:
			sample_search = re.search(r"(%s)\_(\d{1,2})\_(.*)" % prefix, jread)
			if sample_search:
				outdir = sample_search.group(1) + "_" + sample_search.group(2)
				finalpath = outpath + '/' + outdir + '/'
				logfile	= outpath + '/' + outdir + '_logfile.txt'			
				results.append(finalpath)				
				if (os.path.isdir(finalpath)):
					print ('\tisomiRs analysis for sample %s already exists' %outdir)
				else:
					cmd = 'java -jar %s dbPath=%s input=%s output=%s microRNA=hsa isoMiR=true plotLibs=true graphics=true plotMiR=true bedGraphMode=true writeGenomeDist=true chromosomeLevel=true chrMappingByLength=true > %s' %(sRNAbench_exe, sRNAbench_db, jread, finalpath, logfile)
					# print into file
					output_file.write(cmd)
					output_file.write('\n')				
					# get command
					command2sent.append(cmd)
	
	## close file
	output_file.close()				
	#sent commands on threads			
	sender(command2sent)
	return results
###############   
    
###############   
def miRTop (results, outpath, output_file):

	## sent miRTop using threads	
	# We can use a with statement to ensure threads are cleaned up promptly
	with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
		# Start the load operations and mark each future with its URL
		commandsSent = { executor.submit(miRTop_threads, fol, outpath, output_file): fol for fol in results }
		for cmd2 in concurrent.futures.as_completed(commandsSent):
			details = commandsSent[cmd2]
			try:
				data = cmd2.result()
			except Exception as exc:
				print ('***ERROR:')
				print (string2send)
				print('%r generated an exception: %s' % (details, exc))
	
	## return gtf file generated/retrieved
	gtfs2return = []
	for folder in results:
		name = folder.split('/')[-2]
		gtf_name = outpath + '/' + name + "/" + name + ".gff"
		gtfs2return.append(gtf_name)
	return gtfs2return
###############

###############
def miRTop_threads(folder, outpath, file_name):
	gtfs = []
	sRNAbench_hairpin = config['EXECUTABLES']['sRNAbenchtoolbox'] + 'libs/hairpin.fa'
	mirtop_exec = config['EXECUTABLES']['mirtop_exec']
	miRNA_gff = config['FILES']['miRNA_gff']	
	species = 'hsa' #homo sapiens
	name = folder.split('/')[-2]
	outdir = outpath + '/' + name
	outdir_stats = outdir + "/stats"
	outdir_gtf = outdir + "/" + name + ".gff"
	logfile = outdir + '_logfile.txt'

	## open file
	output_file = open(file_name, 'a')
	
	## start process
	if folder.endswith("/"):
		folder = folder[:-1]
		
	reads_annot = folder + "/reads.annotation"
	if not (os.path.isfile(reads_annot)):
		#print ("\n##########################################")
		print ('No isomiRs detected for sample %s' %name)
		#print ("##########################################")
		return ""
	
	if (os.path.isdir(outdir)):
		print ('\tSample %s has already an isomiRs gtf file' %name)
	else:
		cmd = mirtop_exec + ' gff --sps %s --hairpin %s --gtf %s --format srnabench -o %s %s 2> %s' %(species, sRNAbench_hairpin, miRNA_gff, outdir, folder, logfile)
		output_file.write(cmd)
		output_file.write('\n')
		try:
			#print ("\n##########################################")
			print ('Creating isomiRs gtf file for sample %s' %name)
			#print ("-------------------------------------------")
			# ToDOs: print to file mirtop_info.txt
			#print ('The following cmd is being executed at the shell: \n', cmd)
			subprocess.check_output(cmd, shell = True)
		except subprocess.CalledProcessError as err:
			print (err.output)
			sys.exit()
		## get stats for each
	if (os.path.isdir(outdir_stats)):
		print ('\tSample %s has already an isomiRs stats folder' %name)
	else:
		cmd_stats = mirtop_exec + ' stats -o %s %s 2>> %s' %(outdir_stats, outdir_gtf, logfile)
		output_file.write(cmd_stats)
		output_file.write('\n')		
		try:
			#print ("\n##########################################")
			print ('Creating isomiRs stats for sample %s' %name)
			#print ("-------------------------------------------")
			# ToDOs: print to file mirtop_info.txt
			#print ('The following cmd is being executed at the shell: \n', cmd_stats)
			#print ("##########################################")
			subprocess.check_output(cmd_stats, shell = True)
		except subprocess.CalledProcessError as err:
			print (err.output)
			#sys.exit()

	# close
	output_file.close()
###############sRNAbenchtoolbox:

###############
def isomiR_analysis (path, count, reads, time_partial, file_name):
	##############################
    ####### Step: sRNAbench ######
	##############################
	## open file
	output_file = open(file_name, 'a')
	output_file.write("\nsRNAbench samples:\n")
	output_file.close()
	
	print ("\n+ Run sRNAbenchtoolbox:")
	name_sRNAbench_folder = str(count) + '.1.isomiR_sRNAbenchtoolbox'
	sRNAbench_folder = create_subfolder(name_sRNAbench_folder, path)
	results = sRNAbench(reads, sRNAbench_folder, file_name)	
	## timestamp
	time_partial = timestamp(time_partial)
	
	############################
    ####### Step: miRTop #######
	############################
	## open file
	output_file = open(file_name, 'a')
	output_file.write("\nmiRTop samples:\n")
	output_file.close()
	name_miRTop_folder = str(count) + '.2.isomiR_miRTop'
	miRTop_folder = create_subfolder(name_miRTop_folder, path)
	gtfs=miRTop(results, miRTop_folder, file_name)	
	## timestamp
	time_partial = timestamp(time_partial)

	##############################################
    ####### Step: create expression matrix #######
	##############################################
	name_isomiR_matrix_folder = str(count) + '.3.isomiR_matrix'
	isomiR_matrix_folder = create_subfolder(name_isomiR_matrix_folder, path)

	for gtffile in gtfs:
		sample = gtffile.rpartition('/')[-1][:-4]
		print ("\tParsing sample", sample)
		filename = isomiR_matrix_folder + '/' + sample + '.tsv'

		## parse gtf file & create matrix
		if not (os.path.isfile(filename)):
			if (os.path.isfile(gtffile)):
				parse_gtf(gtffile, filename, sample)
				print ('\t + Expression matrix created...')
			else:
				print ('\t - Information is missing for sample ', sample)
		else:
			print ('\t + Expression matrix already exists...')
			
	## timestamp
	time_partial = timestamp(time_partial)
	return time_partial	
###############

###############   
def parse_gtf(gtffile, filename, sample):

	gtfile = open(gtffile)
	text = gtfile.read()
	lines = text.splitlines()
	sample_dict = {}
	
	## Open file
	fil = open(filename, 'w')    
	string2write = 'type\tsample_name\tident\tname\tvariant\texpression\tseq\n'
	fil.write(string2write)
	for line in lines:
		if not line.startswith('#'):        
			#print ('## ',line)
			seq = line.split('\t')[-1].split(';')[0].split("Read=")[-1]
			ident = line.split('\t')[0]
			name = line.split('\t')[-1].split(';')[2].split("Name=")[-1]
			parent = line.split('\t')[-1].split(';')[3].split("Parent=")[-1]
			variant = line.split('\t')[-1].split(';')[4].split("Variant=")[-1]
			expression = str(line.split('\t')[-1].split(';')[6].split("Expression=")[-1])			
			string2write = 'isomiR\t' + sample + '\t' + ident + '\t' + name + '\t' + variant + '\t' + expression + '\t' + seq + '\n'
			fil.write(string2write)
			
	fil.close()      
###############

###############
def MINTmap(reads, folder, file_name):
	MINTmap = config['EXECUTABLES']['MINTmap_folder'] + 'MINTmap.pl'	
	MINTmap_table = config['EXECUTABLES']['MINTmap_folder'] + 'LookupTable.tRFs.MINTmap_v1.txt'
	MINTmap_tRNAseq = config['EXECUTABLES']['MINTmap_folder'] + 'tRNAspace.Spliced.Sequences.MINTmap_v1.fa'
	MINTmap_tRF = config['EXECUTABLES']['MINTmap_folder'] + 'OtherAnnotations.MINTmap_v1.txt'	
	MINTmap_MINTplates = config['EXECUTABLES']['MINTmap_folder'] + 'MINTplates/'
	results = []
	command2sent = []
	
	## open file
	output_file = open(file_name, 'a')
	output_file.write("\nMINTmap:\n")
	
	for jread in reads:	
		for prefix in prefix_list:
			sample_search = re.search(r"(%s)\_(\d{1,2})\_(.*)" % prefix, jread)
			if sample_search:
				outdir = sample_search.group(1) + "_" + sample_search.group(2)
				sample_folder =  folder + '/' + outdir + '/'
				results.append(sample_folder)
				logfile = sample_folder + outdir + '_logfile.txt'
				if (os.path.isdir(sample_folder)):
					print ('\tMINTmap analysis for sample %s already exists' %outdir) 		
				else:
					#MINTmap.pl -f trimmedfastqfile [-p outputprefix] [-l lookuptable] [-s tRNAsequences] [-o tRFtypes] [-d customRPM] [-a assembly] [-j MINTplatesPath] [-h]
					fol = create_subfolder(outdir, folder)
					cmd = 'perl '+ MINTmap + ' -f %s -p %s -l %s -s %s -o %s -j %s > %s' %(jread, sample_folder + outdir, MINTmap_table, MINTmap_tRNAseq, MINTmap_tRF, MINTmap_MINTplates, logfile) 
					# get command
					command2sent.append(cmd)
					# print into file
					output_file.write(cmd)
					output_file.write('\n')

	#sent commands on threads			
	sender(command2sent)
	output_file.close()
	return results		
###############

###############
def tRFs_analysis(path, count, reads, time_partial, output_file):
	##############################
    ####### Step: sRNAbench ######
	##############################
	print ("\n+ Run MINTmap: ")
	name_MINTmap_folder = str(count) + '.1.tRFs_MINTmap'
	MINTmap_folder = create_subfolder(name_MINTmap_folder, path)
	results = MINTmap(reads, MINTmap_folder, output_file)
	
	print ("\n+ Get MINTmap matrix: ")
	name_MINTmap_matrix = str(count) + '.2.tRFs_matrix'
	MINTmap_matrix_folder = create_subfolder(name_MINTmap_matrix, path)

	for folder in results:
		files = os.listdir(folder)
		for item in files:
			if 'countsmeta' in item:
				continue
			if item.endswith('html'):
				continue
			if 'ambigu' in item:
				parse_tRF(folder, item, MINTmap_matrix_folder, 'ambiguous')		
			elif 'exclu' in item:
				parse_tRF(folder, item, MINTmap_matrix_folder, 'exclusive')		
	
	## timestamp
	time_partial = timestamp(time_partial)
	
###############
def parse_tRF(path, fileGiven, matrix_folder, ident):
	pathFile = path + '/' + fileGiven
	sample_search = re.search('(.*)\-MINTmap_v1.*', fileGiven)	
	if sample_search:
		sample_name = sample_search.group(1)
		#sample_folder =  matrix_folder + '/' + sample_name
		skip = 0
		tsv_file = matrix_folder + '/' + sample_name + '_' + ident + '.tsv'
		if os.path.isfile(tsv_file):
			print ('\tMatrix for ', sample_name , ' (' + ident + ') is already generated')
			skip = 1
		if skip == 0:
 			## Open file
			fil = open(tsv_file, 'w')    
			string2write = 'type\tsample_name\tident\tname\tvariant\texpression\tseq\n'
			fil.write(string2write)
			## Read file
			expression_file = open(pathFile)
			expression_text = expression_file.read()
			expression_lines = expression_text.splitlines()
			for line in expression_lines:
				if not line.startswith('MINTbase'):
					ID = line.split('\t')[0]
					seq = line.split('\t')[1]
					variant = line.split('\t')[2]
					expression = line.split('\t')[3]
					string2write = 'tRFs\t'+ sample_name + '\t' + ident + '\t' + ID +'\t' + variant + '\t' + expression + '\t' + seq+ '\n'
					fil.write(string2write)

			fil.close()
###############

###############
def mapReads(read, folder, output_file_name):
	## open file
	output_file = open(output_file_name, 'a')
	output_file.write("\nSTAR command for Mapping RNA:\n")
	
	STAR_exe = config['EXECUTABLES']['STAR_exe']
	genomeDir = config['FILES']['STAR_genomeDir']
	num_threads = config['VARIABLES']['thread']
	limitRAM_option = config['PARAMETERS']['limitRAM']
	
	## For many samples it will have to load genome index in memory every time.
	## For a unique sample it will not matter. Take care genome might stay in memory.
	## Use before loop option LoadAndExit and then:
		## in loop
		## Use option LoadAndKeep, set shared memory > 30 Gb
	## when finished loop Remove memory		
	## Send a process for each sample
	command2sent = []
	item = 0
	results_STAR = {}
	for jread in read:
		for prefix in prefix_list:
			sample_search = re.search(r"(%s)\_(\d{1,2})\_(.*)" % prefix, jread)
			if sample_search:
				outdir = sample_search.group(1) + "_" + sample_search.group(2)
				sample_folder =  folder + '/' + outdir + '/'
				logfile = sample_folder + outdir + '_logfile.txt'
				out_folder = create_subfolder(outdir, folder)
				bam_file = sample_folder + 'Aligned.sortedByCoord.out.bam'

				## to return
				results_STAR[outdir] = bam_file

				if (os.path.isfile(bam_file)):
					print ('\tMapping for sample %s is done...' %outdir)
				else:
					## prepare command
					cmd = "%s --genomeDir %s --runThreadN 1 --readFilesIn %s " %(STAR_exe, genomeDir, jread)
					## all this options and parameters have been obtained from https://www.encodeproject.org/rna-seq/small-rnas/
					cmd = cmd + "--outFilterMultimapNmax 1 --alignIntronMax 1"
					cmd = cmd + "--outFilterMismatchNoverLmax 0.03 --outFilterScoreMinOverLread 0 --outFilterMatchNminOverLread 0 --outFilterMatchNmin 16 "
					cmd = cmd + "--outSAMheaderHD @HD VN:1.4 SO:coordinate --outSAMtype BAM SortedByCoordinate "
					cmd = cmd + "--genomeLoad LoadAndKeep --alignSJDBoverhangMin 1000 "
					cmd = cmd + "--limitBAMsortRAM %s --outFileNamePrefix %s > %s" %(limitRAM_option, sample_folder, logfile)
					# get command
					command2sent.append(cmd)
					# print into file
					output_file.write(cmd)
					output_file.write('\n')
					item = item + 1
	
	## check if samples are done
	if (item > 1):	
		## --genomeLoad Remove
		removeDir = 'RemoveMem'
		remove_folder = create_subfolder(removeDir, folder)
		cmd_RM = "%s --genomeDir %s --outFileNamePrefix %s --runThreadN %s --genomeLoad Remove" %(STAR_exe, genomeDir, remove_folder, num_threads)
		## send command	
		try:
			print ('\t+ Removing previous memory loaded for STAR mapping (if any)')
			subprocess.check_output(cmd_RM, shell = True)
		except subprocess.CalledProcessError as err:
			print (err.output)	
	
		## --genomeLoad LoadAndExit
		LoadDir = 'LoadMem'
		Load_folder = create_subfolder(LoadDir, folder)
		cmd_LD = "%s --genomeDir %s --runThreadN %s --outFileNamePrefix %s --genomeLoad LoadAndExit" %(STAR_exe, genomeDir, num_threads, Load_folder)
		## send command	
		try:
			print ('\t+ Loading memory for STAR mapping')
			subprocess.check_output(cmd_LD, shell = True)
		except subprocess.CalledProcessError as err:
			print (err.output)
		# print into file
		output_file.write(cmd_LD)
		output_file.write('\n')
		print ("\t+ Done...\n")
		print ("\t+ Mapping now...\n")
		
		#sent commands on threads			
		sender(command2sent)	
	
		## --genomeLoad Remove
		removeDir = 'RemoveMem'
		remove_folder = create_subfolder(removeDir, folder)
		cmd_RM = "%s --genomeDir %s --outFileNamePrefix %s --runThreadN %s --genomeLoad Remove" %(STAR_exe, genomeDir, remove_folder, num_threads)
		## send command	
		try:
			print ('\t+ Removing memory loaded for STAR mapping')
			subprocess.check_output(cmd_RM, shell = True)
		except subprocess.CalledProcessError as err:
			print (err.output)
	
		# print into file
		output_file.write(cmd_RM)
		output_file.write('\n')
	else:
		## there is no need to load info on memory as there are no samples to process
		## They are all done already
		print ("")	
	
	output_file.close()					

	return results_STAR
###############

###############
def parse_RNAbiotype(bam, ID, output_file_name, RNABiotype_folder):
	## call script to get RNAbiotype
	# get path for file
	RNAbiotype_script = os.path.dirname(argv[0]) + '/tools/RNAbiotype.py'
	
	## create folder	
	name_RNABiotype_sample = str(ID)
	RNABiotype_folder_sample = create_subfolder(name_RNABiotype_sample, path=RNABiotype_folder)	
	## get variables
	gtf_annotation = config['FILES']['gtf_file']
	featureCount_bin = config['EXECUTABLES']['featureCount_exe']	
	cmd = ('python3 %s %s %s %s %s %s' %(RNAbiotype_script, bam, RNABiotype_folder_sample, gtf_annotation, featureCount_bin, output_file_name))
	## send command	
	try:
		print ('\t+ Parsing mapping reads for RNAbiotype results for samples %s' %ID)
		subprocess.check_output(cmd, shell = True)		
	except subprocess.CalledProcessError as err:
		print (err.output)
		
###############

def BAMtoPILFER(bam, ID, piRNA_folder, command_file_name, bed_file, repeatmasker_bed):

	output_file = open(command_file_name, 'a')	
	name_piRNA_folder_sample = str(ID)
	folder_sample = create_subfolder(name_piRNA_folder_sample, piRNA_folder)		

	## results conversion	
	split_name_bam = os.path.splitext( os.path.basename(bam) )
	pilfer_file = folder_sample + '/' + split_name_bam[0] + '.pilfer.bed'

	bedtools_bin = config['EXECUTABLES']['bedtools_exe']	
	samtools_bin = config['EXECUTABLES']['samtools_exe']

	print ('+ Convert BAM file in PILFER input file for sample %s' %ID)			
	if (os.path.isfile(pilfer_file)):
		print ('\t + Conversion done for sample %s' %ID)		
	else:
		## call script to get convert bam into PILFER Input
		# get path for file
		PILFERconversion_script = os.path.dirname(argv[0]) + '/tools/convertBAMtoPILFER.py'
		print ('\t+ Converting BAM file in PILFER input for sample %s' %ID)
		cmd = ('python3 %s %s %s %s %s %s' %(PILFERconversion_script, bam, folder_sample, bedtools_bin, samtools_bin, command_file_name ))
		output_file.write(cmd)
		output_file.write('\n')
		## send command	
		try:
			subprocess.check_output(cmd, shell = True)
		except subprocess.CalledProcessError as err:
			print (err.output)

	## discard other non-coding annotations
	# bedtools substract	
	print ('+ Filter PILFER input file for sample %s' %ID)			
	ncRNA_bed = bed_file
	filter_pilfer_file = folder_sample + '/' + split_name_bam[0] + '.pilfer_filtered.bed'
	if (os.path.isfile(filter_pilfer_file)):
		print ('\t+ PILFER file filtered for %s' %ID)
	else:
		cmd_subtract = '%s subtract -b %s -a %s -s -f 0.5 -A > %s' %(bedtools_bin, ncRNA_bed, pilfer_file, filter_pilfer_file)
		output_file.write(cmd_subtract)
		output_file.write('\n')
		## send command	
		try:
			subprocess.check_output(cmd_subtract, shell = True)
		except subprocess.CalledProcessError as err:
			print (err.output)

	## generate clusters
	# pilfer
	print ('+ Generate PILFER clusters for sample %s' %ID)			
	pilfer_cluster = folder_sample + '/' + split_name_bam[0] + '.pilfer_clustered.bed'
	pilfer_python = config['EXECUTABLES']['pilfer']
	if (os.path.isfile(pilfer_cluster)):
		print ('\t+ PILFER file clustered for %s' %ID)
	else:
		cmd_pilfer = 'python2 %s -i %s > %s' %(pilfer_python, filter_pilfer_file, pilfer_cluster)
		output_file.write(cmd_pilfer)
		output_file.write('\n')

		## send command	
		try:
			subprocess.check_output(cmd_pilfer, shell = True)
		except subprocess.CalledProcessError as err:
			print (err.output)

	## intersect with repeat annotations
	# bedtools intersect -a <path/>retro-transposons.bed -b $out_dir_prefix"bed/ncrna_subtract_putative/"$prefix.bed -s -F 1 -wa -wb |
	# awk 'BEGIN{OFS="\t"}{print $7,$8,$9,$10,$11,$12,$4}' > $out_dir_prefix"bed/TE_origin/"$prefix
	pilfer_intersect = folder_sample + '/' + split_name_bam[0] + '.pilfer_clustered_intersection.bed'

	if (os.path.isfile(pilfer_intersect)):
		print ('\t+ PILFER file intersected for %s' %ID)
	else:
		cmd_intersect = '%s intersect -a %s -b %s -s -F 1 -wa -wb > %s' %(bedtools_bin, repeatmasker_bed, filter_pilfer_file, pilfer_intersect)
		output_file.write(cmd_intersect)
		output_file.write('\n')
		## send command	
		try:
			subprocess.check_output(cmd_intersect, shell = True)
		except subprocess.CalledProcessError as err:
			print (err.output)
			
	

	output_file.close()
	
###############
def	piRNA_analysis(path, count, bam_files, command_file_name, bed_file):

	output_file = open(command_file_name, 'a')
	output_file.write("\npiRNA Analysis:\n")
	print ("\n+ Run piRNA analysis: ")
	name_piRNA_folder = str(count) + '.piRNA'
	piRNA_folder = create_subfolder(name_piRNA_folder, path)

	## repeatmasker information
	# get path for file
	repeatmasker2bed = os.path.dirname(argv[0]) + '/tools/repeatMasker2bed.py'

	#send
	repeatmasker_file = config['FILES']['repeatmasker']
	info_file = config['FILES']['Sequence_Names']
	cmd_repeatmasker2bed = 'python3 %s %s %s %s' %(repeatmasker2bed, repeatmasker_file, info_file, piRNA_folder)

	print ("+ Check repeatmasker and generate BED annotation.")
	split_name_repeat = os.path.splitext( os.path.basename(repeatmasker_file) )
	repeatmasker_bed = piRNA_folder + '/' + split_name_repeat[0] + '.bed'
	
	if os.path.isfile(repeatmasker_bed):
		# do not send command
		print ("\t+ Repeatmasker BED file already exists")

	else:
		output_file.write("repeatmasker2bed conversion:\n")
		output_file.write(cmd_repeatmasker2bed)
		output_file.write('\n')		
		# send command
		try:
			subprocess.check_output(cmd_repeatmasker2bed, shell = True)
		except subprocess.CalledProcessError as err:
			print (err.output)
			exit()
	
	output_file.close()
	
	## bam_files is  a dictionary containing IDs and bam file paths
	# We can use a with statement to ensure threads are cleaned up promptly
	with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
		commandsSent = { executor.submit(BAMtoPILFER, bam, ID, piRNA_folder, command_file_name, bed_file, repeatmasker_bed): bam for ID, bam in bam_files.items() }
		for cmd2 in concurrent.futures.as_completed(commandsSent):
			details = commandsSent[cmd2]
			try:
				data = cmd2.result()
			except Exception as exc:
				print ('***ERROR:')
				print (cmd2)
				print('%r generated an exception: %s' % (details, exc))

	

###############

#***************************#
#*****		MAIN		****#
#***************************#
if __name__ == "__main__":

	start_time_total = time.time()
  
  	## control if options provided or help
	if len(sys.argv) > 1:
		print ("")
	else:
		help_options()
		exit()    	
	##
    	 
	print ("\n######## Starting Process ########")
	now = datetime.now()
	date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
	print (date_time, "\n")
  
    ########################
    ## get configuration  ##
	########################
	configuration_path_file = os.path.abspath(argv[1])
	config = configparser.ConfigParser()
	config.read(configuration_path_file)

	print ("------ Get configuration options ------")
	print ("Reading configuration file: ", configuration_path_file, "\n")
	
	## dump config file to stdout
	f = open(configuration_path_file, 'r')
	print ("\n***********************************************")
	configuration_file = f.read()
	f.close()
	print (configuration_file)
	print ("\n***********************************************")
	
	## configuration options:
	merge_option = config['VARIABLES']['merge_samples']
	analysis_option = config['VARIABLES']['option']
	num_threads = int(config['VARIABLES']['thread'])	
    
    ####################
    ## create folder  ##	
 	####################
	print ("\n------ Create project folder ------")
	project_name = config["GENERAL"]["project"]
	try:
		folder_path = os.path.abspath(project_name)
	except OSError:  
		path = os.getcwd()  
		print ("The current working directory is %s", path)
		print ("Folder for project name: ",  project_name, " will be created here")
		folder_path = path.append(project_name)
	    
	## generate file to print commands
	timeprint = now.strftime("%m%d%Y_%H%M")
	command_file_name = timeprint + '-commands.txt'
	command_file = open(command_file_name, 'w')    
	string2write = '\nStarting process: ' + date_time + '\n'
	command_file.write(string2write)
	    
    # define the access rights
	access_rights = 0o755
	try:
		os.mkdir(folder_path, access_rights)
	except OSError:  
	   	print ("Directory %s already exists" % folder_path)
	else:  
		print ("Successfully created the directory %s " % folder_path)
	
	print ("")
	## print out
	folder_string = '\nDirectory: ' + folder_path + '\n'
	command_file.write(folder_string)

    ## checking file(s) exists
	paired_end = False
	print ("------ Checking files provided ------")
	file_R1 = config["GENERAL"]["fastq_R1"]
	file_R2 = []
	if config.has_option("GENERAL","fastq_R2"):
		file_R2 = config["GENERAL"]["fastq_R2"]
		paired_end = True

	try:
		os.path.isfile(file_R1)
	except FileNotFoundError:
		print ("ERROR: No file R1 provided\n")
		print ("Exit")
		exit()
	else:
		print ("+ Folder for fastq R1 is readable and accessible")
    
	if paired_end:
		try:
		    os.path.isfile(file_R2)
		except FileNotFoundError:
			print ("+ Folder for fastq R2 does not exists")
			print ("+ Using single end option")
		else:
			print ("+ Folder for fastq R2 is readable and accessible")
			print ("+ Using paired-end option\n")
	else:
		print ("+ Using single end option")

    ## checking prefix provided
	print ("------ Checking prefix provided ------")
	prefix_option = config["VARIABLES"]["prefix"]
	prefix_list = prefix_option.split(",")
	for samples in prefix_list:
		print ("+ Samples with prefix %s will be retrieved" % samples)
	
	print ("")

	################################################
	print ("------ Starting pipeline ------")
	################################################
  	
	#####################################
    ####### Step1: select_samples #######
	#####################################
	all_list_R1 = []
	all_list_R2 = []

	print ("\n+ Select samples: ")
	if prefix_list == 'all':
		sample_listR1 = select_samples("all", file_R1)
		all_list_R1.extend(sample_listR1)

		if paired_end:
			sample_listR2 = select_samples("all", file_R2)
			all_list_R2.extend(sample_listR2)
	else:

		for samples in prefix_list:
			print ("\t+",samples,"samples")
			sample_listR1 = select_samples(samples, file_R1)
			all_list_R1.extend(sample_listR1)
			if paired_end:
				sample_listR2 = select_samples(samples, file_R2)
				all_list_R2.extend(sample_listR2)

	print ("")

	##################################
    ####### Step2: get_samples #######
	##################################
	sample_folder = []
	samplesR1 = []
	samplesR2 = []
	sample_folder = create_subfolder("1.samples", path=folder_path)

	### merge_option
	if merge_option == "YES":
		print ("\n+ Merge samples: ")
		samplesR1 = one_file_per_sample(all_list_R1, file_R1, sample_folder, read="R1", output_file=command_file_name)
		if paired_end:
			samplesR2 = one_file_per_sample(all_list_R2, file_R2, sample_folder, read="R2", output_file=command_file_name)
	else:
		print ("\n+ Retrieve samples:")
		samplesR1 = get_symbolic_link(all_list_R1, file_R1, sample_folder)
		if paired_end:
			samplesR2 = get_symbolic_link(all_list_R2, file_R2, sample_folder)
		
	## timestamp
	start_time_partial = timestamp(start_time_total)

	###############################
    ####### Step3: cutadapt #######
	###############################
	print ("\n+ Trimming samples: ")
	cutadapt_folder = create_subfolder("2.cutadapt", path=folder_path)
	trimmed_R1_return, trimmed_R2_return = cutadapt(samplesR1, samplesR2, sample_folder, cutadapt_folder, command_file_name)
	## timestamp
	start_time_partial = timestamp(start_time_partial)
		
	###############################
	####### Step: fastqjoin ######
	###############################
	folder_id = 3
	joined_read = []
	if paired_end:
		print ("\n+ Joining samples: ")
		name = str(folder_id) + ".fastqjoin"
		fastqjoin_folder = create_subfolder(name, path=folder_path)
		joined_read = fastqjoin(trimmed_R1_return, trimmed_R2_return, fastqjoin_folder, command_file_name)
		## timestamp
		start_time_partial = timestamp(start_time_partial)
		folder_id = folder_id + 1
	else:
		joined_read = trimmed_R1_return

	###################################
	######## Step: Map RNA reads ######
	###################################
	name_MapReads = str(folder_id) + ".MapRNA"
	MapReads_folder = create_subfolder(name_MapReads, path=folder_path)

	print ("\n+ Map RNA reads for samples: ")
	results_STAR = mapReads(joined_read, MapReads_folder, command_file_name)

	folder_id = folder_id + 1
	## timestamp
	start_time_partial = timestamp(start_time_partial)

	######################################
	########## RNA Biotype analisis ######
	######################################
	name_RNABiotype = str(folder_id) + ".RNA_Biotype"
	RNABiotype_folder = create_subfolder(name_RNABiotype, path=folder_path)

	## Get feature Counts and plot
	command_file.write('\nRNA biotype\n')
	print ("\n+ Get RNA Biotype for samples: ")
	with concurrent.futures.ThreadPoolExecutor(max_workers= int(num_threads)) as executor:
		# Start the load operations and mark each future with its URL
		commandsSent = { executor.submit(parse_RNAbiotype, bam, ID, command_file_name, RNABiotype_folder): bam for ID,bam in results_STAR.items() }
		for cmd2 in concurrent.futures.as_completed(commandsSent):
			details = commandsSent[cmd2]
			try:
				data = cmd2.result()
			except Exception as exc:
				print ('***ERROR:')
				print ('[CMD: %s ]' %details)
				print('%r generated an exception: %s' % (details, exc))

	folder_id = folder_id + 1
	## timestamp
	start_time_partial = timestamp(start_time_partial)

	######################################
	## Prepare GTF file for later
	######################################
	print ("\n+ Parsing GTF annotation for further analysis: ")
	# get path for file
	## save names
	GTF_file = config['FILES']['gtf_file']
	tmp_folder = create_subfolder("tmp", path=folder_path)
	split_name_GTF = os.path.splitext( os.path.basename(GTF_file) )		
	Exon_gtf = tmp_folder + '/' + split_name_GTF[0] + '_exon.gtf' 
	miRNA_gtf = tmp_folder + '/' + split_name_GTF[0] + '_miRNA.gtf' 
	ncRNA_bed = tmp_folder + '/' + split_name_GTF[0] + '_ncRNA.bed' 
	
	if (os.path.isfile(ncRNA_bed)):
		print ('\t+ Process is already done')
	else:
		command_file.write('Parse GTF')
		get_genetype_GTF = os.path.dirname(argv[0]) + '/tools/get_genetype_gtf.py'
		cmd_genetype_GTF = 'python3 %s %s %s' %(get_genetype_GTF, GTF_file, tmp_folder)
		command_file.write(cmd_genetype_GTF)

		# send command
		try:
			subprocess.check_output(cmd_genetype_GTF, shell = True)
		except subprocess.CalledProcessError as err:
			print (err.output)
			exit()

	######################################
	####### Step: Small RNA analysis #####
	######################################
	if analysis_option == "isomiR":
		isomiR_analysis(folder_path, folder_id, joined_read, start_time_partial, command_file_name)

	elif analysis_option == "tRFs":
		tRFs_analysis(folder_path, folder_id, joined_read, start_time_partial, command_file_name)

	elif analysis_option == "piRNA":
		piRNA_analysis(folder_path, folder_id, results_STAR, command_file_name, ncRNA_bed)
		
	elif analysis_option == "all":
		## isomiR
		isomiR_analysis(folder_path, folder_id, joined_read, start_time_partial, command_file_name)
		
		## tRFS
		folder_id = folder_id + 1
		## timestamp
		start_time_partial = timestamp(start_time_partial)
		tRFs_analysis(folder_path, folder_id, joined_read, start_time_partial, command_file_name)

		## timestamp
		start_time_partial = timestamp(start_time_partial)
		folder_id = folder_id + 1

		## piRNA analysis
		piRNA_analysis(folder_path, folder_id, results_STAR, command_file_name, ncRNA_bed)

	else:
		print ("**ERROR: No valid analysis provided: ", analysis_option)
		print ("Please provide: isomiR|tRFs|all")
		

	print ("\n*************** Finish *******************")
	start_time_partial = timestamp(start_time_total)

	command_file.close()      
	
#############################
