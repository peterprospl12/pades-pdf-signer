import os
import platform
import psutil
import string

class UsbStorage:
    
    @staticmethod
    def get_usb_drives():
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
        if not os.path.exists(usb_path):
            raise ValueError(f"USB path {usb_path} does not exist")
            
        full_path = os.path.join(usb_path, filename)
        
        with open(full_path, 'wb') as f:
            f.write(data)
            
        return full_path
    
    @staticmethod
    def load_from_usb(filepath):
        if not os.path.exists(filepath):
            raise ValueError(f"File {filepath} does not exist")
            
        with open(filepath, 'rb') as f:
            return f.read()
