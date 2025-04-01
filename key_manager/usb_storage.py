"""
Module for handling USB storage operations related to cryptographic keys.
"""

import os
import platform
import psutil
import string

class UsbStorage:
    """
    Class providing methods for detecting USB drives and reading/writing data to them.
    """
    
    @staticmethod
    def get_usb_drives():
        """
        Detect and list available USB drives. Works both on Windows and Linux operating systems

        Returns:
            list: List of paths to detected USB drives.
        """
        usb_drives = []
        
        if platform.system() == 'Windows':
            drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
            for drive in drives:
                try:
                    if psutil.disk_partitions(all=True):
                        for partition in psutil.disk_partitions(all=True):
                            if partition.device == drive and 'removable' in partition.opts.lower():
                                usb_drives.append(drive)
                except Exception:
                    pass
        
        elif platform.system() == 'Linux':
            try:
                import pyudev
                context = pyudev.Context()
                for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
                    if device.get('ID_BUS') == 'usb':
                        mount_point = device.get('DEVNAME')
                        if mount_point:
                            usb_drives.append(mount_point)
            except ImportError:
                import pyudev
                for partition in psutil.disk_partitions(all=True):
                    if 'sd' in partition.device and partition.mountpoint:
                        usb_drives.append(partition.mountpoint)
                    
        return usb_drives
    
    @staticmethod
    def save_to_usb(usb_path, filename, data):
        """
        Save data to a file on the USB drive.

        Args:
            usb_path (str): Path to the USB drive.
            filename (str): Name of the file to save data to.
            data (bytes): Data to be saved.

        Returns:
            str: Full path to the saved file.

        Raises:
            ValueError: When the USB path does not exist.
        """
        if not os.path.exists(usb_path):
            raise ValueError(f"USB path {usb_path} does not exist")
            
        full_path = os.path.join(usb_path, filename)
        
        with open(full_path, 'wb') as f:
            f.write(data)
            
        return full_path
    
    @staticmethod
    def load_from_usb(filepath):
        """
        Load data from a file on the USB drive.

        Args:
            filepath (str): Path to the file on the USB drive.

        Returns:
            bytes: Data loaded from the file.

        Raises:
            ValueError: When the file does not exist.
        """
        if not os.path.exists(filepath):
            raise ValueError(f"File {filepath} does not exist")
            
        with open(filepath, 'rb') as f:
            return f.read()
