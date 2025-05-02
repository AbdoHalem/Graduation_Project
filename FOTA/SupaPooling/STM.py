#_________________________________________ Modules 
import time
import serial
import os
import sys
import glob
import struct

#_________________________________________ Global Variables

#Flashing Address
CODE_ADDERSS                                        = "0x08002400"


#Return Codes
Flash_HAL_OK                                        = 0x00
Flash_HAL_ERROR                                     = 0x01
Flash_HAL_BUSY                                      = 0x02
Flash_HAL_TIMEOUT                                   = 0x03
Flash_HAL_INV_ADDR                                  = 0x04

#BL Commands
COMMAND_BL_GET_VER                                  = 0x51
COMMAND_BL_GET_HELP                                 = 0x52
COMMAND_BL_GET_CID                                  =0x53
COMMAND_BL_GET_RDP_STATUS                           =0x54
COMMAND_BL_GO_TO_ADDR                               =0x55
COMMAND_BL_FLASH_ERASE                              =0x56
COMMAND_BL_MEM_WRITE                                =0x57
COMMAND_BL_EN_R_W_PROTECT                           =0x58
COMMAND_BL_MEM_READ                                 =0x59
COMMAND_BL_READ_SECTOR_P_STATUS                     =0x5A
COMMAND_BL_OTP_READ                                 =0x5B
COMMAND_BL_DIS_R_W_PROTECT                          =0x5C
COMMAND_BL_Jump_To_User_App                         =0x5D
COMMAND_BL_MY_NEW_COMMAND                           =0x5E


#len details of the command
COMMAND_BL_GET_VER_LEN                              =6
COMMAND_BL_GET_HELP_LEN                             =6
COMMAND_BL_GET_CID_LEN                              =6
COMMAND_BL_GET_RDP_STATUS_LEN                       =6
COMMAND_BL_GO_TO_ADDR_LEN                           =10
COMMAND_BL_FLASH_ERASE_LEN                          =8
COMMAND_BL_MEM_WRITE_LEN                            = 11
COMMAND_BL_EN_R_W_PROTECT_LEN                       =8
COMMAND_BL_READ_SECTOR_P_STATUS_LEN                 =6
COMMAND_BL_DIS_R_W_PROTECT_LEN                      =6
COMMAND_BL_MY_NEW_COMMAND_LEN                       =8
COMMAND_BL_Jump_To_User_App_LEN                     =6

#BL General
verbose_mode = 1
mem_write_active =0
TimeCounter = 0


#_________________________________________ Functions

#----------------------------- file ops----------------------------------------
selected_file_path = ""

def calc_file_len():
    global selected_file_path
    if selected_file_path:
        size = os.path.getsize(selected_file_path)
        return size
    else:
        print("No file selected.")
        return 0

def open_the_file():
    global bin_file
    bin_file = open(selected_file_path,'rb')
    
def close_the_file():
    bin_file.close()


#----------------------------- utilities----------------------------------------

def word_to_byte(addr, index , lowerfirst):
    value = (addr >> ( 8 * ( index -1)) & 0x000000FF )
    return value

def get_crc(buff, length):
    Crc = 0xFFFFFFFF
    #print(length)
    for data in buff[0:length]:
        Crc = Crc ^ data
        for i in range(32):
            if(Crc & 0x80000000):
                Crc = (Crc << 1) ^ 0x04C11DB7
            else:
                Crc = (Crc << 1)
    return Crc


#----------------------------- Serial ----------------------------------------

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def Serial_Port_Configuration(port):
    global ser
    try:
        ser = serial.Serial(port,115200,timeout=2)
    except:
        print("\n   Oops! That was not a valid port")
        
        port = serial_ports()
        if(not port):
            print("\n   No ports Detected")
        else:
            print("\n   Here are some available ports on your PC. Try Again!")
            print("\n   ",port)
        return -1
    if ser.is_open:
        print("\n   Port Open Success")
    else:
        print("\n   Port Open Failed")
    return 0

              
