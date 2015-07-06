#!/bin/bash
tmux start-server
tmux new-session -d -s main
# tmux select-window -t 0
tmux send -t main 'bash' ENTER
tmux send -t main 'source ~/.bash_profile' ENTER
tmux send -t main 'cd ~/scripts-2.0/' ENTER
tmux send -t main 're' ENTER
tmux send -t main 'git pull' ENTER
tmux send -t main 'python shades/rtmdb.py' ENTER
