#!/usr/bin/env bash
set -e

input_dir="/data/EMT"
dry_run=false

ipc_stat_py=$(realpath ipc_with_inst.py)
ipc_stat_folder=$(realpath ./ipc_stats)
inst_stat_py=$(realpath ./VM-Bench/run_scripts/get_unified_kern_inst_ae.py)
inst_stat_folder=$(realpath ./inst_stats)
ipc_analyze_py=$(realpath ecpt_unified.py)
inst_analyze_py=$(realpath kern-inst-breakdown-with-khuge-unified.py)
graph_folder=$(realpath ./graph)

thp=never

while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
    --dry)
        dry_run="true"
        shift 1
        ;;
    --thp)
        if [[ -z "$2" ]]; then
            echo "Error: --thp requires a non-empty argument."
            exit 1
        fi
        thp="$2"
        shift 2
        ;;
    --input)
        if [[ -z "$2" ]]; then
            echo "Error: --input requires a non-empty argument."
            exit 1
        fi
        input_dir="$2"
        shift 2
        ;;
    --ipc_stats)
        if [[ -z "$2" ]]; then
            echo "Error: --ipc_stats requires a non-empty argument."
            exit 1
        fi
        ipc_stat_folder="$2"
        shift 2
        ;;
    --inst_stats)
        if [[ -z "$2" ]]; then
            echo "Error: --inst_stats requires a non-empty argument."
            exit 1
        fi
        inst_stat_folder="$2"
        shift 2
        ;;
    --graph)
        if [[ -z "$2" ]]; then
            echo "Error: --graph requires a non-empty argument."
            exit 1
        fi
        graph_folder="$2"
        shift 2
        ;;
    *)
        echo "Unknown option: $key"
        exit 1
        ;;
    esac
done

if [[ $dry_run != true ]]; then

    if [[ "$thp" == "never" || "$thp" == "all" ]]; then
        python $ipc_stat_py --input $input_dir --output $ipc_stat_folder --thp never
        
        cd VM-Bench
        python $inst_stat_py --input $input_dir --output $inst_stat_folder --thp never
        cd ..

        python $ipc_analyze_py --input $ipc_stat_folder --output $graph_folder --thp never
        python $inst_analyze_py --input $inst_stat_folder --output $graph_folder --thp never
    fi

    if [[ "$thp" == "always" || "$thp" == "all" ]]; then
        python $ipc_stat_py --input $input_dir --output $ipc_stat_folder --thp always
        
        cd VM-Bench
        python $inst_stat_py --input $input_dir --output $inst_stat_folder --thp always
        cd ..

        python $ipc_analyze_py --input $ipc_stat_folder --output $graph_folder --thp always
        python $inst_analyze_py --input $inst_stat_folder --output $graph_folder --thp always
    fi
else
    echo "Input directory: $input_dir"
    echo "IPC stats folder: $ipc_stat_folder"
    echo "Inst stats folder: $inst_stat_folder"
    echo "Graph folder: $graph_folder"
    echo "THP setting: $thp"
    
    # output all commands:
    if [[ "$thp" == "never" || "$thp" == "all" ]]; then
        echo "python $ipc_stat_py --input $input_dir --output $ipc_stat_folder --thp never"
        echo "cd VM-Bench"
        echo "python $inst_stat_py --input $input_dir --output $inst_stat_folder --thp never"
        echo "cd .."
        echo "python $ipc_analyze_py --input $ipc_stat_folder --output $graph_folder --thp never"
        echo "python $inst_analyze_py --input $inst_stat_folder --output $graph_folder --thp never"
    fi
    if [[ "$thp" == "always" || "$thp" == "all" ]]; then
        echo "python $ipc_stat_py --input $input_dir --output $ipc_stat_folder --thp always"
        echo "cd VM-Bench"
        echo "python $inst_stat_py --input $input_dir --output $inst_stat_folder --thp always"
        echo "cd .."
        echo "python $ipc_analyze_py --input $ipc_stat_folder --output $graph_folder --thp always"
        echo "python $inst_analyze_py --input $inst_stat_folder --output $graph_folder --thp always"
    fi
fi