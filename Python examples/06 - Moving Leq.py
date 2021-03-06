import asyncio
import socket
import requests
# Modules to convert webxi data
import webxi.webxi_header as webxiHead
import webxi.webxi_stream as webxiStream
# Help functions located in HelpFunction folder
# Read these files to get examples on how to communicate with the SLM
import HelpFunctions.stream_handler as stream           # SLM stream functions
import HelpFunctions.measurment_handler as meas         # Start/pause/Stop measurments functions
import HelpFunctions.sequence_handler as seq            # Get sequences, e.g. LAeq functions
from HelpFunctions.Leq import MovingLeq, SLM_Setup_LAeq # Class to hold moving Leq 
import HelpFunctions.websocket_handler as webSocket     # Async functions to control communication


# Setup device 
ip = "169.254.3.40"
host = "http://" + ip
socket.gethostbyname(socket.gethostname())

# Setup streaming info 
"""Sequence 6 is logging LAeq, but this is not guaranteed. """
sequenceId = 6


def print_LAeq_mov(message, data_type, leq_mov):
    """This is the function handling the data from the BK2245\n
       This function prints the data to the terminal in the format:\n
       "LAeq: Inst_Val | LAeq,mov,10s: AVG_Val"""
    package = webxiStream.WebxiStream.from_bytes(message)
    if package.header.message_type == webxiStream.WebxiStream.Header.EMessageType.e_sequence_data:
        value = package.content.sequence_blocks[0].values
        # Convert data from binary stream data to Int format
        LAeq_value = stream.data_type_conv(data_type, value, None) / 100 
        LAeq_mov_value = leq_mov.move(LAeq_value)
        print("LAeq: " + "%.1f" % LAeq_value + "  |  LAeq,mov,10s:" + "%.1f" % LAeq_mov_value)

async def main():
    # Setup the SLM to run LAeq 
    SLM_Setup_LAeq(host)

    # Get ID and object of sequence, the data for the wanted logging mode
    ID, sequence = seq.get_sequence(host,sequenceId) 

    # Get URI for stream
    uri = stream.setup_stream(host,ip,ID,"Test")   

    # Get datatype of the logging data 
    data_type = sequence["DataType"]  

    # Start a measurement. This is needed to obtain data from the device
    meas.start_pause_measurement(host,True)

    # Initilize a MovingLeq object to handle the data. 
    # This example uses a 10s moving leq (assuming 1s logging)
    leq_10_mov = MovingLeq(10)

    # Create lambda function to use for the stream message. In this example is a function
    # call used
    msg_func = lambda msg : print_LAeq_mov(msg, data_type, leq_10_mov)

    # Initilize and run the websocket to retrive data
    await webSocket.next_async_websocket(uri,msg_func)

if __name__ == "__main__":
    asyncio.run(main())
