#!/bin/env python
import os
import time
import subprocess
import shlex
import sys
from datetime import datetime as dt
#------------------------------------------------------#
def get_datetime():
    '''
    gets date and time in a str in format
    yyyy-mm-dd_hh:mm:ss
    :return: string with date and time
    '''
    return str(dt.now())[:-7].replace(' ', '_')
#----------------------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------Constant-Values---------------------------------------------------------#
Cts  = [15.0, 4.0, 3.5, 3.0, 4.0]#[3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
Ats  = [9.0, 6.0, 2.222]#[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
Csss = [0.5, 1.0, 1.5]#, 2.0, 2.5, 3.0]
a2s  = [0.45]
#----------------------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------Filenames-and-other-constants-------------------------------------------#
#----------------------------------------------------------------and-magic-numbers-------------------------------------------------#

#-----Run_and_stop_jobs-------#
cmd     = 'qsub' # 'sbatch' # Command to start a new job
job_fn	= 'tr_bl.pbs'#'matr.slrm' # File that starts the job
kill_cmd = 'qdel'    # Command to kill process using it's id
queue_cmd = 'q'  # Command to list running jobs

#-------files-----#
d_file  = 'd_uduct.in' # Menu file for the job
log_fn  = 'log' + get_datetime() + '.txt' # Name of log output file
exit_fn = 'exit.in' # Name of file to control the exit from the program (analogous to keyboard.cfg)
base_dir = 'base' # Directory for base of the tasks, without code and grid
code_fn = 's_tr_bl-r8' # Filename for NTS code executable, the program will create a link without copying it
code_dir = 'code' # Directory name for code
grid_fn = 'Grid_tbl.blk' # Filename for grid .blk file, the program will create a link without copying it
grid_dir = 'grid' # Directory name for grid

#------Magic-numbers-----#
max_jobs   = 6  # Maximum number of running jobs
check_time = 20 # Check if any jobs finished each this number of seconds

#------------------------------------------------------#
def read_file(fn):
    '''
    Reads file
    :param fn: str, filename
    :return: list, a list of strings of a file
    '''
    with open(fn, 'r') as f:
        ss = f.readlines()
    return ss

#------------------------------------------------------#
def write_file(fn, ss):
    '''
    Writes list of strings to file
    :param fn: str, filename
    :param ss: list of str, strings to write
    :return: no return
    '''
    with open(fn, "w") as f:
        f.writelines(ss)

#------------------------------------------------------#
def write_log_header():
    '''
    Creates log file and writes it's header
    :return:
    '''
    with open(log_fn, "w") as f:
        f.write('{} -- Log start\n'.format(get_datetime()))

#------------------------------------------------------#
def add_to_log(string):
    '''
    Adds a string to log file with datetime stamp
    :param string: str, a string to add to log
    :return: no return
    '''
    with open(log_fn, "a") as f:
        f.write('{} -- {}\n'.format(get_datetime(), string))

#------------------------------------------------------#
def set_constants(path, ct, at, css, a2):
    '''
    Changes constatns in menu file
    :param path: str, path to folder containing menu file
    :param ct: float, value of constant Ct
    :param at: float, value of constant At
    :param css: float, value of constant Css
    :param a2: float, value of constant a2
    :return: no return
    '''
    in_fname = path + '/' + d_file
    menus = read_file(in_fname)
    for i in range(len(menus)):
        if menus[i].split()[-2] == '52':
            menus[i + 3]  ='   {}             ; A_gam    12.0                     10.0\n'.format(at)
            menus[i + 4]  ='   {}             ; C_s      21.0                      2.0\n'.format(css)
            menus[i + 6]  ='   {}             ; C_psi    10.0                     14.5\n'.format(ct)
            menus[i + 10] ='   {}             ; a_l      0.45                     0.45\n'.format(a2)
    write_file(in_fname, menus)

#------------------------------------------------------#
def run_cmd(cmd, cwd = None):
    '''
    Function for running Linux command
    :param cmd: str, containing the command
    :param cwd: str, containing cwd attribute the path to directory from where to run the command
    :return: tuple of 2 str, command output and error code
    '''
    command = shlex.split(cmd)
    p = subprocess.Popen(command,
	stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd = cwd)
    out, err = p.communicate()
    return (out, err)

#------------------------------------------------------#
def run_job(path, pwd, ids):
    '''
    Runs NTS code jobs
    :param path: str, relative path to job location
    :param pwd: str, absolute path to directory from where the python script is run
    :param ids: dict {jobid(int): path(str}, dictionary of currently running job ids that were run from this script
    with relative paths to their locations
    :return: dict {jobid(int): path(str}: updated ids dict, containing new job
    '''
    path_to_job = pwd + path + '/' # Constructiong absolute path to the job to queue
    cmd_job = cmd + ' ' + path_to_job + job_fn # Constructing the command to run to run the job
    (o, e) = run_cmd(cmd_job, cwd = path_to_job) # Running the command, with cwd attribute
    id = o.split('.')[0] # Parsing output to get new job id
    ids[id] = path # adding new id and path to ids
    return ids

