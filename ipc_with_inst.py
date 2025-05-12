#!/usr/bin/env python3

import os
import re
import socket
import subprocess

import pandas as pd

LATENCY = {
    "ZERO": 0,
    "PWC": 1,
    # "PWC"    : 0.25,
    "TLB": 1,
    "ICACHE": 0,
    # "L1"     : 4,
    # "L2"     : 14,
    # "LLC"    : 54,
    # "MEMORY" : 200,
    "L1": 2,
    "L2": 16,
    "LLC": 56,
    "MEMORY": 180,
    "INST": 0.5,
}

# LATENCY = {
#     "ZERO": 0,
#     "PWC": 1,
#     # "PWC"    : 0.25,
#     "TLB": 1,
#     "ICACHE": 0,
#     # "L1"     : 4,
#     # "L2"     : 14,
#     # "LLC"    : 54,
#     # "MEMORY" : 200,
#     "L1": 2,
#     "L2": 16,
#     "LLC": 56,
#     "MEMORY": 160,
#     "INST": 0.25,
# }

detailed_stats_base = {
    "bench": "",
    
    "total_inst": 0.0,
    "total_cycles": 0.0,
    "ipc": 0.0,
    "kernel_inst": 0.0,
    "user_inst": 0.0,
    "ifcache_cycles": 0.0,
    "inst_exec_cycles": 0.0,
    "n_ifcache_hit": 0.0,
    "n_ifcache_miss": 0.0,
    "tlb_cycles": 0.0,
    "n_tlb_hit": 0.0,
    "n_tlb_miss": 0.0,
    "page_walk_cycles": 0.0,
    "n_page_walk": 0.0,
    "page_walk_latency": 0.0,
    "data_cycles": 0.0,
    "n_data": 0.0,
    "n_inst_data"  : 0.0,
    "n_rw_data"  : 0.0,
}

THP = "never"
DATA_FOLDER = "/data/EMT"
STAT_FOLDER = "./ipc_stats"

HASH_LATENCY = 2
PUD_CWC_LATENCY = LATENCY["PWC"]
PMD_CWC_LATENCY = LATENCY["PWC"]


RADIX_MATCH = re.compile(
    "^core=(?P<core>\d+),is_inst=(?P<inst>0|1),is_non_memory_exec=(?P<nmem>0|1),"
    "cached_ifb=(?P<icah>0|1),tlb_hit= (?P<tlbh>0|1),(?P<pgwk_str>(?:(?:ZERO|PWC|L1|L2|LLC|MEMORY),)*)"
    "data=(?P<data>ZERO|PWC|L1|L2|LLC|MEMORY),\t(?P<freq>\d+)$",
    re.MULTILINE,
)

ECPT_MATCH = re.compile(
    "^core=(?P<core>\d+),is_inst=(?P<inst>0|1),is_non_memory_exec=(?P<nmem>0|1),"
    "cached_ifb=(?P<icah>0|1),tlb_hit= (?P<tlbh>0|1),(?P<pgwk_str>(?:(?:ZERO|PWC|L1|L2|LLC|MEMORY),)*)selected_way=(?P<selected_way>\d+),"
    "data=(?P<data>ZERO|PWC|L1|L2|LLC|MEMORY),\s?(?P<freq>\d+)$",
    re.MULTILINE,
)


def get_inst_num(dyna_log_path):
    number = 0

    kernel_inst = 0
    user_inst = 0
    current_section = ""

    with open(dyna_log_path, "r") as file:
        for _, line in enumerate(file):

            # print(line)
            if line.startswith("kernel memory references"):
                current_section = "kernel"
            elif line.startswith("user memory references"):
                current_section = "user"

            if current_section != "":
                if line.startswith("16,"):
                    n_inst = int(line.split(",")[1].strip())
                    if current_section == "kernel":
                        kernel_inst = n_inst
                    elif current_section == "user":
                        user_inst = n_inst

    return kernel_inst, user_inst


def readAllLines(path: str) -> list[str]:
    with open(path) as file:
        lines = [line.strip() for line in file]
        return lines


