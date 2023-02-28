"""
    Sarah Windeknecht
    February 7, 2023
    
    This program continuously listens for messages from the Smart Smoker producer on the producer queue.
   

"""

import pika
import sys
from collections import deque

# declare variables
smoker_temp_queue = "01-smoker"
smoker_deque = deque(maxlen=5)  # limited to 5 items (the 5 most recent readings)

# define a callback function to be called when a message is received
def smoker_callback(ch, method, properties, body):
    """ Define behavior on getting a message about the smoker temperature."""
    #define a list to place smoker temps initializing with 0
    smokertemp = ['0']
    # split timestamp and temp
    message = body.decode().split(",")
    # assign the temp to a variable and convert to float
    smokertemp[0] = float(message[-1])
    # add the temp to the deque
    smoker_deque.append(smokertemp[0])
    # check to see that the deque has 5 items before analyzing
    if len(smoker_deque) == 5:
        # assign difference in most recent temp and oldest temp in deque to a variable as a float
        smoker_temp_check = round(float(smoker_deque[-1]-smoker_deque[0]), 1)
        # if the temp decreases by 15 degrees or more in 2.5 minutes, then an alert is sent
        if smoker_temp_check <= -15:
            print("SMOKER ALERT: Current smoker temp is:", smokertemp[0],";", "Smoker temp change in last 2.5 minutes is:", smoker_temp_check, "degrees")
        # Show work in progress, letting the user know the changes
        else:
            print("Current smoker temp is:", smokertemp[0])
    else:
        #if the deque has less than 5 items the current temp is printed
        print("Current smoker temp is:", smokertemp[0])
    # acknowledge the message was received and processed 
    # (now it can be deleted from the queue)
    ch.basic_ack(delivery_tag=method.delivery_tag)



# define a main function to run the program
def main(hn: str = "localhost", qn: str = "task_queue"):
    """ Continuously listen for task messages on a named queue.
    
    Parameters:
        host (str): the host name or IP address of the RabbitMQ server
        smoker_temp_queue (str): smoker queue
        """

    # when a statement can go wrong, use a try-except block
    try:
        # try this code, if it works, keep going
        # create a blocking connection to the RabbitMQ server
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=hn))

    # except, if there's an error, do this
    except Exception as e:
        print()
        print("ERROR: connection to RabbitMQ server failed.")
        print(f"Verify the server is running on host={hn}.")
        print(f"The error says: {e}")
        print()
        sys.exit(1)

    try:
        # use the connection to create a communication channel
        channel = connection.channel()

        # use the channel to clear the queue
        channel.queue_delete(smoker_temp_queue)
        
        # use the channel to declare a durable queue
        # a durable queue will survive a RabbitMQ server restart
        # and help ensure messages are processed in order
        # messages will not be deleted until the consumer acknowledges
        channel.queue_declare(smoker_temp_queue, durable=True)

        # The QoS level controls the # of messages
        # that can be in-flight (unacknowledged by the consumer)
        # at any given time.
        # Set the prefetch count to one to limit the number of messages
        # being consumed and processed concurrently.
        # This helps prevent a worker from becoming overwhelmed
        # and improve the overall system performance. 
        # prefetch_count = Per consumer limit of unaknowledged messages      
        channel.basic_qos(prefetch_count=1) 

        # configure the channel to listen on a specific queue,  
        # use the callback function named smoker_callback,
        # and do not auto-acknowledge the message (let the callback handle it)
        channel.basic_consume(smoker_temp_queue, auto_ack = False, on_message_callback=smoker_callback)

        # print a message to the console for the user
        print(" [*] Ready for work. To exit press CTRL+C")

        # start consuming messages via the communication channel
        channel.start_consuming()

    # except, in the event of an error OR user stops the process, do this
    except Exception as e:
        print()
        print("ERROR: something went wrong.")
        print(f"The error says: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print(" User interrupted continuous listening process.")
        sys.exit(0)
    finally:
        print("\nClosing connection. Goodbye.\n")
        connection.close()


# Standard Python idiom to indicate main program entry point
# This allows us to import this module and use its functions
# without executing the code below.
# If this is the program being run, then execute the code below
if __name__ == "__main__":
    # call the main function with the information needed
    main("localhost", "smoker_temp_queue")
