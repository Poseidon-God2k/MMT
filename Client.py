import tkinter.messagebox as tkMessageBox
from tkinter import *
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    STOP = 0

    COUNT =0

    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0
        self.listfileName = []


    def re_connect(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0
        self.listfileName = []

    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Switch"
        self.setup["command"] = self.switchMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)
        

        
        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Stop"
        self.teardown["command"] = self.stopMovie
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

    def setupMovie(self):
        """Setup button handler."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

    def exitClient(self):
        """Stop file socket"""
        self.fileSocket.shutdown(socket.SHUT_RDWR)
        self.fileSocket.close()
        """Teardown button handler."""
        self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy()  # Close the gui window
        os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)  # Delete the cache image from video

    def stopMovie(self):
        self.sendRtspRequest(self.TEARDOWN)
    
    def pauseMovie(self):

        """Pause button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)
            # if tkMessageBox.askokcancel("Play", "Click OK to continue."):
            #     threading.Thread(target=self.listenRtp).start()
            #     self.playEvent = threading.Event()
            #     self.playEvent.clear()
            #     self.sendRtspRequest(self.PLAY)
        while True:
            print(self.state)
            if self.state == self.READY:
                # Create a new thread to listen for RTP packets
                threading.Thread(target=self.listenRtp).start()
                self.playEvent = threading.Event()
                self.playEvent.clear()
                self.sendRtspRequest(self.PLAY)
                break

        
    



    def switchMovie(self):
        # root=Tk()
        # def retrieve_input(input):
        #     inputValue=input.get("1.0","end-1c")
        #     print(inputValue)
        #     self.fileName = inputValue
        #     self.playMovie()
        # textBox=Text(root, height=2, width=10)
        # textBox.pack()
        # buttonCommit=Button(root, height=1, width=10, text="Commit", 
        #             command=lambda: retrieve_input(textBox))
        # #command=lambda: retrieve_input() >>> just means do this when i press the button
        # buttonCommit.pack()
        def go(event): 
            cs = Lb.curselection() 
            
            # Updating label text to selected option 
            w.config(text=Lb.get(cs))
            self.stopMovie()
            self.re_connect(self.master,self.serverAddr,self.serverPort,self.rtpPort,"./video/"+Lb.get(cs))
            # Setting Background Colour 
            # for list in cs: 
                
            #     if list == 0: 
            #         self.fileName = Lb.get(c)
            #     elif list == 1: 
            #         top.configure(background='green') 
            #     elif list == 2: 
            #         top.configure(background='yellow') 
            #     elif list == 3: 
            #         top.configure(background='white') 
   
   
        top = Tk() 
        top.geometry('250x275') 
        top.title('Double Click')
        response = self.listfileName
        
        # Creating Listbox
        Lb = Listbox(top, height=6) 
        # Inserting items in Listbox
        for res in response:
            Lb.insert(response.index(res), res)
        
        # Binding double click with left mouse 
        # button with go function 
        Lb.bind('<Double-1>', go) 
        Lb.pack() 
        
        # Creating Edit box to show selected option 
        w = Label(top, text='Default') 
        w.pack() 
        top.mainloop()



    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    currFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(currFrameNbr))


                    if currFrameNbr > self.frameNbr:  # Discard the late packet
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
            except:
                # Stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break

                # Upon receiving ACK for TEARDOWN request,
                # close the RTP socket
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()

        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('connect succeess')
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            tkMessageBox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

        self.fileSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.fileSocket.connect((self.serverAddr, 12345))
        except:
            tkMessageBox.showwarning('Connection Video list Failed', 'Connection to \'%s\' failed.' % self.serverAddr)
        threading.Thread(target=self.recvFileReply).start()
        self.fileSocket.send("READFILE".encode())
    
    def recvFileReply(self):
        while True:
            reply = self.fileSocket.recv(1024).decode("utf-8")
            if reply:
                print(reply)
                self.listfileName = reply.split(' ')
            

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # -------------
        # TO COMPLETE
        # -------------

        # Setup request
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            self.rtspSeq = 1

            # Write the RTSP request to be sent.
            request = ( "SETUP " + str(self.fileName) + " RTSP/1.0 " + "\n"
                        "CSeq: " + str(self.rtspSeq) + "\n"
                        "Transport: RTP/UDP; client_port= " + str(self.rtpPort))

            # Keep track of the sent request.
            self.requestSent = self.SETUP

        # Play request
        elif requestCode == self.PLAY and self.state == self.READY:
            # Update RTSP sequence number.
            self.rtspSeq = self.rtspSeq + 1

            # Write the RTSP request to be sent.
            request = ("PLAY " + str(self.fileName) + " RTSP/1.0 " + "\n" +
                        "CSeq: " + str(self.rtspSeq) + "\n" +
                        "Session: " + str(self.sessionId))

            # Keep track of the sent request.
            self.requestSent = self.PLAY

        # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            # Update RTSP sequence number.
            self.rtspSeq = self.rtspSeq + 1

            # Write the RTSP request to be sent.
            request = ( "PAUSE " + str(self.fileName) + " RTSP/1.0 " + "\n" +
                        "CSeq: " + str(self.rtspSeq) + "\n" +
                        "Session: " + str(self.sessionId))

            # Keep track of the sent request.
            self.requestSent = self.PAUSE

        # Teardown request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            # Update RTSP sequence number.
            self.rtspSeq = self.rtspSeq + 1

            # Write the RTSP request to be sent.
            request = ( "TEARDOWN " + str(self.fileName) + " RTSP/1.0" + "\n"
                        "CSeq: " + str(self.rtspSeq) + "\n"
                        "Session: " + str(self.sessionId))

            # Keep track of the sent request.
            self.requestSent = self.TEARDOWN
        else:
            return


        # Send the RTSP request using rtspSocket.
        self.rtspSocket.send(request.encode("utf-8"))

        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

            # Close the RTSP socket upon requesting Teardown
            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = data.split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # Process only if the server reply's sequence number is the same as the request's
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # -------------
                        # TO COMPLETE
                        # -------------
                        # Update RTSP state.
                        self.state = self.READY

                        # Open RTP port.
                        self.openRtpPort()
                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY

                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT

                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1




    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # -------------
        # TO COMPLETE
        # -------------
        # Create a new datagram socket to receive RTP packets from the server
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set the timeout value of the socket to 0.5sec
        self.rtpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port given by the client user
            self.state = self.READY
            self.rtpSocket.bind(('', self.rtpPort))
        except:
            tkMessageBox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()
