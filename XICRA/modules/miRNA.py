#!/usr/bin/env python3
##########################################################
## Jose F. Sanchez                                        ##
## Copyright (C) 2019 Lauro Sumoy Lab, IGTP, Spain        ##
##########################################################
"""
Create miRNA analysis using sRNAbenchtoolbox and miRTop.
"""
## import useful modules
import os
import sys
import re
import time
from io import open
import shutil
import concurrent.futures
from termcolor import colored

## import my modules
from XICRA.scripts import sampleParser
from XICRA.scripts import functions
from XICRA.config import set_config
from XICRA.modules import help_XICRA
from XICRA.scripts import generate_DE

##############################################
def run_miRNA(options):

    ## init time
    start_time_total = time.time()

    ##################################
    ### show help messages if desired    
    ##################################
    if (options.help_format):
        ## help_format option
        help_XICRA.help_fastq_format()
    elif (options.help_project):
        ## information for project
        help_XICRA.project_help()
        exit()
    elif (options.help_miRNA):
        ## information for join reads
        help_XICRA.help_miRNA()
        exit()
        
    ## debugging messages
    global Debug
    if (options.debug):
        Debug = True
    else:
        Debug = False
        
    ### set as default paired_end mode
    if (options.single_end):
        options.pair = False
    else:
        options.pair = True
    
    functions.pipeline_header()
    functions.boxymcboxface("Join paired-end reads")
    print ("--------- Starting Process ---------")
    functions.print_time()

    ## absolute path for in & out
    input_dir = os.path.abspath(options.input)
    outdir=""

    ## set mode: project/detached
    if (options.detached):
        outdir = os.path.abspath(options.output_folder)
        options.project = False
    else:
        options.project = True
        outdir = input_dir        
    
    ## get files
    if options.pair:
        pd_samples_retrieved = sampleParser.get_files(options, input_dir, "join", ['_trim_joined'])
    else:
        pd_samples_retrieved = sampleParser.get_files(options, input_dir, "trim", ['_trim'])
    
    ## debug message
    if (Debug):
        print (colored("**DEBUG: pd_samples_retrieve **", 'yellow'))
        print (pd_samples_retrieved)

    ## Additional sRNAbench or miRTop options
    
    ## miRNA_gff: can be set as automatic to download from miRBase
    if not options.miRNA_gff:
        print (colored("** ERROR: No miRNA gff file provided", 'red'))
        exit()
    else:
        options.miRNA_gff = os.path.abspath(options.miRNA_gff)

    ## generate output folder, if necessary
    if not options.project:
        print ("\n+ Create output folder(s):")
        functions.create_folder(outdir)
    ## for samples
    outdir_dict = functions.outdir_project(outdir, options.project, pd_samples_retrieved, "miRNA")
    
    ## optimize threads
    name_list = set(pd_samples_retrieved["new_name"].tolist())
    threads_job = functions.optimize_threads(options.threads, len(name_list)) ## threads optimization
    max_workers_int = int(options.threads/threads_job)

    ## debug message
    if (Debug):
        print (colored("**DEBUG: options.threads " +  str(options.threads) + " **", 'yellow'))
        print (colored("**DEBUG: max_workers " +  str(max_workers_int) + " **", 'yellow'))
        print (colored("**DEBUG: cpu_here " +  str(threads_job) + " **", 'yellow'))

    print ("+ Create a miRNA analysis for each sample retrieved...")    
    
    ## call miRNA_analysis: sRNAbench & miRTop
    ## dictionary results
    global results_dict
    results_dict = {}
    
    # Group dataframe by sample name
    sample_frame = pd_samples_retrieved.groupby(["new_name"])
    
    ## send for each sample
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers_int) as executor:
        commandsSent = { executor.submit(miRNA_analysis, sorted(cluster["sample"].tolist()), 
                                         outdir_dict[name], name, threads_job, options.miRNA_gff,
                                         Debug): name for name, cluster in sample_frame }

        for cmd2 in concurrent.futures.as_completed(commandsSent):
            details = commandsSent[cmd2]
            try:
                data = cmd2.result()
            except Exception as exc:
                print ('***ERROR:')
                print (cmd2)
                print('%r generated an exception: %s' % (details, exc))

    print ("\n\n+ miRNA analysis is finished...")
    
    ## outdir
    outdir_report = functions.create_subfolder("report", outdir)
    expression_folder = functions.create_subfolder("miRNA", outdir_report)

    ## debugging messages
    if options.debug:
        print (results_dict)
    
    ## merge all parse gtf files created
    print ("+ Summarize miRNA analysis for all samples...")
    generate_DE.generate_DE(results_dict, options.debug, expression_folder)

    print ("\n*************** Finish *******************")
    start_time_partial = functions.timestamp(start_time_total)
    print ("\n+ Exiting miRNA module.")
    exit()


