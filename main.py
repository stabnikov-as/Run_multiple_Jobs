#!/bin/env python
import os
import time
import subprocess
import shlex


#----------------------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------Constant-Values---------------------------------------------------------#
Cts  = [1.0, 2.0]#, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0]
Ats  = [1.0, 2.0]#, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0]
Csss = [0.4, 0.6]#, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6]
a2  = 0.99#[]
#----------------------------------------------------------------------------------------------------------------------------------#
cmd		= 'sbatch'
job_fn	= 'tr_bl.pbs'#'matr.slrm'
d_file  = 'd_uduct.in'
cmd     = 'qsub' # 'sbatch'
#------------------------------------------------------#
def read_file(fn):
    f = open(fn, 'r')
    ss = f.readlines()
    f.close()
    return ss

#------------------------------------------------------#
def write_file(fn, ss):
    f = open(fn, "w")
    f.writelines(ss)
    f.close()

#------------------------------------------------------#

def set_constants(path, ct, at, css, a2):
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
def run_cmd(cmd):
    command = shlex.split(cmd)
    p = subprocess.Popen(command,
	stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (out, err)

#------------------------------------------------------#
def run_job(path, ids):
    cmd_job = cmd + ' ' + path + '/' + job_fn
    (o, e) = run_cmd(cmd_job)
    id = o.split('.')[0]
    ids.append(id)
    print('  Run job: {}'.format(id))
    return ids

#------------------------------------------------------#
def count_jobs(ids):
    # wait for job
    num_jobs = 0
    s = 'q'
    (o, e) = run_cmd(s)
    n = o.split('\n')
    for job in n[:-1]:
        if job.split()[0] in ids: num_jobs += 1
    return num_jobs
#------------------------------------------------------#
def main():
    ids = []
    for ct in Cts:
        path1 = 'Ct_=_' + str(ct)
        for at in Ats:
            path2 = '/At_=_' + str(at)
            path = path1 + path2
            s = 'mkdir -p {}'.format(path)
            (o, e) = run_cmd(s)
            for css in Csss:
                path3 = '/Css_=_' + str(css)
                path = path1 + path2 + path3
                s = 'cp -avr base {}'.format(path)
                (o, e) = run_cmd(s)
                set_constants(path, ct, at, css, a2)
                ids = run_job(path, ids)

#------------------------------------------------------#
if __name__ == '__main__':
    main()
