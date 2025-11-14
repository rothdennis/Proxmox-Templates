import urllib.request
import lzma
import shutil
import sys
import subprocess

username = input('Enter username: ')
print('\n-----\n')
ssh_key = input('Enter SSH key: ')
print('\n-----\n')
storage= input('Enter storage (local-lvm): ') or 'local-lvm'
print('\n-----\n')
id= input('Enter VM ID: ')
print('\n-----\n')

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

def generate_template():
    print(f'Generating template ...')

    # create new vm
    subprocess.run(['qm', 'create', id, '--name', name, '--ostype', 'l26'])
    # set networking to default bridge
    subprocess.run(['qm', 'set', id, '--net0', 'virtio,bridge=vmbr0'])
    # set memory, cpu, type defaults
    subprocess.run(['qm', 'set', id, '--memory', '1024', '--cores', '2', '--sockets', '1', '--cpu', 'host'])
    # set boot device to new file
    subprocess.run(['qm', 'set', id, '--scsi0', f'{storage}:0,import-from={image_name},discard=on'])
    # set scsi hardware as default boot disk using virtio scsi single
    subprocess.run(['qm', 'set', id, '--boot', 'order=scsi0', '--scsihw', 'virtio-scsi-single'])
    # enable Qemu guest agent in case the guest has it available
    subprocess.run(['qm', 'set', id, '--agent', 'enabled=1,fstrim_cloned_disks=1'])
    # add cloud-init device
    subprocess.run(['qm', 'set', id, '--ide2', f'{storage}:cloudinit'])
    # set CI ip config
    subprocess.run(['qm', 'set', id, '--ipconfig0', 'ip6=auto,ip=dhcp'])
    # set ssh key
    subprocess.run(['qm', 'set', id, '--sshkey', ssh_key])
    # set username
    subprocess.run(['qm', 'set', id, '--ciuser', username])
    # resize the disk to 10G
    subprocess.run(['qm', 'resize', id, 'scsi0', '10G'])
    # finally convert to template
    subprocess.run(['qm', 'template', id])

    # delete downloaded image
    subprocess.run(['rm', image_name])
                

images = {
    'Ubuntu':[
        {'22.04': 'https://cloud-images.ubuntu.com/releases/22.04/release/ubuntu-22.04-server-cloudimg-amd64.img'},
        {'24.04': 'https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64.img'}
    ],
    'Debian':[
        {'12': 'https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-genericcloud-amd64.qcow2'},
        {'13': 'https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2'}
    ],
    'Fedora':[
        {'43': 'https://download.fedoraproject.org/pub/fedora/linux/releases/43/Cloud/x86_64/images/Fedora-Cloud-Base-Generic-43-1.6.x86_64.qcow2'}
    ],
    'Rocky':[
        {'8': 'https://dl.rockylinux.org/pub/rocky/8/images/x86_64/Rocky-8-GenericCloud-Base.latest.x86_64.qcow2'},
        {'9': 'https://dl.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud-Base.latest.x86_64.qcow2'},
        {'10': 'https://dl.rockylinux.org/pub/rocky/10/images/x86_64/Rocky-10-GenericCloud-Base.latest.x86_64.qcow2'},
    ],
    'Alpine':[
        {'3.20': 'https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/cloud/generic_alpine-3.20.8-x86_64-bios-cloudinit-r0.qcow2'},
        {'3.21': 'https://dl-cdn.alpinelinux.org/alpine/v3.21/releases/cloud/generic_alpine-3.21.5-x86_64-bios-cloudinit-r0.qcow2'},
        {'3.22': 'https://dl-cdn.alpinelinux.org/alpine/v3.22/releases/cloud/generic_alpine-3.22.2-x86_64-bios-cloudinit-r0.qcow2'},
    ],
    'FreeBSD':[
        {'14.3': 'https://download.freebsd.org/releases/VM-IMAGES/14.3-RELEASE/amd64/Latest/FreeBSD-14.3-RELEASE-amd64-BASIC-CLOUDINIT-ufs.qcow2.xz'}
    ]
    }

print('Select OS')
for i, disto in enumerate(images):
    print(f'{i+1}) {disto}')
distro_choice = int(input('Enter choice: ')) - 1

print('\n-----\n')

print('Select Version')
distro_name = list(images.keys())[distro_choice]
for i, version in enumerate(images[distro_name]):
    version_name = list(version.keys())[0]
    print(f'{i+1}) {version_name}')
version_choice = int(input('Enter choice: ')) - 1

print('\n-----\n')

# download image using wget
image_url = list(images[distro_name][version_choice].values())[0]
image_name = image_url.split('/')[-1]
print(f'Downloading image from {image_url} ...')
urllib.request.urlretrieve(image_url, image_name, reporthook=show_progress)

print('\n-----\n')

if image_name.endswith('.xz'):
    decompressed_name = image_name[:-3]
    print(f'Decompressing {image_name} to {decompressed_name} ...')
    with lzma.open(image_name) as f_in:
        with open(decompressed_name, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    image_name = decompressed_name

    print('\n-----\n')

name = f'template-{"-".join(distro_name.lower().split())}-{list(images[distro_name][version_choice].keys())[0].replace(".","-")}'
generate_template()