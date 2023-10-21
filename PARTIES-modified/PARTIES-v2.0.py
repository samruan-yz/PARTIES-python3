#!/usr/bin/python

from time import sleep
import random
import sys
import os
import collections
import threading

# sys.path.append('/home/sc2682/scripts/monitor')
# from monitorN import startMonitoring, endMonitoring
import subprocess

# MLat, State,CORES,CACHE WAYS, helpID,
CONFIG = "input.txt"  # default path to the input config.txt file
if len(sys.argv) > 1:
    CONFIG = sys.argv[1]

# QoS target of each application, in nanoseconds.
QOS = {"Resnet50": 15000000, "bert": 130000000}

INTERVAL = 0.1  # Frequency of monitoring, unit is second
TIMELIMIT = 200  # How long to run this controller, unit is in second.
# In essence, REST seems to define a period during which certain actions
# (like downsizing resources) cannot be taken again immediately for a particular application,
# ensuring there's a pause or "rest" period between such actions.
REST = 100
# Later in the script, within the init function,
# NUM is updated based on the contents of the configuration file
NUM = 0  # Number of colocated applications
# creates a list named APP that contains 10 None values.
APP = [None for i in range(10)]  # Application names
# IP = [None for i in range(10)]  # IP of clients that run applications
QoS = [None for i in range(10)]  # Target QoS of each application
ECORES = [i for i in range(8, 22, 1)]  # unallocated cores
CORES = [[] for i in range(10)]  # CPU allocation
# LOAD = []
# FREQ = [2200 for i in range(10)]  # Frequency allocation
EWAY = 0  # unallocated ways
WAY = [0 for i in range(10)]  # Allocation of LLC ways
Lat = [0 for i in range(10)]  # Real-time tail latency
MLat = [0 for i in range(10)]  # Real-time tail latency of a moving window
Slack = [0 for i in range(10)]  # Real-time tail latency slack
LSlack = [0 for i in range(10)]  # Real-time tail latency slack in the last interval
LLSlack = [0 for i in range(10)]  # Real-time tail latency slack in the last interval
LDOWN = [0 for i in range(10)]  # Time to wait before this app can be downsized again
CPU = [0 for i in range(10)]  # CPU Utilization per core of each application
cCPU = collections.deque(maxlen=(int(5.0 / INTERVAL)))
MEM = [0 for i in range(10)]  # Total memory bandwidth usage of each application
State = [0 for i in range(10)]  # FSM State during resource adjustment
rLat = [[] for i in range(10)]  # Save real-time latency for final plotting
rrLat = [[] for i in range(10)]  # Save real-time latency for final plotting
rCORES = [[] for i in range(10)]  # Save real-time #cores for final plotting
rWAY = [[] for i in range(10)]  # Save real-time #ways for final plotting
rFREQ = [[] for i in range(10)]  # Save real-time frequency for final plotting
# FF        = open("gabage.txt", "w")    # random outputs
PLOT = True  # If needed to do the final plotting
saveEnergy = True  # If needed to save energy when QoSes can all be satisfied
helpID = 0  # Application ID that is being helped. >0 means upSize, <0 means Downsize
victimID = 0  # Application that is helping helpID, thus is a innocent victim
TOLERANCE = 5  # Check these times of latency whenver an action is taken


