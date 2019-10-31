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

#-------files-----#
d_file  = 'd_uduct.in' # Menu file for the job
log_fn  = 'log' + get_datetime() + '.txt' # Name of log output file
exit_fn = 'exit.in' # Name of file to control the exit from the program (analogous to keyboard.cfg)
base_dir = 'base'
code_fn = 's_tr_bl-r8'
code_dir = 'code'
grid_fn = 'Grid_tbl.blk'
grid_dir = 'grid'

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
    command = shlex.split(cmd)
    p = subprocess.Popen(command,
	stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd = cwd)
    out, err = p.communicate()
    return (out, err)

#------------------------------------------------------#
def run_job(path, pwd, ids):
    path_to_job = pwd + path + '/'
    cmd_job = cmd + ' ' + path_to_job + job_fn
    (o, e) = run_cmd(cmd_job, cwd = path_to_job)
    id = o.split('.')[0]
    ids[id] = path
    return ids

#------------------------------------------------------#
def check_exit(ids):
    s = read_file(exit_fn)
    if s[0].rstrip(' \n').lstrip(' ') == '2':
        add_to_log('--------------------------------')
        add_to_log('--------------------------------')
        add_to_log('Program exited due to user input')
        add_to_log('----------Jobs killed:----------')
        cmd = kill_cmd
        for id in ids:
            cmd+= ' ' + id
            add_to_log('{} {}'.format(id, ids[id]))
        (o, e) = run_cmd(cmd)
        add_to_log('--------End-of-program.---------')
        sys.exit()
    elif s[0].rstrip(' \n').lstrip(' ') == '1':
        add_to_log('--------------------------------')
        add_to_log('--------------------------------')
        add_to_log('Program exited due to user input')
        add_to_log('--------No-jobs-killed.---------')
        add_to_log('--------Remaining-jobs.---------')
        for id in ids:
            add_to_log('{} {}'.format(id, ids[id]))
        add_to_log('--------End-of-program.---------')
        sys.exit()

#------------------------------------------------------#
def count_jobs(ids):
    num_jobs = 0
    s = 'q'
    (o, e) = run_cmd(s)
    n = o.split('\n')
    for job in n[:-1]:
        if job.split()[0] in ids and job.split()[1] != 'C': num_jobs += 1
    return num_jobs

#------------------------------------------------------#
def cleanse_ids(ids):
    jobs = []
    new_ids = ids.copy()
    s = 'q'
    (o, e) = run_cmd(s)
    n = o.split('\n')
    for job in n[2:-1]:
        if job.split()[1] != 'C':
            jobs.append(job.split()[0])
    for id in ids:
        if not id in jobs:
            new_ids.pop(id)
    ids = new_ids.copy()
    return ids

def copy_data(pwd, path):
    s = 'cp -avr {} {}'.format(base_dir, path)
    (o, e) = run_cmd(s)
    s = 'ln -s {3}{0}/{1} {2}/{1}'.format(grid_dir, grid_fn, path, pwd)
    (o, e) = run_cmd(s)
    s = 'ln -s {3}{0}/{1} {2}/{1}'.format(code_dir, code_fn, path, pwd)
    (o, e) = run_cmd(s)
#------------------------------------------------------#
def main():
    write_file(exit_fn, ['0'])
    add_to_log('Cts = '+ str(Cts))
    add_to_log('Ats = '+ str(Ats))
    add_to_log('Csss = '+ str(Csss))
    add_to_log('a2s = '+ str(a2s))
    a2 = a2s[0]
    i = 0
    cmd_path = 'pwd'
    (o, e) = run_cmd(cmd_path)
    pwd = o.split('\n')[0]+'/'
    write_log_header()
    total_tasks = len(Ats) * len(Cts) * len(Csss) * len(a2s)
    add_to_log('amount of jobs = {}'.format(total_tasks))
    add_to_log('max jobs       = {}'.format(max_jobs))
    ids = {}
    for ct in Cts:
        path1 = 'Ct_=_' + str(ct)
        add_to_log('\n')
        add_to_log('----------------------------------{}% complete'.format(float(i)/float(total_tasks)*100.0))
        add_to_log('\n')
        add_to_log(path1)
        for at in Ats:
            path2 = '/At_=_' + str(at)
            path = path1 + path2
            s = 'mkdir -p {}'.format(path)
            (o, e) = run_cmd(s)
            add_to_log('  ' + path2[1:])
            for css in Csss:
                i += 1
                path3 = '/Css_=_' + str(css)
                path = path1 + path2 + path3
                copy_data(pwd, path)
                set_constants(path, ct, at, css, a2)
                ids = run_job(path, pwd, ids)
                add_to_log('    ' + path3[1:] + ', job {} out of {}'.format(i, total_tasks))
                ids = cleanse_ids(ids)
                while count_jobs(ids) >= max_jobs:
                    check_exit(ids)
                    time.sleep(check_time)
    add_to_log('Program finished')

#------------------------------------------------------#
if __name__ == '__main__':
    main()
