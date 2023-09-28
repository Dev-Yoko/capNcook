from flask import Flask, render_template, request, session, jsonify
from flask_caching import Cache
from flask import redirect
import os
from termcolor import colored
import requests
import subprocess
import json
import urllib.parse
from tqdm import tqdm
from time import sleep
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

tor_link = os.system("echo '<sudo_password>' | sudo -S cat /var/lib/tor/hidden_service/hostname | lolcat")

command = "curl https://api.ipify.org"
process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, _ = process.communicate()

pub_ip = output.decode().strip()
print(colored("\nPublic IP: " + pub_ip, "yellow"))

command = "curl --socks5 '127.0.0.1:9050' https://api.ipify.org"
process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, _ = process.communicate()

anon_ip = output.decode().strip()
print(colored("\nAnonymized IP: " + anon_ip, "red"))
print("\n")

app = Flask(__name__, static_url_path='/static', template_folder='templates')
app.config['CACHE_TYPE'] = 'simple'  # You can choose a caching type that suits your needs
cache = Cache(app)
app.config['CACHE_DEFAULT_TIMEOUT'] = 3000

app.secret_key = os.getenv('secret_key')

@app.route("/") 

def index():
    
    return render_template("index.html")

@app.route('/onion_check')

def onion_check():
    if 'onionCheck_results' in session:
        # If the results are already cached in the session, use them
        results = session['onionCheck_results']
    else:
        # Otherwise, run the backend operation and cache the results
        results = run_backend_onionCheck()  # Replace with your actual backend code
        session['onionCheck_results'] = results  # Cache the results in the session

    return render_template("onion_check.html", results=results)
   
    
def run_backend_onionCheck():
    proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
    }

    print("\nTor Connection Check")
    try:
        system_ip = requests.get('https://ident.me', proxies=proxies).text
        tor_ip_list = requests.get('https://check.torproject.org/exit-addresses').text
        if system_ip in tor_ip_list:
            print('Tor_IP: ', system_ip)
            print("\nTor Connection Success \n")
    except:
        print("Error: Configure Tor as service")
        exit()

    with open('domains.txt', 'r') as file:
        domains = file.readlines()

    results = []

    for url in domains:
        url = url.strip('\n') 
        result = {} 
        status = 'N/A'
        status_code = 'N/A'

        try:
            data = requests.get(url, proxies=proxies)
        except:
            data = 'error'

        if data != 'error':
            status = 'Active'
            status_code = data.status_code
            soup = BeautifulSoup(data.text, 'html.parser')
            page_title = str(soup.title)
            page_title = page_title.replace('<title>', '')
            page_title = page_title.replace('</title>', '')
            result['url'] = url
            result['status'] = 'Active'
            result['status_code'] = data.status_code
            result['page_title'] = page_title
        
        elif data == 'error':
            status = "Inactive"
            status_code = 'NA'
            page_title = 'NA'
            result['url'] = url
            result['status'] = 'Inactive'
            result['status_code'] = 'NA'
            result['page_title'] = 'NA'

        results.append(result)

        print(url, ': ', status, ': ', status_code, ': ', page_title)

    return results

@app.route('/recon')
def recon():
    if 'recon_results' in session:
        # If the results are already cached in the session, use them
        recon_outputs = session['recon_results']
    else:
        # Otherwise, run the backend operation and cache the results
        recon_outputs = run_backend_recon()  # Replace with your actual backend code
        session['recon_results'] = recon_outputs  # Cache the results in the session

    return render_template("recon.html", recon_outputs=recon_outputs)

# Example backend operation (replace with your actual code)
def run_backend_recon():
    def run_whois(onion_link, index):
        command = f"whois -h torwhois.com {onion_link} | tee recon_output/recon{index}.txt"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            output_lines = result.stdout.splitlines()
            output_lines = output_lines[:-3]  # Exclude the last four lines
            output = '\n'.join(output_lines)

        else:
            output = f"Error: {result.stderr}"

        return output

    if not os.path.exists('recon_output'):
        os.makedirs('recon_output')
            
    with open('domains.txt', 'r') as file:
        onion_links = file.read().splitlines()

    recon_outputs = []

    for index, onion_link in enumerate(onion_links, start=1):
        whois_output = run_whois(onion_link, index)

        header_line = f"Output for {onion_link} (Domain {index}):\n"
        recon_outputs.append({
            'header': header_line,
            'output': whois_output.splitlines(),
        })

    return recon_outputs

@app.route('/headers')

def headers():

    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }

    with open('domains.txt', 'r') as file:
        onion_urls = file.read().splitlines()

    domains = []

    cmd2 = "cat domains.txt 2>/dev/null | aquatone -out static/aqua_out -ports 80 -proxy socks5://127.0.0.1:9050 -http-timeout 30000 -screenshot-timeout 60000 2>/dev/null"

    cmd3 = "eog static/aqua_out/screenshots/ &"

    screenshot_dir = 'aqua_out/screenshots'
    
    print(colored("\n[+] Capturing Screenshots...", "green"))
    os.system(cmd2)  # Execute cmd2

    print(colored("\n[+] Opening screenshots...", "green"))
    os.system(cmd3)  # Open Screenshots

    for onion_url in onion_urls:
        try:
            onion_url = onion_url.strip()
            screenshot_filename = f"{onion_url.replace('://', '__').replace('.onion', '_onion')}__da39a3ee5e6b4b0d.png"
            screenshot_path = os.path.join(screenshot_dir, screenshot_filename)

            response = requests.get(onion_url, headers={'User-Agent': 'Mozilla/5.0'}, proxies=proxies)
            if response.status_code == 200:
                headers = {
                    'title': onion_url,
                    'headers': response.headers,
                    'screenshot': screenshot_path,
                }

                # Print the headers in the terminal
                print(colored(f"\n{'-' * 40}\nHeaders for {onion_url}\n{'-' * 40}", "green"))
                for header, value in response.headers.items():
                    print(f"{header}: {value}")
                print("-" * 40) 

                domains.append(headers)
        except Exception as e:
            print(f"An error occurred for {onion_url}: {str(e)}")
            print("-" * 40) 

    return render_template("headers.html", domains=domains)

