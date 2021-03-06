import luigi
from luigi import worker, scheduler, rpc
import subprocess
import glob
import os
import sys
from time import strftime, gmtime
import simplejson
import argparse


###Parse for number of workers

# def parse_arguments(silent=False):
# 	parser = argparse.ArgumentParser()
# 	parser.add_argument("--NUM_WORKERS", required=False, default=16)
# 	args = parser.parse_args()
	
# 	num_workers = args.NUM_WORKERS

# 	return num_workers


#############################################################################################################
#This pipeline automates genome downloading and processing from CGHub. The bottom of the file is the head of the graph.
#############################################################################################################
__author__ = "David Liu"
__version__ = 1.1


"""
Global variables
"""
#Add config file to path.
os.environ["LUIGI_CONFIG_PATH"] ="client.cfg"

#Configure things here.
output_dir = os.path.abspath("./all_outputs")
download_dir = os.path.abspath("./all_downloads")

subprocess.call(["mkdir", output_dir])
subprocess.call(["mkdir", download_dir])

pipeline_output = luigi.Parameter(is_global = True, default = output_dir)
pipeline_downloads = luigi.Parameter(is_global = True, default = download_dir)


#############################################################################################################
#Deletes the BAM files after everything is finished.
#############################################################################################################
class deleteBAMFiles(luigi.Task):
	global samples
	name = luigi.Parameter()
	pipeline_output = pipeline_output
	pipeline_downloads = pipeline_downloads
	time_began = strftime("Time began: %a, %d %b %Y %H:%M:%S", gmtime())
	this_download_dir = ""
	this_out_dir = ""
	def requires(self):
		self.this_out_dir = os.path.join(self.pipeline_output, self.name)
		self.this_download_dir = os.path.join(self.pipeline_downloads, self.name)
		return {"RunTHetA":RunTHetA(name = self.name, out_dir = self.this_out_dir, download_dir = self.this_download_dir),
				"virtualSNPArray":virtualSNPArray(name = self.name, out_dir = self.this_out_dir, download_dir = self.this_download_dir)}
	def run(self):
		subprocess.call(["rm", "-rf", self.this_download_dir])
		file = open(os.path.join(self.this_out_dir, "job_summary.txt"), "w")
		file.write(simplejson.dumps(samples[self.name], indent = 3))
		file.write(self.time_began + "\n")
		file.write(strftime("Time finished: %a, %d %b %Y %H:%M:%S", gmtime()))
		file.close()
	def output(self):
		print self.this_out_dir
		return luigi.LocalTarget(os.path.join(self.this_out_dir, "job_summary.txt"))


#############################################################################################################
#RunTheta depends on the intervalCountingPipeline and BICSeqToTHetA.
#############################################################################################################
class RunTHetA(luigi.Task):
	global samples
	name = luigi.Parameter()
	out_dir = luigi.Parameter()
	download_dir = luigi.Parameter()
	this_out_dir = ""	
	def requires(self):
		self.this_out_dir = os.path.join(self.out_dir, "THetA")
		# theta_input_dir = os.path.join(self.this_out_dir, "THetA_input"
		#subprocess.call(["mkdir", theta_input_dir])
		return {'BICSeq': BICSeq(name = self.name, out_dir = self.out_dir, download_dir = self.download_dir),
				'intervalCountingPipeline': intervalCountingPipeline(name = self.name, out_dir = self.out_dir, download_dir = self.download_dir)}
	def run(self):
		#Get bicseg location
		subprocess.call(["mkdir", self.this_out_dir])
		bicseq_output_loc = os.path.join(self.out_dir, "BICSeq/output", self.name + ".bicseg")
		#Get read depth file location (_processed)
		intervalPipeline_dir = os.path.join(self.out_dir, "intervalPipeline")
		
		processed_file = subprocess.Popen("cd "  + intervalPipeline_dir +"; echo $(ls *_processed)", stdout=subprocess.PIPE, shell = True)
		processed_file = processed_file.communicate()[0].strip()
		processed_file_loc = os.path.join(intervalPipeline_dir, processed_file)
		#Run THETA!!!
		if subprocess.call(["./pipeline/scripts/runTHetA.sh", bicseq_output_loc, self.name, self.this_out_dir, processed_file_loc]) != 0:
			sys.exit()
		subprocess.call(["touch", os.path.join(self.download_dir, "THetA_complete.txt")])
	def output(self):
		return luigi.LocalTarget(os.path.join(self.download_dir, "THetA_complete.txt"))

