#!/bin/bash
# Auto-Correction Script Runner for Unix/Linux/Mac
# This script runs the automatic correction for low-scored responses

echo "========================================"
echo "CloudFuze Auto-Correction System"
echo "========================================"
echo ""
echo "This will automatically correct responses with score < 6"
echo ""
echo "Options:"
echo "  1. Run once (check now and exit)"
echo "  2. Process ALL low-scored traces (no limit)"
echo "  3. Run in polling mode (check every 5 minutes)"
echo "  4. Dry run (show what would be corrected)"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "Running once (limit: 10 traces)..."
        python scripts/auto_correct_low_scores.py
        ;;
    2)
        echo ""
        echo "Processing ALL low-scored traces..."
        python scripts/auto_correct_low_scores.py --all
        ;;
    3)
        echo ""
        echo "Running in polling mode (Ctrl+C to stop)..."
        python scripts/auto_correct_low_scores.py --poll --interval 300
        ;;
    4)
        echo ""
        echo "Running dry run..."
        python scripts/auto_correct_low_scores.py --dry-run
        ;;
    *)
        echo "Invalid choice!"
        exit 1
        ;;
esac