@app.route('/enumeration')

def enumeration():
    if 'enumeration_results' in session:
        # If the results are already cached in the session, use them
        enumeration_outputs = session['enumeration_results']
    else:
        # Otherwise, run the backend operation and cache the results
        enumeration_outputs = run_backend_enum()  # Replace with your actual backend code
        session['enumeration_results'] = enumeration_outputs  # Cache the results in the session

    return render_template("enumeration.html", enumeration_outputs=enumeration_outputs)

def run_backend_enum():
    def run_nikto(onion_link, index):
        nikto_command = f"proxychains nikto -h {onion_link} -Tuning 2,3,5,0,a,b -Display 3,S -maxtime 60s -o nikto_log/vuln{index}.json"
        subprocess.run(nikto_command, shell=True)
        return colored(f"\nNikto scan for {onion_link} completed.", "yellow")

    def run_feroxbuster(onion_link, index):
        feroxbuster_command = f"proxychains -q feroxbuster -u {onion_link} -w wordlist.txt --threads 30 -C 404 --time-limit 30s --auto-bail -q"
        subprocess.run(feroxbuster_command, shell=True)
        feroxbuster_process = subprocess.Popen(feroxbuster_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        feroxbuster_output, _ = feroxbuster_process.communicate()

        # Filter out lines containing "404"
        filtered_output_lines = [line for line in feroxbuster_output.split('\n') if "404" not in line]

        # Combine the filtered lines back into a single string
        filtered_output = '\n'.join(filtered_output_lines)

        with open(f'ferox_log/fuzz{index}.log', 'w') as log_file:
            log_file.write(filtered_output)

        return filtered_output

    with open('domains.txt', 'r') as file:
        onion_links = file.read().splitlines()

    enumeration_outputs = []

    for index, onion_link in enumerate(onion_links, start=1):
        print(colored(f"\n{'-' * 40}\nScanning {onion_link}\n{'-' * 40}", "green"))

        nikto_message = run_nikto(onion_link, index)
        print(nikto_message)

        print(colored(f"\n{'-' * 40}\nFuzzing {onion_link}\n{'-' * 40}", "green"))

        feroxbuster_output = run_feroxbuster(onion_link, index)

        enumeration_outputs.append({
            'onion_link': onion_link,
            'feroxbuster_output': feroxbuster_output
        })

    return enumeration_outputs

@app.route("/search", methods=["GET", "POST"])

def search():
    # Check if the "Refresh Cache" button was pressed
    if request.method == "POST" and request.form.get("refresh_cache"):
        # Clear the cache
        session.pop('search_results', None)

    search_results = session.get('search_results')

    if search_results is None:
        keywords = request.form.get("keywords")

        if keywords is None:
            return "No search input provided in the request."

        search_results = run_backend_search(keywords)
        session['search_results'] = search_results  # Cache the results in the session

    return render_template("index.html", **search_results)

def run_backend_search(keywords):
    keywords = request.form.get("keywords")
    
    if keywords is None:

        return "No search input provided in the request."
    
    encoded_keywords = urllib.parse.quote(keywords.encode("utf-8"))
    
    print(colored("[+] Searching for top domains... \n", "yellow"))
    
    cmd1 = f"curl -s 'https://ahmia.fi/search/?q={encoded_keywords}' | grep -oE 'http[s]?://[^/]+\.onion' 2>/dev/null | head -n 30 > domains.txt 2>/dev/null"
    
    # cmd2 = "cat domains.txt 2>/dev/null | ./aquatone -out templates/aqua_out -proxy socks5://127.0.0.1:9050 -ports 80 -threads 50 -http-timeout 30000 -screenshot-timeout 10000 -resolution \"1920,1080\" 2>/dev/null"

    total_iterations = 15  # Total number of iterations for both cmd1 and cmd2
    
    # Use tqdm to create a progress bar for cmd1
    custom_bar_format = "{desc} | {bar} | {percentage:3.0f}%"
    with tqdm(total=total_iterations, unit="onions", desc="Indexing: ", dynamic_ncols=True, bar_format=custom_bar_format, colour="green") as pbar:
        for i in range(total_iterations):
            os.system(cmd1)  # Execute cmd1
            pbar.update(1)   # Update the progress bar
            print('\r', end='')

    print(colored("\n[-] Done!", "blue"))

    with open('domains.txt', 'r') as file:
        links = file.readlines()        

    domain_links = [{'title': link.strip(), 'link': 'http://' + link.strip()} for link in links]

    message = f"Domains Listed for {keywords}|"

    return {
        'pub_ip': pub_ip,
        'anon_ip': anon_ip,
        'message': message,
        'domain_links': domain_links
    }

@app.route('/refresh_cache', methods=['POST'])
def refresh_cache():

    if 'onionCheck_results' in session:
        del session['onionCheck_results']
    if 'recon_results' in session:
        del session['recon_results']
    if 'headers_results' in session:
        del session['headers_results']
    if 'enumeration_results' in session:
        del session['enumeration_results']
    if 'search_results' in session:
        del session['search_results']

    return redirect(request.referrer)


if __name__ == "__main__":

    app.run(port=5000)