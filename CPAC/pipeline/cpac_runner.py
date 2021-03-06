import os
import warnings
from multiprocessing import Process
from time import strftime

import yaml
import yamlordereddictloader

from CPAC.utils.configuration import Configuration
from CPAC.utils.ga import track_run


# Run condor jobs
def run_condor_jobs(c, config_file, subject_list_file, p_name):
    '''
    '''

    # Import packages
    import subprocess
    from time import strftime

    try:
        sublist = yaml.safe_load(open(os.path.realpath(subject_list_file), 'r'))
    except:
        raise Exception("Subject list is not in proper YAML format. Please check your file")

    cluster_files_dir = os.path.join(os.getcwd(), 'cluster_files')
    subject_bash_file = os.path.join(cluster_files_dir, 'submit_%s.condor' % str(strftime("%Y_%m_%d_%H_%M_%S")))
    f = open(subject_bash_file, 'w')

    print("Executable = /usr/bin/python", file=f)
    print("Universe = vanilla", file=f)
    print("transfer_executable = False", file=f)
    print("getenv = True", file=f)
    print("log = %s" % os.path.join(cluster_files_dir, 'c-pac_%s.log' % str(strftime("%Y_%m_%d_%H_%M_%S"))), file=f)

    for sidx in range(1,len(sublist)+1):
        print("error = %s" % os.path.join(cluster_files_dir, 'c-pac_%s.%s.err' % (str(strftime("%Y_%m_%d_%H_%M_%S")), str(sidx))), file=f)
        print("output = %s" % os.path.join(cluster_files_dir, 'c-pac_%s.%s.out' % (str(strftime("%Y_%m_%d_%H_%M_%S")), str(sidx))), file=f)

        print("arguments = \"-c 'import CPAC; CPAC.pipeline.cpac_pipeline.run( ''%s'',''%s'',''%s'',''%s'',''%s'',''%s'',''%s'')\'\"" % (str(config_file), subject_list_file, str(sidx), c.maskSpecificationFile, c.roiSpecificationFile, c.templateSpecificationFile, p_name), file=f)
        print("queue", file=f)

    f.close()

    #commands.getoutput('chmod +x %s' % subject_bash_file )
    print(subprocess.getoutput("condor_submit %s " % (subject_bash_file)))


# Create and run script for CPAC to run on cluster
def run_cpac_on_cluster(config_file, subject_list_file,
                        cluster_files_dir):
    '''
    Function to build a SLURM batch job submission script and
    submit it to the scheduler via 'sbatch'
    '''

    # Import packages
    import subprocess
    import getpass
    import re
    from time import strftime

    from CPAC.utils import Configuration
    from indi_schedulers import cluster_templates

    # Load in pipeline config
    try:
        pipeline_dict = yaml.safe_load(open(os.path.realpath(config_file), 'r'))
        pipeline_config = Configuration(pipeline_dict)
    except:
        raise Exception('Pipeline config is not in proper YAML format. '\
                        'Please check your file')
    # Load in the subject list
    try:
        sublist = yaml.safe_load(open(os.path.realpath(subject_list_file), 'r'))
    except:
        raise Exception('Subject list is not in proper YAML format. '\
                        'Please check your file')

    # Init variables
    timestamp = str(strftime("%Y_%m_%d_%H_%M_%S"))
    job_scheduler = pipeline_config.resourceManager.lower()

    # For SLURM time limit constraints only, hh:mm:ss
    hrs_limit = 8 * len(sublist)
    time_limit = '%d:00:00' % hrs_limit

    # Batch file variables
    shell = subprocess.getoutput('echo $SHELL')
    user_account = getpass.getuser()
    num_subs = len(sublist)

    # Run CPAC via python -c command
    python_cpac_str = 'python -c "from CPAC.pipeline.cpac_pipeline import run; '\
                      'run(\'%(config_file)s\', \'%(subject_list_file)s\', '\
                      '%(env_arr_idx)s, \'%(pipeline_name)s\', '\
                      'plugin=\'MultiProc\', plugin_args=%(plugin_args)s)"'

    # Init plugin arguments
    plugin_args = {'n_procs': pipeline_config.maxCoresPerParticipant,
                   'memory_gb': pipeline_config.maximumMemoryPerParticipant}

    # Set up run command dictionary
    run_cmd_dict = {'config_file' : config_file,
                    'subject_list_file' : subject_list_file,
                    'pipeline_name' : pipeline_config.pipelineName,
                    'plugin_args' : plugin_args}

    # Set up config dictionary
    config_dict = {'timestamp' : timestamp,
                   'shell' : shell,
                   'job_name' : 'CPAC_' + pipeline_config.pipelineName,
                   'num_tasks' : num_subs,
                   'queue' : pipeline_config.queue,
                   'par_env' : pipeline_config.parallelEnvironment,
                   'cores_per_task' : pipeline_config.maxCoresPerParticipant,
                   'user' : user_account,
                   'work_dir' : cluster_files_dir,
                   'time_limit' : time_limit}

    # Get string template for job scheduler
    if job_scheduler == 'pbs':
        env_arr_idx = '$PBS_ARRAYID'
        batch_file_contents = cluster_templates.pbs_template
        confirm_str = '(?<=Your job-array )\d+'
        exec_cmd = 'qsub'
    elif job_scheduler == 'sge':
        env_arr_idx = '$SGE_TASK_ID'
        batch_file_contents = cluster_templates.sge_template
        confirm_str = '(?<=Your job-array )\d+'
        exec_cmd = 'qsub'
    elif job_scheduler == 'slurm':
        env_arr_idx = '$SLURM_ARRAY_TASK_ID'
        batch_file_contents = cluster_templates.slurm_template
        confirm_str = '(?<=Submitted batch job )\d+'
        exec_cmd = 'sbatch'

    # Populate rest of dictionary
    config_dict['env_arr_idx'] = env_arr_idx
    run_cmd_dict['env_arr_idx'] = env_arr_idx
    config_dict['run_cmd'] = python_cpac_str % run_cmd_dict

    # Populate string from config dict values
    batch_file_contents = batch_file_contents % config_dict
    # Write file
    batch_filepath = os.path.join(cluster_files_dir, 'cpac_submit_%s.%s' \
                                  % (timestamp, job_scheduler))
    with open(batch_filepath, 'w') as f:
        f.write(batch_file_contents)

    # Get output response from job submission
    out = subprocess.getoutput('%s %s' % (exec_cmd, batch_filepath))

    # Check for successful qsub submission
    if re.search(confirm_str, out) == None:
        err_msg = 'Error submitting C-PAC pipeline run to %s queue' \
                  % job_scheduler
        raise Exception(err_msg)

    # Get pid and send to pid file
    pid = re.search(confirm_str, out).group(0)
    pid_file = os.path.join(cluster_files_dir, 'pid.txt')
    with open(pid_file, 'w') as f:
        f.write(pid)


