#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export TK_SILENCE_DEPRECATION=1
python melaninclick.py 