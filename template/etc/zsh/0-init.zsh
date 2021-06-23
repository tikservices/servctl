if [ -d "/usr/share/zsh/oh-my-zsh/" ]; then
	export ZSH=/usr/share/zsh/oh-my-zsh
	#ZSH_THEME=sunrise
	plugins=(command-not-found cp extract github pip django tmux vi-mode vundle branch lol man)
	DISABLE_UPDATE_PROMPT=true
	DISABLE_AUTO_UPDATE=true
	[ -e "$ZSH/oh-my-zsh.sh" ] && source $ZSH/oh-my-zsh.sh
fi

autoload -U colors && colors
autoload -U vcs_info && vcs_info
autoload -U edit-command-line && zle -N edit-command-line \
	&& bindkey -M vicmd v edit-command-line

zmodload zsh/complist
zmodload zsh/terminfo

bindkey -v

if [ -e "/usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]; then
	source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
fi

# for r in /etc/zsh/*.zsh; do
# 	[ -x "$r" ] && source $r
# done

true
