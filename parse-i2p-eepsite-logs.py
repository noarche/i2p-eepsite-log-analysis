import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

def parse_log_line(line):
    """Parse a log line to extract the visiting router, date, request, and status code."""
    try:
        # Extract the visiting router
        router = line.split(' -  -  [')[0]
        
        # Extract the date
        date = line.split('[')[1].split(' +')[0]
        
        # Extract the request
        request = line.split('"')[1]
        
        # Extract the status code
        status_code = line.split('" ')[1].split(' -')[0]
        
        return {
            "router": router,
            "date": datetime.strptime(date, "%d/%b/%Y:%H:%M:%S"),
            "request": request,
            "status_code": status_code
        }
    except (IndexError, ValueError):
        # Return None if the line is not in the expected format
        return None

def parse_log_files(directory):
    """Parse all log files in the specified directory."""
    log_entries = []
    log_pattern = re.compile(r'.*\.log$', re.IGNORECASE)  # Pattern to match .log files

    for root, _, files in os.walk(directory):
        for file in files:
            if log_pattern.match(file):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as log_file:
                    for line in log_file:
                        parsed_line = parse_log_line(line.strip())
                        if parsed_line:
                            log_entries.append(parsed_line)

    return log_entries

def generate_statistics(log_entries):
    """Generate useful statistics from the parsed log entries."""
    # Count requests by router (ignoring '127.0.0.1')
    router_requests = Counter(entry['router'] for entry in log_entries if entry['router'] != '127.0.0.1')
    top_50_routers = router_requests.most_common(50)

    # Count requests for .html pages
    html_requests = [entry for entry in log_entries if ".html" in entry['request']]
    total_html_requests = len(html_requests)

    # Define a set of requests to ignore
    ignored_requests = {'GET /', 'GET /styles.css', 'GET /favicon.png', 'HEAD /'}
    
    # Count most requested pages (ignoring .png, .ico, .css requests and specified ignored requests)
    page_requests = Counter(
        entry['request'] for entry in log_entries 
        if not (entry['request'].endswith(('.png', '.ico', '.css')) or entry['request'] in ignored_requests)
    )
    top_50_pages = page_requests.most_common(50)

    # Calculate average requests per month for the last 56 months
    current_date = datetime.now()
    fifty_six_months_ago = current_date - timedelta(days=56 * 30)  # Approximation of 56 months
    monthly_requests = defaultdict(int)

    for entry in log_entries:
        if entry['date'] > fifty_six_months_ago:
            month = entry['date'].strftime("%Y-%m")
            monthly_requests[month] += 1

    # Average page loads per month for the last 56 months
    total_months = len(monthly_requests)
    average_page_loads_per_month = sum(monthly_requests.values()) / total_months if total_months > 0 else 0

    # Most popular hour of the day
    hours = [entry['date'].hour for entry in log_entries]
    popular_hour = Counter(hours).most_common(1)[0][0] if hours else None

    # Last update date and time
    last_update = current_date.strftime("%d/%b/%Y %H:%M:%S")

    return {
        "top_50_routers": top_50_routers,
        "total_html_requests": total_html_requests,
        "top_50_pages": top_50_pages,
        "average_page_loads_per_month": average_page_loads_per_month,
        "monthly_requests": sorted(monthly_requests.items()),
        "most_popular_time": popular_hour,
        "last_update": last_update
    }

def generate_html_report(statistics, output_file='report.html'):
    """Generate an HTML report with the given statistics."""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Log Analysis Report</title>
        <style>
            body {{
                background-color: #1e1e1e;
                color: #c7c7c7;
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
            }}
            h1 {{
                color: #f0f0f0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #3a3a3a;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #333;
                color: #fff;
            }}
            tr:nth-child(even) {{
                background-color: #2a2a2a;
            }}
        </style>
    </head>
    <body>
        <h1>Log Analysis Report</h1>
        <h2>Total .html Requests (Total Page Loads)</h2>
        <p>{statistics['total_html_requests']}</p>

        <h2>Average Page Loads Per Month (Last 56 Months)</h2>
        <p>{statistics['average_page_loads_per_month']:.2f}</p>

        <h2>Monthly Page Loads (Last 56 Months)</h2>
        <table>
            <thead>
                <tr>
                    <th>Month</th>
                    <th>Request Count</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f"<tr><td>{month}</td><td>{count}</td></tr>" for month, count in statistics['monthly_requests'])}
            </tbody>
        </table>

        <h2>Most Popular Time of Day</h2>
        <p>{statistics['most_popular_time']}:00</p>
        
        <h2>Top 50 Visiting Routers</h2>
        <table>
            <thead>
                <tr>
                    <th>Router</th>
                    <th>Request Count</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f"<tr><td>{router}</td><td>{count}</td></tr>" for router, count in statistics['top_50_routers'])}
            </tbody>
        </table>
        <h2>Top 50 Most Requested Pages</h2>
        <table>
            <thead>
                <tr>
                    <th>Page</th>
                    <th>Request Count</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f"<tr><td>{page}</td><td>{count}</td></tr>" for page, count in statistics['top_50_pages'])}
            </tbody>
        </table>

        <p style="text-align: right; font-size: small;">Last Updated: {statistics['last_update']}</p>
    </body>
    </html>
    """

    with open(output_file, 'w') as file:
        file.write(html_content)

    print(f"HTML report generated: {output_file}")

def main():
    print("Log File Parser and HTML Report Generator")
    print("==========================================")
    print("This script parses all .log files in a specified directory and generates an HTML report with detailed statistics.\n")
    
    # Prompt user for directory
    directory = input("Enter the directory containing log files (leave blank for current directory): ").strip() or '.'
    
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        return
    
    # Parse log files
    print(f"Parsing log files in '{directory}'...")
    log_entries = parse_log_files(directory)
    
    if log_entries:
        # Generate statistics
        statistics = generate_statistics(log_entries)
        
        # Generate HTML report
        generate_html_report(statistics)
    else:
        print("No valid log data found in the specified directory.")

if __name__ == "__main__":
    main()
