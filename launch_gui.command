#!/bin/bash
# macOS launcher — delegates to the cross-platform script
cd "$(dirname "$0")"
exec bash ./launch_gui.sh
