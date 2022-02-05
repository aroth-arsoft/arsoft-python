#!/bin/bash
SCRIPTFILE=`readlink -f "$0"`
SCRIPTNAME=`basename "$SCRIPTFILE"`
SCRIPTDIR=`dirname "$SCRIPTFILE"`

VENV_DIR="$SCRIPTDIR/venv"

function do_initialize_venv() {
    msg=`python -m venv "$VENV_DIR" 2>&1`
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        pip install -r "$SCRIPTDIR/requirements.txt"
        deactivate
    else
        echo "Unable to create virtual environment $VENV_DIR. Please run 'sudo apt install virtualenv'." >&2
        false
    fi
}

do_initialize_venv