#############################################################################################################
#Virtual SNP Array
#############################################################################################################

class virtualSNPArray(luigi.Task):
	global samples
	name = luigi.Parameter()
	out_dir = luigi.Parameter()
	download_dir = luigi.Parameter()
	this_out_dir = ""	
	def requires(self):
		return downloadGenome(name = self.name, download_dir = self.download_dir)
	def run(self):
		#run SNP Array
		self.this_out_dir = os.path.join(self.out_dir, "virtualSNPArray")
		subprocess.call(["mkdir", self.this_out_dir])
		norm_bam_extension = subprocess.Popen("cd "  + samples[self.name]['norm_download_dir'] +"; echo $(ls *.bam)", stdout=subprocess.PIPE, shell = True)
		tumor_bam_extension = subprocess.Popen("cd " + samples[self.name]['tumor_download_dir'] + "; echo $(ls *.bam)", stdout=subprocess.PIPE,shell = True)
		norm_bam_extension = norm_bam_extension.communicate()[0].strip()
		tumor_bam_extension = tumor_bam_extension.communicate()[0].strip()
			paths_file = os.path.join(self.download_dir, self.name, "downloadComplete.txt")
		lines = []
		with self.input().open('r') as in_file:
			lines = in_file.readlines()
		lines = [a_dir.strip() for a_dir in lines]
		normal_bam = os.path.join(lines[0], norm_bam_extension) #os.path.join(samples[self.name]['norm_download_dir'], norm_bam_extension)
		tumor_bam = os.path.join(lines[1], tumor_bam_extension) #os.path.join(samples[self.name]['tumor_download_dir'], tumor_bam_extension)
		snp_dir = os.path.abspath("./PipelineSoftware/virtualSNPArray")
		#HG19 or HG18?
		ref_assem = samples[self.name]['ref_assem']
		if ref_assem == "hg19":
			if subprocess.call(["./pipeline/scripts/runVirtualSNPArray.sh", self.this_out_dir, normal_bam, tumor_bam, "hg19", snp_dir, self.name]) != 0:
				sys.exit(0)
		else:#hg19
			if subprocess.call(["./pipeline/scripts/runVirtualSNPArray.sh", self.this_out_dir, normal_bam, tumor_bam,  "hg18", snp_dir, self.name]) != 0:
				sys.exit(0)

		subprocess.call(["touch", os.path.join(self.download_dir, "virtualSNPArrayDone.txt")])
	def output(self):
		return luigi.LocalTarget(os.path.join(self.download_dir, "virtualSNPArrayDone.txt"))


#############################################################################################################
#Define the main workflow dependency graph.
#############################################################################################################

"""
The C++ code that counts the 50kb bins.
"""
class intervalCountingPipeline(luigi.Task):
	global samples
	name = luigi.Parameter()
	out_dir = luigi.Parameter()
	download_dir = luigi.Parameter()
	this_out_dir = ""	
	def requires(self):
		return BAMtoGASV(name = self.name, out_dir = self.out_dir, download_dir = self.download_dir)
	def run(self):
		self.this_out_dir = os.path.join(self.out_dir, "intervalPipeline")
		subprocess.call(["mkdir", self.this_out_dir])
		parameter_file_path = os.path.abspath(os.path.join(self.this_out_dir, "parameters.txt"))
		normal_conc = os.path.join(self.out_dir, "BAMtoGASV_output", "NORMAL", "NORMAL_" + samples[self.name]['norm_prefix'] + "-lib1.concordant")
		tumor_conc = os.path.join(self.out_dir, "BAMtoGASV_output", "TUMOR", "TUMOR_" + samples[self.name]['tumor_prefix'] + "-lib1.concordant")
		#Write parameter file
		with open(parameter_file_path, "w") as parameter_file:
			parameter_file.write("IntervalFile: "+ os.path.join(self.this_out_dir, "intervals.txt") + "\n")
			parameter_file.write("Software: PREGO" + "\n")
			parameter_file.write("ConcordantFile: " + samples[self.name]['norm_concordant'] + "\n")
			parameter_file.write("ConcordantFile: " + samples[self.name]['tumor_concordant'])
		#Run script
		if subprocess.call(["./pipeline/scripts/runIntervalPipeline.sh", self.this_out_dir, parameter_file_path]) != 0:
			sys.exit()
		subprocess.call(["touch", os.path.join(self.download_dir, "intervalsDone.txt")])
	def output(self):
		#????????????????
		return luigi.LocalTarget(os.path.join(self.download_dir, "intervalsDone.txt"))
	# def complete(self):
	# 	return True

