import serial
import time
import binascii
class CySmart:
    Commands = {
        'CMD_INIT_BLE_STACK':binascii.unhexlify("435907FC0000"),
        'CMD_START_SCAN':binascii.unhexlify("435993FE0000"),
        'CMD_STOP_SCAN':binascii.unhexlify("435994FE0000")
    }


    def __init__(self, ComPort='\\.\COM6'):
        self.serin = serial.Serial(ComPort, 115200, timeout=1)
        self.serin.isOpen()

    def hexPrint(self,s):
        return ":".join("{:02x}".format(ord(c)) for c in s)
    
    def hexArray(self,s):
        return self.hexPrint(s).split(":")
    
    def sendCommand(self,command,timeout = 3):
        self.serin.write(command)
        self.serin.flush()
        out = ''
        check_timout = 0
        while (out.endswith(binascii.unhexlify("FE0000")) or  out.endswith(binascii.unhexlify("FC0000")) or out.endswith(binascii.unhexlify("FE0200"))) == False:
            time.sleep(1)
            out = out + self.serin.read(self.serin.inWaiting())
            check_timout +=1
            if timeout == check_timout:
                break
        if out != '':
            return ">>:( " + out +" ) 0x>>:"+ self.hexPrint(out), out
        else:
            return "",out
        
    def close(self):
        self.serin.close()
        
        
cy = CySmart()
cy.sendCommand(cy.Commands['CMD_INIT_BLE_STACK'])
stro, ops = cy.sendCommand(cy.Commands['CMD_START_SCAN'],10)

print (ops, cy.hexArray(ops))

cy.sendCommand(cy.Commands['CMD_STOP_SCAN'])
cy.close()