# Run C-PAC subjects via job queue
def run(subject_list_file, config_file=None, p_name=None, plugin=None,
        plugin_args=None, tracking=True, num_subs_at_once=None, debug=False, test_config=False):

    # Import packages
    import subprocess
    import os
    import pickle
    import time

    from CPAC.pipeline.cpac_pipeline import run_workflow

    print('Run called with config file {0}'.format(config_file))

    if not config_file:
        import pkg_resources as p
        config_file = \
            p.resource_filename("CPAC",
                                os.path.join("resources",
                                             "configs",
                                             "pipeline_config_template.yml"))

    # Init variables
    sublist = None
    if '.yaml' in subject_list_file or '.yml' in subject_list_file:
        subject_list_file = os.path.realpath(subject_list_file)
    else:
        from CPAC.utils.bids_utils import collect_bids_files_configs, \
            bids_gen_cpac_sublist
        (file_paths, config) = collect_bids_files_configs(subject_list_file,
                                                          None)
        sublist = bids_gen_cpac_sublist(subject_list_file, file_paths,
                                        config, None)
        if not sublist:
            import sys
            print("Did not find data in {0}".format(subject_list_file))
            sys.exit(1)

    # take date+time stamp for run identification purposes
    unique_pipeline_id = strftime("%Y%m%d%H%M%S")
    pipeline_start_stamp = strftime("%Y-%m-%d_%H:%M:%S")

    # Load in pipeline config file
    config_file = os.path.realpath(config_file)
    try:
        if not os.path.exists(config_file):
            raise IOError
        else:
            c = Configuration(yaml.safe_load(open(config_file, 'r')))
    except IOError:
        print("config file %s doesn't exist" % config_file)
        raise
    except yaml.parser.ParserError as e:
        error_detail = "\"%s\" at line %d" % (
            e.problem,
            e.problem_mark.line
        )
        raise Exception(
            "Error parsing config file: {0}\n\n"
            "Error details:\n"
            "    {1}"
            "\n\n".format(config_file, error_detail)
        )
    except Exception as e:
        raise Exception(
            "Error parsing config file: {0}\n\n"
            "Error details:\n"
            "    {1}"
            "\n\n".format(config_file, e)
        )

    c.logDirectory = os.path.abspath(c.logDirectory)
    c.workingDirectory = os.path.abspath(c.workingDirectory)
    if 's3://' not in c.outputDirectory:
        c.outputDirectory = os.path.abspath(c.outputDirectory)
    c.crashLogDirectory = os.path.abspath(c.crashLogDirectory)

    if debug:
        c.write_debugging_outputs = "[1]"

    if num_subs_at_once:
        if not str(num_subs_at_once).isdigit():
            raise Exception('[!] Value entered for --num_cores not a digit.')
        c.numParticipantsAtOnce = int(num_subs_at_once)

    # Do some validation
    if not c.workingDirectory:
        raise Exception('Working directory not specified')

    if len(c.workingDirectory) > 70:
        warnings.warn("We recommend that the working directory full path "
                      "should have less then 70 characters. "
                      "Long paths might not work in your operational system.")
        warnings.warn("Current working directory: %s" % c.workingDirectory)

    # Get the pipeline name
    p_name = p_name or c.pipelineName

    # Load in subject list
    try:
        if not sublist:
            sublist = yaml.safe_load(open(subject_list_file, 'r'))
    except:
        print("Subject list is not in proper YAML format. Please check " \
              "your file")
        raise Exception

    # Populate subject scan map
    sub_scan_map = {}
    try:
        for sub in sublist:
            if sub['unique_id']:
                s = sub['subject_id'] + "_" + sub["unique_id"]
            else:
                s = sub['subject_id']
            scan_ids = ['scan_anat']

            if 'func' in sub:
                for id in sub['func']:
                    scan_ids.append('scan_'+ str(id))

            if 'rest' in sub:
                for id in sub['rest']:
                    scan_ids.append('scan_'+ str(id))

            sub_scan_map[s] = scan_ids
    except:
        print("\n\n" + "ERROR: Subject list file not in proper format - " \
              "check if you loaded the correct file?" + "\n" + \
              "Error name: cpac_runner_0001" + "\n\n")
        raise Exception

    pipeline_timing_info = []
    pipeline_timing_info.append(unique_pipeline_id)
    pipeline_timing_info.append(pipeline_start_stamp)
    pipeline_timing_info.append(len(sublist))

    if tracking:
        try:
            track_run(level='participant', participants=len(sublist))
        except:
            pass

    # If we're running on cluster, execute job scheduler
    if c.runOnGrid:

        # Create cluster log dir
        cluster_files_dir = os.path.join(c.logDirectory, 'cluster_files')
        if not os.path.exists(cluster_files_dir):
            os.makedirs(cluster_files_dir)

        # Check if its a condor job, and run that
        if 'condor' in c.resourceManager.lower():
            run_condor_jobs(c, config_file, subject_list_file, p_name)
        # All other schedulers are supported
        else:
            run_cpac_on_cluster(config_file, subject_list_file, cluster_files_dir)

    # Run on one computer
    else:

        if not os.path.exists(c.workingDirectory):
            try:
                os.makedirs(c.workingDirectory)
            except:
                err = "\n\n[!] CPAC says: Could not create the working " \
                      "directory: %s\n\nMake sure you have permissions " \
                      "to write to this directory.\n\n" % c.workingDirectory
                raise Exception(err)

        # If it only allows one, run it linearly
        if c.numParticipantsAtOnce == 1:
            for sub in sublist:
                run_workflow(sub, c, True, pipeline_timing_info,
                              p_name, plugin, plugin_args, test_config)
            return

        pid = open(os.path.join(c.workingDirectory, 'pid.txt'), 'w')

        # Init job queue
        job_queue = []

        # Allocate processes
        processes = [
            Process(target=run_workflow,
                    args=(sub, c, True, pipeline_timing_info,
                          p_name, plugin, plugin_args, test_config))
            for sub in sublist
        ]

        # If we're allocating more processes than are subjects, run them all
        if len(sublist) <= c.numParticipantsAtOnce:
            for p in processes:
                p.start()
                print(p.pid, file=pid)

        # Otherwise manage resources to run processes incrementally
        else:
            idx = 0
            while idx < len(sublist):
                # If the job queue is empty and we haven't started indexing
                if len(job_queue) == 0 and idx == 0:
                    # Init subject process index
                    idc = idx
                    # Launch processes (one for each subject)
                    for p in processes[idc: idc+c.numParticipantsAtOnce]:
                        p.start()
                        print(p.pid, file=pid)
                        job_queue.append(p)
                        idx += 1
                # Otherwise, jobs are running - check them
                else:
                    # Check every job in the queue's status
                    for job in job_queue:
                        # If the job is not alive
                        if not job.is_alive():
                            # Find job and delete it from queue
                            print('found dead job ', job)
                            loc = job_queue.index(job)
                            del job_queue[loc]
                            # ...and start the next available process
                            # (subject)
                            processes[idx].start()
                            # Append this to job queue and increment index
                            job_queue.append(processes[idx])
                            idx += 1
                    # Add sleep so while loop isn't consuming 100% of CPU
                    time.sleep(2)
        # Close PID txt file to indicate finish
        pid.close()
