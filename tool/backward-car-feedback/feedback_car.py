import os
import random
import sys
import threading
import math
from threading import Thread, Lock
import time

class Aiger:
    def __init__(self):
        self.name = ''
        self.latch = 0
        self.ands = 0
        self.frame = 0
        self.input = 0
        self.time = 0
        self.index = 0
        self.res = False


cmd_gen = './generate_car.sh '
cmd_regen = './re_generate_car.sh '
cmd_check = './validation_car.sh '
of = open('result_thread/record.txt', 'a+')
of_2 = open('result_thread/relation.txt', 'a+')

index = 1
unsafe_q = []  # unsafe_q is unsafe case queue
safe_q = [] # safe_q is safe case queue
aiger_obj = {}
aiger_nums = 1000000
thread_nums = 8
lock = Lock()

start_time = time.time()

def get_latch_ands(aiger, str):
    list = str.split()
    for i in range(len(list)):
        if list[i] == 'latches,':
            aiger.latch = int(list[i-1])
            # print(aiger.latch)
        if list[i] == 'ands.':
            aiger.ands = int(list[i-1])
            # print(aiger.ands)
        if list[i] == 'inputs,':
            aiger.input = int(list[i-1])


def get_frame_time(aiger, thread_id):
    f_res = open("temp/gen" + str(thread_id) + ".res")
    f_log = open("temp/gen" + str(thread_id) + ".log")
    res_lines = f_res.readlines()
    if res_lines[0] == '0\n': aiger.res = True
    aiger.frame = len(res_lines)
    # print(aiger.frame)
    log_lines = f_log.readlines()
    str_list = log_lines[len(log_lines)-1].split()
    aiger.time = float(str_list[2])
    # print(aiger.time)
    f_res.close()
    f_log.close()


def get_pos(queue_len):
    pos = math.floor(math.sqrt(random.randint(0, queue_len**2)))
    return pos


def func():
    global index
    global unsafe_q
    global safe_q
    global aiger_obj
    global aiger_nums
    pos = 0
    t = threading.currentThread()   
    print(t.ident)  # thread id
    while index <= aiger_nums:
        lock.acquire()
        of_2.write("index:" + str(index) + '\n')
        lock.release()
        if index == 1: 
            res_gen = os.popen(cmd_gen + str(t.ident))
        else:
            pos = random.randint(0, len(unsafe_q))
            if pos == 0:
                res_gen = os.popen(cmd_gen + str(t.ident))
            else:
                res_gen = os.popen(cmd_regen + unsafe_q[pos-1] + ' ' + str(t.ident))
        output = res_gen.read()
        
        line_list = output.split('\n')
        # print(line_list[-2])
        if line_list[-2] == '124':  # generate aiger timeout
            print('generate aiger timeout')
            continue
        aiger = Aiger()   
        get_latch_ands(aiger, line_list[0]) 
        if aiger.input == 0:
            print('==1==')
            continue
        
        res = os.popen(cmd_check + str(t.ident))  # verify
        output_vali = res.read() 
        if output_vali.split('\n')[0] == '124':  # verify aiger timeout
            aiger.time = 7200   
        else:             
            get_frame_time(aiger, t.ident)       
        
        # print(aiger.time)
        
        lock.acquire()
        aiger.name = 'gen' + str(index) + '.aag'
        if pos == 0 or index == 1:
            if aiger.res == True:
                lock.release()
                continue            
            unsafe_q.append(aiger.name)
            aiger_obj[aiger.name] = aiger
            of.write(aiger.name + ' ' + line_list[0] + '\n')
            end_time = time.time()
            of.write(str(aiger.res) + ' frame:' + str(aiger.frame) + ' time:' + str(aiger.time) + ' gen_time:'+str(end_time-start_time) + '\n')
            of_2.write("produce a new aiger:" + aiger.name + '\n')
            # lock.release()
        else:
            aiger_temp = aiger_obj[unsafe_q[pos-1]]
            if (aiger.res != aiger_temp.res):  # safecase
                of.write(aiger.name + ' ' + line_list[0] + '\n')
                end_time = time.time()
                of.write(str(aiger.res) + ' frame:' + str(aiger.frame) + ' time:' + str(aiger.time) + ' gen_time:'+str(end_time-start_time) + '\n')
                of_2.write('regenerate a new aiger:' + aiger.name + ' based on ' + aiger_temp.name + '\n')
            elif (aiger.ands > aiger_temp.ands and aiger.time > aiger_temp.time) or aiger.time == 7200:
                if aiger.res == False:  # case is unsafe
                    unsafe_q.append(aiger.name)
                aiger_obj[aiger.name] = aiger
                of.write(aiger.name + ' ' + line_list[0] + '\n')
                end_time = time.time()
                of.write(str(aiger.res) + ' frame:' + str(aiger.frame) + ' time:' + str(aiger.time) + ' gen_time:'+str(end_time-start_time) + '\n')
                of_2.write('regenerate a new aiger:' + aiger.name + ' based on ' + aiger_temp.name + '\n')
            else:
                lock.release()
                continue
        res = os.popen('cp temp/gen'+str(t.ident)+'.aag '+'aigerfile_thread/gen'+str(index)+'.aag')
        res.read()
        res = os.popen('cp temp/gen'+str(t.ident)+'.aig '+'aigerfile_thread/gen'+str(index)+'.aig')
        res.read()
        res = os.popen('cp temp/gen'+str(t.ident)+'.log '+'res_log/gen'+str(index)+'.log')
        res.read()
        res = os.popen('cp temp/gen'+str(t.ident)+'.res '+'res_log/gen'+str(index)+'.res')
        res.read()
        print(index)
        of.flush()
        of_2.flush()
        aiger.index = index
        index += 1
        lock.release()   


def main():
    l = []
    for i in range(thread_nums):
        p = Thread(target=func)
        l.append(p)
        p.start()
        time.sleep(3)
    for p in l:
        p.join()
       


if __name__=='__main__':
    main()
    of.close()
    of_2.close()