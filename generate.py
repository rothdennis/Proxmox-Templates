import urllib.request
import lzma
import shutil
import sys
import subprocess
import tempfile
import os
from getpass import getpass
import argparse
import curses
import json

IMAGES_URL = 'https://raw.githubusercontent.com/rothdennis/Proxmox-Templates/refs/heads/main/images.json'
# Load images configuration
IMAGES = json.loads(urllib.request.urlopen(IMAGES_URL).read().decode('utf-8'))

### HELPER FUNCTIONS ###

def show_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = downloaded / total_size * 100
        percent = min(percent, 100)  # Avoid going slightly over 100%
        sys.stdout.write(f"\rDownloading: {percent:5.1f}%")
        sys.stdout.flush()
    else:
        # Total size is unknown
        sys.stdout.write(f"\rDownloaded {downloaded} bytes")
        sys.stdout.flush()

def is_valid_ssh_public_key(key: str) -> bool:
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(key)
        filename = f.name

    result = subprocess.run(
        ["ssh-keygen", "-lf", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Clean up the temp file
    try:
        os.remove(filename)
    except:
        pass
    
    return result.returncode == 0

def parse_arguments():
    parser = argparse.ArgumentParser(
                        prog='Proxmox VM Template Generator',
                        description='Generate Proxmox VM templates from cloud images with custom configurations.')
    # hardware
    parser.add_argument('--memory', type=int, default=1024, help='set the memory size in MB (default: 1024)')
    parser.add_argument('--cores', type=int, default=2, help='set the number of CPU cores (default: 2)')
    parser.add_argument('--sockets', type=int, default=1, help='set the number of CPU sockets (default: 1)')
    parser.add_argument('--disk-size', type=str, default='10G', help='set the disk size (default: 10G)')
    parser.add_argument('--cpu', type=str, default='host', help='set the CPU type (default: host)')
    # network
    parser.add_argument('--network-bridge', type=str, default='vmbr0', help='set the network bridge (default: vmbr0)')
    parser.add_argument('--ipv4', type=str, default='dhcp', help='set the IPv4 configuration (default: dhcp)')
    parser.add_argument('--ipv6', type=str, default='auto', help='set the IPv6 configuration (default: auto)')
    # naming and IDs
    parser.add_argument('--prefix', type=str, default='template', help='set the prefix for VM template names (default: template)')
    parser.add_argument('--id-start', type=int, default=900, help='set the starting ID for VM templates (default: 900)')
    return parser.parse_args()

def clear_screen():
    subprocess.run('clear', shell=True)

def get_username():
    username = input('Enter username [root]: ') or 'root'
    print('\n-----\n')
    return username

def get_password():
    password = ''
    while True:
        password = getpass('Enter password: ')
        if password:
            break
        else:
            print('Password cannot be empty. Please try again.\n')
    print('\n-----\n')
    
    while True:
        password_confirm = getpass('Confirm password: ') or ''
        if password == password_confirm:
            break
        else:
            print('Passwords do not match. Please try again.\n')
    print('\n-----\n')
    
    return password

def get_ssh_key():
    ssh_key = ''
    while True:
        ssh_key = input('Enter SSH key: ')
        if is_valid_ssh_public_key(ssh_key):
            break
        else:
            print('Invalid SSH public key. Please try again.\n')
    print('\n-----\n')
    return ssh_key

def select_storage():
    res = subprocess.run("pvesm status --content images | awk 'NR>1 {print $1}'", capture_output=True, text=True, shell=True)
    available_storages = res.stdout.strip().split('\n')
    print('Select storage\n')
    for i, storage in enumerate(available_storages):
        print(f'{i+1}) {storage}')
    
    while True:
        try:
            storage_choice = int(input('\nEnter choice: ')) - 1
            if 0 <= storage_choice < len(available_storages):
                break
            else:
                print('Invalid choice. Please try again.\n')
        except ValueError:
            print('Invalid input. Please enter a number.\n')
    
    storage = available_storages[storage_choice]
    print('\n-----\n')
    return storage

def get_snippet_storages():
    """Get list of storage pools that support snippets content type."""
    # Get storage status with snippets content type
    res = subprocess.run(['pvesm', 'status', '--content', 'snippets'], 
                        capture_output=True, text=True)
    output = res.stdout.strip()
    if not output:
        return []
    
    # Parse output: skip header line, extract first column (storage name)
    lines = output.split('\n')
    storages = []
    for line in lines[1:]:  # Skip header
        parts = line.split()
        if parts:
            storages.append(parts[0])
    return [s for s in storages if s]  # Filter out empty strings

def get_cloud_init_files():
    """Get list of yaml/yml files from all snippet-enabled storage pools.
    Returns list of volume paths in format storage:snippets/file.yaml
    """
    snippet_storages = get_snippet_storages()
    cloud_init_files = []
    
    for storage in snippet_storages:
        # Validate storage name contains only allowed characters (alphanumeric, dash, underscore)
        if not storage or not all(c.isalnum() or c in '-_' for c in storage):
            continue

        # Use pvesm list to get snippets in this storage
        # This returns volumes like: storage:snippets/file.yaml
        res = subprocess.run(['pvesm', 'list', storage, '--content', 'snippets'], 
                            capture_output=True, text=True)
        output = res.stdout.strip()
        if not output:
            continue
        
        # Parse output: skip header line, extract volume paths
        # Output format:
        # Volid                              Format     Type       Size
        # local:snippets/cloud-init.yaml     snippets   snippets   1234
        lines = output.split('\n')
        if len(lines) <= 1:
            continue  # Only header or empty, no actual content
        
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if parts:
                volume_path = parts[0]  # First column is the volume ID
                # Validate volume path format: storage:snippets/filename.yaml
                if ':snippets/' in volume_path and volume_path.endswith(('.yaml', '.yml')):
                    cloud_init_files.append(volume_path)

    return cloud_init_files

def select_cloud_init_method():
    """Ask user whether to input credentials manually or use a cloud-init file."""
    print('Cloud-Init Configuration\n')
    print('1) Enter credentials manually')
    print('2) Use a cloud-init file')
    
    while True:
        try:
            choice = int(input('\nEnter choice: '))
            if choice in [1, 2]:
                break
            else:
                print('Invalid choice. Please enter 1 or 2.\n')
        except ValueError:
            print('Invalid input. Please enter a number.\n')
    
    print('\n-----\n')
    return choice

def select_cloud_init_file():
    """Display list of cloud-init files and let user select one."""
    cloud_init_files = get_cloud_init_files()
    
    if not cloud_init_files:
        print('No cloud-init files found in snippet-enabled storage pools.')
        snippet_storages = get_snippet_storages()
        if snippet_storages:
            print(f'Checked the following snippet-enabled storages: {", ".join(snippet_storages)}')
            print('To add a cloud-init file, upload a yaml/yml file to the snippets directory')
            print('of one of these storages using the Proxmox web interface or pvesm.')
        else:
            print('No snippet-enabled storage pools found.')
        print('Please add yaml/yml files to a storage pool that supports snippets.')
        sys.exit(1)
    
    print('Select cloud-init file\n')
    for i, file_path in enumerate(cloud_init_files):
        print(f'{i+1}) {file_path}')
    
    while True:
        try:
            choice = int(input('\nEnter choice: ')) - 1
            if 0 <= choice < len(cloud_init_files):
                break
            else:
                print('Invalid choice. Please try again.\n')
        except ValueError:
            print('Invalid input. Please enter a number.\n')
    
    selected_file = cloud_init_files[choice]
    print('\n-----\n')
    return selected_file

def select_os():
    print('Select OS\n')
    for i, distro in enumerate(IMAGES):
        print(f'{i+1}) {distro}')
    
    while True:
        try:
            distro_choice = int(input('\nEnter choice: ')) - 1
            if 0 <= distro_choice < len(IMAGES):
                break
            else:
                print('Invalid choice. Please try again.\n')
        except ValueError:
            print('Invalid input. Please enter a number.\n')
    print('\n-----\n')
    
    distro_name = list(IMAGES.keys())[distro_choice]
    return distro_name

def select_version(distro_name):
    print('Select Version\n')
    versions = IMAGES[distro_name]['versions']
    for i, version in enumerate(versions):
        version_name = version['name']
        deprecated_tag = " (deprecated)" if version.get('deprecated', False) else ""
        print(f'{i+1}) {version_name}{deprecated_tag}')
    
    while True:
        try:
            version_choice = int(input('\nEnter choice: ')) - 1
            if 0 <= version_choice < len(versions):
                break
            else:
                print('Invalid choice. Please try again.\n')
        except ValueError:
            print('Invalid input. Please enter a number.\n')
    print('\n-----\n')
    
    return version_choice

def select_os_versions_multi():
    """Multi-selection interface for OS/version combinations using curses.
    Returns a list of tuples: [(distro_name, version_index), ...]
    """
    # Build flat list of all OS/version options
    options = []
    for distro_name in IMAGES:
        versions = IMAGES[distro_name]['versions']
        for version_index, version in enumerate(versions):
            version_name = version['name']
            deprecated_tag = " (deprecated)" if version.get('deprecated', False) else ""
            options.append({
                'distro_name': distro_name,
                'version_index': version_index,
                'version_name': version_name,
                'display': f'{distro_name} / {version_name}{deprecated_tag}',
                'selected': False
            })
    
    def draw_menu(stdscr, current_row, selected_options):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Header
        title = "Select OS/Version Combinations (Space to toggle, Enter to confirm, q to quit)"
        stdscr.addstr(0, 0, title[:w-1], curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * min(len(title), w-1))
        
        # Calculate visible range
        visible_rows = h - 4  # Leave space for header and footer
        start_row = max(0, current_row - visible_rows // 2)
        end_row = min(len(options), start_row + visible_rows)
        
        # Adjust start_row if we're near the end
        if end_row - start_row < visible_rows and len(options) > visible_rows:
            start_row = max(0, end_row - visible_rows)
        
        # Display options
        for idx in range(start_row, end_row):
            option = options[idx]
            row = idx - start_row + 3
            
            if row >= h - 1:  # Prevent writing to last line
                break
            
            # Build display string
            checkbox = "[X]" if option['selected'] else "[ ]"
            display_text = f"{checkbox} {option['display']}"
            
            # Truncate if necessary
            if len(display_text) >= w:
                display_text = display_text[:w-4] + "..."
            
            # Highlight current row
            if idx == current_row:
                stdscr.addstr(row, 0, display_text, curses.A_REVERSE)
            else:
                stdscr.addstr(row, 0, display_text)
        
        # Footer
        if h > 3:
            footer = f"Selected: {selected_options}/{len(options)}"
            stdscr.addstr(h - 1, 0, footer[:w-1], curses.A_BOLD)
        
        stdscr.refresh()
    
    def main_curses(stdscr):
        # Initialize curses settings
        curses.curs_set(0)  # Hide cursor
        stdscr.keypad(True)  # Enable keypad mode
        
        current_row = 0
        
        while True:
            selected_count = sum(1 for opt in options if opt['selected'])
            draw_menu(stdscr, current_row, selected_count)
            
            key = stdscr.getch()
            
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(options) - 1:
                current_row += 1
            elif key == ord(' '):  # Space to toggle
                options[current_row]['selected'] = not options[current_row]['selected']
            elif key == ord('\n') or key == 10:  # Enter to confirm (newline)
                break
            elif key == ord('q') or key == ord('Q'):  # q to quit
                return []
        
        # Return selected options
        return [(opt['distro_name'], opt['version_index']) 
                for opt in options if opt['selected']]
    
    try:
        selected = curses.wrapper(main_curses)
        return selected
    except Exception as e:
        print(f"\nError initializing curses interface: {e}")
        print("This may happen if:")
        print("  - Running in a non-interactive terminal")
        print("  - Terminal doesn't support curses")
        print("  - TERM environment variable is not set properly")
        print("\nFalling back to single selection mode...")
        print("(To use multi-selection, run in a proper terminal)\n")
        # Fallback to original single selection
        distro_name = select_os()
        version_choice = select_version(distro_name)
        return [(distro_name, version_choice)]

def generate_unique_id(id_start):
    res = subprocess.run("qm list | awk 'NR>1 {print $1}'", capture_output=True, text=True, shell=True)
    output = res.stdout.strip()
    if output:
        used_ids = set(map(int, output.split('\n')))
    else:
        used_ids = set()
    
    current_id = id_start
    while current_id in used_ids:
        current_id += 1
    
    return str(current_id)

def download_image(image_url):
    image_name = image_url.split('/')[-1]
    print(f'Downloading image from {image_url} ...')
    urllib.request.urlretrieve(image_url, image_name, reporthook=show_progress)
    print('\n-----\n')
    return image_name

def decompress_image(image_name):
    if image_name.endswith('.tar.xz'):
        print(f'Decompressing {image_name} ...')
        with lzma.open(image_name) as f_in:
            with open('temp.tar', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        # List contents of tar to find the actual filename
        result = subprocess.run(['tar', '-tf', 'temp.tar'], capture_output=True, text=True)
        extracted_files = result.stdout.strip().split('\n')
        # Find the disk image file (typically .raw, .qcow2, or .img)
        disk_file = next((f for f in extracted_files if f.endswith(('.raw', '.qcow2', '.img'))), extracted_files[0])
        subprocess.run(['tar', '-xf', 'temp.tar'])
        subprocess.run(['rm', 'temp.tar'])
        subprocess.run(['rm', image_name])
        print('\n-----\n')
        return disk_file
    elif image_name.endswith('.xz'):
        decompressed_name = image_name[:-3] # remove .xz
        print(f'Decompressing {image_name} to {decompressed_name} ...')
        with lzma.open(image_name) as f_in:
            with open(decompressed_name, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        subprocess.run(['rm', image_name])
        print('\n-----\n')
        return decompressed_name
    
    return image_name

def generate_template_name(distro_name, version_choice, prefix):
    os_name = distro_name.lower().replace(' ', '-')
    os_version = IMAGES[distro_name]['versions'][version_choice]['name'].lower().replace(' ', '-').replace('.', '-')
    return f'{prefix}-{os_name}-{os_version}'

def create_template(vm_id, name, image_name, storage, username, password, ssh_key, config, cloud_init_file=None):
    print(f'Generating template ...')

    os_tag = name.split('-')[1] if '-' in name else name

    # create VM
    subprocess.run(['qm', 'create', vm_id, '--name', name, '--ostype', 'l26'])
    subprocess.run(['qm', 'set', vm_id, '--net0', f"virtio,bridge={config['network_bridge']}"])
    subprocess.run(['qm', 'set', vm_id, '--memory', str(config['memory'])])
    subprocess.run(['qm', 'set', vm_id, '--cores', str(config['cores'])])
    subprocess.run(['qm', 'set', vm_id, '--sockets', str(config['sockets'])])
    subprocess.run(['qm', 'set', vm_id, '--cpu', config['cpu']])
    subprocess.run(['qm', 'set', vm_id, '--serial0', 'socket'])
    subprocess.run(['qm', 'set', vm_id, '--vga', 'std'])

    # import disk
    disk_format = 'qcow2' if image_name.endswith('.qcow2') or image_name.endswith('.img') else 'raw'
    subprocess.run(['qm', 'importdisk', vm_id, image_name, storage, '--format', disk_format])
    subprocess.run(['qm', 'set', vm_id, '--scsi0', f'{storage}:vm-{vm_id}-disk-0,discard=on'])
    subprocess.run(['qm', 'set', vm_id, '--boot', 'order=scsi0'])
    subprocess.run(['qm', 'set', vm_id, '--scsihw', 'virtio-scsi-single'])

    if os_tag in ['gentoo']:
        subprocess.run(['qm', 'set', vm_id, '--bios', 'ovmf'])
        subprocess.run(['qm', 'set', vm_id, '--efidisk0', f'{storage}:1,size=4M,pre-enrolled-keys=0'])

    # cloud-init
    subprocess.run(['qm', 'set', vm_id, '--ide2', f'{storage}:cloudinit'])
    
    if cloud_init_file:
        # Use custom cloud-init file
        subprocess.run(['qm', 'set', vm_id, '--cicustom', f'user={cloud_init_file},network={cloud_init_file}'])
    else:
        subprocess.run(['qm', 'set', vm_id, '--ipconfig0', f"ip6={config['ipv6']},ip={config['ipv4']}"])
        # Use interactive credentials
        subprocess.run(['qm', 'set', vm_id, '--ciuser', username])
        subprocess.run(['qm', 'set', vm_id, '--cipassword', password])

        # save SSH key to temp file
        with open('temp_ssh_key.pub', 'w') as f:
            f.write(ssh_key)
        subprocess.run(['qm', 'set', vm_id, '--sshkey', 'temp_ssh_key.pub'])

    # resize disk
    subprocess.run(['qm', 'resize', vm_id, 'scsi0', config['disk_size']])

    # enable qemu-guest-agent
    subprocess.run(['qm', 'set', vm_id, '--agent', 'enabled=1,fstrim_cloned_disks=1'])

    # add tag
    
    subprocess.run(['qm', 'set', vm_id, '--tags', os_tag])

    # convert to template
    subprocess.run(['qm', 'template', vm_id])

    # cleanup
    subprocess.run(['rm', image_name])
    if not cloud_init_file:
        subprocess.run(['rm', 'temp_ssh_key.pub'])

def main():
    args = parse_arguments()
    
    config = {
        'memory': args.memory,
        'cores': args.cores,
        'sockets': args.sockets,
        'cpu': args.cpu,
        'disk_size': args.disk_size,
        'network_bridge': args.network_bridge,
        'ipv6': args.ipv6,
        'ipv4': args.ipv4,
        'prefix': args.prefix,
        'id_start': args.id_start,
    }
    
    clear_screen()
    
    # Ask user for cloud-init configuration method
    cloud_init_method = select_cloud_init_method()
    
    if cloud_init_method == 2:
        # User wants to use a cloud-init file
        cloud_init_file = select_cloud_init_file()
        print(f'Using cloud-init file: {cloud_init_file}')
        print('\n-----\n')
        username = None
        password = None
        ssh_key = None
    else:
        # User wants to enter credentials manually
        cloud_init_file = None
        username = get_username()
        password = get_password()
        ssh_key = get_ssh_key()
    
    storage = select_storage()
    
    # Use multi-selection interface
    selected_combinations = select_os_versions_multi()
    
    if not selected_combinations:
        print('No OS/version combinations selected. Exiting.')
        sys.exit(0)
    
    clear_screen()
    print(f'Creating {len(selected_combinations)} template(s)...\n')
    
    # Create templates for all selected combinations
    current_id = config['id_start']
    for idx, (distro_name, version_choice) in enumerate(selected_combinations, 1):
        print(f'\n{"="*60}')
        print(f'Processing template {idx}/{len(selected_combinations)}: {distro_name} / {IMAGES[distro_name]["versions"][version_choice]["name"]}')
        print(f'{"="*60}\n')
        
        vm_id = generate_unique_id(current_id)
        current_id = int(vm_id) + 1  # Increment for next template
        
        image_url = IMAGES[distro_name]['versions'][version_choice]['url']
        image_name = download_image(image_url)
        image_name = decompress_image(image_name)
        
        name = generate_template_name(distro_name, version_choice, config['prefix'])
        
        create_template(vm_id, name, image_name, storage, username, password, ssh_key, config, cloud_init_file)
        
        print(f'\nTemplate {name} (ID: {vm_id}) created successfully!\n')
    
    print(f'\n{"="*60}')
    print(f'All {len(selected_combinations)} template(s) created successfully!')
    print(f'{"="*60}\n')


if __name__ == '__main__':
    main()