###############
def miRNA_analysis(reads, folder, name, threads, miRNA_gff, Debug):
    
    ## create sRNAbench
    sRNAbench_folder = functions.create_subfolder('sRNAbench', folder)
    code_success = sRNAbench_caller(reads, sRNAbench_folder, name, threads, Debug) ## Any additional sRNAbench parameter?
        
    if not code_success:
        print ('** miRTop would not be executed for sample %s...' %name)
        return ()
    
    ## create miRTop
    miRTop_caller(sRNAbench_folder, folder, name, threads, miRNA_gff, Debug)
    
    ## parse gtf to accommodate all data
    filename = os.path.join(folder, 'miRTop', 'counts', 'mirtop.tsv')
    results_dict[name] = filename
    #parse_gtf.parse_gtf(sample_gff, filename, name, 'miRNA')

###############       
def sRNAbench_caller(reads, sample_folder, name, threads, Debug):
    # check if previously generated and succeeded
    filename_stamp = sample_folder + '/.success'
    if os.path.isfile(filename_stamp):
        stamp = functions.read_time_stamp(filename_stamp)
        print (colored("\tA previous command generated results on: %s [%s -- %s]" %(stamp, name, 'sRNAbench'), 'yellow'))
    else:
        # Call sRNAbench
        code_returned = sRNAbench(reads, sample_folder, name, threads, Debug)
        if code_returned:
            functions.print_time_stamp(filename_stamp)
        else:
            print ('** Sample %s failed...' %name)
            return(False)
        
    return(True)

###############       
def sRNAbench (reads, outpath, file_name, num_threads, Debug):
    
    sRNAbench_exe = set_config.get_exe("sRNAbench", Debug=Debug)
    sRNAbench_db = os.path.abspath(os.path.join(os.path.dirname(sRNAbench_exe), '..')) ## sRNAtoolboxDB
    logfile = os.path.join(outpath, 'sRNAbench.log')
    
    if (len(reads) > 1):
        print (colored("** ERROR: Only 1 fastq file is allowed please joined reads before...", 'red'))
        exit()
    
    ## create command    
    java_exe = set_config.get_exe('java', Debug=Debug)
    cmd = '%s -jar %s dbPath=%s input=%s output=%s' %(java_exe, sRNAbench_exe, sRNAbench_db, reads[0], outpath)  
    cmd = cmd + ' microRNA=hsa isoMiR=true plotLibs=true graphics=true' 
    cmd = cmd + ' plotMiR=true bedGraphMode=true writeGenomeDist=true'
    cmd = cmd + ' chromosomeLevel=true chrMappingByLength=true > ' + logfile 
    
    return(functions.system_call(cmd))

###############       
def miRTop_caller(sRNAbench_folder, sample_folder, name, threads, miRNA_gff, Debug):
    
    # check if previously generated and succeeded
    mirtop_folder = functions.create_subfolder('miRTop', sample_folder)

    mirtop_folder_gff = functions.create_subfolder('gff', mirtop_folder)
    mirtop_folder_stats = functions.create_subfolder('stats', mirtop_folder)
    mirtop_folder_counts = functions.create_subfolder('counts', mirtop_folder)

    filename_stamp = mirtop_folder_counts + '/.success'
    if os.path.isfile(filename_stamp):
        stamp = functions.read_time_stamp(filename_stamp)
        print (colored("\tA previous command generated results on: %s [%s -- %s]" %(stamp, name, 'miRTop'), 'yellow'))
    else:
        # Call miRTop
        code_returned = miRTop(sRNAbench_folder, mirtop_folder, name, threads, miRNA_gff, Debug)
        if code_returned:
            functions.print_time_stamp(filename_stamp)
        else:
            print ('** Sample %s failed...' %name)
            return(False)
        
        return(True)

