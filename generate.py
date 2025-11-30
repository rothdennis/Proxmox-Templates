import urllib.request
import lzma
import shutil
import sys
import subprocess
import tempfile
import os
from getpass import getpass
import argparse

### IMAGES ###

IMAGES = {
    'Alma Linux':[
        {'10': 'https://repo.almalinux.org/almalinux/10/cloud/x86_64/images/AlmaLinux-10-GenericCloud-latest.x86_64.qcow2'},
        {'9': 'https://repo.almalinux.org/almalinux/9/cloud/x86_64/images/AlmaLinux-9-GenericCloud-latest.x86_64.qcow2'},
        {'8': 'https://repo.almalinux.org/almalinux/8/cloud/x86_64/images/AlmaLinux-8-GenericCloud-8.10-20240530.x86_64.qcow2'},
    ],
    'Alpine Linux':[
        {'3.22': 'https://dl-cdn.alpinelinux.org/alpine/v3.22/releases/cloud/generic_alpine-3.22.2-x86_64-bios-cloudinit-r0.qcow2'},
        {'3.21': 'https://dl-cdn.alpinelinux.org/alpine/v3.21/releases/cloud/generic_alpine-3.21.5-x86_64-bios-cloudinit-r0.qcow2'},
        {'3.20': 'https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/cloud/generic_alpine-3.20.8-x86_64-bios-cloudinit-r0.qcow2'},
    ],
    'Amazon Linux':[
        {'2023': 'https://cdn.amazonlinux.com/al2023/os-images/2023.9.20251110.1/kvm/al2023-kvm-2023.9.20251110.1-kernel-6.1-x86_64.xfs.gpt.qcow2'},
        {'2': 'https://cdn.amazonlinux.com/os-images/2.0.20251110.1/kvm/amzn2-kvm-2.0.20251110.1-x86_64.xfs.gpt.qcow2'},
    ],
    'Arch Linux':[
        {'Latest': 'https://fastly.mirror.pkgbuild.com/images/latest/Arch-Linux-x86_64-cloudimg.qcow2'},
    ],
    'CentOS Stream':[
        {'10': 'https://cloud.centos.org/centos/10-stream/x86_64/images/CentOS-Stream-GenericCloud-10-latest.x86_64.qcow2'},
        {'9': 'https://cloud.centos.org/centos/9-stream/x86_64/images/CentOS-Stream-GenericCloud-x86_64-9-latest.x86_64.qcow2'},
    ],
    'Debian':[
        {'13': 'https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2'},
        {'12': 'https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-genericcloud-amd64.qcow2'},
    ],
    'Fedora':[
        {'Cloud 43': 'https://download.fedoraproject.org/pub/fedora/linux/releases/43/Cloud/x86_64/images/Fedora-Cloud-Base-Generic-43-1.6.x86_64.qcow2'},
    ],
    'Kali Linux':[
        {'2025.3': 'https://kali.download/cloud-images/kali-2025.3/kali-linux-2025.3-cloud-genericcloud-amd64.tar.xz'},
    ],
    'openSUSE':[
        {'Tumbleweed':'https://download.opensuse.org/tumbleweed/appliances/openSUSE-Tumbleweed-Minimal-VM.x86_64-Cloud.qcow2'},
    ],
    'Oracle Linux':[
        {'10.0': 'https://yum.oracle.com/templates/OracleLinux/OL10/u0/x86_64/OL10U0_x86_64-kvm-b266.qcow2'},
        {'9.6': 'https://yum.oracle.com/templates/OracleLinux/OL9/u6/x86_64/OL9U6_x86_64-kvm-b265.qcow2'},
        {'8.10': 'https://yum.oracle.com/templates/OracleLinux/OL8/u10/x86_64/OL8U10_x86_64-kvm-b258.qcow2'},
        {'7.9': 'https://yum.oracle.com/templates/OracleLinux/OL7/u9/x86_64/OL7U9_x86_64-kvm-b257.qcow2'},
    ],
    'Rocky Linux':[
        {'10': 'https://dl.rockylinux.org/pub/rocky/10/images/x86_64/Rocky-10-GenericCloud-Base.latest.x86_64.qcow2'},
        {'9': 'https://dl.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud-Base.latest.x86_64.qcow2'},
        {'8': 'https://dl.rockylinux.org/pub/rocky/8/images/x86_64/Rocky-8-GenericCloud-Base.latest.x86_64.qcow2'},
    ],
    'Ubuntu':[
        {'25.10': 'https://cloud-images.ubuntu.com/releases/25.10/release/ubuntu-25.10-server-cloudimg-amd64.img'},
        {'25.04': 'https://cloud-images.ubuntu.com/releases/25.04/release/ubuntu-25.04-server-cloudimg-amd64.img'},
        {'24.04': 'https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64.img'},
        {'22.04': 'https://cloud-images.ubuntu.com/releases/22.04/release/ubuntu-22.04-server-cloudimg-amd64.img'},   
    ],    
    }

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
    res = subprocess.run("pvesm status | awk 'NR>1 {print $1}'", capture_output=True, text=True, shell=True)
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
        
        # Get the path for this storage using list form to avoid shell injection
        res = subprocess.run(['pvesm', 'path', f'{storage}:snippets/'], 
                           capture_output=True, text=True)
        storage_path = res.stdout.strip()
        
        # Validate storage_path is an absolute path and exists
        if not storage_path or not os.path.isabs(storage_path) or not os.path.isdir(storage_path):
            continue
        
        # Find all yaml/yml files in the snippets directory
        for filename in os.listdir(storage_path):
            # Validate filename contains no path separators
            if os.sep in filename or (os.altsep and os.altsep in filename):
                continue
            if filename.endswith(('.yaml', '.yml')):
                # Format: storage:snippets/filename.yaml
                volume_path = f"{storage}:snippets/{filename}"
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
    for i, version in enumerate(IMAGES[distro_name]):
        version_name = list(version.keys())[0]
        print(f'{i+1}) {version_name}')
    
    while True:
        try:
            version_choice = int(input('\nEnter choice: ')) - 1
            if 0 <= version_choice < len(IMAGES[distro_name]):
                break
            else:
                print('Invalid choice. Please try again.\n')
        except ValueError:
            print('Invalid input. Please enter a number.\n')
    print('\n-----\n')
    
    return version_choice

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
    os_version = list(IMAGES[distro_name][version_choice].keys())[0].lower().replace(' ', '-').replace('.', '-')
    return f'{prefix}-{os_name}-{os_version}'

def create_template(vm_id, name, image_name, storage, username, password, ssh_key, config, cloud_init_file=None):
    print(f'Generating template ...')

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

    # cloud-init
    subprocess.run(['qm', 'set', vm_id, '--ide2', f'{storage}:cloudinit'])
    subprocess.run(['qm', 'set', vm_id, '--ipconfig0', f"ip6={config['ipv6']},ip={config['ipv4']}"])
    
    if cloud_init_file:
        # Use custom cloud-init file
        subprocess.run(['qm', 'set', vm_id, '--cicustom', f'user={cloud_init_file}'])
    else:
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
    os_name = name.split('-')[1] if '-' in name else name
    subprocess.run(['qm', 'set', vm_id, '--tags', os_name])

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
    distro_name = select_os()
    version_choice = select_version(distro_name)
    
    vm_id = generate_unique_id(config['id_start'])
    
    image_url = list(IMAGES[distro_name][version_choice].values())[0]
    image_name = download_image(image_url)
    image_name = decompress_image(image_name)
    
    name = generate_template_name(distro_name, version_choice, config['prefix'])
    
    create_template(vm_id, name, image_name, storage, username, password, ssh_key, config, cloud_init_file)


if __name__ == '__main__':
    main()