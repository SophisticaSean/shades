#!/bin/bash
tmux start-server
tmux new-session -d -s main
# tmux select-window -t 0
tmux send -t main 'bash' ENTER
tmux send -t main 'source ~/.bash_profile' ENTER
tmux send -t main 'cd ~/shades/' ENTER
tmux send -t main 're' ENTER
tmux send -t main 'git pull' ENTER
tmux send -t main 'python rtmdb.py' ENTER
