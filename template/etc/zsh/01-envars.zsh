# sourced by interactive shell after sourcing 00-environment.zsh file
export CLICOLOR=1
export HISTSIZE=1000
export SAVEHIST=1000
export HISTFILE=~/.zsh_history
export HISTFILESIZE=1000
export LESS='-F -g -i -M -R -S -w -X -z-4'
export LESS_TERMCAP_mb=$(printf "\e[1;31m")
export LESS_TERMCAP_md=$(printf "\e[0;93m")
export LESS_TERMCAP_me=$(printf "\e[0m")
export LESS_TERMCAP_se=$(printf "\e[0m")
export LESS_TERMCAP_so=$(printf "\e[1;104;30m")
export LESS_TERMCAP_ue=$(printf "\e[0m")
export LESS_TERMCAP_us=$(printf "\e[1;32m")
export LESSCHARSET="UTF-8"
export PAGER="less"
export MANPAGER="$PAGER"
export SDCV_PAGER="$PAGER"
export _NROFF_U=1

# export VIMINIT='let $MYVIMRC="$XDG_CONFIG_HOME/vim/vimrc" | source $MYVIMRC'

export SHELL='/bin/zsh'

[ -n "$TMUX" ] && export TERM="screen-256color"
