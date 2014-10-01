#!/usr/bin/env python

"""A static execution plugin RE pattern 1
For this pattern exchange is synchronous - all replicas must finish MD run before
an exchange can take place and all replicas must participate. Exchange is performed 
in centralized way (not on compute)
"""

__author__    = "Antons Treikalis <antons.treikalis@rutgers.edu>"
__copyright__ = "Copyright 2014, http://radical.rutgers.edu"
__license__   = "MIT"

import os 
import random
import radical.pilot

from radical.ensemblemd.exec_plugins.plugin_base import PluginBase

# ------------------------------------------------------------------------------
# 
_PLUGIN_INFO = {
    "name":         "replica_exchange.static_pattern_1",
    "pattern":      "ReplicaExchange",
    "context_type": "Static"
}

_PLUGIN_OPTIONS = []


# ------------------------------------------------------------------------------
# 
class Plugin(PluginBase):

    # --------------------------------------------------------------------------
    #
    def __init__(self):
        super(Plugin, self).__init__(_PLUGIN_INFO, _PLUGIN_OPTIONS)

    # --------------------------------------------------------------------------
    #
    def verify_pattern(self, pattern):
        """
        """
        self.get_logger().info("Pattern workload verification passed.")

    # --------------------------------------------------------------------------
    #
    def execute_pattern(self, pattern, resource):

        #####
        # launching pilot
        #####
        session = radical.pilot.Session()
        pmgr = radical.pilot.PilotManager(session=session)

        pdesc = radical.pilot.ComputePilotDescription()
        pdesc.resource = resource._resource_key
        pdesc.runtime  = resource._walltime
        pdesc.cores    = resource._cores
        pdesc.cleanup  = False

        pilot = pmgr.submit_pilots(pdesc)

        unit_manager = radical.pilot.UnitManager(session=session,scheduler=radical.pilot.SCHED_DIRECT_SUBMISSION)
        unit_manager.add_pilots(pilot)
        #####

        replicas = pattern.get_replicas()

        for i in range(pattern.nr_cycles):
            compute_replicas = []
            for r in replicas:
                self.get_logger().info("Building input files for replica %d" % r.id)
                pattern.build_input_file(r)
                self.get_logger().info("Preparing replica %d for MD run" % r.id)
                r_kernel = pattern.prepare_replica_for_md(r)
                r_kernel._bind_to_resource(resource._resource_key)

                cu = radical.pilot.ComputeUnitDescription()
                cu.pre_exec = r_kernel._cu_def_pre_exec
                cu.executable     = r_kernel._cu_def_executable
                cu.arguments      = r_kernel.arguments
                cu.mpi            = r_kernel.uses_mpi
                cu.cores          = r_kernel.cores
                cu.input_staging  = r_kernel._cu_def_input_data
                cu.output_staging = r_kernel._cu_def_output_data
                compute_replicas.append( cu )

            self.get_logger().info("Performing MD step for replicas")
            submitted_replicas = unit_manager.submit_units(compute_replicas)
            unit_manager.wait_units()
            
            if (i < (pattern.nr_cycles-1)):
                #####################################################################
                # computing swap matrix
                #####################################################################
                self.get_logger().info("Computing swap matrix")
                swap_matrix = pattern.get_swap_matrix(replicas)
            
                # this is actual exchange
                for r_i in replicas:
                    r_j = pattern.exchange(r_i, replicas, swap_matrix)
                    if (r_j != r_i):
                        # swap parameters   
                        self.get_logger().info("Performing exchange of parameters between replica %d and replica %d" % ( r_j.id, r_i.id ))            
                        pattern.perform_swap(r_i, r_j)

        self.get_logger().info("Replica Exchange simulation finished successfully!")
