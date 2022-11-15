import os
import random
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

cmd_gen = './generate_thread.sh '
cmd_regen = './re_generate_thread.sh '
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


def get_frame_time(aiger, str_list):
    str_1 = ''
    str_2 = ''
    for i in range(len(str_list)):
        if str_list[i].startswith('Output') or str_list[i].startswith('Invariant'):
            str_1 = str_list[i]
        if str_list[i].startswith('Property'):
            str_2 = str_list[i]
    list = str_1.split()
    if str_1 == '':
        print("ERROR!") 
        return 1
    if list[0] == 'Output':
        for i in range(len(list)):
            if list[i] == 'frame':
                aiger.frame = int(list[i+1][0:-1])
            if list[i] == '=':
                aiger.time = float(list[i+1])
    elif list[0] == 'Invariant':
        aiger.res = True  # case is safe
        aiger.frame = int(list[1][2:-1])
    else:
        print("取出frame错误!")
        return 1

    if str_2 != '':
        list_2 = str_2.split()
        for i in range(len(list_2)):
            if list_2[i] == '=':
                aiger.time = float(list_2[i+1])
    
    return 0


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
    print("thread id" + str(t.ident))  # thread id
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
        aiger = Aiger()   
        get_latch_ands(aiger, line_list[0])
        # print(line_list[-2])
        if line_list[-2] == '124':
            aiger.time = 7200
        elif get_frame_time(aiger, line_list):
            print(t.ident)
            exit(0)
        if aiger.input == 0:
            continue
        # print(aiger.time)

        lock.acquire()
        aiger.name = 'gen' + str(index) + '.aag'
        if pos == 0 or index == 1:            
            if aiger.res == True:  # new safe case is not included
                lock.release()
                continue            
            unsafe_q.append(aiger.name)
            aiger_obj[aiger.name] = aiger
            end_time = time.time()
            of.write(aiger.name + ' ' + output)
            of.write('gen_time:' + str(end_time-start_time)+'\n')  # time stamp
            of_2.write("produce a new aiger:" + aiger.name + '\n')
        else:
            aiger_temp = aiger_obj[unsafe_q[pos-1]]
            if (aiger.res != aiger_temp.res):  # safe case
                end_time = time.time()
                of.write(aiger.name + ' ' + output)
                of.write('gen_time:' + str(end_time-start_time)+'\n')
                of_2.write('regenerate a new aiger:' + aiger.name + ' based on ' + aiger_temp.name + '\n')
            elif (aiger.frame > aiger_temp.frame and aiger.ands > aiger_temp.ands 
            and aiger.time > aiger_temp.time) or aiger.time == 7200:
                unsafe_q.append(aiger.name)                
                aiger_obj[aiger.name] = aiger
                end_time = time.time()
                of.write(aiger.name + ' ' + output)
                of.write('gen_time:' + str(end_time-start_time)+'\n')
                of_2.write('regenerate a new aiger:' + aiger.name + ' based on ' + aiger_temp.name + '\n')
            else:
                lock.release()
                continue
        res = os.popen('cp temp/gen'+str(t.ident)+'.aag '+'aigerfile_thread/gen'+str(index)+'.aag')
        res.read()
        res = os.popen('cp temp/gen'+str(t.ident)+'.aig '+'aigerfile_thread/gen'+str(index)+'.aig')
        res.read()
        of.flush()
        of_2.flush()
        print(index)
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
    