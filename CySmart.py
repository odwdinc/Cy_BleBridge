import serial
import time
import binascii
from struct import *
class CySmart:
    Commands = {
        'CMD_Resolve_and_Set_Peer_Device_BD_Address':binascii.unhexlify("A1FE"),
        'CMD_Hedder':binascii.unhexlify("4359"),
        'CMD_Footer':binascii.unhexlify("0000"),
        'CMD_INIT_BLE_STACK':binascii.unhexlify("07FC"),
        'CMD_START_SCAN':binascii.unhexlify("93FE"),
        'CMD_STOP_SCAN':binascii.unhexlify("94FE"),
        'CMD_ESTABLISH_CONNECTION':binascii.unhexlify("97FE"),
        'CMD_TERMINATE_CONNECTION':binascii.unhexlify("98FE"),
        'CMD_EXCHANGE_GATT_MTU_SIZE':binascii.unhexlify("12FE"),
        'CMD_READ_CHARACTERISTIC_VALUE':binascii.unhexlify("06FE"),
        'CMD_READ_USING_CHARACTERISTIC_UUID':binascii.unhexlify("07FE"),
        'CMD_FIND_INCLUDED_SERVICES':binascii.unhexlify("02FE"),
        'CMD_DISCOVER_ALL_CHARACTERISTICS':binascii.unhexlify("03FE"),
        'CMD_INITIATE_PAIRING_REQUEST':binascii.unhexlify("99FE")
    }
    
    
    Flag_DISABLE_ALL_CHECK = 0x00
    Flag_CHECK_PARAMETER_LENGTH = 0x1
    Flag_IMMEDIATE_RESPONSE = 0x2
    Flag_API_RETURN = 0x4
    Flag_TRIGGER_COMPLETE = 0x8
    Flag_SECONDARY_CMD = 0x10
    
    CYSMT_EVT_HEADER_CODE = binascii.unhexlify("BDA7")
    EVT_SCAN_PROGRESS_RESULT = binascii.unhexlify("8A06")
    EVT_COMMAND_STATUS =  binascii.unhexlify("7E04")
    EVT_COMMAND_COMPLETE =  binascii.unhexlify("7F04")
    EVT_READ_CHARACTERISTIC_VALUE_RESPONSE  =  binascii.unhexlify("0606")

    def __init__(self, ComPort='\\.\COM6'):
        self.serin = serial.Serial(ComPort, 115200, timeout=3)
        self.serin.isOpen()

    def hexPrint(self,s):
        if type(s) is not int:
            return ":".join("{:02x}".format(ord(c)) for c in s)
        return "{:02x}".format(s)
    
    def hexArray(self,s):
        return self.hexPrint(s).split(":")
    
    def sendCommand(self,command, hedder = True, footer = True):
        cmd = ""
        if hedder:
            cmd += self.Commands['CMD_Hedder']
        cmd += command
        
        if footer:
            cmd+= self.Commands['CMD_Footer']
        
        self.serin.write(cmd)
        self.serin.flush()
        time.sleep(.1)
        return self.prossesOutput()
    
    
    def prossesOutput(self):
        payloads = {}
        time.sleep(.1)
        while self.serin.inWaiting():
            hedderTest = self.serin.read(2)
            if self.CYSMT_EVT_HEADER_CODE in hedderTest:
                #Have Hedder message
                mesageLen = self.serin.read(2)
                mesageLen = unpack('h',mesageLen)[0]
                message = self.serin.read(mesageLen)
                if len(message) > 4:
                # have message                   
                    event, command = unpack('2s2s', message[0:4])
                    if event not in self.EVT_COMMAND_STATUS and event not in self.EVT_COMMAND_COMPLETE:
                        body = message[4:]
                        if event not in payloads:
                             payloads[event] = []      
                        payloads[event].append(body)
            else:
                time.sleep(.1)
        return payloads
        
    def getScanData(self,cyd):
        Ble = {'address':[], 'name':""}
        
        if self.EVT_SCAN_PROGRESS_RESULT in cyd:
            for scan in cyd[self.EVT_SCAN_PROGRESS_RESULT]:
                if len(scan) > 10:
                    inputString = scan
                    Ble['address'] = inputString[1:6]
                    if '\t' in inputString:
                        nm_length=  int(self.hexArray(inputString.split('\t')[0])[-1],16)-1
                        Ble['name'] = inputString.split('\t')[1][0:nm_length]
        return Ble
    
    
    def openConection(self,address):
        out = {'CMD_Resolve_and_Set_Peer_Device_BD_Address':{},
               'CMD_ESTABLISH_CONNECTION':{},
               'EXCHANGE_GATT_MTU_SIZE':{},
               'Read_using_Characteristic_UUID':{}
               }
        
        cmd = cy.Commands['CMD_Resolve_and_Set_Peer_Device_BD_Address']+ binascii.unhexlify("0700") +address 
        out['CMD_Resolve_and_Set_Peer_Device_BD_Address'] = self.sendCommand(cmd)
        
        cmd = cy.Commands['CMD_ESTABLISH_CONNECTION'] + binascii.unhexlify("0700") +address
        out['CMD_ESTABLISH_CONNECTION'] = self.sendCommand(cmd)
        
        out['EXCHANGE_GATT_MTU_SIZE'] = self.EXCHANGE_GATT_MTU_SIZE(0x0200)
        out['Read_using_Characteristic_UUID'] = self.Read_using_Characteristic_UUID(0x0001,0xFFFF,0x2A00)
        return out
        
    def close_Conection(self):
        cmd = cy.Commands['CMD_TERMINATE_CONNECTION']
        cmd += binascii.unhexlify("02000400")
        return self.sendCommand(cmd)
    
    def API_RETURN(self,pack,prams):
        values = (self.Flag_API_RETURN,)
        if type(prams) == tuple and type(pack) == str:
             values += prams
                
        pack = '=B '+ pack
        s = Struct(pack)
        packed_data = s.pack(*values)
        h=Struct('H')
        packsize = h.pack(s.size) 
        packed_data = packsize + packed_data
        return packed_data
    
    def EXCHANGE_GATT_MTU_SIZE(self,size):
        cmd = cy.Commands['CMD_EXCHANGE_GATT_MTU_SIZE']
        cmd += self.API_RETURN('H',(0x200,))
        return self.sendCommand(cmd,footer=False)
    
    def Read_using_Characteristic_UUID(self,Start_Handle,End_Handle,UUID):
        cmd = self.Commands['CMD_READ_USING_CHARACTERISTIC_UUID']
        cmd += self.API_RETURN('H H H H',(0x100, UUID, Start_Handle, End_Handle))
        return self.sendCommand(cmd,footer=False)
    
    def Read_Characteristic_Value(self,Attribute):
        cmd = self.Commands['CMD_READ_CHARACTERISTIC_VALUE']
        cmd += pack('H H H',*(cy.Flag_API_RETURN, cy.Flag_API_RETURN, Attribute ))
        Response = self.sendCommand(cmd,footer=False)
        #event, rest = Response[0:3], Response[4:]
        out_Response = []
        if self.EVT_READ_CHARACTERISTIC_VALUE_RESPONSE in Response:
                for cs in  Response[self.EVT_READ_CHARACTERISTIC_VALUE_RESPONSE]:
                    out_Response.append(cs[4:])
                    
        return out_Response
    
    def Read_All_characteristics(self):
        data_set = {0x0003:{},
                    0x0005:{},
                    0x0007:{},
                    0x000A:{},
                    0x000E:{},
                    0x0010:{},
                    0x0014:{},
                    0x0018:{},
                    0x001D:{},
                    0x001F:{},
                    0x0022:{}
                    }
        for se in data_set:
            data_set[se] = self.Read_Characteristic_Value(se)
        return data_set
    
    def Initiate_Pairing(self):
        cmd = self.Commands['CMD_INITIATE_PAIRING_REQUEST']
        cmd += pack('H H',*(cy.Flag_IMMEDIATE_RESPONSE, cy.Flag_API_RETURN ))
        return self.sendCommand(cmd,footer=False)
            
    def close(self):
        self.serin.close()
        
        
cy = CySmart()
cy.sendCommand(cy.Commands['CMD_INIT_BLE_STACK'])
cyd= cy.sendCommand(cy.Commands['CMD_START_SCAN'])
time.sleep(3)
cy.sendCommand(cy.Commands['CMD_STOP_SCAN'])

if cy.EVT_SCAN_PROGRESS_RESULT in cyd:
    client = cy.getScanData(cyd)
    print client['name']
    cy.openConection(client['address'])
    cy.Initiate_Pairing()
    allcs =  cy.Read_All_characteristics()
    for cs in allcs:
        print cy.hexPrint(cs), allcs[cs]
    print cy.Read_Characteristic_Value(0x1F) 
    cy.close_Conection()
else:
     print "nothing found:"
cy.close()