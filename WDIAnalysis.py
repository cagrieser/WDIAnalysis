import xml.etree.ElementTree as ET
import os
import math
import argparse
import sys
import datetime
import hashlib

def decode_filetime_duration(ticks_str):
    try:
        if not str(ticks_str).isdigit(): return ticks_str
        ticks = float(ticks_str)
        seconds = ticks / 10_000_000
        duration = datetime.timedelta(seconds=seconds)
        days = duration.days
        hours = (duration.seconds // 3600)
        minutes = (duration.seconds % 3600) // 60
        secs = duration.seconds % 60
        return f"{days}g {hours:02d}:{minutes:02d}:{secs:02d}"
    except:
        return ticks_str

def get_html_template(stats, process_data, thread_data, image_data, disk_data, current_part, total_parts, source_file, file_hash):
    base_name = os.path.splitext(os.path.basename(source_file))[0]
    
    prev_link = f"{base_name}_Part_{current_part - 1}.html"
    next_link = f"{base_name}_Part_{current_part + 1}.html"
    
    prev_btn = f'<a href="{prev_link}" class="nav-btn">DATA_BLOCK_PREV [{current_part - 1}]</a>' if current_part > 1 else '<span class="nav-btn disabled">:: START OF STREAM ::</span>'
    next_btn = f'<a href="{next_link}" class="nav-btn">DATA_BLOCK_NEXT [{current_part + 1}]</a>' if current_part < total_parts else '<span class="nav-btn disabled">:: END OF STREAM ::</span>'

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CASE: {base_name} | SEGMENT {current_part}</title>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #050505;
            --panel: #0f0f0f;
            --header-border: #333;
            --accent-cyan: #00f0ff;
            --accent-green: #0aff0a;
            --accent-red: #ff3333;
            --text-main: #d0d0d0;
            --text-dim: #666;
            --font-head: 'Share Tech Mono', monospace;
            --font-body: 'JetBrains Mono', monospace;
        }}

        body {{
            background-color: var(--bg);
            color: var(--text-main);
            font-family: var(--font-body);
            margin: 0;
            padding: 15px;
            font-size: 11px;
            overflow: hidden; 
        }}

        /* --- FORENSIC HEADER DESIGN --- */
        .forensic-header {{
            display: grid;
            grid-template-columns: 200px 1fr 250px;
            gap: 10px;
            border: 1px solid var(--header-border);
            background: var(--panel);
            padding: 10px;
            margin-bottom: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
            position: relative;
        }}
        
        .forensic-header::before {{
            content: "";
            position: absolute; top: 0; left: 0; width: 100%; height: 2px;
            background: linear-gradient(90deg, var(--accent-cyan), transparent);
        }}

        .header-box {{
            display: flex; flex-direction: column; justify-content: center;
        }}

        .label {{ font-family: var(--font-head); color: var(--text-dim); font-size: 10px; letter-spacing: 1px; margin-bottom: 2px; }}
        .value {{ font-family: var(--font-head); color: var(--accent-cyan); font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .hash-val {{ font-size: 10px; color: var(--accent-green); word-break: break-all; }}

        .nav-controls {{
            display: flex; align-items: center; justify-content: flex-end; gap: 5px;
        }}
        
        .nav-btn {{
            background: #000; border: 1px solid var(--header-border); color: var(--accent-cyan);
            padding: 6px 12px; text-decoration: none; font-family: var(--font-head); font-size: 11px;
            transition: 0.2s;
        }}
        .nav-btn:hover {{ background: var(--accent-cyan); color: #000; }}
        .nav-btn.disabled {{ color: #444; border-color: #222; cursor: not-allowed; }}

        /* --- STATS BAR --- */
        .stats-bar {{
            display: flex; gap: 15px; border-bottom: 1px solid var(--header-border);
            padding-bottom: 8px; margin-bottom: 8px;
        }}
        .stat-item {{ font-family: var(--font-head); color: #888; font-size: 12px; }}
        .stat-item span {{ color: #fff; font-weight: bold; }}

        /* --- TABS --- */
        .tabs {{ display: flex; gap: 2px; }}
        .tab-btn {{
            background: #111; border: 1px solid var(--header-border); border-bottom: none;
            color: #777; padding: 8px 20px; cursor: pointer;
            font-family: var(--font-head); font-size: 13px; letter-spacing: 1px;
        }}
        .tab-btn:hover {{ color: var(--accent-cyan); background: #1a1a1a; }}
        .tab-btn.active {{ 
            color: var(--bg); background: var(--accent-cyan); font-weight: bold;
            box-shadow: 0 0 10px var(--accent-cyan);
        }}

        /* --- TABLE CONTAINER --- */
        .table-wrap {{
            height: calc(100vh - 180px);
            overflow: auto;
            border: 1px solid var(--header-border);
            border-top: 2px solid var(--accent-cyan);
            background: #080808;
        }}

        table {{ width: 100%; border-collapse: collapse; min-width: 1000px; }}
        
        thead th {{
            position: sticky; top: 0;
            background: #161616; color: var(--accent-cyan);
            text-align: left; padding: 6px 8px;
            font-family: var(--font-head); font-size: 11px;
            border-bottom: 1px solid #333; z-index: 5;
            text-transform: uppercase;
        }}

        tbody td {{
            padding: 3px 8px; border-bottom: 1px solid #111;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            max-width: 450px; color: #ccc;
        }}

        tbody tr:hover {{ background: #1a1a1a; color: #fff; }}
        tbody tr:nth-child(even) {{ background: #0b0b0b; }}
        
        tbody td:hover {{
            white-space: normal; word-break: break-all;
            background: #222; position: relative; z-index: 2;
        }}

        /* Search Box */
        .search-box {{
            margin-left: auto; background: #000; border: 1px solid #444; color: var(--accent-green);
            padding: 5px; font-family: var(--font-body); width: 250px; font-size: 11px;
        }}
        .search-box:focus {{ outline: none; border-color: var(--accent-green); }}

        /* Colors */
        .time {{ color: #e5c07b; }}
        .pid {{ color: var(--accent-red); font-weight: bold; }}
        .exe {{ color: var(--accent-green); }}
        .disk-read {{ color: #58a6ff; }}
        .disk-write {{ color: #ffb700; }}

        .tab-content {{ display: none; }}
    </style>
</head>
<body>

    <div class="forensic-header">
        <div class="header-box">
            <div class="label">CASE FILE ID</div>
            <div class="value">{base_name}</div>
            <div class="label" style="margin-top:5px">SEGMENT</div>
            <div class="value" style="color:#fff">{current_part} <span style="color:#666">/ {total_parts}</span></div>
        </div>
        <div class="header-box">
            <div class="label">SOURCE INTEGRITY (MD5)</div>
            <div class="hash-val">{file_hash}</div>
            <div class="label" style="margin-top:5px">ANALYSIS TIMESTAMP</div>
            <div class="value" style="font-size:12px; color:#aaa">{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        </div>
        <div class="nav-controls">
            {prev_btn}
            {next_btn}
        </div>
    </div>

    <div class="stats-bar">
        <div class="stat-item">DISK I/O: <span>{stats['disk_count']}</span></div>
        <div class="stat-item">THREADS: <span>{stats['thread_count']}</span></div>
        <div class="stat-item">IMAGES: <span>{stats['image_count']}</span></div>
        <div class="stat-item">PROCESSES: <span>{stats['process_count']} (Global)</span></div>
        <input type="text" id="filterInput" class="search-box" placeholder="[FILTER LOG DATA...]" onkeyup="filterTable()">
    </div>

    <div class="tabs">
        <button class="tab-btn active" onclick="openTab('DiskIO')">DISK / FILE I/O</button>
        <button class="tab-btn" onclick="openTab('Threads')">THREADS</button>
        <button class="tab-btn" onclick="openTab('Images')">IMAGE LOADS</button>
        <button class="tab-btn" onclick="openTab('Processes')">PROCESSES (ALL)</button>
    </div>

    <div id="DiskIO" class="tab-content" style="display: block;">
        <div class="table-wrap">
            <table>
                <colgroup><col width="100"><col width="60"><col width="60"><col width="80"><col width="auto"><col width="80"></colgroup>
                <thead><tr><th>DURATION</th><th>PID</th><th>TYPE</th><th>OPERATION</th><th>FILE PATH / KEY</th><th>SIZE (B)</th></tr></thead>
                <tbody>{disk_data}</tbody>
            </table>
        </div>
    </div>

    <div id="Threads" class="tab-content">
        <div class="table-wrap">
            <table>
                <colgroup><col width="100"><col width="60"><col width="80"><col width="120"><col width="auto"></colgroup>
                <thead><tr><th>DURATION</th><th>PID</th><th>TID</th><th>STACK BASE</th><th>START ADDRESS</th></tr></thead>
                <tbody>{thread_data}</tbody>
            </table>
        </div>
    </div>

    <div id="Images" class="tab-content">
        <div class="table-wrap">
            <table>
                <colgroup><col width="100"><col width="60"><col width="200"><col width="auto"><col width="80"></colgroup>
                <thead><tr><th>DURATION</th><th>PID</th><th>IMAGE NAME</th><th>FULL PATH</th><th>SIZE</th></tr></thead>
                <tbody>{image_data}</tbody>
            </table>
        </div>
    </div>

    <div id="Processes" class="tab-content">
        <div class="table-wrap">
            <table>
                <colgroup><col width="100"><col width="60"><col width="60"><col width="150"><col width="auto"></colgroup>
                <thead><tr><th>DURATION</th><th>PID</th><th>PPID</th><th>IMAGE NAME</th><th>COMMAND LINE</th></tr></thead>
                <tbody>{process_data}</tbody>
            </table>
        </div>
    </div>

    <script>
        function openTab(name) {{
            document.querySelectorAll('.tab-content').forEach(x => x.style.display = 'none');
            document.querySelectorAll('.tab-btn').forEach(x => x.classList.remove('active'));
            document.getElementById(name).style.display = 'block';
            event.target.classList.add('active');
        }}

        function filterTable() {{
            let input = document.getElementById("filterInput").value.toUpperCase();
            let activeTab = document.querySelector('.tab-content[style*="block"]');
            let rows = activeTab.getElementsByTagName("tr");
            
            for (let i = 1; i < rows.length; i++) {{
                let text = rows[i].innerText || rows[i].textContent;
                rows[i].style.display = text.toUpperCase().indexOf(input) > -1 ? "" : "none";
            }}
        }}
    </script>
</body>
</html>
"""
    return html

def parse_and_split_xml(file_path, chunk_size):
    try:
        print(f"[*] Reading file: {file_path}")
        
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        file_hash = hasher.hexdigest().upper()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip().startswith('<root>'):
            content = f"<root>{content}</root>"
            
        root = ET.fromstring(content)
    except Exception as e:
        print(f"[!] Critical Error: {e}")
        return

    all_images = []
    all_threads = []
    all_processes = []
    all_disk_io = []

    print("[*] Parsing XML Data (Images, Threads, Processes, Disk/Reg I/O)...")

    for event in root.findall('.//event'):
        mof = event.find('mof')
        if mof is None: continue
        
        attrs = {attr.get('name'): attr.get('value') for attr in mof.findall('attribute')}
        provider = mof.get('provider', '')
        
        raw_time = event.get('timestamp', '0')
        decoded_time = decode_filetime_duration(raw_time)
        pid = attrs.get("ProcessId", event.get("PID", "-"))

        if "DiskIo" in provider or "FileIo" in provider or "Registry" in provider:
            op_type = mof.get('type', attrs.get('Type', 'Unknown'))
            filename = attrs.get('FileName', attrs.get('KeyName', ''))
            
            if not filename: filename = f"Ref: {attrs.get('FileObject', '-')}"
            
            size = attrs.get('TransferSize', attrs.get('IoSize', '-'))
            
            css_class = "disk-read" if "Read" in op_type else ("disk-write" if "Write" in op_type else "")
            
            row = f'<tr><td class="time">{decoded_time}</td><td class="pid">{pid}</td><td>{provider}</td><td class="{css_class}">{op_type}</td><td>{filename}</td><td>{size}</td></tr>'
            all_disk_io.append(row)

        elif "ImageLoad" in provider:
            full_path = attrs.get('FileName', '')
            image_name = full_path.split('\\')[-1] if full_path else "-"
            row = f'<tr><td class="time">{decoded_time}</td><td class="pid">{pid}</td><td class="exe">{image_name}</td><td>{full_path}</td><td>{attrs.get("ImageSize")}</td></tr>'
            all_images.append(row)

        elif "Thread" in provider:
            row = f'<tr><td class="time">{decoded_time}</td><td class="pid">{pid}</td><td>{attrs.get("ThreadId")}</td><td>{attrs.get("StackBase")}</td><td>{attrs.get("Win32StartAddr")}</td></tr>'
            all_threads.append(row)

        elif "Process" in provider or attrs.get('ImageFileName'):
            p_name = attrs.get('ImageFileName', 'Unknown')
            cmd_line = attrs.get('CommandLine', '-')
            ppid = attrs.get('ParentId', attrs.get('ParentProcessId', '-'))
            row = f'<tr><td class="time">{decoded_time}</td><td class="pid">{pid}</td><td>{ppid}</td><td class="exe">{p_name}</td><td>{cmd_line}</td></tr>'
            all_processes.append(row)

    full_process_html = "".join(all_processes)

    max_len = max(len(all_images), len(all_threads), len(all_disk_io))
    
    if max_len == 0:
        print("[!] Data not found.")
        return

    total_parts = math.ceil(max_len / chunk_size)
    
    print(f"\n[+] Analysis Complete: {os.path.basename(file_path)}")
    print(f"    - Processes : {len(all_processes)}")
    print(f"    - Threads   : {len(all_threads)}")
    print(f"    - Images    : {len(all_images)}")
    print(f"    - Disk/Reg  : {len(all_disk_io)}")
    print(f"    - Total     : Generating {total_parts} HTML Parts...")

    for i in range(total_parts):
        start = i * chunk_size
        end = start + chunk_size
        
        chunk_disk = all_disk_io[start:end]
        chunk_threads = all_threads[start:end]
        chunk_images = all_images[start:end]
        
        stats = {
            'process_count': len(all_processes),
            'thread_count': len(chunk_threads),
            'image_count': len(chunk_images),
            'disk_count': len(chunk_disk)
        }
        
        html_content = get_html_template(
            stats, 
            full_process_html, 
            "".join(chunk_threads), 
            "".join(chunk_images),
            "".join(chunk_disk),
            i + 1,
            total_parts,
            file_path,
            file_hash
        )
        
        fname = f"{os.path.splitext(os.path.basename(file_path))[0]}_Part_{i+1}.html"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"    [+] Report Generated: {fname}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", required=True)
    parser.add_argument("--chunk", "-c", type=int, default=15000)
    args = parser.parse_args()
    parse_and_split_xml(args.file, args.chunk)