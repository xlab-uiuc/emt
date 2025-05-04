#!/usr/bin/env bash

while [[ $# -gt 0 ]]; do
	key="$1"

	case $key in
	--dry)
		dry_run="true"
        shift 1
		;;
	*)
        echo "Unknown option: $key"
        exit 1
        ;;
	esac
done

image_path=$(realpath image_record_loading.ext4)

benchmarks=(
    "graphbig_bfs_small"
    # "gups_8G"

    # "graphbig_bfs" 
    # "graphbig_dfs" 
    # "graphbig_dc" 
    # "graphbig_sssp"
    # "gups"
    # "redis"
)

commands=(
    "cd rethinkVM_bench; ./run_scripts/simulation/graphbig_bfs_small.sh <stage>; /shutdown;"
    "cd rethinkVM_bench; ./run_scripts/simulation/gups_8G.sh <stage>; /shutdown;"

    # "cd rethinkVM_bench; ./run_scripts/simulation/graphbig_bfs.sh <stage>; /shutdown;"
    # "cd rethinkVM_bench; ./run_scripts/simulation/graphbig_dfs.sh <stage>; /shutdown;"
    # "cd rethinkVM_bench; ./run_scripts/simulation/graphbig_dc.sh <stage>; /shutdown;"
    # "cd rethinkVM_bench; ./run_scripts/simulation/graphbig_sssp.sh <stage>; /shutdown;"
    # "cd rethinkVM_bench; ./run_scripts/simulation/gups.sh <stage>; /shutdown;"
    # TODO: run redis
)

recording_stage=(
    1
    3
)

recording_stage_str=(
    "running"
    "loading_end"
)

thp_config=(
    "never"
    "always"
)

arch=(
    "radix"
    "ecpt"
)

for arch in "${arch[@]}"; do
    cd emt-linux-$arch
    for b_i in "${!benchmarks[@]}"; do
        benchmark=${benchmarks[$b_i]}
        for thp in "${thp_config[@]}"; do
            for s_i in "${!recording_stage[@]}"; do
                stage=${recording_stage[$s_i]}
                stage_str=${recording_stage_str[$s_i]}
                command=${commands[$b_i]//<stage>/$stage}
                output_dir="/data/EMT/${arch}/${stage_str}"
                file_prefix="${arch}_${thp}_${benchmark}_${stage_str}"
                sudo mkdir -p $output_dir
                sudo chmod 777 $output_dir
                
                echo "./run_linux_free_cmd --arch $arch --thp $thp --cmd \"$command\" --out ${output_dir}/${file_prefix}_walk_log.bin --image ${image_path} --run-dynamorio"
                if [[ $dry_run != true ]]; then
                    ./run_linux_free_cmd --arch $arch --thp $thp --cmd "$command" --out ${output_dir}/${file_prefix}_walk_log.bin --image ${image_path} --run-dynamorio
                fi
            done
        done
        if [[ $dry_run != true ]]; then
            wait
            sleep 5
        fi
    done
    cd ..
done
