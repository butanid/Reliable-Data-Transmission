# Name: Deep Butani
# OSU Email: butanid@oregonstate.edu
# Course: CS372 - Intro to Computer Networks
# Assignment: Project 2 - Reliable Data Transmission (RDT)
# Due Date: 8/2/24 (3-day extension)
# Description: RDT layer class that allows the transfer of string data through an unreliable channel
# Sources: Computer Networking - A Top Down Approach James F. Kurose & Keith Ross (Section 3.5)
#          https://pythonexamples.org/python-split-string-into-specific-length-chunks/
#          

from segment import Segment


# #################################################################################################################### #
# RDTLayer                                                                                                             #
#                                                                                                                      #
# Description:                                                                                                         #
# The reliable data transfer (RDT) layer is used as a communication layer to resolve issues over an unreliable         #
# channel.                                                                                                             #
#                                                                                                                      #
#                                                                                                                      #
# Notes:                                                                                                               #
# This file is meant to be changed.                                                                                    #
#                                                                                                                      #
#                                                                                                                      #
# #################################################################################################################### #


class RDTLayer(object):
    # ################################################################################################################ #
    # Class Scope Variables                                                                                            #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    DATA_LENGTH = 4 # in characters                     # The length of the string data that will be sent per packet...
    FLOW_CONTROL_WIN_SIZE = 15 # in characters          # Receive window size for flow-control
    sendChannel = None
    receiveChannel = None
    dataToSend = ''
    currentIteration = 0                                # Use this for segment 'timeouts'
    # Add items as needed
    windowSize = (FLOW_CONTROL_WIN_SIZE + DATA_LENGTH - 1) // DATA_LENGTH
    currentSeq = 0
    currentWindow = [0, DATA_LENGTH]
    ACK_next = DATA_LENGTH
    received_segments = []

    # ################################################################################################################ #
    # __init__()                                                                                                       #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def __init__(self):
        self.sendChannel = None
        self.receiveChannel = None
        self.dataToSend = ''
        self.currentIteration = 0
        # Add items as needed
        self.base_state = 0
        self.ACK_curr = 0
        self.expected_seqnum = 0
        self.timeout = 0
        self.countSegmentTimeouts = 0
        self.slicedSegment = []

    # ################################################################################################################ #
    # setSendChannel()                                                                                                 #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Called by main to set the unreliable sending lower-layer channel                                                 #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def setSendChannel(self, channel):
        self.sendChannel = channel

    # ################################################################################################################ #
    # setReceiveChannel()                                                                                              #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Called by main to set the unreliable receiving lower-layer channel                                               #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def setReceiveChannel(self, channel):
        self.receiveChannel = channel

    # ################################################################################################################ #
    # setDataToSend()                                                                                                  #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Called by main to set the string data to send                                                                    #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def setDataToSend(self,data):
        self.dataToSend = data
        # Initialize sliced segment list
        self.slicedSegment = []

        # Loop through dataToSend
        for i in range(0, len(self.dataToSend), 4):
            # Slice data into segments of DATA_LENGTH
            segment = self.dataToSend[i:i + self.DATA_LENGTH]
            self.slicedSegment.append(segment)

    # ################################################################################################################ #
    # getDataReceived()                                                                                                #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Called by main to get the currently received and buffered string data, in order                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def getDataReceived(self):
        # ############################################################################################################ #
        # Identify the data that has been received...

        # print('getDataReceived(): Complete this...')

        # Sorting received segments by segment number
        sortedSegment = sorted(self.received_segments)
        # Initializing string variable to store sorted data
        sortedString = ""
        
        # Looping through sorted segment
        for i in range(len(sortedSegment)):
            # Append segment payload to sortedString
            sortedString += sortedSegment[i][1]
        
        return sortedString

    # ################################################################################################################ #
    # processData()                                                                                                    #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # "timeslice". Called by main once per iteration                                                                   #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def processData(self):
        self.currentIteration += 1
        self.processSend()
        self.processReceiveAndSendRespond()

    # ################################################################################################################ #
    # processSend()                                                                                                    #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Manages Segment sending tasks                                                                                    #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def processSend(self):
        # Checks if there is still data to be sent
        if self.dataToSend:
            # If so switch to client state
            self.base_state = 1
        
        # Checks if segment ACKs in receive queue
        if self.receiveChannel.receiveQueue:
            # Checks if RDTLayer in client state
            if self.base_state:
                # Receive segments from receive queue
                receiveQueue = self.receiveChannel.receive()
                # Looping through each segment in the receive queue
                for i in range(len(receiveQueue)):
                    # Checks if queue ACK is equal to next ACK
                    if receiveQueue[i].acknum == self.ACK_next:
                        # Increment current sequence number
                        self.currentSeq += self.windowSize
                        # Increment next ACK number
                        self.ACK_next += self.windowSize
                        # Updating start window
                        self.currentWindow[0] += self.windowSize
                        # Updating end window
                        self.currentWindow[1] += self.windowSize
        # Checks if no segment ACKs in receive queue
        else:
            # Checks if timeout limit has been reached
            if self.timeout == 10:
                # Increment count of segment timeouts
                self.countSegmentTimeouts += 1
            else:
                # Incrementing timeout counter
                self.timeout += 1
                return
        
        # Checks if RDTLayer in client state
        if self.base_state:
            # Send current sliced segment data to server using helper method
            self.sendToServer(self.currentSeq, self.slicedSegment)

        # ############################################################################################################ #
        # print('processSend(): Complete this...')

        # You should pipeline segments to fit the flow-control window
        # The flow-control window is the constant RDTLayer.FLOW_CONTROL_WIN_SIZE
        # The maximum data that you can send in a segment is RDTLayer.DATA_LENGTH
        # These constants are given in # characters

        # Somewhere in here you will be creating data segments to send.
        # The data is just part of the entire string that you are trying to send.
        # The seqnum is the sequence number for the segment (in character number, not bytes)


        # seqnum = "0"
        # data = "x"
    
    def sendToServer(self, expected_seqnum, slicedSegment):
        # Loop through windowSize
        for i in range(int(self.windowSize)):
            # Checks if there is data to send and expected seq number within range
            if self.dataToSend and expected_seqnum < len(slicedSegment):
                segmentSend = Segment()
                # Setting data
                segmentSend.setData(expected_seqnum, slicedSegment[expected_seqnum])
                # Display sending segment
                print(f"Sending segment: {segmentSend.to_string()}")
                # Use the unreliable sendChannel to send the segment
                self.sendChannel.send(segmentSend)
                expected_seqnum += 1

        # ############################################################################################################ #
        # Display sending segment
        # segmentSend.setData(seqnum,data)
        # print("Sending segment: ", segmentSend.to_string())

        # Use the unreliable sendChannel to send the segment
        # self.sendChannel.send(segmentSend)

    # ################################################################################################################ #
    # processReceive()                                                                                                 #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Manages Segment receive tasks                                                                                    #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def processReceiveAndSendRespond(self):
        # This call returns a list of incoming segments (see Segment class)...
        listIncomingSegments = self.receiveChannel.receive()

        # Initializing list to store processed segments
        processedSegments = []

        # Checks if incoming segments in receive channel
        if listIncomingSegments:
            # Looping through incoming segment list
            for segment in listIncomingSegments:
                # Checks if segment contains data, has valid checksum, not duplicated
                if (segment.payload is not None and segment.checkChecksum() and segment not in processedSegments
                    and self.currentWindow[0] <= segment.seqnum <= self.currentWindow[1]):
                    # Append valid segments to processed list
                    processedSegments.append([segment.seqnum, segment.payload])
            
            # Looping through processed segment list
            for segment in processedSegments:
                # Checks if segment already in receiving pipeline
                if segment not in self.received_segments:
                    # Append segment to receiving pipeline
                    self.received_segments.append(segment)
            
            # Checks if segments within current window are proccessed
            if len(processedSegments) == 4:
                # Increment current ACK number
                self.ACK_curr += 4
                segmentAck = Segment()                  # Segment acknowledging packet(s) received
                # Setting ACK number
                segmentAck.setAck(self.currentWindow[0] + 4)
                # Display response segment
                print("Sending ack: ", segmentAck.to_string())
                # Send segment ACK to server
                self.sendChannel.send(segmentAck)

        # ############################################################################################################ #
        # What segments have been received?
        # How will you get them back in order?
        # This is where a majority of your logic will be implemented
        # print('processReceive(): Complete this...')

        # ############################################################################################################ #
        # How do you respond to what you have received?
        # How can you tell data segments apart from ack segemnts?
        # print('processReceive(): Complete this...')

        # Somewhere in here you will be setting the contents of the ack segments to send.
        # The goal is to employ cumulative ack, just like TCP does...
        # acknum = "0"

        # ############################################################################################################ #
        # Display response segment
        # segmentAck.setAck(acknum)
        # print("Sending ack: ", segmentAck.to_string())

        # Use the unreliable sendChannel to send the ack packet
        # self.sendChannel.send(segmentAck)
