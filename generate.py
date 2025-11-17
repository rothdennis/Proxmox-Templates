import urllib.request
import lzma
import shutil
import sys
import subprocess
from getpass import getpass

### CONSTANTS ###

MEMORY = 1024
CORES = 2
SOCKETS = 1
CPU = 'host'
DISK_SIZE = '10G'
NETWORK_BRIDGE = 'vmbr0'
IPV6 = 'auto'
IPV4 = 'dhcp'
PREFIX='template'
ID_START=900

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

### INPUTS ###

username = input('Enter username (root): ') or 'root'
print('\n-----\n')
password = getpass('Enter password: ') or ''
print('\n-----\n')
ssh_key = input('Enter SSH key: ')
print('\n-----\n')
res = subprocess.run("pvesm status | awk 'NR>1 {print $1}'", capture_output=True, text=True, shell=True)
available_storages = res.stdout.strip().split('\n')
print('Select storage\n')
for i, storage in enumerate(available_storages):
    print(f'{i+1}) {storage}')
storage_choice = int(input('\nEnter choice: ')) - 1
storage = available_storages[storage_choice]
print('\n-----\n')
res = subprocess.run("qm list | awk 'NR>1 {print $1}'", capture_output=True, text=True, shell=True)
used_ids = set(map(int, res.stdout.strip().split('\n')))
while ID_START in used_ids:
    ID_START += 1
id = str(ID_START)
# id= input('Enter VM ID: ')
# print('\n-----\n')

print('Select OS\n')
for i, disto in enumerate(IMAGES):
    print(f'{i+1}) {disto}')
distro_choice = int(input('\nEnter choice: ')) - 1

print('\n-----\n')

print('Select Version\n')
distro_name = list(IMAGES.keys())[distro_choice]
for i, version in enumerate(IMAGES[distro_name]):
    version_name = list(version.keys())[0]
    print(f'{i+1}) {version_name}')
version_choice = int(input('\nEnter choice: ')) - 1

print('\n-----\n')

### DOWNLOAD IMAGE ###
image_url = list(IMAGES[distro_name][version_choice].values())[0]
image_name = image_url.split('/')[-1]
print(f'Downloading image from {image_url} ...')
urllib.request.urlretrieve(image_url, image_name, reporthook=show_progress)

print('\n-----\n')

### DECOMPRESS IMAGE IF NEEDED ###

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
    image_name = disk_file
elif image_name.endswith('.xz'):
    decompressed_name = image_name[:-3] # remove .xz
    print(f'Decompressing {image_name} to {decompressed_name} ...')
    with lzma.open(image_name) as f_in:
        with open(decompressed_name, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    subprocess.run(['rm', image_name])
    image_name = decompressed_name

    print('\n-----\n')

### GENERATE NAME ###

os_name = distro_name.lower().replace(' ', '-')
os_version = list(IMAGES[distro_name][version_choice].keys())[0].lower().replace(' ', '-').replace('.', '-')
name = f'{PREFIX}-{os_name}-{os_version}'

### GENERATE TEMPLATE ###

print(f'Generating template ...')

# create VM
subprocess.run(['qm', 'create', id, '--name', name, '--ostype', 'l26'])
subprocess.run(['qm', 'set', id, '--net0', f'virtio,bridge={NETWORK_BRIDGE}'])
subprocess.run(['qm', 'set', id, '--memory', str(MEMORY), '--cores', str(CORES), '--sockets', str(SOCKETS), '--cpu', CPU])

# import disk
format = 'qcow2' if image_name.endswith('.qcow2') or image_name.endswith('.img') else 'raw'
subprocess.run(['qm', 'importdisk', id, image_name, storage, '--format', format])
subprocess.run(['qm', 'set', id, '--scsi0', f'{storage}:vm-{id}-disk-0,discard=on'])
subprocess.run(['qm', 'set', id, '--boot', 'order=scsi0', '--scsihw', 'virtio-scsi-single'])

# cloud-init
subprocess.run(['qm', 'set', id, '--ide2', f'{storage}:cloudinit'])
subprocess.run(['qm', 'set', id, '--ipconfig0', f'ip6={IPV6},ip={IPV4}'])
subprocess.run(['qm', 'set', id, '--ciuser', username])
subprocess.run(['qm', 'set', id, '--cipassword', password])

# save SSH key to temp file
with open('temp_ssh_key.pub', 'w') as f:
    f.write(ssh_key)
subprocess.run(['qm', 'set', id, '--sshkey', 'temp_ssh_key.pub'])

# resize disk
subprocess.run(['qm', 'resize', id, 'scsi0', DISK_SIZE])

# enable qemu-guest-agent
subprocess.run(['qm', 'set', id, '--agent', 'enabled=1,fstrim_cloned_disks=1'])

# add tag
subprocess.run(['qm', 'set', id, '--tags', os_name.split('-')[0]])

# convert to template
subprocess.run(['qm', 'template', id])

# cleanup
subprocess.run(['rm', image_name])
subprocess.run(['rm', 'temp_ssh_key.pub'])