def read_serial_port(length):
    read_value = ser.read(length)
    return read_value

def purge_serial_port():
    ser.reset_input_buffer()
    
def Write_to_serial_port(value, *length):
        data = struct.pack('>B', value)
        if (verbose_mode):
            value = bytearray(data)
            print("   "+"0x{:02x}".format(value[0]),end=' ')
        if(mem_write_active and (not verbose_mode)):
                print("#",end=' ')
        ser.write(data)


#----------------------------- Commands ----------------------------------------

def process_COMMAND_BL_FLASH_ERASE(length):
    erase_status=0
    value = read_serial_port(length)
    if len(value):
        erase_status = bytearray(value)
        if(erase_status[0] == Flash_HAL_OK):
            print("\n   Erase Status: Success  Code: FLASH_HAL_OK")
        elif(erase_status[0] == Flash_HAL_ERROR):
            print("\n   Erase Status: Fail  Code: FLASH_HAL_ERROR")
        elif(erase_status[0] == Flash_HAL_BUSY):
            print("\n   Erase Status: Fail  Code: FLASH_HAL_BUSY")
        elif(erase_status[0] == Flash_HAL_TIMEOUT):
            print("\n   Erase Status: Fail  Code: FLASH_HAL_TIMEOUT")
        elif(erase_status[0] == Flash_HAL_INV_ADDR):
            print("\n   Erase Status: Fail  Code: FLASH_HAL_INV_SECTOR")
        else:
            print("\n   Erase Status: Fail  Code: UNKNOWN_ERROR_CODE")
    else:
        print("Timeout: Bootloader is not responding")


def process_COMMAND_BL_MEM_WRITE(length):
    write_status=0
    value = read_serial_port(length)
    write_status = bytearray(value)
    if(write_status[0] == Flash_HAL_OK):
        print("\n   Write_status: FLASH_HAL_OK")
    elif(write_status[0] == Flash_HAL_ERROR):
        print("\n   Write_status: FLASH_HAL_ERROR")
    elif(write_status[0] == Flash_HAL_BUSY):
        print("\n   Write_status: FLASH_HAL_BUSY")
    elif(write_status[0] == Flash_HAL_TIMEOUT):
        print("\n   Write_status: FLASH_HAL_TIMEOUT")
    elif(write_status[0] == Flash_HAL_INV_ADDR):
        print("\n   Write_status: FLASH_HAL_INV_ADDR")
    else:
        print("\n   Write_status: UNKNOWN_ERROR")
    print("\n")

    
def read_bootloader_reply(command_code):
    len_to_follow=0 
    ret = -2 
    ack=read_serial_port(2)
    if(len(ack) ):
        a_array=bytearray(ack)
        #print("read uart:",ack) 
        if (a_array[0]== 0xA5):
            #CRC of last command was good .. received ACK and "len to follow"
            len_to_follow=a_array[1]
            print("\n   CRC : SUCCESS Len :",len_to_follow)
        
            if(command_code) == COMMAND_BL_FLASH_ERASE:
                    process_COMMAND_BL_FLASH_ERASE(len_to_follow)
                    
            elif(command_code) == COMMAND_BL_MEM_WRITE:
                    process_COMMAND_BL_MEM_WRITE(len_to_follow)
            
            ret = 0    
        
        elif a_array[0] == 0x7F:
            #CRC of last command was bad .. received NACK
            print("\n   CRC: FAIL \n")
            ret= -1
    else:
        print("\n   Timeout : Bootloader not responding")
        
    return ret


