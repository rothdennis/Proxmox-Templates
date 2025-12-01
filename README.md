# Proxmox Templates

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python tool for automating the creation of cloud-init enabled VM templates in Proxmox VE. Simplifies downloading official cloud images and converting them into ready-to-use templates.

![Proxmox Templates Screenshot](img/screenshot1.png)

## Features

- Automated template creation from cloud images
- Automatic VM ID assignment (starting at 900)
- Smart storage selection from available pools
- Cloud-init support with SSH key integration
- Support for 15+ operating systems (Linux & BSD)
- Interactive command-line interface
- QEMU guest agent pre-configured
- Automatic cleanup of temporary files

## Prerequisites

- Proxmox VE 7.0 or higher
- Python 3
- Root or sudo access
- Sufficient storage space
- Internet connection
- SSH public key (recommended)

## Quick Start

SSH into your Proxmox node and run:

```bash
python3 <(curl -s https://raw.githubusercontent.com/rothdennis/Proxmox-Templates/main/generate.py)
```

Or download first:

```bash
wget https://raw.githubusercontent.com/rothdennis/Proxmox-Templates/main/generate.py
python3 generate.py
```

Follow the interactive prompts to:
1. Choose cloud-init method (manual credentials or cloud-init file)
2. Enter credentials manually OR select a cloud-init file from snippet storage
3. Select storage pool
4. Choose OS and version

The script automatically assigns the next available VM ID starting at 900.

## Supported Operating Systems

| OS | Versions |Images|
|:---|:--|:--|
| [**Alpine**](https://alpinelinux.org/) | 3.22, 3.21, 3.20 | [Link](https://alpinelinux.org/cloud/) |
| [**Alma Linux**](https://almalinux.org/) | 10, 9, 8 | [Link](https://almalinux.org/get-almalinux/#Cloud_Images) |
| [**Amazon Linux**](https://aws.amazon.com/de/linux/) | 2023<br>2 | [Link](https://cdn.amazonlinux.com/al2023/os-images/latest/)<br>[Link](https://cdn.amazonlinux.com/os-images/latest/)  |
| [**Arch Linux**](https://archlinux.org/) | Latest | [Link](https://mirror.pkgbuild.com/images/latest/) |
| [**CentOS Stream**](https://www.centos.org/) | 10, 9 | [Link](https://cloud.centos.org/centos/) |
| [**Debian**](https://www.debian.org/) | 13 (Trixie), 12 (Bookworm) | [Link](https://cloud.debian.org/images/cloud/) |
| [**Fedora**](https://getfedora.org/) | Cloud 43 | [Link](https://fedoraproject.org/cloud/download) |
| [**Flatcar Container Linux**](https://flatcar-linux.org/) | Stable, Beta, Alpha | [Link](https://www.flatcar.org/releases) |
| [**FreeBSD**](https://www.freebsd.org/) | 14.3 | [Link](https://download.freebsd.org/releases/VM-IMAGES/) |
| [**Gentoo Linux**](https://www.gentoo.org/) | 20251130 | [Link](https://www.gentoo.org/downloads/#other-arches) |
| [**Kali Linux**](https://www.kali.org/) | 2025.3 | [Link](https://www.kali.org/get-kali/#kali-cloud) |
| [**openSUSE**](https://www.opensuse.org/) | Tumbleweed | [Link](https://get.opensuse.org/tumbleweed/?type=server#download) |
| [**Oracle Linux**](https://www.oracle.com/linux/) | 10.0, 9.6, 8.10, 7.9 | [Link](https://yum.oracle.com/oracle-linux-templates.html) |
| [**Rocky Linux**](https://rockylinux.org/) | 10, 9, 8 | [Link](https://rockylinux.org/download) |
| [**Ubuntu**](https://ubuntu.com/) | 25.10, 25.04, 24.04 LTS, 22.04 LTS | [Link](https://cloud-images.ubuntu.com/) |

## Template Specifications

| Component | Default Configuration |
|-----------|----------------------|
| Memory | 1 GB |
| CPU | 2 cores, 1 socket, host type |
| Network | VirtIO on vmbr0 |
| Disk | 10 GB, VirtIO SCSI |
| Cloud-Init | Enabled with SSH keys |
| Guest Agent | Enabled |

## Using Templates

**Via Web UI:**
- Right-click template → Clone → Full Clone
- Set VM ID and name
- Customize settings as needed

**Via CLI:**
```bash
qm clone <template-id> <new-vm-id> --name <vm-name> --full
```

**Resize disk after cloning:**
```bash
qm resize <vm-id> scsi0 +10G
```

## Customizing Defaults

To change default settings you can modify the script parameters:

```bash
# python3 generate.py --help
usage: Proxmox VM Template Generator [-h] [--memory MEMORY] [--cores CORES] [--sockets SOCKETS] [--disk-size DISK_SIZE] [--cpu CPU] [--network-bridge NETWORK_BRIDGE] [--ipv4 IPV4] [--ipv6 IPV6] [--prefix PREFIX] [--id-start ID_START]

Generate Proxmox VM templates from cloud images with custom configurations.

options:
  -h, --help            show this help message and exit
  --memory MEMORY       set the memory size in MB (default: 1024)
  --cores CORES         set the number of CPU cores (default: 2)
  --sockets SOCKETS     set the number of CPU sockets (default: 1)
  --disk-size DISK_SIZE
                        set the disk size (default: 10G)
  --cpu CPU             set the CPU type (default: host)
  --network-bridge NETWORK_BRIDGE
                        set the network bridge (default: vmbr0)
  --ipv4 IPV4           set the IPv4 configuration (default: dhcp)
  --ipv6 IPV6           set the IPv6 configuration (default: auto)
  --prefix PREFIX       set the prefix for VM template names (default: template)
  --id-start ID_START   set the starting ID for VM templates (default: 900)
```

### Using a Custom Cloud-Init File

When running the script, you will be prompted to choose between:
1. **Enter credentials manually** - Enter username, password, and SSH key interactively
2. **Use a cloud-init file** - Select from available cloud-init files in snippet-enabled storage pools

If you choose to use a cloud-init file, the script will list all `.yaml` and `.yml` files found in the snippets directory of storage pools that support the `snippets` content type. Files are displayed in the Proxmox volume format (e.g., `local:snippets/userconfig.yaml`).

To add cloud-init files for selection:
1. Ensure you have a storage pool with `snippets` content type enabled
2. Place your cloud-init YAML files in the storage's snippets directory
3. Run the script and select option 2 to choose from available files

Example cloud-init user-data file:

```yaml
#cloud-config
users:
  - name: myuser
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ssh-rsa AAAA...your-public-key...
```

## Troubleshooting

**Storage not found:**
- Check available storage: `pvesm status`
- Ensure storage is enabled and mounted

**Download fails:**
- Check internet connectivity
- Verify Proxmox can reach external URLs
- Try again

**Insufficient disk space:**
- Free up space or choose different storage
- Cloud images typically need 2-5GB during download

**Template not visible:**
- Refresh Proxmox web interface
- Check correct node in tree view

**Check logs:**
```bash
tail -f /var/log/pve/tasks/active
```

## Contributing

Contributions welcome! Please:
- Report issues on GitHub
- Submit pull requests with clear descriptions
- Test changes on Proxmox
- Update documentation

## Credits

- Based on [this project](https://www.apalrd.net/posts/2023/pve_cloud/) by apalrd
- Cloud images provided by respective Linux distributions

---

**Note:** Unofficial tool, not affiliated with Proxmox Server Solutions GmbH or any Linux distributions.

Made with ❤️ for the Proxmox community