###############
def miRTop(sRNAbench_folder, sample_folder, name, threads, miRNA_gff, Debug):

    miRTop_exe = set_config.get_exe('miRTop', Debug=Debug)
    sRNAbench_exe = set_config.get_exe("sRNAbench", Debug=Debug)
    sRNAbench_hairpin = os.path.abspath(os.path.join(os.path.dirname(sRNAbench_exe), '..', 'libs', 'hairpin.fa')) ## sRNAtoolboxDB
    species = 'hsa' #homo sapiens ## set as option if desired
    
    logfile = os.path.join(sample_folder, name + '.log')
    
    ## folders
    mirtop_folder_gff = os.path.join(sample_folder, 'gff')
    mirtop_folder_stats = os.path.join(sample_folder, 'stats')
    mirtop_folder_counts = os.path.join(sample_folder, 'counts')
    
    ## get sRNAbench info
    reads_annot = os.path.join(sRNAbench_folder, "reads.annotation")
    
    ## check non zero
    if not functions.is_non_zero_file(reads_annot):
        print (colored("\tNo isomiRs detected for sample [%s -- %s]" %(name, 'sRNAbench'), 'yellow'))
        return (False)
    
    ## miRTop analysis gff
    filename_stamp_gff = mirtop_folder_gff + '/.success'
    if os.path.isfile(filename_stamp_gff):
        stamp = functions.read_time_stamp(filename_stamp_gff)
        print (colored("\tA previous command generated results on: %s [%s -- %s - gff]" %(stamp, name, 'miRTop'), 'yellow'))
    else:
        print ('Creating isomiRs gtf file for sample %s' %name)
        cmd = miRTop_exe + ' gff --sps %s --hairpin %s --gtf %s --format srnabench -o %s %s 2> %s' %(species, sRNAbench_hairpin, miRNA_gff, mirtop_folder_gff, sRNAbench_folder, logfile)
        
        ## execute
        code_miRTop = functions.system_call(cmd)
        if code_miRTop:
            functions.print_time_stamp(filename_stamp_gff)
        else:
            return(False)
        
    ## miRTop stats
    mirtop_folder_gff_file = os.path.join(mirtop_folder_gff, 'mirtop.gff')

    filename_stamp_stats = mirtop_folder_stats + '/.success'
    if os.path.isfile(filename_stamp_stats):
        stamp = functions.read_time_stamp(filename_stamp_stats)
        print (colored("\tA previous command generated results on: %s [%s -- %s - stats]" %(stamp, name, 'miRTop'), 'yellow'))
    else:
        print ('Creating isomiRs stats for sample %s' %name)
        cmd_stats = miRTop_exe + ' stats -o %s %s 2>> %s' %(mirtop_folder_stats, mirtop_folder_gff_file, logfile)
        code_miRTop_stats = functions.system_call(cmd_stats)
        if code_miRTop_stats:
            functions.print_time_stamp(filename_stamp_stats)
        else:
            return(False)
            
    ## miRTop counts
    filename_stamp_counts = mirtop_folder_counts + '/.success'
    if os.path.isfile(filename_stamp_counts):
        stamp = functions.read_time_stamp(filename_stamp_counts)
        print (colored("\tA previous command generated results on: %s [%s -- %s - counts]" %(stamp, name, 'miRTop'), 'yellow'))
    else:
        print ('Creating isomiRs counts for sample %s' %name)
        ## if both succeeded
        cmd_stats = miRTop_exe + ' counts -o %s --gff %s --hairpin %s --gtf %s --sps %s 2>> %s' %(mirtop_folder_counts, mirtop_folder_gff_file, sRNAbench_hairpin, miRNA_gff, species, logfile)
        code_miRTop_counts = functions.system_call(cmd_stats)
        
        if code_miRTop_counts:
            functions.print_time_stamp(filename_stamp_counts)
        else:
            return(False)
    
    ## return all success
    outdir_tsv = os.path.join(mirtop_folder_counts, 'mirtop.tsv')
    return (outdir_tsv)
    
    ## if any command failed
    #return(False)
    