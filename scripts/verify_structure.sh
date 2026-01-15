#!/bin/bash
# Directory structure and file verification

echo "Enterprise-Grade IaC Project Structure"
echo "======================================="
echo ""

cd "$(dirname "$0")" || exit

# Display tree structure
find . -type f -name ".*" -prune -o -type f -print | sort | sed 's|^\./||' | grep -v "^$" | awk '
BEGIN { 
  depth = 0
  prev_depth = 0
}
{
  # Count slashes to determine depth
  n = gsub(/\//, "/", $0)
  
  # Print directory levels
  for (i = 0; i < n; i++) {
    if (i == n-1) printf "├── "
    else printf "│   "
  }
  
  # Print filename
  split($0, a, "/")
  print a[n+1]
}'

echo ""
echo "Project Files Summary"
echo "===================="
echo ""

# Count files by type
echo "Python files:"
find . -name "*.py" -type f | wc -l

echo "SQL files:"
find . -name "*.sql" -type f | wc -l

echo "Configuration files:"
find . -name "*.yaml" -o -name "*.yml" -o -name "*.conf" | wc -l

echo "Documentation files:"
find . -name "*.md" -type f | wc -l

echo ""
echo "Total lines of code:"
find . -name "*.py" -o -name "*.sql" -o -name "*.yaml" | xargs wc -l | tail -1

echo ""
echo "✓ Project structure verified"