def STM_COMMAND(Command):
    
    TimeCounter = 0
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)


    if Command == "FLASH":
        print("\n   Command == > BL_MEM_WRITE")
        bytes_remaining=0
        t_len_of_file=0
        bytes_so_far_sent = 0
        len_to_read=0
        base_mem_address=0

        data_buf[1] = COMMAND_BL_MEM_WRITE

        #First get the total number of bytes in the .bin file.
        t_len_of_file =calc_file_len()

        #keep opening the file
        open_the_file()

        bytes_remaining = t_len_of_file - bytes_so_far_sent

        base_mem_address = CODE_ADDERSS   #0x08002300
        base_mem_address = int(base_mem_address, 16)
        global mem_write_active
        while(bytes_remaining):
            mem_write_active=1
            if(bytes_remaining >= 128):
                len_to_read = 128
            else:
                len_to_read = bytes_remaining
            #get the bytes in to buffer by reading file
            for x in range(len_to_read):
                file_read_value = bin_file.read(1)
                file_read_value = bytearray(file_read_value)
                data_buf[7+x]= int(file_read_value[0])
                #read_the_file(&data_buf[7],len_to_read) 
                #print("\n   base mem address = \n",base_mem_address, hex(base_mem_address)) 

            #populate base mem address
            data_buf[2] = word_to_byte(base_mem_address,1,1)
            data_buf[3] = word_to_byte(base_mem_address,2,1)
            data_buf[4] = word_to_byte(base_mem_address,3,1)
            data_buf[5] = word_to_byte(base_mem_address,4,1)

            data_buf[6] = len_to_read

            #/* 1 byte len + 1 byte command code + 4 byte mem base address
            #* 1 byte payload len + len_to_read is amount of bytes read from file + 4 byte CRC
            #*/
            mem_write_cmd_total_len = COMMAND_BL_MEM_WRITE_LEN+len_to_read

            #first field is "len_to_follow"
            data_buf[0] =mem_write_cmd_total_len-1

            crc32       = get_crc(data_buf,mem_write_cmd_total_len-4)
            data_buf[7+len_to_read] = word_to_byte(crc32,1,1)
            data_buf[8+len_to_read] = word_to_byte(crc32,2,1)
            data_buf[9+len_to_read] = word_to_byte(crc32,3,1)
            data_buf[10+len_to_read] = word_to_byte(crc32,4,1)

            #update base mem address for the next loop
            base_mem_address+=len_to_read

            Write_to_serial_port(data_buf[0],1)
            
            for i in data_buf[1:mem_write_cmd_total_len]:
                Write_to_serial_port(i,mem_write_cmd_total_len-1)

            bytes_so_far_sent+=len_to_read
            bytes_remaining = t_len_of_file - bytes_so_far_sent
            print("\n   bytes_so_far_sent:{0} -- bytes_remaining:{1}\n".format(bytes_so_far_sent,bytes_remaining)) 

                
            if(TimeCounter == 0):
                time.sleep(2)
                TimeCounter = 1

            ret_value = read_bootloader_reply(data_buf[1])
        mem_write_active=0

    elif Command == "RUN":
        print("\n   Command == > BL_Jump_To_User_App")
        COMMAND_BL_Jump_To_User_App_LEN     = 6
        data_buf[0] = COMMAND_BL_Jump_To_User_App_LEN-1 
        data_buf[1] = COMMAND_BL_Jump_To_User_App 
        crc32       = get_crc(data_buf,COMMAND_BL_Jump_To_User_App_LEN-4)
        crc32 = crc32 & 0xffffffff
        data_buf[2] = word_to_byte(crc32,1,1) 
        data_buf[3] = word_to_byte(crc32,2,1) 
        data_buf[4] = word_to_byte(crc32,3,1) 
        data_buf[5] = word_to_byte(crc32,4,1) 

        
        Write_to_serial_port(data_buf[0],1)
        for i in data_buf[1:COMMAND_BL_Jump_To_User_App_LEN]:
            Write_to_serial_port(i,COMMAND_BL_Jump_To_User_App_LEN-1)
        

        ret_value = read_bootloader_reply(data_buf[1])