#------------------------------------------------------#
def check_exit(ids):
    '''
    Checks exit_fn file for:
    '1' - kill script, don't kill running jobs
    or
    '2'  - kill script and running jobs
    and then exits accordingly, if found
    :param ids: dict {jobid(int): path(str}, dictionary of currently running job ids that were run from this script
    with relative paths to their locations
    :return:
    '''
    s = read_file(exit_fn) # read exit_fn file
    if s[0].rstrip(' \n').lstrip(' ') == '2': # If it contains 2 exit and kill all jobs
        add_to_log('--------------------------------')
        add_to_log('--------------------------------')
        add_to_log('Program exited due to user input')   # Header to log
        add_to_log('----------Jobs killed:----------')
        cmd = kill_cmd # Initialize kill comand
        for id in ids: # For all currently running jobs
            cmd+= ' ' + id # Add id to kill list
            add_to_log('{} {}'.format(id, ids[id])) # List job in log
        (o, e) = run_cmd(cmd) # Kill jobs
        add_to_log('--------End-of-program.---------')
        sys.exit() # End script
    elif s[0].rstrip(' \n').lstrip(' ') == '1': # If it contains 2 exit and kill all jobs
        add_to_log('--------------------------------')
        add_to_log('--------------------------------')
        add_to_log('Program exited due to user input') # Header to log
        add_to_log('--------No-jobs-killed.---------')
        add_to_log('--------Remaining-jobs.---------')
        for id in ids: # For all currently running jobs
            add_to_log('{} {}'.format(id, ids[id])) # List job in log
        add_to_log('--------End-of-program.---------')
        sys.exit() # End script

#------------------------------------------------------#
def count_jobs(ids):
    '''
    Counts currently running jobs
    :param ids: dict {jobid(int): path(str}, dictionary of currently running job ids that were run from this script
    with relative paths to their locations
    :return: int, number of running jobs
    '''
    num_jobs = 0 # Initialize number of jobs
    (o, e) = run_cmd(queue_cmd) # run command for queue currently running tasks
    n = o.split('\n') # Parse output into strings
    for job in n[2:-1]: # For all jobs listed by command s
        if job.split()[0] in ids and job.split()[1] != 'C': num_jobs += 1 # If the job is in ids (was launched by this script) and is not complete ('C' status) add to count
    return num_jobs

#------------------------------------------------------#
def cleanse_ids(ids):
    '''
    Deletes jobs that are already finished from ids dict
    :param ids: dict {jobid(int): path(str}, dictionary of currently running job ids that were run from this script
    with relative paths to their locations
    :return: updated ids dict
    '''
    jobs = [] # initialize list of jobs
    new_ids = ids.copy() # Copy ids dict to be able to macke changes
    (o, e) = run_cmd(queue_cmd) # run command for queue currently running tasks
    n = o.split('\n') # Parse output into strings
    for job in n[2:-1]: # For all jobs listed by command s
        if job.split()[1] != 'C': # If the job isn't finished
            jobs.append(job.split()[0]) # Add to list of currently running jobs
    for id in ids: # For all jobs in ids
        if not id in jobs: # If it is not running
            new_ids.pop(id) # Remove in from the copy
    ids = new_ids.copy() # Assign modified copy to ids
    return ids

#------------------------------------------------------#
def copy_data(pwd, path):
    '''
    Copies base directory along with links for code and grid
    :param pwd: str, absolute path to directory from where the python script is run
    :param path: str, path to the directory where to copy the files
    :return:
    '''
    s = 'cp -avr {} {}'.format(base_dir, path) # copy the base directory
    (o, e) = run_cmd(s)
    s = 'ln -s {3}{0}/{1} {2}/{1}'.format(grid_dir, grid_fn, path, pwd) # Make link to grid
    (o, e) = run_cmd(s)
    s = 'ln -s {3}{0}/{1} {2}/{1}'.format(code_dir, code_fn, path, pwd) # Make link to NTS code executable file
    (o, e) = run_cmd(s)

#------------------------------------------------------#
def main():
    '''
    Main function
    :return: no return
    '''
    write_file(exit_fn, ['0']) # Initialize file for exit
    write_log_header() # Initialize log file
    add_to_log('Cts = '+ str(Cts)) # Add info on constants to log file
    add_to_log('Ats = '+ str(Ats))
    add_to_log('Csss = '+ str(Csss))
    add_to_log('a2s = '+ str(a2s))
    a2 = a2s[0]
    i = 0 # Variable to count tastks started
    cmd_path = 'pwd' # Commant to get current pwd
    (o, e) = run_cmd(cmd_path)
    pwd = o.split('\n')[0]+'/'
    total_tasks = len(Ats) * len(Cts) * len(Csss) * len(a2s)
    add_to_log('amount of jobs = {}'.format(total_tasks))
    add_to_log('max jobs       = {}'.format(max_jobs))
    ids = {} # Initialize ids dict
    for ct in Cts: # Nested loops over all constants
        path1 = 'Ct_=_' + str(ct)
        add_to_log('\n')
        add_to_log('----------------------------------{}% complete\n'.format(float(i)/float(total_tasks)*100.0))
        add_to_log(' ')
        add_to_log(path1)
        for at in Ats:
            path2 = '/At_=_' + str(at)
            path = path1 + path2
            s = 'mkdir -p {}'.format(path) # Make directories to copy base into, because Linux won't let you if the child directorieis are not there
            (o, e) = run_cmd(s)
            add_to_log('  ' + path2[1:])
            for css in Csss:
                i += 1
                path3 = '/Css_=_' + str(css)
                path = path1 + path2 + path3
                copy_data(pwd, path) # Make a directory for the job and copy all the data in it
                set_constants(path, ct, at, css, a2) # Change constants in menu file to current ct, at, and css
                ids = run_job(path, pwd, ids) # Run jobs and update ids
                add_to_log('    ' + path3[1:] + ', job {} out of {}'.format(i, total_tasks)) # Log that the job has been run
                ids = cleanse_ids(ids) # Chack for finished tasks and remove them from ids
                while count_jobs(ids) >= max_jobs: # Wait for the amount of tasks started will be less than maximum allowed
                    check_exit(ids) # Check if the user decided to end script
                    time.sleep(check_time) # Pause for check_time amount of time
    add_to_log(' ')
    add_to_log('Program finished')

#------------------------------------------------------#
if __name__ == '__main__':
    main()