"""
THetA stuff
"""

#BICSeq
class BICSeq(luigi.Task):
	global samples
	name = luigi.Parameter()
	out_dir = luigi.Parameter()
	download_dir = luigi.Parameter()
	this_out_dir = ""	
	def requires(self):
		self.this_out_dir = os.path.join(self.out_dir, "BICSeq")
		return BAMtoGASV(name = self.name, out_dir = self.out_dir, download_dir = self.download_dir)
	def run(self):
		# Takes concordant files as input
		subprocess.call(["mkdir", self.this_out_dir])
		normal_conc = os.path.join(self.out_dir, "BAMtoGASV_output", "NORMAL", "NORMAL_" + samples[self.name]['norm_prefix'] + "-lib1.concordant")
		tumor_conc = os.path.join(self.out_dir, "BAMtoGASV_output", "TUMOR", "TUMOR_" + samples[self.name]['tumor_prefix'] + "-lib1.concordant")
		samples[self.name]['norm_concordant'] = normal_conc
		samples[self.name]['tumor_concordant'] = tumor_conc
		bicseq_input_loc = self.this_out_dir #To be created
		#Run script
		if subprocess.call(["./pipeline/scripts/runBICseq.sh", self.this_out_dir, tumor_conc, normal_conc, bicseq_input_loc, self.name]) != 0:
			sys.exit()
		#Remove input file
		subprocess.call(["rm", "-f", os.path.join(self.this_out_dir, "*.input")])
		#done
		subprocess.call(["touch", os.path.join(self.download_dir, "BICSeqDone.txt")])
	def output(self):
		return luigi.LocalTarget(os.path.join(self.download_dir, "BICSeqDone.txt"))

class BAMtoGASV(luigi.Task):
	global samples
	name = luigi.Parameter()
	out_dir = luigi.Parameter()
	download_dir = luigi.Parameter()
	this_out_dir = ""
	def requires(self):
		return downloadGenome(name = self.name, download_dir = self.download_dir)
	def run(self):
		#Run BAMtoGASV
		self.this_out_dir = os.path.join(self.out_dir, "BAMtoGASV_output")
		subprocess.call(["mkdir", self.out_dir])
		subprocess.call(["mkdir", self.this_out_dir])
		normal_dir = os.path.join(self.this_out_dir, "NORMAL")
		tumor_dir = os.path.join(self.this_out_dir, "TUMOR")
		subprocess.call(["mkdir", normal_dir])
		subprocess.call(["mkdir", tumor_dir])
		#Download dirs
		paths_file = os.path.join(self.download_dir, self.name, "downloadComplete.txt")
		lines = []
		with self.input().open('r') as in_file:
			lines = in_file.readlines()
		lines = [a_dir.strip() for a_dir in lines]
		#Get the names of the bam files.
		# norm_bam_extension = subprocess.Popen("cd "  + samples[self.name]['norm_download_dir'] +"; echo $(ls *.bam)", stdout=subprocess.PIPE, shell = True)
		# tumor_bam_extension = subprocess.Popen("cd " + samples[self.name]['tumor_download_dir'] + "; echo $(ls *.bam)", stdout=subprocess.PIPE,shell = True)
		norm_bam_extension = subprocess.Popen("cd "  + lines[0] +"; echo $(ls *.bam)", stdout=subprocess.PIPE, shell = True)
		tumor_bam_extension = subprocess.Popen("cd " + lines[1] + "; echo $(ls *.bam)", stdout=subprocess.PIPE,shell = True)
		norm_bam_extension = norm_bam_extension.communicate()[0].strip()
		tumor_bam_extension = tumor_bam_extension.communicate()[0].strip()
		normal_bam = os.path.join(lines[0], norm_bam_extension)
		tumor_bam = os.path.join(lines[1], tumor_bam_extension)
		#Run on normal
		if subprocess.call(["./pipeline/scripts/runBAMtoGASV.sh", normal_dir, normal_bam, samples[self.name]['norm_prefix'], "NORMAL"]) != 0:
			sys.exit(0)
		#Run on tumor
		if subprocess.call(["./pipeline/scripts/runBAMtoGASV.sh", tumor_dir, tumor_bam, samples[self.name]['tumor_prefix'], "TUMOR"]) != 0:
			sys.exit(0)
		subprocess.call(["touch", os.path.join(self.download_dir, "BAMtoGASVfinished.txt")])
	def output(self):
		return luigi.LocalTarget(os.path.join(self.download_dir, "BAMtoGASVfinished.txt"))

