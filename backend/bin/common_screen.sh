#!/bin/bash
set -e

start_or_restart_in_screen() {
    local name="$1"
    local dir="$2"
    local setup_and_run_cmd="$3"

    echo "Screen 세션 관리: $name"

    if screen -list | grep -q "$name"; then
        echo "Screen 세션 '$name' 존재 → 종료 후 재시작"
        # 세션을 완전히 종료합니다.
        screen -S "$name" -X quit
        # 세션이 완전히 종료될 때까지 잠시 기다립니다.
        while screen -list | grep -q "$name"; do
            sleep 1
        done
        echo "이전 세션 '$name' 종료 완료."
    fi

    echo "Screen 세션 '$name' 생성/시작"
    screen -dmS "$name" bash -c "cd \"$dir\" && $setup_and_run_cmd; exec bash"
    echo "연결: screen -r $name"
}
