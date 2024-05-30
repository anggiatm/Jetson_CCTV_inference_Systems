
class DeviceInfo:
    def __init__(self):
        self.cpu = 0
        self.max_cpu = 0
        self.mem = 0
        self.max_mem = 0
        self.thread = 0
        self.max_thread = 0 
    
    def updateValue(self):
        self.cpu, self.mem, self.thread = self.get_cpu_load()
        if self.cpu > self.max_cpu:
            self.max_cpu = self.cpu
        if self.mem > self.max_mem:
            self.max_mem = self.mem
        if self.thread > self.max_thread:
            self.max_thread = self.thread

    def get_cpu_load(self):
        return [psutil.cpu_percent(interval=1), psutil.virtual_memory().percent, len(psutil.Process().threads())]
