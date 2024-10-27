# Protocol Explanation
A simple protocol used to send and receive messages from a client to a server and vice versa. Each message is made of:
* A command key word in a specified length of 3 
* A 3 digit integer representing the length of the Data to be received
* The data to be received

Diagram:
Command(3) + Length(3) + Data(Length)
