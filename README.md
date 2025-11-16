# Proxmox Templates

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python-based tool for automating the creation of cloud-init enabled VM templates in Proxmox VE. This script simplifies the process of downloading official cloud images and converting them into ready-to-use Proxmox templates with cloud-init support.

## Features

- **Automated Template Creation**: Streamlines the process of creating VM templates from cloud images
- **Automatic VM ID Assignment**: Intelligently detects and assigns the next available VM ID (starting at 900)
- **Smart Storage Selection**: Displays available storage pools for easy selection
- **Cloud-Init Support**: Pre-configured cloud-init setup for easy VM customization
- **Multiple OS Support**: Supports 10+ Linux distributions
- **Interactive Interface**: User-friendly command-line prompts for easy configuration
- **SSH Key Integration**: Automatically configures SSH keys for secure access
- **QEMU Guest Agent**: Pre-configured for better VM management
- **Disk Optimization**: Includes discard support for efficient storage usage
- **Automatic Cleanup**: Removes temporary files after template creation

## Prerequisites

Before using this tool, ensure you have:

- **Proxmox VE** server (version 7.0 or higher recommended)
- **Python 3** installed on your Proxmox host
- **Root or sudo access** to the Proxmox node
- **Storage** with sufficient space for downloading and storing images
- **Internet connection** for downloading cloud images
- **SSH public key** (optional but recommended for secure access)

### Required Proxmox Packages

The script uses Proxmox's `qm` command-line tool, which is installed by default on Proxmox VE.

## Quick Start

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
   - Select storage from the displayed list of available options
   - Choose OS distribution and version
   - VM ID is automatically assigned (starting at 900)

4. **Wait for completion**: The script will download the image, create the template, and clean up temporary files.

## Supported Images

The script supports the following operating systems and versions:

| OS | Versions |
|:---|:---------|
| **Alpine** | 3.22, 3.21, 3.20 |
| **Alma Linux** | 10, 9, 8 |
| **Arch Linux** | Latest |
| **CentOS Stream** | 10, 9 |
| **Debian** | 13 (Trixie), 12 (Bookworm) |
| **Fedora** | 43 |
| **openSUSE** | Tumbleweed |
| **Oracle Linux** | 10.0, 9.6, 8.10, 7.9 |
| **Rocky Linux** | 10, 9, 8 |
| **Ubuntu** | 25.10, 25.04, 24.04 LTS, 22.04 LTS |

All images are official cloud images provided by the respective distributions and are optimized for cloud/virtualization environments.

## Detailed Usage

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
   Select storage

   1) local-lvm
   2) local
   3) local-zfs

   Enter choice: 1
   ```
   The script displays a list of all available storage pools on your Proxmox system. Select the storage where the template will be created by entering the corresponding number. Common storage types include:
   - `local-lvm` (LVM thin provisioning)
   - `local` (directory storage)
   - `local-zfs` (ZFS storage)
   - Any other configured storage pools

5. **OS Selection**
   ```
   Select OS
   1) Alpine
   2) Alma Linux
   3) CentOS Stream
   ...
   Enter choice: 10
   ```
   Select your desired operating system from the numbered list.

6. **Version Selection**
   ```
   Select Version
   1) 24.04
   2) 22.04
   Enter choice: 1
   ```
   Choose the specific version of the selected OS.

### Automatic VM ID Assignment

The script automatically detects the next available VM ID starting from 900. It checks existing VMs and assigns the first unused ID, ensuring no conflicts. This eliminates the need to manually track VM IDs and prevents accidental overwrites.

### What Happens Next

The script will:
1. Detect the next available VM ID (starting at 900)
2. Download the selected cloud image (progress bar shown)
3. Decompress the image if needed (for `.xz` files)
4. Create a new VM with the automatically assigned ID
5. Configure VM hardware (CPU, memory, network)
6. Import the cloud image as the VM's disk
7. Set up cloud-init configuration
8. Add your SSH key to the template
9. Resize the disk to 10GB
10. Enable QEMU guest agent
11. Convert the VM to a template
12. Clean up temporary files

## Configuration Options

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

## Template Specifications

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

## Troubleshooting

### Common Issues and Solutions

#### "VM ID already exists"
**Problem**: In rare cases, the automatic VM ID detection might fail if a VM is created between the check and template creation.  
**Solution**: Run the script again. It will automatically detect the next available ID. If the problem persists, you can manually verify available IDs with `qm list`.

#### "Storage not found"
**Problem**: Selected storage doesn't exist or isn't accessible.  
**Solution**: 
- Check available storage: `pvesm status`
- Ensure the storage is enabled and mounted
- Select a different storage option from the list when prompted

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

## Advanced Usage

### Customizing Template Specifications

You can modify the constants at the top of the `generate.py` script to customize default template specifications:

#### Change Default Memory/CPU
```python
MEMORY = 2048  # Default is 1024
CORES = 4      # Default is 2
SOCKETS = 1
CPU = 'host'
```

#### Change Disk Size
```python
DISK_SIZE = '20G'  # Default is 10G
```

#### Use Different Network Bridge
```python
NETWORK_BRIDGE = 'vmbr1'  # Default is vmbr0
```

#### Change Network Configuration
```python
IPV6 = 'auto'  # Default is auto
IPV4 = 'dhcp'  # Default is dhcp
```

#### Change Template Naming Prefix
```python
PREFIX = 'my-template'  # Default is 'template'
```

#### Change Starting VM ID
```python
ID_START = 1000  # Default is 900
```

### Automation

For automated template creation without interactive prompts, you can modify the script or provide inputs via pipe:

```bash
echo -e "myuser\nmypass\nssh-rsa AAA...\n1\n10\n1" | python3 generate.py
```

Note: The inputs are now (in order):
1. Username
2. Password
3. SSH key
4. Storage choice number (e.g., 1 for first storage option)
5. OS choice number
6. Version choice number

The VM ID is automatically assigned and no longer needs to be provided.

### Batch Template Creation

Create a wrapper script to generate multiple templates:

```bash
#!/bin/bash
# IDs are automatically assigned starting at 900
for os_choice in 1 2 3; do
    echo "Creating template for OS choice $os_choice..."
    # Run generate.py with different parameters
    # Each run will get the next available ID automatically
done
```

### Integration with Infrastructure as Code

The script can be integrated into automation tools:
- **Ansible**: Use the `script` or `command` module
- **Terraform**: Use `null_resource` with local-exec provisioner
- **Packer**: Create custom Packer builders using this script

## Contributing

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

## Credits

- **Original Concept**: Based on [this project](https://www.apalrd.net/posts/2023/pve_cloud/) by apalrd
- **Cloud Images**: Provided by respective Linux distributions
- **Proxmox VE**: The excellent virtualization platform that makes this possible

---

**Note**: This is an unofficial tool and is not affiliated with or endorsed by Proxmox Server Solutions GmbH or any of the Linux distributions mentioned.

## Support

- **Issues**: [GitHub Issues](https://github.com/rothdennis/Proxmox-Templates/issues)
- **Pull Requests**: Contributions welcome!

---

Made with ❤️ for the Proxmox community
