# First fix aliases not passed to sudo
alias sudo='/usr/bin/sudo '
alias nobody='sudo -u nobody'

alias s='/usr/bin/sudo '
alias vi="vim"
alias v="vim"
alias nv="nvim"

# CD
alias cd..='cd ..'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
alias ......='cd ../../../../..'
alias ~='cd ~'
alias bk='cd $OLDPWD'
alias -- -='cd -'

# MV
alias mv='mv -v'

# LN
alias ln='ln -v'

# RM
alias rm='rm -rv --preserve-root'
alias rmf='rm -rvf --preserve-root'

# CP
alias cp='cp -rv'
alias cpp='rsync -PrlpE'
alias cpz='rsync -PrlpEz'

# LS/DIR/VDIR
alias l='ls -Xp --color=auto'
alias ls='ls -Xp -GFh --color=auto'
alias la='ls -A'
alias ll='ls -al -GFh --color=auto'
alias lh='ls -d .*'
alias dir='dir -h --color=auto'
alias vdir='vdir -h --color=auto'

# GREP
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

# MKDIR
alias mk='mkdir -pv'
alias mkdir='mkdir -pv'

alias info="info --vi-keys"
alias diff="colordiff"

# Various
alias cls='clear'
alias h='history'
alias -- +x='chmod +x'
alias wget='wget -c'
alias curl='curl -C -'

alias hgrep="fc -El 0 | grep"
alias help='man'
alias p='ps -f'
alias sortnr='sort -n -r'
alias unexport='unset'

# Ping
alias pr='ping -c 1 192.168.1.1 | tail -3'
alias pg='ping -c 1 google.com | tail -3'

# Git ( more at ~/.gitconfig )
alias g='git'

# Systemctl
alias suspend='sudo systemctl suspend'
alias hibernate='sudo systemctl hibernate'
alias hybrid-sleep='sudo systemctl hybrid-sleep'
alias -- s+='sudo systemctl start'
alias -- s-='sudo systemctl stop'
alias sr='sudo systemctl restart'
alias se='sudo systemctl enable'
alias sd='sudo systemctl disable'
alias s!='systemctl status -l'
alias -- u+='systemctl --user start'
alias -- u-='systemctl --user stop'
alias ur='systemctl --user restart'
alias u!='systemctl --user status -l'

# Journalctl
alias jx="sudo journalctl -xea"
alias ju="sudo journalctl -xea -u"

# Parenting changing perms on / #
alias chown='chown --preserve-root'
alias chmod='chmod --preserve-root'
alias chgrp='chgrp --preserve-root'

# Fun with sed
alias df='df -h |\
	sed -e "s_/dev/sda[1-9]_\x1b[34m&\x1b[0m_" |\
	sed -e "s_/dev/sd[b-z][1-9]_\x1b[33m&\x1b[0m_" |\
	sed -e "s_[.,0-9]*[MG]_\x1b[36m&\x1b[0m_" |\
	sed -e "s_[0-9]*%_\x1b[32m&\x1b[0m_" |\
	sed -e "s_9[0-9]%_\x1b[31m&\x1b[0m_" |\
	sed -e "s_/mnt/[-_A-Za-z0-9]*_\x1b[34;1m&\x1b[0m_"'

# -------------------------------------------------------------------
# Source: http://aur.archlinux.org/packages/lolbash/lolbash/lolbash.sh
# -------------------------------------------------------------------
alias wtf='dmesg'
alias rtfm='man'
alias visible='echo'
alias invisible='cat'
alias moar='more'
alias icanhas='mkdir'
alias donotwant='rm'
alias dowant='cp'
alias gtfo='mv'
alias hai='cd'
alias plz='pwd'
alias inur='locate'
alias nomz='ps aux | less'
alias nomnom='killall'
alias cya='reboot'
alias kthxbai='halt'
