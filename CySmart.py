import serial
import time
import binascii
class CySmart:
    Commands = {
        'CMD_Hedder':binascii.unhexlify("4359"),
        'CMD_Footer':binascii.unhexlify("0000"),
        'CMD_INIT_BLE_STACK':binascii.unhexlify("07FC"),
        'CMD_START_SCAN':binascii.unhexlify("93FE"),
        'CMD_STOP_SCAN':binascii.unhexlify("94FE")
        'CMD_ESTABLISH_CONNECTION':binascii.unhexlify("97FE")
        'CMD_TERMINATE_CONNECTION':binascii.unhexlify("98FE")
        'CMD_EXCHANGE_GATT_MTU_SIZE':binascii.unhexlify("12FE")
        'CMD_READ_USING_CHARACTERISTIC_UUID':binascii.unhexlify("07FE")
        'CMD_FIND_INCLUDED_SERVICES':binascii.unhexlify("02FE")
        'CMD_DISCOVER_ALL_CHARACTERISTICS':binascii.unhexlify("03FE")
    }
    
    
    CYSMT_EVT_HEADER_CODE = binascii.unhexlify("BDA7")
    EVT_SCAN_PROGRESS_RESULT = binascii.unhexlify("8A06")
    EVT_COMMAND_STATUS =  binascii.unhexlify("7E04")
    
    
    CMD_ESTABLISH_CONNECTION:binascii.unhexlify("A1FE")

    def __init__(self, ComPort='\\.\COM6'):
        self.serin = serial.Serial(ComPort, 115200, timeout=1)
        self.serin.isOpen()

    def hexPrint(self,s):
        return ":".join("{:02x}".format(ord(c)) for c in s)
    
    def hexArray(self,s):
        return self.hexPrint(s).split(":")
    
    def sendCommand(self,command,timeout = 3):
        self.serin.write(self.Commands['CMD_Hedder']+command+self.Commands['CMD_Footer'])
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
    def getScanData(self,inputString):
        Ble = {'address':[], 'name':""}
        if self.CYSMT_EVT_HEADER_CODE in inputString:
            prossesData = inputString.split(self.CYSMT_EVT_HEADER_CODE)
            for pd in prossesData[1:]:
                les = self.hexArray(pd)
                if int(les[0],16) > 0x0E:
                    if self.Commands['CMD_START_SCAN'] in pd:
                        data_set = pd.split(self.Commands['CMD_START_SCAN'])[1]
                        Ble['address'] =  self.hexArray(data_set)[1:6]
                        if '\t' in data_set:
                            nm_length=  int(self.hexArray(data_set.split('\t')[0])[-1],16)-1
                            Ble['name'] = data_set.split('\t')[1][0:nm_length]
        return Ble
    def openConection(self,address):
        
        ads = "".join("{:s}".format(c) for c in address)
        ads = self.Commands['CMD_ESTABLISH_CONNECTION'] +"0700"+ ads
        print self.sendCommand(ads)
        
        
    def close(self):
        self.serin.close()
        
        
cy = CySmart()
cy.sendCommand(cy.Commands['CMD_INIT_BLE_STACK'])
stro, ops = cy.sendCommand(cy.Commands['CMD_START_SCAN'])
cy.sendCommand(cy.Commands['CMD_STOP_SCAN'])
cy.close()

print cy.getScanData(ops)