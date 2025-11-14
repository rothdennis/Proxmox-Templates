# Proxmox Templates

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python-based tool for automating the creation of cloud-init enabled VM templates in Proxmox VE. This script simplifies the process of downloading official cloud images and converting them into ready-to-use Proxmox templates with cloud-init support.

## 📋 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Supported Images](#-supported-images)
- [Detailed Usage](#-detailed-usage)
- [Configuration Options](#-configuration-options)
- [Template Specifications](#-template-specifications)
- [Troubleshooting](#-troubleshooting)
- [Advanced Usage](#-advanced-usage)
- [Contributing](#-contributing)
- [License](#-license)
- [Credits](#-credits)

## ✨ Features

- **Automated Template Creation**: Streamlines the process of creating VM templates from cloud images
- **Cloud-Init Support**: Pre-configured cloud-init setup for easy VM customization
- **Multiple OS Support**: Supports 10+ Linux distributions and FreeBSD
- **Interactive Interface**: User-friendly command-line prompts for easy configuration
- **SSH Key Integration**: Automatically configures SSH keys for secure access
- **QEMU Guest Agent**: Pre-configured for better VM management
- **Disk Optimization**: Includes discard support for efficient storage usage
- **Automatic Cleanup**: Removes temporary files after template creation

## 🔧 Prerequisites

Before using this tool, ensure you have:

- **Proxmox VE** server (version 7.0 or higher recommended)
- **Python 3** installed on your Proxmox host
- **Root or sudo access** to the Proxmox node
- **Storage** with sufficient space for downloading and storing images
- **Internet connection** for downloading cloud images
- **SSH public key** (optional but recommended for secure access)

### Required Proxmox Packages

The script uses Proxmox's `qm` command-line tool, which is installed by default on Proxmox VE.

## 🚀 Quick Start

1. **SSH into your Proxmox node** (or use the web console)

2. **Download and run the script**:

```bash
wget https://raw.githubusercontent.com/rothdennis/Proxmox-Templates/main/generate.py
python3 generate.py
```

3. **Follow the interactive prompts**:
   - Enter username (default: root)
   - Enter password (optional)
   - Paste your SSH public key
   - Select storage location (default: local-lvm)
   - Enter a unique VM ID
   - Choose OS distribution and version

4. **Wait for completion**: The script will download the image, create the template, and clean up temporary files.

![Screenshot](images/screenshot1.png)

## 📦 Supported Images

The script supports the following operating systems and versions:

| OS | Versions |
|:---|:---------|
| **Alpine** | 3.22, 3.21, 3.20 |
| **Alma Linux** | 10, 9, 8 |
| **CentOS Stream** | 10, 9 |
| **Debian** | 13 (Trixie), 12 (Bookworm) |
| **Fedora** | 43 |
| **FreeBSD** | 14.3 |
| **openSUSE** | Tumbleweed |
| **Oracle Linux** | 10.0, 9.6, 8.10, 7.9 |
| **Rocky Linux** | 10, 9, 8 |
| **Ubuntu** | 25.10, 25.04, 24.04 LTS, 22.04 LTS |

All images are official cloud images provided by the respective distributions and are optimized for cloud/virtualization environments.

## 📖 Detailed Usage

### Step-by-Step Guide

1. **Username Configuration**
   ```
   Enter username (root): myuser
   ```
   This sets the default cloud-init user. Press Enter to use 'root' as default.

2. **Password Setup**
   ```
   Enter password: ********
   ```
   Set a password for the cloud-init user. Can be left empty if using SSH keys only.

3. **SSH Key**
   ```
   Enter SSH key: ssh-rsa AAAAB3NzaC1yc2EA...
   ```
   Paste your SSH public key (from `~/.ssh/id_rsa.pub` or similar). This enables passwordless SSH access.

4. **Storage Selection**
   ```
   Enter storage (local-lvm): local-lvm
   ```
   Specify the Proxmox storage where the template will be created. Common options:
   - `local-lvm` (default, LVM thin)
   - `local` (directory storage)
   - `local-zfs` (ZFS)
   - Any other configured storage pool

5. **VM ID**
   ```
   Enter VM ID: 9000
   ```
   Choose a unique VM ID. Template IDs typically use high numbers (9000+) to distinguish them from regular VMs.

6. **OS Selection**
   ```
   Select OS
   1) Alpine
   2) Alma Linux
   3) CentOS Stream
   ...
   Enter choice: 10
   ```
   Select your desired operating system from the numbered list.

7. **Version Selection**
   ```
   Select Version
   1) 24.04
   2) 22.04
   Enter choice: 1
   ```
   Choose the specific version of the selected OS.

### What Happens Next

The script will:
1. Download the selected cloud image (progress bar shown)
2. Decompress the image if needed (for `.xz` files)
3. Create a new VM with the specified ID
4. Configure VM hardware (CPU, memory, network)
5. Import the cloud image as the VM's disk
6. Set up cloud-init configuration
7. Add your SSH key to the template
8. Resize the disk to 10GB
9. Enable QEMU guest agent
10. Convert the VM to a template
11. Clean up temporary files

## ⚙️ Configuration Options

### Template Name Format

Templates are automatically named using the format:
```
template-{os-name}-{version}
```

Examples:
- `template-ubuntu-24-04`
- `template-debian-12`
- `template-rocky-9`

### Default Template Specifications

The script creates templates with the following specifications:

- **Memory**: 1024 MB (1 GB)
- **CPU**: 2 cores, 1 socket, host CPU type
- **Network**: VirtIO network adapter on vmbr0
- **Disk**: 
  - SCSI disk on specified storage
  - Discard enabled for thin provisioning
  - Resized to 10GB
  - VirtIO SCSI single controller
- **Cloud-Init**: IDE2 drive for cloud-init configuration
- **Network Config**: DHCP for IPv4, auto for IPv6
- **Guest Agent**: Enabled with fstrim for cloned disks

## 📝 Template Specifications

### VM Hardware Configuration

| Component | Configuration |
|-----------|---------------|
| Memory | 1 GB (can be adjusted when cloning) |
| CPU | 2 cores, 1 socket, host type |
| Network | VirtIO on vmbr0 |
| Disk Controller | VirtIO SCSI Single |
| Disk Size | 10 GB (expandable) |
| Boot Order | SCSI0 (disk) |
| Guest Agent | Enabled |

### Cloud-Init Configuration

The template includes cloud-init support with:
- Custom username (default: root)
- Password authentication (optional)
- SSH key authentication
- DHCP network configuration
- IPv6 auto-configuration

### Using the Template

Once created, you can use the template to create new VMs:

1. **Via Web UI**:
   - Right-click the template in Proxmox
   - Select "Clone"
   - Choose "Full Clone"
   - Set new VM ID and name
   - Customize cloud-init settings if needed

2. **Via Command Line**:
   ```bash
   qm clone <template-id> <new-vm-id> --name <vm-name> --full
   ```

3. **Customize Before Starting**:
   - Adjust CPU/memory as needed
   - Resize disk: `qm resize <vm-id> scsi0 +10G`
   - Configure cloud-init in the Proxmox UI or via CLI

## 🔍 Troubleshooting

### Common Issues and Solutions

#### "VM ID already exists"
**Problem**: The VM ID you entered is already in use.  
**Solution**: Choose a different VM ID (unused numbers typically 100+ or 9000+).

#### "Storage not found"
**Problem**: The specified storage doesn't exist.  
**Solution**: 
- Check available storage: `pvesm status`
- Use a valid storage name from the list

#### "Failed to download image"
**Problem**: Network issues or broken image URL.  
**Solution**:
- Check internet connectivity
- Verify Proxmox can reach external URLs
- Try again - downloads may occasionally fail

#### "Permission denied"
**Problem**: Script doesn't have necessary permissions.  
**Solution**: 
- Ensure you're running as root or with sudo
- Check storage permissions

#### "Insufficient disk space"
**Problem**: Not enough space in the storage pool.  
**Solution**:
- Free up space in the storage
- Choose a different storage location
- Cloud images typically need 2-5GB during download/extraction

#### Template not showing in Proxmox UI
**Problem**: Template was created but isn't visible.  
**Solution**:
- Refresh the Proxmox web interface
- Check the correct node in the tree view
- Templates are marked with a special icon

### Debug Mode

For detailed output, you can modify the script to print command outputs:
```python
# Change subprocess.run to include stdout
subprocess.run(['qm', 'create', ...], capture_output=True, text=True)
```

### Logs

Check Proxmox logs for detailed information:
```bash
tail -f /var/log/pve/tasks/active
```

## 🎯 Advanced Usage

### Customizing Template Specifications

You can modify the `generate.py` script to customize template specifications:

#### Change Default Memory/CPU
```python
subprocess.run(['qm', 'set', id, '--memory', '2048', '--cores', '4', '--sockets', '1'])
```

#### Change Disk Size
```python
subprocess.run(['qm', 'resize', id, 'scsi0', '20G'])  # Instead of 10G
```

#### Use Different Network Bridge
```python
subprocess.run(['qm', 'set', id, '--net0', 'virtio,bridge=vmbr1'])
```

#### Add Additional Disks
```python
subprocess.run(['qm', 'set', id, '--scsi1', f'{storage}:32,discard=on'])
```

### Automation

For automated template creation without interactive prompts, you can modify the script or provide inputs via pipe:

```bash
echo -e "myuser\nmypass\nssh-rsa AAA...\nlocal-lvm\n9000\n10\n1" | python3 generate.py
```

### Batch Template Creation

Create a wrapper script to generate multiple templates:

```bash
#!/bin/bash
for id in 9001 9002 9003; do
    echo "Creating template $id..."
    # Run generate.py with different parameters
done
```

### Integration with Infrastructure as Code

The script can be integrated into automation tools:
- **Ansible**: Use the `script` or `command` module
- **Terraform**: Use `null_resource` with local-exec provisioner
- **Packer**: Create custom Packer builders using this script

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report Issues**: Found a bug or have a suggestion? Open an issue on GitHub
2. **Submit Pull Requests**: 
   - Fork the repository
   - Create a feature branch
   - Make your changes
   - Submit a PR with a clear description
3. **Add OS Support**: Know of other cloud images that should be supported? Add them!
4. **Improve Documentation**: Help make this README even better
5. **Share Feedback**: Let us know how you're using this tool

### Guidelines

- Test your changes on a Proxmox environment
- Keep the code style consistent
- Update documentation for new features
- Ensure backward compatibility when possible

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ❌ Liability
- ❌ Warranty

## 🙏 Credits

- **Original Concept**: Based on [this project](https://www.apalrd.net/posts/2023/pve_cloud/) by apalrd
- **Cloud Images**: Provided by respective Linux distributions
- **Proxmox VE**: The excellent virtualization platform that makes this possible

---

**Note**: This is an unofficial tool and is not affiliated with or endorsed by Proxmox Server Solutions GmbH or any of the Linux distributions mentioned.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/rothdennis/Proxmox-Templates/issues)
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Pull Requests**: Contributions welcome!

---

Made with ❤️ for the Proxmox community