def get_page_walk_latency_radix(pgwk_str: str) -> float:
    if len(pgwk_str) == 0:
        return 0

    cur_latency = 0.0
    for idx, stat in enumerate(pgwk_str.split(",")):
        if stat in LATENCY:
            cur_latency += LATENCY[stat]

            pwc_extra = 0
            if stat == "PWC":
                pwc_extra = LATENCY["PWC"] * (2 - idx)

            cur_latency += pwc_extra

            assert idx < 4

        else:
            print("Invalid stat: {}".format(stat))
    return cur_latency
    # return sum([LATENCY[pgst] for pgst in pgwk_str.split(',')])

def get_page_walk_latency_ecpt(pgwk_str: str, selected_way: str) -> float:
    if len(pgwk_str) == 0:
        return 0

    latency = 0.0
    selected_way_int = int(selected_way)
    
    pgwak_arr = pgwk_str.split(",")
    
    latency = LATENCY[pgwak_arr[selected_way_int]]
    
    assert(latency != 0)
    
    latency += max(HASH_LATENCY, PUD_CWC_LATENCY, PMD_CWC_LATENCY)
    
    # latency = max(latency + HASH_LATENCY, PUD_CWC_LATENCY,  PMD_CWC_LATENCY)
    return latency
    # return sum([LATENCY[pgst] for pgst in pgwk_str.split(',')])


# Memory parallism
DATA_PARALLELISM = 8

def parseOneLine(line: str, stats: dict[str, float], arch: str):
    
    if arch == "radix":
        match_regex = RADIX_MATCH
    elif arch == "ecpt":
        match_regex = ECPT_MATCH
    else:
        assert(False)
    
    match = match_regex.match(line)

    if not match:
        if line.startswith("core"):
            print("Invalid line: {}".format(line))
        return 0

    core = int(match.group("core"))
    inst = int(match.group("inst"))
    nmem = int(match.group("nmem"))
    icache_hit = int(match.group("icah"))
    ltb_hit = int(match.group("tlbh"))
    data = LATENCY[match.group("data")]
    freq = int(match.group("freq"))

    pgwk_str = match.group("pgwk_str").rstrip(",")

    if arch == "radix":
        pgwk_latency = get_page_walk_latency_radix(pgwk_str)
    elif arch == "ecpt":
        selected_way = match.group("selected_way")
        pgwk_latency = get_page_walk_latency_ecpt(pgwk_str, selected_way)
        # print(pgwk_latency, pgwk_str, selected_way)
    else:
        assert(False)
        
    # print(line)
    
    # nonmemory exec = 0 ->  data acces latency
    # non memory exec = 1 ->  exec_latency + fetch instruction latency
    
    

    if inst == 1:
        if nmem == 0:
            # instruction fetch miss with data access
            # executiont latency hidden.
            pass
        else:
            
            
            if icache_hit == 1:
                stats["n_ifcache_hit"] += freq
                stats["ifcache_cycles"] += freq * LATENCY["ICACHE"]
                stats["inst_exec_cycles"] += freq * LATENCY["INST"]
            else:
                stats["n_ifcache_miss"] += freq
                stats["ifcache_cycles"] += freq * LATENCY["ICACHE"]
                stats["inst_exec_cycles"] += freq * LATENCY["INST"]

                if ltb_hit == 1:
                    # icache miss tlb hit instruction fetch
                    stats["n_tlb_hit"] += freq
                    stats["tlb_cycles"] += freq * LATENCY["TLB"]

                    # return inst_lat(freq, freq, LATENCY["ICACHE"] + LATENCY["TLB"] + data + LATENCY["INST"])
                else:
                    stats["n_tlb_miss"] += freq
                    stats["tlb_cycles"] += freq * LATENCY["TLB"]

                    stats["page_walk_cycles"] += freq * pgwk_latency
                    stats["n_page_walk"] += freq
                
                stats["data_cycles"] += (freq / DATA_PARALLELISM) * data 
                stats["n_data"] += freq
                stats["n_inst_data"] += freq
                    
                    
        # # instruction fetch
        # if icache_hit == 1:
        #     # icache hit instruction fetch
        #     stats["n_ifcache_hit"] += freq
        #     stats["ifcache_cycles"] += freq * LATENCY["ICACHE"]
        #     stats["inst_exec_cycles"] += freq * LATENCY["INST"]
        #     # return inst_lat(freq, freq, LATENCY["ICACHE"] + LATENCY["INST"])
        # else:

        #     stats["n_ifcache_miss"] += freq
        #     stats["ifcache_cycles"] += freq * LATENCY["ICACHE"]
        #     stats["inst_exec_cycles"] += freq * LATENCY["INST"]

        #     # instruction fetch miss
            
        #     if nmem == 0:
        #         # instruction fetch miss with data access
        #         # data fetching latency hidden.
        #         pass
        #     else:
        #         stats["data_cycles"] += (freq / DATA_PARALLELISM) * data 
        #         stats["n_data"] += freq
        #         stats["n_inst_data"] += freq
            
        #         # icache miss instruction fetch
        #         if ltb_hit == 1:
        #             # icache miss tlb hit instruction fetch
        #             stats["n_tlb_hit"] += freq
        #             stats["tlb_cycles"] += freq * LATENCY["TLB"]

        #             # return inst_lat(freq, freq, LATENCY["ICACHE"] + LATENCY["TLB"] + data + LATENCY["INST"])
        #         else:
        #             stats["n_tlb_miss"] += freq
        #             stats["tlb_cycles"] += freq * LATENCY["TLB"]

        #             stats["page_walk_cycles"] += freq * pgwk_latency
        #             stats["n_page_walk"] += freq    

                # icache miss tlb miss instruction fetch
                # return inst_lat(freq, freq, LATENCY["ICACHE"] + LATENCY["TLB"] + pgwk_latency + data + LATENCY["INST"])
    else:
        # data fetch
        
        stats["n_data"] += freq
        stats["n_rw_data"] += freq
        stats["data_cycles"] += (freq / DATA_PARALLELISM) * data
        
        para_freq = freq 
        if ltb_hit == 1:
            # tlb hit data fetch

            stats["n_tlb_hit"] += para_freq
            stats["tlb_cycles"] += para_freq * LATENCY["TLB"]

            # return inst_lat(0, freq / MEMPARA, LATENCY["TLB"] + data)
        else:
            stats["n_tlb_miss"] += para_freq
            stats["tlb_cycles"] += para_freq * LATENCY["TLB"]

            stats["page_walk_cycles"] += para_freq * pgwk_latency
            stats["n_page_walk"] += para_freq

            # tlb miss data fetch
            # return inst_lat(0, freq / MEMPARA, LATENCY["TLB"] + pgwk_latency + data)


