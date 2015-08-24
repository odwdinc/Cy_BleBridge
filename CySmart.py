import serial
import time
import binascii
from struct import *
import threading
import Queue
import sys
import datetime


class Cy_serailCommand (object):
    def __init__ (self, heder, cmd, payload, whateforpayload, whateforCompleate):
        self.command = heder + cmd + payload
        self.cmd = cmd
        self.whateforpayload = whateforpayload
        self.whateforCompleate = whateforCompleate
        self.finished = False
        
class Cy_serialProsses(threading.Thread):
    
    def __init__ (self, in_Q, out_Q, ComPort, Cy):
        self.cy = Cy
        self.in_Q = in_Q
        self.out_Q = out_Q
        self.serin = serial.Serial(ComPort, 115200)
        self.running = True
        self.nextJob = True
        self.dataarray = []
        threading.Thread.__init__ (self)
        
    def hexPrint(self,s):
        if type(s) is not int:
            return ":".join("{:02x}".format(ord(c)) for c in s)
        return "{:02x}".format(s)
    
    def getTimeout(self):
        if self.this_job:
            if self.this_job.starTime and not self.this_job.finished:
                a = self.this_job.starTime
                b = datetime.datetime.now()
                delta = b - a
                return int(delta.total_seconds() * 1000) 
        return 0
    
    def run(self):
        while self.running:
            time.sleep(.1)
            #print "loop"
            if not self.in_Q.empty() and self.running and self.nextJob:
                self.nextJob = False
                self.dataarray = []
                self.this_job = self.in_Q.get()
                self.this_job.starTime = datetime.datetime.now()
                self.serin.write(self.this_job.command)
                while self.serin.outWaiting():
                    pass
            if self.getTimeout() > 2000:
                print "Timeout"
                sys.stdout.flush()
                self.nextJob = True
                self.out_Q.put(True) 
                self.this_job.finished = True
                
            if self.running and self.serin.inWaiting():
                #print "self.serin.inWaiting()"
                sys.stdout.flush()
                data =  self.serin.read(self.serin.inWaiting())
                #print self.hexPrint(data)
                data =  self.foundData(data)
                cmd  = self.hexPrint(self.this_job.cmd)
                playload = {}
                for responce in data:
                    #print responce
                    if self.this_job.cmd == responce['request_cmd']:
                        #print responce['cmd']
                        
                        if self.this_job.whateforCompleate:
                            if self.cy.EVT_COMMAND_COMPLETE in responce['cmd']:
                                self.nextJob = True
                                
                        else:
                            if self.nextJob == False:
                                self.nextJob = True
                        if len(responce['playload']) > 0 and not self.cy.EVT_COMMAND_STATUS in responce['cmd'] and not self.cy.EVT_COMMAND_COMPLETE in responce['cmd']:
                            if not responce['cmd'] in playload:
                                playload[responce['cmd']] = []
                            playload[responce['cmd']].append(responce['playload'])
                             
                #print "playload:",playload,  self.nextJob 
              
                    
                if len(playload) > 0:
                    self.out_Q.put(playload)
                elif self.nextJob == True and self.this_job.whateforpayload == False:
                    self.out_Q.put(True)  
                
                if self.nextJob:
                    self.this_job.finished = True
                    
                
    def kill(self):
        self.running = False
        self.serin.close()
    def foundData(self,data):
        for cmd in data.split(binascii.unhexlify("bda7"))[1:]:
            data = {}
            data['len'] = self.hexPrint(cmd[0:2])
            data['cmd'] = cmd[2:4]
            data['request_cmd'] = cmd[4:6]
            data['playload'] =cmd[6:]
            self.dataarray.append(data)
        return self.dataarray
   