#############################################################################################################
#Head of the stream. Download a file from CGHub.
#############################################################################################################

class downloadGenome(luigi.Task):
	global samples
	name = luigi.Parameter()
	download_dir = luigi.Parameter()
	pipeline_downloads = pipeline_downloads
	def run(self):
		subprocess.call(["mkdir", self.pipeline_downloads])
		self.download_dir = os.path.join(self.pipeline_downloads, self.name)
		subprocess.call(["mkdir", self.download_dir])
		normal_dir = os.path.join(self.download_dir, "NORMAL")
		tumor_dir = os.path.join(self.download_dir, "TUMOR")
		subprocess.call(["mkdir", normal_dir])
		subprocess.call(["mkdir", tumor_dir])
		#Download normal
		if subprocess.call(["./PipelineSoftware/CGHub/runGeneTorrentNew.bash", samples[self.name]['norm_aurid'], normal_dir]) != 0:
			sys.exit(0)
		#Download tumor
		if subprocess.call(["./PipelineSoftware/CGHub/runGeneTorrentNew.bash", samples[self.name]['tumor_aurid'], tumor_dir]) !=0:
			sys.exit(0)
		#Add the name of the download hash directory to the directory name.
		normal_hash = subprocess.Popen("cd " + normal_dir + "; echo $(ls -d */)", stdout=subprocess.PIPE, shell = True)
		tumor_hash = subprocess.Popen("cd " + tumor_dir + "; echo $(ls -d */)", stdout=subprocess.PIPE,shell = True)
		normal_hash = normal_hash.communicate()[0].strip()
		tumor_hash = tumor_hash.communicate()[0].strip()
		samples[self.name]['norm_download_dir'] = os.path.join(normal_dir, normal_hash)
		samples[self.name]['tumor_download_dir'] = os.path.join(tumor_dir, tumor_hash)
		with self.output().open('w') as out_file:
			out_file.write(samples[self.name]['norm_download_dir'] + "\n")
			out_file.write(samples[self.name]['tumor_download_dir'])
		#subprocess.call(["touch", os.path.join(self.download_dir, self.name + "downloadComplete.txt")])
	def output(self):
		return luigi.LocalTarget(os.path.join(self.download_dir, self.name + "downloadComplete.txt"))


#############################################################################################################
#Run Pipeline
#############################################################################################################

# class TriggerAll(luigi.Task):
# 	global tasks_to_run
# 	def requires(self):
# 		for task in tasks_to_run:
# 			yield task
# 	def run(self):
# 		# subprocess.call(["touch", "pipelineComplete.txt"])
# 		pass
# 	def output(self):
# 		return luigi.LocalTarget("pipelineComplete.txt")

#############################################################################################################
#Set up the internal data usage format
#############################################################################################################

#GLOBAL DATA FORMAT: samples

# {
# 	sample_name [name] (e.g. Ovarian Cancer X Y):{
# 		norm_prefix
# 		tumor_prefix
# 		norm_dir
# 		tumor_dir
# 		ref_assem
# 		#Optional for download: norm_aurid, tumor_aurid
# 	}
# }

global samples
#Load in the data
try:
	with open ("tumor_sample_info.json", "r") as f:
		samples = simplejson.loads(f.read())
except:
 	raise Exception("You must generate the input file in pipeline first. Consult the README.")

#Create tasks_to_run from samples.
tasks_to_run = []
for name in samples.keys():
	#Only keep TCGA ones. We don't seem to have permission to download the TARGET ones.
	if "TCGA" in name:
		tasks_to_run.append(deleteBAMFiles(name))
	else:
		continue


#Run with workers

tasks_to_run.append(deleteBAMFiles("TCGA-A7-A0CE"))

luigi.build(tasks_to_run, workers=16, scheduler_port=8082)

# if name == '__main__':
# 	luigi.run()

