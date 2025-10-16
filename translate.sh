#!/bin/bash
# Translation Workflow Wrapper
# Makes common commands easier to run
#
# Author: Austin Morrissey
# Co-Authored-By: Claude <noreply@anthropic.com>

PROJECT_DIR="$HOME/pdf-translator"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Parse command
case "$1" in
    status|s)
        python3 translate_helper.py --status
        ;;
    next|n)
        python3 translate_helper.py --next
        ;;
    chunk|c)
        if [ -z "$2" ]; then
            echo "Usage: ./translate.sh chunk <number>"
            exit 1
        fi
        python3 translate_helper.py --chunk "$2"
        ;;
    assemble|a)
        python3 assemble_output.py
        ;;
    help|h|*)
        echo "PDF Translation Workflow Helper"
        echo ""
        echo "Usage: ./translate.sh <command>"
        echo ""
        echo "Commands:"
        echo "  status, s           Show translation progress"
        echo "  next, n             Show next untranslated chunk"
        echo "  chunk <n>, c <n>    Show specific chunk number"
        echo "  assemble, a         Assemble final output"
        echo "  help, h             Show this help message"
        echo ""
        echo "Example workflow:"
        echo "  ./translate.sh next          # Show next chunk"
        echo "  [Tell Claude to translate it]"
        echo "  ./translate.sh status        # Check progress"
        echo "  ./translate.sh assemble      # Create final output"
        ;;
esac