class CySmart(object):
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
        'CMD_WRITE_CHARACTERISTIC_VALUE':binascii.unhexlify("0BFE"),
        'CMD_WRITE_CHARACTERISTIC_VALUE_WITHOUT_RESPONSE':binascii.unhexlify("0AFE"),
        'CMD_FIND_INCLUDED_SERVICES':binascii.unhexlify("02FE"),
        'CMD_DISCOVER_ALL_CHARACTERISTICS':binascii.unhexlify("03FE"),
        'CMD_INITIATE_PAIRING_REQUEST':binascii.unhexlify("99FE"),
        'CMD_UPDATE_CONNECTION_PARAMETER_RESPONSE':binascii.unhexlify("9FFE")
    }
    
    
    
    Flag_DISABLE_ALL_CHECK = 0x00
    Flag_CHECK_PARAMETER_LENGTH = 0x1
    Flag_IMMEDIATE_RESPONSE = 0x2
    Flag_API_RETURN = 0x4
    Flag_Exchange_RETURN = 0x3
    Flag_TRIGGER_COMPLETE = 0x8
    Flag_SECONDARY_CMD = 0x10
    
    CYSMT_EVT_HEADER_CODE = binascii.unhexlify("BDA7")
    EVT_SCAN_PROGRESS_RESULT = binascii.unhexlify("8A06")
    EVT_COMMAND_STATUS =  binascii.unhexlify("7E04")
    EVT_COMMAND_COMPLETE =  binascii.unhexlify("7F04")
    EVT_READ_CHARACTERISTIC_VALUE_RESPONSE  =  binascii.unhexlify("0606")
    
    

    
    dataarray = []
    flag = False
    conectioninfo = {}
    
    lock = threading.Lock()
    
    def __init__(self):
        pass
    
    def hexPrint(self,s):
        if type(s) is not int:
            return ":".join("{:02x}".format(ord(c)) for c in s)
        return "{:02x}".format(s)
    
    def hexArray(self,s):
        return self.hexPrint(s).split(":")
    
    def sendCommand(self,command, payload = binascii.unhexlify("0000"), whateforPayload = False, whateforCompleate = True):
        
        #__init__(self,heder, cmd, payload, whateforpayload, whateforCompleate):
        self.in_q.put(Cy_serailCommand(self.Commands['CMD_Hedder'] ,command, payload , whateforPayload, whateforCompleate))
        while self.out_q.empty():
            pass
        return self.out_q.get()
        
        
    def start(self,_flag, ComPort='\\.\COM6' ): 
        self.Flag_RETURN = _flag
        self.in_q = Queue.PriorityQueue()
        self.out_q = Queue.PriorityQueue()

        self.myThread = Cy_serialProsses(self.in_q,self.out_q,ComPort,self)
        self.myThread.start()

        self.sendCommand(self.Commands['CMD_INIT_BLE_STACK'],self.Commands['CMD_Footer'])
        
    
        
    def getScanData(self,cyd):
        scanList = []
        
        
        if self.EVT_SCAN_PROGRESS_RESULT in cyd:
            for scan in cyd[self.EVT_SCAN_PROGRESS_RESULT]:
                #print self.hexPrint(scan)
                sys.stdout.flush()
                
                Ble = {'BD_Address':[],'RSSI':0, 'Advertisement_Event_Data':[],'name':""}
                Ble['BD_Address'] = scan[1:6]
                #print self.hexPrint(scan[7:9])
                Ble['RSSI'] = unpack('b', scan[8:9])
                Ble['Advertisement_Event_Data'] = scan[10:-1]
                if len(scan) > 10:
                    inputString = scan
                    if '\t' in inputString:
                        nm_length=  int(self.hexArray(inputString.split('\t')[0])[-1],16)-1
                        Ble['name'] = inputString.split('\t')[1][0:nm_length]
                scanList.append(Ble)
        return scanList
    
    
    def openConection(self,address):
        out = {'CMD_Resolve_and_Set_Peer_Device_BD_Address':{},
               'CMD_ESTABLISH_CONNECTION':{},
               'EXCHANGE_GATT_MTU_SIZE':{},
               'Read_using_Characteristic_UUID':{}
               }
        
        out['CMD_Resolve_and_Set_Peer_Device_BD_Address'] = self.sendCommand(
            self.Commands['CMD_Resolve_and_Set_Peer_Device_BD_Address'], 
            binascii.unhexlify("0700") +address+ self.Commands['CMD_Footer']
        )
        
        out['CMD_ESTABLISH_CONNECTION'] = self.sendCommand(
            self.Commands['CMD_ESTABLISH_CONNECTION'] , 
            binascii.unhexlify("0700") + address + self.Commands['CMD_Footer']
        )
        
        out['EXCHANGE_GATT_MTU_SIZE'] = self.EXCHANGE_GATT_MTU_SIZE(0x0200)
        
        out['Read_using_Characteristic_UUID'] = self.Read_using_Characteristic_UUID(0x0001,0xFFFF,0x2A00)
        return out
        
    def close_Conection(self):
        return self.sendCommand(self.Commands['CMD_TERMINATE_CONNECTION'],binascii.unhexlify("02000400"))
    
    def _RETURN(self,pack,prams):
        values = (self.Flag_RETURN,)
        if type(prams) == tuple and type(pack) == str:
             values += prams
                
        pack = '=H '+ pack
        s = Struct(pack)
        packed_data = s.pack(*values)
        h=Struct('H')
        packsize = h.pack(s.size) 
        packed_data = packsize + packed_data
        return packed_data
    
    def EXCHANGE_GATT_MTU_SIZE(self,size):
        return self.sendCommand(self.Commands['CMD_EXCHANGE_GATT_MTU_SIZE'],self._RETURN('H',(0x200,)))
    
    def Read_using_Characteristic_UUID(self,Start_Handle,End_Handle,UUID):
        return self.sendCommand(self.Commands['CMD_READ_USING_CHARACTERISTIC_UUID'],self._RETURN('B H H H',(0x01, UUID, Start_Handle, End_Handle)))
    
    def Read_Characteristic_Value(self,Attribute):
        cmd = pack('H H H',*(self.Flag_RETURN, self.Flag_RETURN, Attribute ))
        Response = self.sendCommand(self.Commands['CMD_READ_CHARACTERISTIC_VALUE'],cmd)
        
        #print"Read_Characteristic_Value: ",Response
        #event, rest = Response[0:3], Response[4:]
        out_Response = []
        if self.EVT_READ_CHARACTERISTIC_VALUE_RESPONSE in Response:
                for cs in  Response[self.EVT_READ_CHARACTERISTIC_VALUE_RESPONSE]:
                    out_Response.append(cs[4:])
                    
        return out_Response
    
    def Write_Characteristic_Value(self,Attribute,payload):
        pramcount = binascii.unhexlify("0400")
        le = len(payload)
        package = pramcount+pack("H",*(Attribute,))+pack("H",*(le,))+payload
        package = pack("H",*(len(package),)) + package
        return self.sendCommand(self.Commands['CMD_WRITE_CHARACTERISTIC_VALUE'],package)
    
    def Read_All_characteristics(self,data_set):
        for se in data_set:
            data_set[se] = self.Read_Characteristic_Value(se)
        return data_set
    
    def Initiate_Pairing(self):
        cmd = pack('H H',*(self.Flag_IMMEDIATE_RESPONSE, self.Flag_RETURN ))
        return self.sendCommand(self.Commands['CMD_INITIATE_PAIRING_REQUEST'],cmd)
    
    def Update_Connection_Parameter(self,Response):
        cmd = ''
        if Response:
            cmd += binascii.unhexlify("040003000000")
        else:
            cmd += binascii.unhexlify("040003000100")
            
        return self.sendCommand(self.Commands['CMD_UPDATE_CONNECTION_PARAMETER_RESPONSE'],cmd)
    
    def close(self):
        self.myThread.kill()
        self.myThread.join()