#!/bin/bash

# Easydict Alfred Workflow Builder

WORKFLOW_NAME="Easydict.alfredworkflow"

# Remove existing workflow file
rm -f "$WORKFLOW_NAME"

# Create the workflow file by zipping required files
# We exclude hidden files (starting with .) except .gitkeep if needed
zip -r "$WORKFLOW_NAME" \
    info.plist \
    icon.png \
    di.py \
    tr.py \
    play_audio.py \
    lib \
    icons \
    README.md \
    LICENSE

echo "Created $WORKFLOW_NAME"
