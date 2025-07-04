#!/usr/bin/env python3
"""
Checkmaa System CLI Tool
A cross-platform command-line tool for searching various data types via Checkmaa API
"""

import argparse
import json
import sys
import os
import re
import time

# Try to use requests library if available (more reliable), otherwise use urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError


class CheckmaaClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('CHECKMAA_API_KEY')
        if not self.api_key:
            raise ValueError("API key required. Set CHECKMAA_API_KEY environment variable or use --api-key")
        
        self.base_url = "https://api.checkmaasystem.com/api/search"
    
    def search(self, query, search_type):
        """Perform a search with the given query and type"""
        # Clean phone numbers - remove all non-digits
        if search_type == 'phone':
            query = re.sub(r'[^0-9]', '', query)
        
        data = {
            "query": query,
            "type": search_type
        }
        
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        if HAS_REQUESTS:
            return self._search_with_requests(data, headers)
        else:
            return self._search_with_urllib(data, headers)
    
    def _search_with_requests(self, data, headers):
        """Search using requests library"""
        try:
            response = requests.post(
                self.base_url,
                json=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_json = e.response.json()
                raise Exception(f"API Error {e.response.status_code}: {error_json.get('message', str(error_json))}")
            except:
                raise Exception(f"API Error {e.response.status_code}: {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network Error: {str(e)}")
    
    def _search_with_urllib(self, data, headers):
        """Search using urllib (fallback)"""
        # Add User-Agent to avoid being blocked
        headers['User-Agent'] = 'Maaaa Ma Maaa'
        
        try:
            req = Request(
                self.base_url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
                
        except HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_json = json.loads(error_body)
                raise Exception(f"API Error {e.code}: {error_json.get('message', error_body)}")
            except json.JSONDecodeError:
                raise Exception(f"API Error {e.code}: {error_body}")
        except URLError as e:
            raise Exception(f"Network Error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected Error: {str(e)}")


class QueryDetector:
    """Detect query type and suggest appropriate search types"""
    
    @staticmethod
    def detect_type(query):
        """Detect the type of query and return applicable search types"""
        query = query.strip()
        
        # Email patterns
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        email_prefix_pattern = r'^[a-zA-Z0-9._%+-]+@$'
        
        # Domain pattern
        domain_pattern = r'^([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$'
        
        # Phone pattern (basic international format support)
        phone_pattern = r'^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$'
        
        # URL pattern
        url_pattern = r'^(https?://)?([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
        
        # Username pattern (alphanumeric with some special chars)
        username_pattern = r'^[a-zA-Z0-9_.-]{3,30}$'
        
        detected_types = []
        
        # Check email
        if re.match(email_pattern, query):
            detected_types.append({
                'category': 'email',
                'types': ['email', 'ulp-email', 'whois-email'],
                'confidence': 'high'
            })
        elif re.match(email_prefix_pattern, query):
            detected_types.append({
                'category': 'email-prefix',
                'types': ['email-prefix'],
                'confidence': 'high'
            })
        
        # Check domain
        if re.match(domain_pattern, query) and '@' not in query:
            # More specific domain check to avoid email false positives
            if not any(query.endswith(tld) for tld in ['.html', '.php', '.jpg', '.png', '.pdf']):
                detected_types.append({
                    'category': 'domain',
                    'types': ['domain', 'whois-domain', 'password'],
                    'confidence': 'high'
                })
        
        # Check URL
        if re.match(url_pattern, query) and '/' in query:
            detected_types.append({
                'category': 'url',
                'types': ['ulp-url'],
                'confidence': 'high'
            })
        
        # Check phone
        digits_only = re.sub(r'[^0-9]', '', query)
        if re.match(phone_pattern, query) or (digits_only and 7 <= len(digits_only) <= 15):
            detected_types.append({
                'category': 'phone',
                'types': ['phone'],
                'confidence': 'medium' if len(digits_only) < 10 else 'high'
            })
            # Store the cleaned phone number for display
            detected_types[-1]['cleaned_query'] = digits_only
        
        # Check username (only if not detected as email or domain)
        if not detected_types and re.match(username_pattern, query):
            detected_types.append({
                'category': 'username',
                'types': ['username'],
                'confidence': 'medium'
            })
        
        # Password detection (generic string that could be a password)
        if not detected_types and len(query) >= 4:
            detected_types.append({
                'category': 'password',
                'types': ['password'],
                'confidence': 'low'
            })
        
        return detected_types


def format_output(result, output_format='pretty', search_type=None):
    """Format the output based on the specified format"""
    if output_format == 'json':
        return json.dumps(result, indent=2)
    elif output_format == 'raw':
        return json.dumps(result)
    else:  # pretty
        if isinstance(result, dict):
            if 'error' in result:
                return f"Error: {result['error']}"
            
            # Format based on common response patterns
            output = []
            
            # Add search type header if provided
            if search_type:
                output.append(f"=== {search_type.upper()} SEARCH ===")
            
            for key, value in result.items():
                if isinstance(value, list):
                    output.append(f"\n{key.upper()}:")
                    for item in value:
                        if isinstance(item, dict):
                            output.append("  - " + ", ".join(f"{k}: {v}" for k, v in item.items()))
                        else:
                            output.append(f"  - {item}")
                elif isinstance(value, dict):
                    output.append(f"\n{key.upper()}:")
                    for k, v in value.items():
                        output.append(f"  {k}: {v}")
                else:
                    output.append(f"{key}: {value}")
            
            return "\n".join(output)
        else:
            return str(result)


def perform_auto_search(client, query, delay=5, verbose=False, format_type='pretty'):
    """Automatically detect query type and perform relevant searches"""
    detector = QueryDetector()
    detected = detector.detect_type(query)
    
    if not detected:
        print("Could not detect query type. Please specify search type manually.")
        return
    
    print(f"\nAnalyzing query: '{query}'")
    print("=" * 50)
    
    # Display detected types
    for detection in detected:
        confidence_emoji = {
            'high': '✓✓✓',
            'medium': '✓✓',
            'low': '✓'
        }.get(detection['confidence'], '?')
        
        print(f"\nDetected as {detection['category']} {confidence_emoji}")
        if detection['category'] == 'phone' and 'cleaned_query' in detection:
            print(f"Phone number will be searched as: {detection['cleaned_query']}")
        print(f"Will perform {len(detection['types'])} search(es): {', '.join(detection['types'])}")
    
    print("\n" + "=" * 50)
    
    # Perform searches
    all_results = {}
    search_types = []
    
    # Collect all search types from detections
    for detection in detected:
        search_types.extend(detection['types'])
    
    # Remove duplicates while preserving order
    search_types = list(dict.fromkeys(search_types))
    
    for i, search_type in enumerate(search_types):
        print(f"\n[{i+1}/{len(search_types)}] Searching {search_type}...", end='', flush=True)
        
        try:
            result = client.search(query, search_type)
            all_results[search_type] = result
            print(" ✓ Success")
            
            if verbose or format_type != 'summary':
                print("\n" + format_output(result, format_type, search_type))
            
        except Exception as e:
            all_results[search_type] = {"error": str(e)}
            print(f" ✗ Failed: {e}")
        
        # Delay between requests (except for the last one)
        if i < len(search_types) - 1:
            print(f"Waiting {delay} seconds before next request...", end='', flush=True)
            time.sleep(delay)
            print(" done")
    
    # Summary
    print("\n" + "=" * 50)
    print("SEARCH SUMMARY")
    print("=" * 50)
    
    successful = sum(1 for r in all_results.values() if 'error' not in r)
    print(f"Total searches: {len(search_types)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(search_types) - successful}")
    
    if format_type == 'summary':
        print("\nResults summary:")
        for search_type, result in all_results.items():
            if 'error' in result:
                print(f"  • {search_type}: Failed - {result['error']}")
            else:
                # Try to show a brief summary
                items_found = 0
                for value in result.values():
                    if isinstance(value, list):
                        items_found += len(value)
                print(f"  • {search_type}: Found {items_found} result(s)")
    
    return all_results


def main():
    parser = argparse.ArgumentParser(
        description='Checkmaa System CLI - Search for various data types',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
SEARCH MODES:
  1. Manual mode: Specify exact search type with -t
  2. Auto mode: Automatically detect and search all relevant types
  
SEARCH TYPES:
  email         - Search by exact email address
  email-prefix  - Search by email prefix (e.g., "test@")
  username      - Search by username
  domain        - Search by domain name
  password      - Search by password
  phone         - Search by phone number
  ulp-email     - Search ULP by email
  ulp-url       - Search ULP by URL
  whois-email   - Search WHOIS by email
  whois-domain  - Search WHOIS by domain

EXAMPLES:
  Manual search:
    %(prog)s -q test@gmail.com -t email
    %(prog)s -q john123 -t username
    %(prog)s -q 1234567890 -t phone  # All non-digits auto-removed
  
  Auto-detect and search all relevant types:
    %(prog)s -q test@gmail.com --auto
    %(prog)s -q facebook.com --auto
    %(prog)s -q "+1 (234) 567-8900" --auto  # Cleaned to: 12345678900
  
  Auto-detect with custom delay:
    %(prog)s -q admin@example.com --auto --delay 10

ENVIRONMENT:
  Set CHECKMAA_API_KEY to avoid passing --api-key each time
  
TROUBLESHOOTING:
  If you get API Error 403, try:
  1. pip install requests (for better HTTP handling)
  2. Check if your API key is correct
  3. Try with curl to verify the API is accessible
        """
    )
    
    parser.add_argument('-q', '--query', required=True, help='Search query')
    parser.add_argument('-t', '--type', 
                        choices=['email', 'email-prefix', 'username', 'domain', 
                               'password', 'phone', 'ulp-email', 'ulp-url', 
                               'whois-email', 'whois-domain'],
                        help='Type of search (not needed with --auto)')
    parser.add_argument('--auto', action='store_true', 
                        help='Auto-detect query type and run all relevant searches')
    parser.add_argument('--delay', type=int, default=5,
                        help='Delay between API calls in auto mode (default: 5 seconds)')
    parser.add_argument('-k', '--api-key', help='API key (or set CHECKMAA_API_KEY env var)')
    parser.add_argument('-f', '--format', choices=['pretty', 'json', 'raw', 'summary'], 
                        default='pretty', help='Output format (default: pretty)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.auto and not args.type:
        parser.error("Either --type or --auto must be specified")
    
    if args.auto and args.type:
        parser.error("Cannot use both --type and --auto together")
    
    # Show warning if requests is not available
    if not HAS_REQUESTS and args.verbose:
        print("Note: 'requests' library not found. Using urllib (less reliable).")
        print("Install requests for better reliability: pip install requests\n")
    
    try:
        # Initialize client
        client = CheckmaaClient(api_key=args.api_key)
        
        if args.auto:
            # Auto mode
            perform_auto_search(client, args.query, args.delay, args.verbose, args.format)
        else:
            # Manual mode
            if args.verbose:
                print(f"Searching for '{args.query}' with type '{args.type}'...\n")
            
            result = client.search(args.query, args.type)
            formatted_output = format_output(result, args.format)
            print(formatted_output)
        
    except ValueError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        print("\nSet your API key using one of these methods:")
        print("  1. Export environment variable: export CHECKMAA_API_KEY='your_key'")
        print("  2. Pass via command line: checkmaa -k 'your_key' -q query -t type")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if "403" in str(e):
            print("\nTroubleshooting API Error 403:")
            print("1. Verify your API key is correct")
            print("2. Try: pip install requests (for better HTTP handling)")
            print("3. Test with curl to ensure API is accessible from your location")
        sys.exit(1)


if __name__ == "__main__":
    main()