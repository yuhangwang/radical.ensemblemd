#!/usr/bin/env python
"""
TODO Vivek: Add description and instructions how to run, where to get \
sample data from, etc. Refer to other use-cases for 'inspiration'.

Run this example with ``RADICAL_ENMD_VERBOSE`` set to ``info`` if you want to
see log messages about plug-in invocation and simulation progress::

RADICAL_ENMD_VERBOSE=info python 01_static_gromacs_lsdmap_loop.py
"""

__author__        = "Vivek <vivek.balasubramanian@rutgers.edu>"
__copyright__     = "Copyright 2014, http://radical.rutgers.edu"
__license__       = "MIT"
__use_case_name__ = "'Gromacs + LSDMap' simulation-analysis proof-of-concept (ExTASY)."
  
  
from radical.ensemblemd import Kernel
from radical.ensemblemd import SimulationAnalysisLoop
from radical.ensemblemd import EnsemblemdError
from radical.ensemblemd import SimulationAnalysisLoop
from radical.ensemblemd import SingleClusterEnvironment


# ------------------------------------------------------------------------------
#
class Gromacs_LSDMap(SimulationAnalysisLoop):
  # TODO Vivek: add description.

    def __init__(self, maxiterations, simulation_width=1, analysis_width=1):
        SimulationAnalysisLoop.__init__(self, maxiterations, simulation_width, analysis_width)
    
    def pre_loop(self):
        # Pre_loop is executed before the main simulation-analysis loop is
        # started. It is not used in this current example.
        pass
      
    def simulation_step(self, iteration, instance):
        '''TODO Vivek: add description of this step.
        '''
        pre_sim = Kernel(name="md.pre_gromacs")
        # k.set_upload_input(files='input%s.gro"%(iteration))
        pre_sim.set_args(["--inputfiles=input%s.gro"%(iteration)])
        pre_sim.set_download_output(files='input-iter%{0}-%{1}.gro'.format(iteration,instance))

        gromacs = Kernel(name="md.gromacs")
        # k.set_upload_input(files=['run.sh','input-iter%{0}-%{1}.gro > start.gro'.format(iteration,instance),'grompp.mdp','topol.top'])
        gromacs.set_args(["--grompp=grompp.mdp","--topol=topol.top","--inputfile=['run.sh','input-iter%{0}-%{1}.gro > start.gro'.format(iteration,instance),'grompp.mdp','topol.top']", "--outputfile=['out.gro > out-iter%{0}-%{1}.gro']".format(iteration, instance)])
        gromacs.set_download_output(files='out.gro > out-iter%{0}-%{1}.gro'.format(iteration, instance))

        return [pre_sim, gromacs]
    
    def analysis_step(self, iteration, instance):
        '''TODO Vivek: add description of this step.
        '''
        lsdmap = Kernel(name="md.lsdmap")
        # k.set_upload_input(files=['config.ini','tmp%{0}.gro'.format(iteration),'run_analyzer.sh'])
        lsdmap.set_args(["--nnfile=out.nn","--wfile=weight.w","--grofile=tmp%{0}.gro".format(iteration),"--inputfiles=['config.ini','tmp%{0}.gro'.format(iteration),'run_analyzer.sh']", "--outputfile=['tmp.eg > out.eg','tmp.ev > out.ev','out.nn']"])
        lsdmap.set_download_output(files=['tmp.eg > out.eg','tmp.ev > out.ev','out.nn'])
    
        reweight = Kernel(name="md.update_reweight")
        # k.set_upload_input(files=['out.ev','out.nc','tmp%{0}.gro'.format(iteration)],'out.nn','weight.w')
        reweight.set_args(["--nruns=10000","--evfile=out.ev","--clones=out.nc","--grofile=tmp%{0}.gro".format(iteration),"--nnfile=out.nn","--wfile=weight.w","--outputfile=out.gro"])
        reweight.set_download_output(files='out.gro > input%s.gro'%(iteration+1))

        return [lsdmap, reweight]
  
    def post_loop(self):
        # post_loop is executed after the main simulation-analysis loop has
        # finished. In this case of MSSA it is not required, will be required
        # in the case of Multiple Analysis phases.
        pass
    

# ------------------------------------------------------------------------------
#
if __name__ == "__main__":

  try:
      # Create a new static execution context with one resource and a fixed
      # number of cores and runtime.
      cluster = SingleClusterEnvironment(
        resource="localhost",
        cores=1,
        walltime=15
      )

      # We set the 'width' of the simulation step to 16. This means that 16
      # instances of the simulation are executed every iteration.
      # We set the 'width' of the analysis step to 1. This means that only
      # one instance of the analysis is executed for each iteration
      randomsa = Gromacs_LSDMap(maxiterations=64, simulation_width=16, analysis_width=1)

      cluster.run(randomsa)
  
  except EnsemblemdError, er:

    print "EnsembleMD Error: {0}".format(str(er))
    raise # Just raise the execption again to get the backtrace
