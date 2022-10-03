import datetime
import os
import sys
import struct
from telnetlib import IP
import time
import select
import socket
import binascii

class pingResponseNode() :
    def __init__(self):
        self.numBytes = 0
        self.destAddr = 0
        self.time = 0

pingResponseList = []

ICMP_ECHO_REQUEST = 8
rtt_min = float('+inf')
rtt_max = float('-inf')
rtt_sum = 0
rtt_cnt = 0

def checksum(string):
    csum = 0
    countTo = (len(string) / 2) * 2

    count = 0
    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + ord(string[len(str) - 1])
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr):
    global rtt_min, rtt_max, rtt_sum, rtt_cnt
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024) #recPacket contains the data bytes while addr contains the address the packet was received from

        # TODO
        # Fetch the ICMP header from the IP packet
        ICMPHeader = struct.unpack_from("<BBHHhd", recPacket, 20) #unpack the fields of the ICMP packet header
        if(ICMPHeader[3] == ID): #compares the ID field of the IP header to the ID passed in for verification
            if(ICMPHeader[0] == 0): #checks to make sure the ICMP header code is 0 (ICMP reply)
                #VERIFY WITH CHECKSUM
                #print("IN HERE")
                #print(timeReceived)
                totalLen = struct.unpack_from("!H", recPacket, 2) 
                timeSent = ICMPHeader[5]
                #print(timeSent)

                #CREATE NEW pingResponseNode TO STORE PING INFORMATION
                newPing = pingResponseNode()
                newPing.destAddr = addr #store the destination address in newPing node
                newPing.numBytes = totalLen[0] #store the number of bytes received in newPing node
                newPing.time = (timeReceived - timeSent) * 1000
                pingResponseList.append(newPing)
                return
                # TODO END
            else:
                timeLeft = timeLeft - howLongInSelect
                if timeLeft <= 0:
                    return "Request timed out."

def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)

    myChecksum = 0
    # Make a dummy header with a 0 checksum.
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())    # 8 bytes
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        myChecksum = socket.htons(myChecksum) & 0xffff
        # Convert 16-bit integers from host to network byte order.
    else:
        myChecksum = socket.htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1))  # AF_INET address must be tuple, not str
    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object


def doOnePing(destAddr, timeout):
    icmp = socket.getprotobyname("icmp")
    # SOCK_RAW is a powerful socket type. For more details see: http://sock-raw.org/papers/sock_raw

    # TODO
    # Create Socket here
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    # TODO END

    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)

    mySocket.close()
    return delay


def ping(host, timeout=1):
    global rtt_min, rtt_max, rtt_sum, rtt_cnt
    cnt = 0
    # timeout=1 means: If one second goes by without a reply from the server,
    # the client assumes that either the client's ping or the server's pong is lost
    try:
        dest = socket.gethostbyname(host)
    except:
        print("Invalid domain name/IP address. Exiting program.")
        exit()

    print("Pinging " + dest + " using Python. Press Ctrl-C to view ping results.")
    # Send ping requests to a server separated by approximately one second
    try:
        while True:
            cnt += 1
            retVal = doOnePing(dest, timeout)
            if(retVal != None):
                print(doOnePing(dest, timeout))
            time.sleep(1)
    except KeyboardInterrupt:
        # TODO
        # calculate statistic here
        min = -1
        max = -1
        totalTime = 0
        counter = 0
        for pingNode in pingResponseList:
            counter = counter + 1
            totalTime = totalTime + pingNode.time
            if(pingNode.time > max):
                max = pingNode.time
            if(pingNode.time < min or min == -1):
                min = pingNode.time
            print(str(pingNode.numBytes) + " bytes from " + str(pingNode.destAddr[0]) + "; time = " + str(format(pingNode.time, ".1f")) + " ms")


        print("--- " + str(dest) + " ping statistics ---")
        print("round-trip min/max/avg " + str(format(min, ".3f"))+ "/" + str(format(max, ".3f")) + "/" + str(format(totalTime/counter, ".3f") + " ms"))
        # TODO END

if __name__ == '__main__':
    print("Please enter a valid domain name/IP address to ping: ")
    userInput = input()
    ping(userInput)
    #ping(sys.argv[1]) Originally used to extract command line argument IP address/domain name