def init():
    global EWAY, MLat, TIMELIMIT, CONFIG, NUM, APP, QoS, Lat, Slack, ECORES, CORES, FREQ, WAY, CPU, MEM, INTERVAL
    print("initialize!")

    # Open the file for reading using the CONFIG variable
    with open(CONFIG, "r") as file:
        # Read the first line and extract the number of CPU cores and cache ways
        CPU_num, EWAY = map(int, file.readline().split())
        ECORES = [i for i in range(CPU_num)]

        # Read the second line to get the number of processes
        NUM = int(file.readline().strip())

        # Loop through the file to read each process's details
        for i in range(NUM):
            line = file.readline().split()
            APP[i + 1] = line[0]
            QoS[i + 1] = int(line[1])
            WAY[i + 1] = EWAY // NUM
            MLat[i + 1] = collections.deque(maxlen=(int(1.0 / INTERVAL)))

        EWAY -= NUM * (EWAY // NUM)

        for i, ecore in enumerate(ECORES):
            CORES[i % NUM + 1].append(ecore)

        ECORES.clear()

        for i in range(EWAY):
            WAY[i + 1] += 1
            EWAY -= 1

        # if len(sys.argv) > 2:
        #     TIMELIMIT = int(sys.argv[2])
        # Read the name of colocated applications and their QoS target (may be in different units)

        # Lat = [None, 14197497, 964297742]
        # QoS = [None, 13200000, 160000000]
        # for i in range(1, NUM + 1, 1):
        #     MLat[i] = collections.deque(maxlen=(int(1.0 / INTERVAL)))
        #     MLat[i].append(Lat[i])
        #     print("Lat[", i, "]", Lat[i], "QOS", QoS[i], "MLat:", MLat[i])
        #     LSlack[i] = 1 - sum(MLat[i]) * 1.0 / len(MLat[i]) / QoS[i]
        #     # LSlack[i] = Slack[i]
        #     Slack[i] = (QoS[i] - Lat[i]) * 1.0 / QoS[i]


def update_lat():
    user_input = input("Enter 2 numbers separated by a space: ")
    numbers = [int(num) for num in user_input.split()]

    i = 1
    for num in numbers:
        Lat[i] = num
        MLat[i].append(num)
        i = i + 1


def run_processes():
    sleep(200)


def main():
    init()

    print("after initiation...")
    sleep(1)
    currentTime = 0
    while True:
        run_processes()
        update_lat()
        makeDecision()
        currentTime += 1
        print_res()

        print(MLat, currentTime, helpID, victimID)
        print("Slack:", Slack)
        print("LSlack:", LSlack)
        file_path = str(input("your output file:"))
        parse_output_file(file_path)


def print_res():
    print("Cores after adjustment: \n")
    print(CORES)
    print("Way after adjustment: \n")
    print(WAY)


def makeDecision():
    global Lat, LSlack, TOLERANCE, LLSlack, REST, Slack, NUM, FREQ, helpID, victimID
    print("Make a decision! ", helpID)
    if helpID > 0:
        cur = Lat[helpID]
        cnt = 0
        for i in range(TOLERANCE):
            # wait()
            if Lat[helpID] < cur:
                cnt += 1
            else:
                cnt -= 1
        if cnt <= 0:  # or (State[helpID] == 2 and FREQ[helpID] == 2300):
            # return revert(helpID)
            revert(helpID)
        # else:
        #     cnt = 0
        #     wait()
        #     while (Lat[helpID] < cur):
        #         cur = Lat[helpID]
        #         wait()
        helpID = victimID = 0
    elif helpID < 0:
        cur = Lat[-helpID]
        cnt = 0
        for i in range(TOLERANCE):
            # wait()
            flag = True
            for j in range(1, NUM + 1):
                if Slack[j] < 0.05:
                    flag = False
                    break
            if flag == False:
                cnt -= 1
            else:
                cnt += 1
        if cnt <= 0:
            # return revert(-helpID)  # Revert back as it doesn't benefit from this resource
            revert(helpID)
            #  wait()
            cnt = 0
            for i in range(TOLERANCE):
                # wait()
                flag = True
                for j in range(1, NUM + 1):
                    if Slack[j] < 0.05:
                        flag = False
                        break
                if flag == False:
                    cnt -= 1
                else:
                    cnt += 1
            if cnt <= 0:
                for i in range(TOLERANCE):
                    print("0")
                    # wait()
        #  while Slack[-helpID] < 0 or LSlack[-helpID] < 0:
        #      print "wait..."
        #      wait()
        helpID = victimID = 0
    else:
        # wait()
        print("wait!")
    if helpID == 0:  # Don't need to check any application before making a new decision
        idx = -1
        victimID = 0
        for i in range(1, NUM + 1):  # First find if any app violates QoS
            if Slack[i] < 0.05 and LSlack[i] < 0.05:
                if idx == -1 or LSlack[i] < LSlack[idx]:
                    idx = i
            elif (
                (LDOWN[i] == 0)
                and Slack[i] > 0.2
                and LSlack[i] > 0.2
                and (victimID == 0 or Slack[i] > Slack[victimID])
            ):
                victimID = i
        if idx != -1:
            return upSize(idx)  # If found, give more resources to this app
        elif (
            saveEnergy == True and victimID > 0
        ):  # If not found, try removing resources
            return downSize(victimID)
        else:
            # wait()
            print("wait")
    return True


# FSM state of resource adjustment
# -3: give it fewer cache
# -2: give it fewer frequency
# -1: give it fewer cores
#  0: not in adjustment
#  1: give it more cores
#  2: give it more frequency
#  3: give it more cache


def nextState(idx, upsize=True):
    global State
    if State[idx] == 0:
        if upsize == True:
            State[idx] = random.randint(1, 2)
        else:
            State[idx] = -random.randint(1, 2)
    elif State[idx] == -1:
        State[idx] = -2
    elif State[idx] == -2:
        State[idx] = -1
    elif State[idx] == 1:
        State[idx] = 2
    elif State[idx] == 2:
        State[idx] = 1
    else:
        assert False


def revert(idx):
    global State, APP, helpID, victimID, REST
    print(idx, " revert back")
    if idx < 0:
        if State[-idx] == -1:
            assert adjustCore(-idx, 1, False) == True
        # elif State[-idx] == -2:
        #     assert adjustFreq(-idx, 1) == True
        elif State[-idx] == -2:
            assert adjustCache(-idx, 1, False) == True
        else:
            assert False
        nextState(-idx)
        print(State[-idx])
        LDOWN[-idx] = REST
    else:
        nextState(idx)
        print(State[idx])
    return True


def upSize(idx):
    global State, helpID, victimID, APP
    victimID = 0
    helpID = idx
    if State[idx] <= 0:
        State[idx] = random.randint(1, 2)
    for k in range(3):
        #    (State[idx] == 2 and adjustFreq(idx, 1) == False) or \
        if (State[idx] == 1 and adjustCore(idx, 1, False) == False) or (
            State[idx] == 2 and adjustCache(idx, 1, False) == False
        ):
            nextState(idx)
        else:
            print(State[idx])
            print("Upsize ", APP[idx], "(", State[idx], ")")
            return True
    print("No way to upsize any more...")
    helpID = 0
    return False


def downSize(idx):
    global State, helpID, victimID
    print("Downsize ", APP[idx], "(", State[idx], ")")
    victimID = 0
    if State[idx] >= 0:
        State[idx] = -random.randint(1, 2)
    for k in range(3):
        #    (State[idx] == -2 and adjustFreq(idx, -1) == False) or \
        if (State[idx] == -1 and adjustCore(idx, -1, False) == False) or (
            State[idx] == -2 and adjustCache(idx, -1, False) == False
        ):
            nextState(idx)
        else:
            helpID = -idx
            return True
    return False


# def wait():
#     global INTERVAL, TIMELIMIT
#     sleep(INTERVAL)
#     for i in xrange(1, NUM+1):
# 	if LDOWN[i] > 0:
# 	    LDOWN[i] -= 1
#     getLat()
#     getData()
#     record()
#     if TIMELIMIT != -1:
#         TIMELIMIT -= INTERVAL
#         if TIMELIMIT < 0:
#             printout()
#             exit(0)


# def getLat():
#     global APP, Lat, MLat, LLSlack, LSlack, Slack, QoS, NUM

#     for i in xrange(1, NUM+1):
#         app = APP[i]
#         LLSlack[i] = Slack[i]
#         # hardcode Lat
#         Lat[i] =

#         MLat[i].append(Lat[i])
#         LSlack[i] = 1-sum(MLat[i])*1.0/len(MLat[i])/QoS[i]
#         #LSlack[i] = Slack[i]
#         Slack[i] = (QoS[i] - Lat[i])*1.0 / QoS[i]
#         print '  --', APP[i],':', Lat[i], '(', Slack[i], LSlack[i],')'


# FOLD
def getData():
    global NUM, cCPU, CPU, CORES, MEM
    tmp = 0
    # Monitoring of CPU and cache utilizataion is not needed in PARTIES manager. You can comment them out. These are just legacy codes and may be useful if you want to monitor real-time resource usage.
    # with open("/home/sc2682/scripts/monitor/cpu.txt", "r") as ff:
    #    lines = ff.readlines();
    #    while (len(lines) >=1 and "Average" in lines[-1]):
    #        lines = lines[:-1]
    #    if (len(lines) >= 22):
    #        lines = lines[-22:]
    #        cnt = [0 for i in xrange(0, NUM+10, 1)]
    #        for line in lines:
    #            if "Average" in line:
    #                break
    #            words = line.split()
    #            if len(words)<10:
    #                break
    #            cpuid = int(words[2])
    #            tmp += float(words[3])+float(words[5])+float(words[6])+float(words[8])
    #            for j in xrange(1, NUM+1, 1):
    #                if cpuid in CORES[j]:
    #                    CPU[j] += float(words[3])+float(words[5])+float(words[6])+float(words[8])
    #                    cnt[j] += 1
    #                break
    #        for j in xrange(1, NUM+1):
    #            if cnt[j] > 0:
    #                CPU[j] /= cnt[j]
    # cCPU.append(tmp/14.0)

    # with open("/home/sc2682/scripts/monitor/cat.txt", "r") as ff:
    #    lines = ff.readlines();
    #    if (len(lines) >= 22):
    #        lines = lines[-22:]
    #        for line in lines:
    #            words = line.split()
    #            if words[0] == "TIME" or words[0] == "CORE" or words[0] == "WARN":
    #                continue
    #            if ("WARN:" in words[0]) or ("Ter" in words[0]):
    #                break
    #            cpuid = int(words[0])
    #            for j in xrange(1, NUM+1):
    #                if cpuid in CORES[j]:
    #                    MEM[j] += float(words[4])+float(words[5])


def coreStr(cores):
    return ",".join(str(e) for e in cores)


def coreStrHyper(cores):
    return coreStr(cores) + "," + ",".join(str(e + 48) for e in cores)


def way(ways, rightways):
    return hex(int("1" * ways + "0" * rightways, 2))


def adjustCore(idx, num, hasVictim):
    global State, CORES, Slack, ECORES, victimID
    if num < 0:
        if len(CORES[idx]) <= -num:
            return False
        if hasVictim == False or victimID == 0:
            for i in range(-num):
                core_to_move = CORES[idx].pop()
                ECORES.append(CORES[idx].pop())
                print("Moved core ", core_to_move, "from", CORES[idx], "to ECORES")
        else:
            for i in range(-num):
                core_to_move = CORES[idx].pop()
                CORES[victimID].append(CORES[idx].pop())
                print(
                    "Moved core ", core_to_move, " from ", CORES[victimID], "to ECORES"
                )
            # propogateCore(victimID)
    else:
        assert num == 1 and hasVictim == False
        if len(ECORES) >= 1:
            CORES[idx].append(ECORES.pop())
        else:
            victimID = 0
            for i in range(1, NUM + 1):
                if (
                    i != idx
                    and len(CORES[i]) > 1
                    and (victimID == 0 or Slack[i] > Slack[victimID])
                ):
                    victimID = i
            if victimID == 0:
                return False
            core_to_move = CORES[victimID].pop()
            CORES[idx].append(CORES[victimID].pop())
            print(
                "Moved core", core_to_move, "from", CORES[victimID], "to ", CORES[idx]
            )
            if State[idx] == State[victimID]:
                nextState(victimID)
    #         propogateCore(victimID)
    # propogateCore(idx)
    return True


# def adjustFreq(idx, num):
#     global FREQ, APP, State
#     assert FREQ[idx] >=1200 and FREQ[idx] <= 2300
#     if num < 0:
#         if FREQ[idx] == 1200:
#             return False       # Frequency is already at the lowest. Cannot be reduced further
#         else:
#             FREQ[idx] += 100*num
#             propogateFreq(idx)
#     else:
#         if FREQ[idx] == 2300:
#             return False       # Shuang
#             victimID = 0
#             for i in xrange(1, NUM+1):
#                 if i!=idx and FREQ[i] > 1200 and (victimID == 0 or Slack[i] > Slack[victimID]):
#                     victimID = i
#             if victimID == 0:
#                 return False
#             else:
#                 FREQ[victimID] -= 100*num
#                 propogateFreq(victimID)
#                 if State[victimID] == State[idx]:
#                     nextState(victimID)
#         else:
#             FREQ[idx] += 100*num
#             propogateFreq(idx)
#     return True


def adjustCache(idx, num, hasVictim):
    global WAY, EWAY, NUM, victimID, State, Slack
    # num ==1 upsize, num == -1 downsize
    if num < 0:
        if WAY[idx] <= -num:
            return False
        if hasVictim == False or victimID == 0:
            EWAY -= num
            print("Increased EWAY by", num)
        else:
            WAY[victimID] -= num
            # propogateCache(victimID)
            print("Decreased", WAY[victimID], "by", num)
    else:
        assert num == 1 and hasVictim == False
        if EWAY > 0:
            EWAY -= 1
            print("Decreased EWAY by 1")
        else:
            victimID = 0
            for i in range(1, NUM + 1):
                if (
                    i != idx
                    and WAY[i] > 1
                    and (victimID == 0 or Slack[i] > Slack[victimID])
                ):
                    victimID = i
            if victimID == 0:
                return False
            WAY[victimID] -= num
            # propogateCache(victimID)
            print("Decreased", WAY[victimID], "by ", num)
            if State[idx] == State[victimID]:
                nextState(victimID)
    WAY[idx] += num
    # propogateCache(idx)
    print("Increased", WAY[idx], "by ", num)
    return True


# 只handle 两个app的版本，3个app需要小改
def upsizecores(idx):
    global APP, CORES, NUM, ECORES
    command = "bash"
    script = "collocation.sh"  # 要改
    if len(ECORES) >= 1:
        CORES[idx].append(ECORES.pop())
        if idx == 1:
            args1 = len(CORES[idx]) + 1
            args2 = len(CORES[3 - idx])
            args = [str(args1), str(args2)]
            run_command = [command, script] + args
            subprocess.run(run_command, capture_output=True, text=True)
            return True
        else:
            args1 = len(CORES[3 - idx])
            args2 = len(CORES[idx]) + 1
            args = [str(args1), str(args2)]
            run_command = [command, script] + args
            subprocess.run(run_command, capture_output=True, text=True)
            return True
    else:
        # Assume only 2 apps
        if idx == 2:
            CORES[idx].append(CORES[3 - idx].pop(index=-1))
            args1 = len(CORES[3 - idx]) - 1
            args2 = len(CORES[idx]) + 1
            args = [str(args1), str(args2)]
            run_command = [command, script] + args
            subprocess.run(run_command, capture_output=True, text=True)
            return True
        if idx == 1:
            CORES[idx].insert(0, CORES[3 - idx].pop())
            args1 = len(CORES[idx]) + 1
            args2 = len(CORES[3 - idx]) - 1
            args = [str(args1), str(args2)]
            run_command = [command, script] + args
            subprocess.run(run_command, capture_output=True, text=True)
            return True
    return True


def downsizecores(idx):
    global APP, CORES, NUM, ECORES
    command = "bash"
    script = "collocation.sh"  # 要改
    ECORES.append(CORES[idx].pop())
    if idx == 1:
        args1 = len(CORES[idx]) - 1
        args2 = len(CORES[3 - idx])
        args = [str(args1), str(args2)]
        run_command = [command, script] + args
        subprocess.run(run_command, capture_output=True, text=True)
        return True
    else:
        args1 = len(CORES[3 - idx])
        args2 = len(CORES[idx]) - 1
        args = [str(args1), str(args2)]
        run_command = [command, script] + args
        subprocess.run(run_command, capture_output=True, text=True)
        return True
    return True


def Upsizecache(idx):
    global APP, CORES, EWAY, WAY
    command = "bash"
    script = "collocation.sh"  # 要改
    if EWAY >= 1:
        EWAY -= 1
        WAY[idx] += 1
    else:
        WAY[idx] += 1
        WAY[3 - idx] -= 1
    if idx == 1:
        args1 = WAY[idx]
        args2 = WAY[3 - idx]
        args = [str(args1), str(args2)]
        run_command = [command, script] + args
        subprocess.run(run_command, capture_output=True, text=True)
        return True
    if idx == 2:
        args1 = WAY[3 - idx]
        args2 = WAY[idx]
        args = [str(args1), str(args2)]
        run_command = [command, script] + args
        subprocess.run(run_command, capture_output=True, text=True)
        return True
    return True


def Downsizecache(idx):
    global APP, CORES, EWAY, WAY
    command = "bash"
    script = "collocation.sh"  # 要改
    EWAY += 1
    WAY[idx] -= 1
    if idx == 1:
        args1 = WAY[idx]
        args2 = WAY[3 - idx]
        args = [str(args1), str(args2)]
        run_command = [command, script] + args
        subprocess.run(run_command, capture_output=True, text=True)
        return True
    if idx == 2:
        args1 = WAY[3 - idx]
        args2 = WAY[idx]
        args = [str(args1), str(args2)]
        run_command = [command, script] + args
        subprocess.run(run_command, capture_output=True, text=True)
        return True
    return True


def parse_output_file(file_path):
    global APP, Lat
    try:
        with open(file_path, "r") as file:
            data_lines = []
            for line in file:
                if "Latency/ms" in line:
                    # Get the next two lines
                    for _ in range(2):
                        data_line = next(file, None)
                        if data_line:
                            values = data_line.split()
                            latency = float(values[-5])
                            completed_qps = float(values[-6])
                            issue_qps = float(values[-7])
                            data_lines.append((latency, completed_qps, issue_qps))

            # Check if we have two lines of data and print them
            if len(data_lines) == 2:
                print(
                    f"Resnet50 - Latency: {data_lines[0][0]}, Completed QPS: {data_lines[0][1]}, Issue QPS: {data_lines[0][2]}"
                )
                print(
                    f"Bert - Latency: {data_lines[1][0]}, Completed QPS: {data_lines[1][1]}, Issue QPS: {data_lines[1][2]}"
                )
                print("-----")
                for i in range(2):
                    Lat[i + 1] = data_lines[i][0]

            else:
                print("Error: Did not find two lines of data after 'Latency/ms'")
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except Exception as e:
        print(f"Error: An unexpected error occurred while parsing the file: {e}")


if __name__ == "__main__":
    main()