def post_parsing_process(stats: dict[str, float]):
    stats["total_cycles"] = (
        stats["ifcache_cycles"]
        + stats["tlb_cycles"]
        + stats["page_walk_cycles"]
        + stats["data_cycles"]
        + stats["inst_exec_cycles"]
    )
    stats["total_inst"] = stats["kernel_inst"] +  stats["user_inst"]
    stats["page_walk_latency"] = stats["page_walk_cycles"] / stats["n_page_walk"]

    stats["ipc"] = stats["total_inst"] / stats["total_cycles"]

    return stats


def scp_from_remote(host, remote_path, local_path):
    """
    Transfers a file from a remote machine to the local machine using SCP via subprocess.
    """
    try:
        # Construct the SCP command
        scp_command = ["scp", f"{host}:{remote_path}", local_path]
        # if key_file:
        #     scp_command.extend(["-i", key_file])
        # scp_command.append(f"{username}@{host}:{remote_path}")
        # scp_command.append(local_path)

        # Execute the command
        subprocess.run(scp_command, check=True)
        print(f"File successfully copied from {host}:{remote_path} to {local_path}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running SCP: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def process_one_file_ipc(bench, machine, path, arch):
    
    if machine is None or machine == socket.gethostname():
        file_name = path
    else:
        file_name = f"local/{os.path.basename(path)}.local"
        os.makedirs("local", exist_ok=True)
        scp_from_remote(machine, path, file_name)
        
    
    lines = readAllLines(file_name)
    stats = detailed_stats_base.copy()
    
    stats["bench"] = bench
    
    for line in lines:
        parseOneLine(line, stats, arch)

    stats["kernel_inst"], stats["user_inst"] = get_inst_num(file_name)

    post_parsing_process(stats)
    # print(stats)
    
    stats["machine"] = machine
    stats["path"] = path

    # with open(f"./stats/{arch}/{os.path.basename(file_name)}.ipc.csv", "w") as f:
    #     pd.DataFrame([stats]).to_csv(f, index=False)
    
    return stats

def process_from_list(bench_infos, arch, stage):

    stat_list = []
    
    for info in bench_infos:
        print(info)
        bench, machine, path = info
        stats = process_one_file_ipc(bench, machine, path, arch)
        stat_list.append(stats)
    
    df = pd.DataFrame(stat_list)
    
    # df.to_csv(f"ipc_stats_{arch}_{stage}.csv", index=False)
    # print('save to ', f"ipc_stats_{arch}_{stage}.csv")
    return df

def calc_ipc_speedup(radix_stats, ecpt_stats, stage):
    radix_stats = radix_stats.set_index('bench')
    ecpt_stats = ecpt_stats.set_index('bench')
    
    ipc_speedup = ecpt_stats['ipc']  / radix_stats['ipc']
    e2e_speedup = radix_stats['total_cycles'] / ecpt_stats['total_cycles'] 
    pgwalk_speedup = radix_stats['page_walk_latency'] / ecpt_stats['page_walk_latency']
    
    print(ipc_speedup)
    # print(e2e_speedup)    
    print('Radix IPC: ', radix_stats['ipc'])
    print('IPC speedup: ', ipc_speedup.mean())

    speedups = pd.concat([pgwalk_speedup, ipc_speedup, e2e_speedup], axis=1)
    speedups.columns = ['pgwalk_speedup', 'ipc_speedup', 'e2e_speedup']
    
    ecpt_stats = pd.concat([speedups, ecpt_stats], axis=1)
    print(ecpt_stats)
    
    all_ones = radix_stats['ipc']  / radix_stats['ipc']
    speedups = pd.concat([all_ones, all_ones, all_ones], axis=1)
    speedups.columns = ['pgwalk_speedup', 'ipc_speedup', 'e2e_speedup']
    radix_stats = pd.concat([speedups, radix_stats], axis=1)
    
    with open(f'{STAT_FOLDER}/ipc_stats_radix_{THP}_{stage}.csv', 'w') as f:
        # f.write(f'Radix {stage}\n')
        radix_stats.to_csv(f)
        print('save to', os.path.realpath(f'{STAT_FOLDER}/ipc_stats_radix_{THP}_{stage}.csv'))
    
    with open(f'{STAT_FOLDER}/ipc_stats_ecpt_{THP}_{stage}.csv', 'w') as f:
        # f.write(f'ECPT {stage}\n')
        ecpt_stats.to_csv(f)
        print('save to', os.path.realpath(f'{STAT_FOLDER}/ipc_stats_ecpt_{THP}_{stage}.csv'))

    # print('save to ', f'ipc_stats_{stage}.csv')

    return radix_stats, ecpt_stats


def calc_running_ipc():
    print(LATENCY)
    
    RADIX_FOLDER = f'{DATA_FOLDER}/radix'
    ECPT_FOLDER = f'{DATA_FOLDER}/ecpt'
    stage = 'running'
    arch = 'radix'
    # thp = 'never'
    
    benchs = [
        # 'graphbig_bfs_small',
        # 'gups_8G',
        

        "graphbig_bfs",
        # "graphbig_dfs",
        # "graphbig_dc",
        # "graphbig_sssp",
        # "graphbig_cc",
        # "graphbig_tc",
        # "graphbig_pagerank",
        # "sysbench",
        # "gups",
        # "redis",
        # "memcached",
        # "postgres",
    ]

    bench_infos = [(b, None, f'{RADIX_FOLDER}/{stage}/{arch}_{THP}_{b}_{stage}_walk_log.bin.dyna_asplos_smalltlb_config_realpwc.log') for b in benchs]
    
    # bench_infos = [(b,               None, f'{RADIX_FOLDER}/radix_never_{b}_dyna_asplos_smalltlb_config_realpwc_with_ifetch_2024-07-24_05-34-53.log') for b in benchs]
    # bench_infos += [('sysbench',     'CSL',      '/disk/bak1/collect_trace_fast/radix/radix_never_sysbench_dyna_asplos_smalltlb_config_realpwc_with_ifetch_2024-07-24_05-34-53.log')]
    # bench_infos += [('gups',         'CSL',      '/disk/bak1/collect_trace_fast/radix/radix_never_gups_dyna_asplos_smalltlb_config_realpwc_with_ifetch_2024-07-24_05-34-53.log')]
    # bench_infos += [('redis',        'CSL',      '/disk/bak1/siyuan/radix_never_jiyuan_redis_run_128G_dyna_asplos_smalltlb_config_realpwc_with_ifetch_2024-07-24_05-34-53.log')]
    # bench_infos += [('memcached',    'frontier', '/data1/memcached_nonetwork/radix_never_run_Memcached64Gpure_20insertion_never.bin.dyna_asplos_smalltlb_config_realpwc.log')]
    # bench_infos += [('postgres',     'CSL',      '/disk/bak1/siyuan/postgres64G_sequential_load/radix_never_run_postgres64G_sequential_load.bin.dyna_asplos_smalltlb_config_realpwc.log')]    
    
    radix_stats = process_from_list(bench_infos, arch, stage)
    arch = 'ecpt'
    
    bench_infos = [(b, None, f'{ECPT_FOLDER}/{stage}/{arch}_{THP}_{b}_{stage}_walk_log.bin.dyna_asplos_smalltlb_config_realpwc.log') for b in benchs]

    # bench_infos = [(b,               'frontier',  f'{ECPT_FOLDR}/ecpt_never_{b}_dyna_asplos_smalltlb_config_realpwc_correct_entry_only_with_ifetch.log') for b in benchs]
    # bench_infos += [('sysbench',     'CSL',      '/disk/bak1/collect_trace_fast/ecpt/ecpt_never_sysbench_walk_log_dyna_asplos_smalltlb_config_realpwc_correct_entry_only_short.log')]
    # bench_infos += [('gups',         'CSL',      '/disk/bak1/collect_trace_fast/ecpt/ecpt_never_gups_walk_log_dyna_asplos_smalltlb_config_realpwc_correct_entry_only_short.log')]
    # bench_infos += [('redis',        'CSL',      '/disk/bak1/siyuan/ecpt_never_jiyuan_redis_run_128G_dyna_asplos_smalltlb_config_realpwc_correct_entry_only.log')]
    # bench_infos += [('memcached',    'ajisai',   '/data1/memcached_nonetwork/ecpt_never_run_Memcached64Gpure_20insertion_never.bin.dyna_asplos_smalltlb_config_realpwc.log')]
    # bench_infos += [('postgres',     'CSL',      '/disk/bak1/siyuan/postgres64G_sequential_load/ecpt_never_run_postgres64G_sequential_load.bin.dyna_asplos_smalltlb_config_realpwc.log')]
    
    ecpt_stats = process_from_list(bench_infos, arch, stage)
    
    return calc_ipc_speedup(radix_stats, ecpt_stats, stage)


def calc_loading_end_ipc():
    print(LATENCY)
    
    RADIX_FOLDER = f'{DATA_FOLDER}/radix'
    ECPT_FOLDER = f'{DATA_FOLDER}/ecpt'
    stage = 'loading_end'
    arch = 'radix'
    # thp = 'never'
    
    benchs = [
        # 'graphbig_bfs_small',
        # 'gups_8G',

        "graphbig_bfs",
        # "graphbig_dfs",
        # "graphbig_dc",
        # "graphbig_sssp",
        # "graphbig_cc",
        # "graphbig_tc",
        # "graphbig_pagerank",
        # "sysbench",
        # "gups",
        # "redis",
        # "memcached",
        # "postgres",
    ]

    bench_infos = [(b, None, f'{RADIX_FOLDER}/{stage}/{arch}_{THP}_{b}_{stage}_walk_log.bin.dyna_asplos_smalltlb_config_realpwc.log') for b in benchs]
    
    # bench_infos = [(b,              'frontier', f'{RADIX_FOLDER}/radix_never_{b}_loading_end_phase_walk_log.bin.dyna_asplos_smalltlb_config_realpwc.log') for b in benchs]
    # bench_infos += [('redis',       'CSL',      f'/disk/bak1/alan_loading_phase_end/radix_never_run_jiyuan_redis_run_128G.bin.dyna_asplos_smalltlb_config_realpwc.log')]
    # bench_infos += [('memcached',   'frontier', f'{RADIX_FOLDER}/../memcached_nonetwork/radix_never_run_Memcached64Gpure_20insertion_never_loading_end.bin.dyna_asplos_smalltlb_config_realpwc.log')]
    # bench_infos += [('postgres',    'CSL' ,     f'/disk/bak1/alan_loading_phase_end/postgres64G_sequential_load/radix_never_run_postgres64G_sequential_load_loading_end.bin.dyna_asplos_smalltlb_config_realpwc.log')]
    
    radix_stats = process_from_list(bench_infos, arch, stage)
    
    
    arch = 'ecpt'

    bench_infos = [(b, None, f'{ECPT_FOLDER}/{stage}/{arch}_{THP}_{b}_{stage}_walk_log.bin.dyna_asplos_smalltlb_config_realpwc.log') for b in benchs]
    
    # bench_infos = [(b, 'frontier' ,f'{ECPT_FOLDR}/{arch}_never_{b}_loading_end_phase_walk_log.bin.dyna_asplos_smalltlb_config_realpwc.log') for b in benchs]
    # bench_infos += [('redis',       'CSL',      f'/disk/bak1/alan_loading_phase_end/ecpt_never_run_jiyuan_redis_run_128G_8KCWT.bin.dyna_asplos_smalltlb_config_realpwc.log')]
    # bench_infos += [('memcached',   'frontier', f'{RADIX_FOLDER}/../memcached_nonetwork/ecpt_never_run_Memcached64Gpure_20insertion_never_loading_end.bin.dyna_asplos_smalltlb_config_realpwc.log')]
    # bench_infos += [('postgres',    'CSL' ,     f'/disk/bak1/alan_loading_phase_end/postgres64G_sequential_load/ecpt_never_run_postgres64G_sequential_load_loading_end.bin.dyna_asplos_smalltlb_config_realpwc.log')]
    
    ecpt_stats = process_from_list(bench_infos, arch, stage)
    
    return calc_ipc_speedup(radix_stats, ecpt_stats, stage)

def get_inst_ratio():
    user_running_inst_ratio = {
        "graphbig_bfs_small": 0.006743131952,
        "gups_8G": 0.3733609305,
        
        "graphbig_bfs": 0.006743131952,
        "graphbig_cc": 0.005629112442,
        "graphbig_dc": 0.00435430115,
        "graphbig_dfs": 0.006995487261,
        "graphbig_pagerank": 0.01631641386,
        "graphbig_sssp": 0.01368925429,
        "graphbig_tc": 0.126816471,
        "sysbench": 0.9985808549,
        "gups": 0.3733609305,
        "redis": 0.08022670951,
        "memcached": 0.1508376434,
        "postgres": 0.791978094,
    }

    running_inst_ratio = pd.DataFrame(list(user_running_inst_ratio.items()), columns=["bench", "user_inst_ratio"])
    running_inst_ratio.set_index('bench', inplace=True)
    loading_inst_ratio = 1 - running_inst_ratio

    return running_inst_ratio, loading_inst_ratio

def get_unified_cycles(runnig_perf, loading_perf, selected_running_inst_ratio, selected_loading_inst_ratio, key, SIMULATED_INST):
    return (runnig_perf[key] / runnig_perf['user_inst'] * selected_running_inst_ratio['user_inst_ratio'] \
        + loading_perf[key] / loading_perf['user_inst'] * selected_loading_inst_ratio['user_inst_ratio']) * SIMULATED_INST

def get_unified(runnig_perf, loading_perf, running_inst_ratio, loading_inst_ratio, arch):
    SIMULATED_INST = 2e9
    selected_running_inst_ratio = running_inst_ratio.loc[runnig_perf.index]
    selected_loading_inst_ratio = loading_inst_ratio.loc[loading_perf.index]

    unified_pgwalk_cycles = get_unified_cycles(
        runnig_perf,
        loading_perf,
        selected_running_inst_ratio,
        selected_loading_inst_ratio,
        "page_walk_cycles",
        SIMULATED_INST,
    )

    unified_n_page_walk = get_unified_cycles(
        runnig_perf,
        loading_perf,
        selected_running_inst_ratio,
        selected_loading_inst_ratio,
        "n_page_walk",
        SIMULATED_INST,
    )

    unified_pgwalk = unified_pgwalk_cycles / unified_n_page_walk

    unified_total_cycles = get_unified_cycles(
        runnig_perf,
        loading_perf,
        selected_running_inst_ratio,
        selected_loading_inst_ratio,
        "total_cycles",
        SIMULATED_INST,
    )

    unified_inst_exec_cycles = get_unified_cycles(
        runnig_perf,
        loading_perf,
        selected_running_inst_ratio,
        selected_loading_inst_ratio,
        "inst_exec_cycles",
        SIMULATED_INST,
    )

    unified_data_cycles = get_unified_cycles(
        runnig_perf,
        loading_perf,
        selected_running_inst_ratio,
        selected_loading_inst_ratio,
        "data_cycles",
        SIMULATED_INST,
    )

    unified_kernel_inst = runnig_perf['kernel_inst'] / runnig_perf['user_inst'] * selected_running_inst_ratio['user_inst_ratio'] + \
        loading_perf['kernel_inst'] / loading_perf['user_inst'] * selected_loading_inst_ratio['user_inst_ratio']

    unified_kernel_inst = unified_kernel_inst * SIMULATED_INST
    unified_user_inst = SIMULATED_INST

    unified_toal_inst = unified_kernel_inst + unified_user_inst

    unified_ipc = unified_toal_inst / unified_total_cycles
    # print(runnig_perf.index)
    # print(loading_perf.index)
    unified_df = pd.DataFrame({
        'bench': runnig_perf.index,
        'ipc': unified_ipc,
        'page_walk_latency': unified_pgwalk,
        'total_cycles': unified_total_cycles,
        'kernel_inst': unified_kernel_inst,
        'user_inst': unified_user_inst,
        'total_inst': unified_toal_inst,

        'inst_exec_cycles': unified_inst_exec_cycles,
        'data_cycles': unified_data_cycles,
        'page_walk_cycles': unified_pgwalk_cycles,
    })

    with open(f'ipc_stats/ipc_unified_{THP}_{arch}_running_inst_ratio.csv', 'w') as f:
        # f.write(f'{arch}\n')
        # f.write('running inst ratio\n')
        selected_running_inst_ratio.to_csv(f)
        print('save to ', os.path.realpath(f'ipc_stats/ipc_unified_{THP}_{arch}_running_inst_ratio.csv'))

    with open(f'ipc_stats/ipc_unified_{THP}_{arch}_result.csv', 'w') as f:
        unified_df.to_csv(f)
        print('save to ', os.path.realpath(f'ipc_stats/ipc_unified_{THP}_{arch}_result.csv'))

    return unified_df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='/data/EMT')
    parser.add_argument('--output', default='./ipc_stats')
    parser.add_argument('--thp', default='never')
    args = parser.parse_args()

    if args.input:
        DATA_FOLDER = args.input
    if args.output:
        STAT_FOLDER = args.output
    if args.thp:
        THP = args.thp

    if not os.path.exists(STAT_FOLDER):
        os.makedirs(STAT_FOLDER, exist_ok=True)

    radix_running, ecpt_running = calc_running_ipc()
    radix_loading_end, ecpt_loading_end = calc_loading_end_ipc()
    
    running_inst_ratio, loading_inst_ratio = get_inst_ratio()
    print(running_inst_ratio)
    print(loading_inst_ratio)
    
    radix_unified = get_unified(radix_running, radix_loading_end, running_inst_ratio, loading_inst_ratio, 'radix')
    ecpt_unified = get_unified(ecpt_running, ecpt_loading_end, running_inst_ratio, loading_inst_ratio, 'ecpt')


    ipc_speedup = ecpt_unified['ipc']  / radix_unified['ipc']
    e2e_speedup = radix_unified['total_cycles'] / ecpt_unified['total_cycles'] 
    pgwalk_speedup = radix_unified['page_walk_latency'] / ecpt_unified['page_walk_latency']

    speedups = pd.concat([pgwalk_speedup, ipc_speedup, e2e_speedup], axis=1)
    speedups.columns = ['pgwalk_speedup', 'ipc_speedup', 'e2e_speedup']

    print(speedups)
    print('IPC speedup: ', speedups.mean())
