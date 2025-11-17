# Proxmox Templates

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python tool for automating the creation of cloud-init enabled VM templates in Proxmox VE. Simplifies downloading official cloud images and converting them into ready-to-use templates.

![Proxmox Templates Screenshot](img/screenshot1.png)

## Features

- Automated template creation from cloud images
- Automatic VM ID assignment (starting at 900)
- Smart storage selection from available pools
- Cloud-init support with SSH key integration
- Support for 10+ Linux distributions
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
1. Enter username (default: root)
2. Set password
3. Paste SSH public key
4. Select storage pool
5. Choose OS and version

The script automatically assigns the next available VM ID starting at 900.

## Supported Operating Systems

| OS | Versions |
|:---|:---------|
| **Alpine** | 3.22, 3.21, 3.20 |
| **Alma Linux** | 10, 9, 8 |
| **Amazon Linux** | 2023, 2 |
| **Arch Linux** | Latest |
| **CentOS Stream** | 10, 9 |
| **Debian** | 13 (Trixie), 12 (Bookworm) |
| **Fedora** | Cloud 43 |
| **Kali Linux** | 2025.3 |
| **openSUSE** | Tumbleweed |
| **Oracle Linux** | 10.0, 9.6, 8.10, 7.9 |
| **Rocky Linux** | 10, 9, 8 |
| **Ubuntu** | 25.10, 25.04, 24.04 LTS, 22.04 LTS |

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

Edit these constants at the top of `generate.py`:

```python
MEMORY = 2048              # Change memory (default: 1024)
CORES = 4                  # Change CPU cores (default: 2)
DISK_SIZE = '20G'          # Change disk size (default: '10G')
NETWORK_BRIDGE = 'vmbr1'   # Change network bridge (default: 'vmbr0')
PREFIX = 'my-template'     # Change template name prefix (default: 'template')
ID_START = 1000            # Change starting VM ID (default: 900)
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

## License

MIT License - see LICENSE file for details

## Support

- **Issues:** [GitHub Issues](https://github.com/rothdennis/Proxmox-Templates/issues)
- **Documentation:** [Anthropic API Docs](https://docs.claude.com)

---

**Note:** Unofficial tool, not affiliated with Proxmox Server Solutions GmbH or any Linux distributions.

Made with ❤️ for the Proxmox community