# Checkmaa System CLI Tool

A cross-platform command-line tool for searching various data types using the Checkmaa System API with **automatic query type detection**.

## Key Features

- **Automatic Detection**: Automatically detects emails, domains, phone numbers, usernames, and URLs
- **Smart Phone Cleaning**: Automatically strips all non-digits from phone numbers (removes +, spaces, dashes, dots, parentheses)
- **Bulk Searches**: Run multiple relevant searches with a single command
- **Rate Limit Protection**: Built-in delays between API calls
- **Cross-Platform**: Works on Linux, Windows, and macOS
- **Multiple Output Formats**: Pretty, JSON, raw, or summary output
- **Smart Query Analysis**: Detects query type with confidence levels

## Installation

### Prerequisites
- Python 3.6 or higher (comes pre-installed on most Linux/macOS systems)
- Your Checkmaa API key
- (Optional but recommended) `requests` library: `pip install requests`

### Quick Install

#### Linux/macOS:
```bash
# Download the script
curl -o checkmaa https://raw.githubusercontent.com/OsintSystems/checkmaa/main/checkmaa.py
# OR wget -O checkmaa https://raw.githubusercontent.com/OsintSystems/checkmaa/main/checkmaa.py

# Make it executable
chmod +x checkmaa

# (Optional) Move to PATH for system-wide access
sudo mv checkmaa /usr/local/bin/

# Set your API key (add to ~/.bashrc or ~/.zshrc for persistence)
export CHECKMAA_API_KEY='your_api_key_here'

# (Recommended) Install requests for better reliability
pip3 install requests
```

#### Windows:
```powershell
# Download the script (PowerShell)
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/OsintSystems/checkmaa/main/checkmaa.py" -OutFile "checkmaa.py"

# Set your API key (temporary)
$env:CHECKMAA_API_KEY = "your_api_key_here"

# For permanent API key (User environment variable)
[System.Environment]::SetEnvironmentVariable("CHECKMAA_API_KEY", "your_api_key_here", "User")

# (Recommended) Install requests for better reliability
pip install requests
```

## Usage

### Automatic Mode (Recommended)
The tool automatically detects the query type and runs all relevant searches:

```bash
# Auto-detect email and run email, ulp-email, and whois-email searches
checkmaa -q test@gmail.com --auto

# Auto-detect domain and run domain, whois-domain, and password searches
checkmaa -q facebook.com --auto

# Auto-detect phone number
checkmaa -q +1234567890 --auto

# Auto-detect with custom delay (default is 5 seconds)
checkmaa -q admin@example.com --auto --delay 3

# Get summary only
checkmaa -q example.com --auto -f summary
```

### Manual Mode
Specify exact search type when you know what you want:

```bash
# Search by specific type
checkmaa -q test@gmail.com -t email
checkmaa -q john123 -t username
checkmaa -q facebook.com -t domain
checkmaa -q "555-123-4567" -t phone  # Automatically cleaned to 5551234567
```

### Auto-Detection Examples

#### Email Detection:
```bash
$ checkmaa -q admin@example.com --auto

Analyzing query: 'admin@example.com'
==================================================

Detected as email ✓✓✓
Will perform 3 search(es): email, ulp-email, whois-email

==================================================

[1/3] Searching email... ✓ Success
[2/3] Searching ulp-email... ✓ Success
[3/3] Searching whois-email... ✓ Success

==================================================
SEARCH SUMMARY
==================================================
Total searches: 3
Successful: 3
Failed: 0
```

#### Phone Detection (with automatic cleaning):
```bash
$ checkmaa -q "+1 (555) 123-4567" --auto

Analyzing query: '+1 (555) 123-4567'
==================================================

Detected as phone ✓✓✓
Phone number will be searched as: 15551234567
Will perform 1 search(es): phone

==================================================
[Results follow...]
```

#### Domain Detection:
```bash
$ checkmaa -q google.com --auto

Analyzing query: 'google.com'
==================================================

Detected as domain ✓✓✓
Will perform 3 search(es): domain, whois-domain, password

==================================================
[Results follow...]
```

### Available Search Types
- `email` - Search by exact email address
- `email-prefix` - Search by email prefix (e.g., "test@")
- `username` - Search by username
- `domain` - Search by domain name
- `password` - Search by password
- `phone` - Search by phone number
- `ulp-email` - Search ULP by email
- `ulp-url` - Search ULP by URL
- `whois-email` - Search WHOIS by email
- `whois-domain` - Search WHOIS by domain

### Query Type Detection Rules

| Query Type | Pattern | Auto Searches | Notes |
|------------|---------|---------------|-------|
| Email | `user@domain.com` | email, ulp-email, whois-email | |
| Email Prefix | `user@` | email-prefix | |
| Domain | `example.com` | domain, whois-domain, password | |
| Phone | Any phone format | phone | Auto-strips all non-digits |
| URL | `https://example.com/path` | ulp-url | |
| Username | `john123` | username | |

