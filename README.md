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

> **Note:** The operating system images and their download URLs are now maintained in the [`images.json`](images.json) configuration file. This allows for easier updates and maintenance of supported distributions without modifying the main script.

- Alma Linux
- Alpine Linux
- Amazon Linux
- Arch Linux
- CentOS Stream
- Debian
- Fedora Cloud
- Flatcar Container Linux
- FreeBSD
- Kali Linux
- openSUSE tumbleweed
- Oracle Linux
- Rocky Linux
- Ubuntu

### Gentoo Linux (Manual Configuration Required)

Gentoo Linux cloud images are available but use timestamped URLs that change frequently, making them difficult to maintain in an automated fashion. If you'd like to use Gentoo, you can manually add it to your local `images.json` file:

1. Visit [Gentoo's autobuilds directory](https://distfiles.gentoo.org/releases/amd64/autobuilds/current-di-amd64-cloudinit/)
2. Find the latest `di-amd64-cloudinit-YYYYMMDDTHHMMSSZ.qcow2` file
   - Alternatively, run the included `find_gentoo_url.py` helper script to automatically discover the current URL
3. Add the following entry to your `images.json`:

```json
"Gentoo Linux": {
    "tag": "gentoo",
    "versions": [
        {
            "name": "YYYY-MM-DD",
            "url": "https://distfiles.gentoo.org/releases/amd64/autobuilds/current-di-amd64-cloudinit/di-amd64-cloudinit-YYYYMMDDTHHMMSSZ.qcow2"
        }
    ]
}
```

**Note:** Once Gentoo is added to `images.json`, the `generate.py` script will automatically configure Gentoo templates with the required UEFI/OVMF BIOS and EFI disk settings.

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