#!/usr/bin/env bash

output_dir="/data/EMT"

while [[ $# -gt 0 ]]; do
	key="$1"

	case $key in
	--dry)
		dry_run="true"
        shift 1
		;;
    --output)
        if [[ -z "$2" ]]; then
            echo "Error: --output requires a non-empty argument."
            exit 1
        fi
        output_dir="$2"
        shift 2
        ;;
	*)
        echo "Unknown option: $key"
        exit 1
        ;;
	esac
done

image_path=$(realpath image_record_loading.ext4)

benchmarks=(
    # "graphbig_bfs_small"  # for testing
    # "gups_8G"

    "graphbig_bfs" 
    # "graphbig_dfs" 
    # "graphbig_dc" 
    # "graphbig_sssp"
    "gups"
    "redis"
)

commands=(
    # "cd rethinkVM_bench; ./run_scripts/simulation/graphbig_bfs_small.sh <stage>; /shutdown;"
    # "cd rethinkVM_bench; ./run_scripts/simulation/gups_8G.sh <stage>; /shutdown;"

    "cd rethinkVM_bench; ./run_scripts/simulation/graphbig_bfs.sh <stage>; /shutdown;"
    # "cd rethinkVM_bench; ./run_scripts/simulation/graphbig_dfs.sh <stage>; /shutdown;"
    # "cd rethinkVM_bench; ./run_scripts/simulation/graphbig_dc.sh <stage>; /shutdown;"
    # "cd rethinkVM_bench; ./run_scripts/simulation/graphbig_sssp.sh <stage>; /shutdown;"
    "cd rethinkVM_bench; ./run_scripts/simulation/gups.sh <stage>; /shutdown;"
    "cd rethinkVM_bench/workloads; ./bin/bench_redis_st -- --recording-stage <stage>; /shutdown;"
)

recording_stage=(
    1
    3
)

recording_stage_str=(
    "running"
    "loading_end"
)

recording_stage_str_redis=(
    ""
    "-- --loading-phase"
)

thp_config=(
    "never"
    "always"
)

archs=(
    "radix"
    "ecpt"
)

for arch in "${archs[@]}"; do
    cd emt-linux-$arch
    for b_i in "${!benchmarks[@]}"; do
        benchmark=${benchmarks[$b_i]}
        for thp in "${thp_config[@]}"; do
            for s_i in "${!recording_stage[@]}"; do
                stage=${recording_stage[$s_i]}
                stage_str=${recording_stage_str[$s_i]}
                # if [[ $benchmark == "redis" ]]; then
                #     command=${commands[$b_i]/<stage>/${recording_stage_str_redis[$s_i]}}
                # else
                    command=${commands[$b_i]/<stage>/${recording_stage[$s_i]}}
                # fi
                arch_stage_dir="${output_dir}/${arch}/${stage_str}"
                file_prefix="${arch}_${thp}_${benchmark}_${stage_str}"
                sudo mkdir -p $arch_stage_dir
                sudo chmod 777 $arch_stage_dir
                
                echo "./run_linux_free_cmd --arch $arch --thp $thp --cmd \"$command\" --out ${arch_stage_dir}/${file_prefix}_walk_log.bin --image ${image_path} --run-dynamorio"
                if [[ $dry_run != true ]]; then
                    ./run_linux_free_cmd --arch $arch --thp $thp --cmd "$command" --out ${arch_stage_dir}/${file_prefix}_walk_log.bin --image ${image_path} --run-dynamorio
                fi
                results+=($(realpath ${arch_stage_dir}/${file_prefix}_walk_log.bin.dyna_asplos_smalltlb_config_realpwc.log))
            done
        done
    done
    cd ..
done

echo "Done! List of analysis results:"
for result in "${results[@]}"; do
    echo -e "\033[1;35m\t${result}"
done
