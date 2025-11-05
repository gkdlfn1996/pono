#!/bin/bash
set -e

start_or_restart_in_screen() {
    local name="$1"
    local dir="$2"
    local setup_and_run_cmd="$3"

    echo "Screen 세션 관리: $name"

    if screen -list | grep -q "$name"; then
        echo "Screen 세션 '$name' 존재 → 재시작"
        screen -S "$name" -X stuff "^C^M"
        sleep 2
        screen -S "$name" -X stuff "cd $dir && $setup_and_run_cmd; exec bash^M"
        echo "연결: screen -r $name"
    else
        echo "Screen 세션 '$name' 없음 → 생성/시작"
        screen -dmS "$name" bash -c "cd $dir && $setup_and_run_cmd; exec bash"
        echo "연결: screen -r $name"
    fi
}