### Output Formats
```bash
# Pretty formatted output (default)
checkmaa -q test@gmail.com --auto

# JSON output
checkmaa -q test@gmail.com --auto -f json

# Raw JSON (single line)
checkmaa -q test@gmail.com --auto -f raw

# Summary only (shows counts)
checkmaa -q test@gmail.com --auto -f summary
```

### Advanced Options
```bash
# Use a different API key
checkmaa -k 'your_api_key' -q test@gmail.com --auto

# Verbose mode
checkmaa -v -q test@gmail.com --auto

# Help
checkmaa -h
```

## Real-World Examples

### Investigate an Email Address:
```bash
# Automatically searches email, ulp-email, and whois-email
checkmaa -q suspicious@example.com --auto
```

### Check Domain Information:
```bash
# Automatically searches domain, whois-domain, and password databases
checkmaa -q hackerdomain.com --auto
```

### Quick Phone Lookup:
```bash
# Detects phone format and automatically cleans it
checkmaa -q "(555) 123-4567" --auto
# Searches as: 5551234567
```

### Batch Processing:
```bash
#!/bin/bash
# Process multiple queries with auto-detection
queries=("admin@company.com" "example.org" "+1 (555) 123-4567" "john_doe")

for query in "${queries[@]}"; do
    echo "Processing: $query"
    checkmaa -q "$query" --auto -f summary
    echo "---"
    sleep 10  # Extra delay between different queries
done
```

### Export Results:
```bash
# Save all results to a file
checkmaa -q target@example.com --auto -f json > results.json

# Process with jq
checkmaa -q example.com --auto -f json | jqvir .domain.results[]
```

## API Rate Limits

The tool includes built-in delays to respect API rate limits:
- Default: 5 seconds between searches in auto mode
- Customizable with `--delay` parameter
- Minimum recommended: 5 seconds

## Troubleshooting

### API Error 403 / Error code 1010
This is typically a Cloudflare protection issue. Try these solutions:

1. **Install requests library** (recommended):
   ```bash
   pip install requests
   # or
   pip3 install requests
   ```
   The tool will automatically use requests if available, which handles HTTP requests more reliably.

2. **Verify your API key**:
   ```bash
   # Test with curl first
   curl -X POST https://api.checkmaasystem.com/api/search \
     -H "X-API-Key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"query": "test@gmail.com", "type": "email"}'
   ```

3. **Check if the API is accessible from your location**:
   Some APIs may have geographic restrictions or IP-based blocking.

### "API key requiredAt error
Make sure you've set the CHECKMAA_API_KEY environment variable or pass it via `-k` flag.

### Detection not working as expected
- The tool uses pattern matching for detection
- You can always use manual mode with `-t` for specific searches
- Use `-v` for verbose output to see what's being detected
- For phone numbers: All non-digits are automatically removed before searching

### Rate limit errors
Increase the delay between requests:
```bash
checkmaa -q example.com --auto --delay 10
```

### Python not found
- **Windows**: Install Python from python.org
- **Linux**: Install via package manager: `sudo apt install python3`
- **macOS**: Python 3 comes pre-installed on recent versions, or install via Homebrew: `brew install python3`

## Integration Examples

### Python Script Integration:
```python
import subprocess
import json

def auto_check(query, delay=5):
    """Run auto-detection on a query"""
    cmd = ['python', 'checkmaa.py', '-q', query, '--auto', 
           '--delay', str(delay), '-f', 'json']
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        raise Exception(result.stderr)

# Example usage
results = auto_check('admin@example.com')
for search_type, data in results.items():
    print(f"{search_type}: {data}")
```

### PowerShell Automation:
```powershell
# Auto-check a list of queries
$queries = Get-Content "queries.txt"

foreach ($query in $queries) {
    Write-Host "`nChecking: $query" -ForegroundColor Green
    python checkmaa.py -q $query --auto -f summary
    Start-Sleep -Seconds 10
}
```

### Monitoring Script:
```bash
#!/bin/bash
# Monitor specific emails/domains periodically

targets=("admin@mycompany.com" "mycompany.com")

while true; do
    for target in "${targets[@]}"; do
        echo "[$(date)] Checking $target"
        checkmaa -q "$target" --auto -f summary >> "monitor_${target//[@.]/_}.log"
    done
    sleep 3600  # Check every hour
done
```

## Security Notes
- Keep your API key secure and don't commit it to version control
- Use environment variables instead of hardcoding the API key
- Consider using a secrets manager for production use
- The tool uses HTTPS for all API communications
- Be mindful of rate limits when automating searches

## License
This tool is provided as-is for use with the Checkmaa System API.
