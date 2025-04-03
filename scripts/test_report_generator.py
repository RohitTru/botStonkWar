#!/usr/bin/env python3

import os
import glob
from datetime import datetime

def generate_report(report_dir):
    """Generate a markdown report of test results."""
    report_file = os.path.join(report_dir, "test-report.md")
    
    with open(report_file, "w") as f:
        f.write("# Test Results\n\n")
        f.write("## Summary\n\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Add environment info
        f.write("### Environment\n")
        f.write(f"- Environment: {os.environ.get('TARGET_ENV', 'unknown')}\n")
        f.write(f"- Branch: {os.environ.get('BRANCH_NAME', 'unknown')}\n")
        f.write(f"- Version: {os.environ.get('VERSION', 'unknown')}\n\n")
        
        # Check for coverage reports
        coverage_files = glob.glob(os.path.join(report_dir, "coverage*.xml"))
        if coverage_files:
            f.write("### Test Coverage\n")
            for cov_file in coverage_files:
                test_type = os.path.basename(cov_file).replace("coverage-", "").replace(".xml", "")
                f.write(f"- {test_type.capitalize()} Tests: Coverage report generated\n")
        
        f.write("\n### Test Execution\n")
        f.write("| Test Type | Status |\n")
        f.write("|-----------|--------|\n")
        
        # Check for test execution
        test_types = ["mandatory", "recommended", "optional"]
        for test_type in test_types:
            status = "✅ Completed" if os.path.exists(os.path.join(report_dir, f"coverage-{test_type}.xml")) else "⚪ Not Required"
            f.write(f"| {test_type.capitalize()} | {status} |\n")

if __name__ == "__main__":
    if "TEST_REPORTS_DIR" not in os.environ:
        print("Error: TEST_REPORTS_DIR environment variable not set")
        exit(1)
        
    report_dir = os.environ["TEST_REPORTS_DIR"]
    if not os.path.exists(report_dir):
        print(f"Error: Test reports directory not found: {report_dir}")
        exit(1)
        
    generate_report(report_dir)
    print(f"Test report generated at {os.path.join(report_dir, 'test-report.md')}") 