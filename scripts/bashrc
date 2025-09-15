# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
        . /etc/bashrc
fi


# User specific aliases and functions
alias cdo='cd /project/ckenkel_26/migomez'
alias cdw='cd /project2/ckenkel_26/migomez'
alias cdh='cd /home1/migomez'
alias cds='cd /scratch1/migomez'
alias cdm='cd /project/ckenkel_26/software/metashape-pro'


# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/spack/conda/miniconda3/4.12.0/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/spack/conda/miniconda3/4.12.0/etc/profile.d/conda.sh" ]; then
        . "/spack/conda/miniconda3/4.12.0/etc/profile.d/conda.sh"
    else
        export PATH="/spack/conda/miniconda3/4.12.0/bin:$PATH"
    fi
fi
unset __conda_setup

if [ -f "/spack/conda/miniconda3/4.12.0/etc/profile.d/mamba.sh" ]; then
    . "/spack/conda/miniconda3/4.12.0/etc/profile.d/mamba.sh"
fi
# <<< conda initialize <<<



setup_env_183()
{
        export METASHAPE_ROOT=/project2/ckenkel_26/NEWFILES/metashape-pro_1_8_3

        module purge
        module load legacy/CentOS7 gcc/8.3.0
        module unload usc
        module load ncurses/5.9 nettle/3.4.1 mesa-glu/9.0.0 mesa/18.3.6 gnutls/3.6.14
        module load nano

        export QT_QPA_PLATFORM=offscreen
        export XDG_RUNTIME_DIR=/tmp/migomez

        export AGISOFT_REHOST_PATH=${METASHAPE_ROOT}/MetaNOTOUCH
        export PATH=${METASHAPE_ROOT}:$PATH
}

setup_env_221()
{
        export METASHAPE_ROOT=/project2/ckenkel_26/NEWFILES/metashape-pro_2_2_1

        module purge
        module load legacy/CentOS7 gcc/8.3.0
        module unload usc
        module load ncurses/5.9 nettle/3.4.1 mesa-glu/9.0.0 mesa/18.3.6 gnutls/3.6.14
        module load nano

        export QT_QPA_PLATFORM=offscreen
        export XDG_RUNTIME_DIR=/tmp/migomez

        export AGISOFT_LICENSING_DIR=${METASHAPE_ROOT}/MetaNOTOUCH
        export PATH=${METASHAPE_ROOT}:$PATH
}

deactivate_metashape()
{
        metashape.sh --deactivate
}

activate_metashape()
{
        metashape.sh --activate XXXXX-XXXXX-XXXXX-XXXXX-XXXXX      # your license code here
}

reactivate_metashape()
{
        metashape.sh --deactivate
        metashape.sh --activate XXXXX-XXXXX-XXXXX-XXXXX-XXXXX      # your license code here
}

# These aren't compatible with legacy stack, so hiding for now (these are before the 2025 CARC update)
# export AGISOFT_REHOST_PATH=/project/ckenkel_26/software/metashape-pro/MetaNOTOUCH
# export PATH=/project/ckenkel_26/software/metashape-pro:$PATH
# export PATH=/project/ckenkel_26/software/bbmap:$PATH
# module load gcc/13.3.0
# module load nano/8.0

