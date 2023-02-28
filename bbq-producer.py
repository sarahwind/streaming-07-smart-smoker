"""
BBQ producer

Author: Sarah Windeknecht
Date: February 14, 2023
"""

import csv
import pika
import sys
import time
import webbrowser

# declare variables
smoker_temp_queue = "01-smoker"
foodA_temp_queue = "02-food-A"
foodB_temp_queue = "03-food-B"
csv_file = 'smoker-temps.csv'

def offer_rabbitmq_admin_site(show_offer):

    """Offer to open the RabbitMQ Admin website"""

    if show_offer == "True":
        ans = input("Would you like to monitor RabbitMQ queues? y or n ")
        print()
        if ans.lower() == "y":
            webbrowser.open_new("http://localhost:15672/#/queues")
            print()
    else: 
        webbrowser.open_new("http://localhost:15672/#/queues")
        print()

def main(host: str):
    """
    Creates and sends a message to the queue each execution.
    This process runs and finishes.

    Parameters:
        host (str): the host name or IP address of the RabbitMQ server
        smoker_temp_queue (str): smoker queue
        foodA_temp_queue (str): food A queue
        foodB_temp_queue (str): food B queue
        csv_file: csv read
    """
    # read csv
    with open(csv_file, 'r') as file:
        reader = csv.reader(file, delimiter=',')
        #skip header
        header = next(reader)
    
        try:
            # create a blocking connection to the RabbitMQ server
            conn = pika.BlockingConnection(pika.ConnectionParameters(host))
            # use the connection to create a communication channel
            ch = conn.channel()
        
            # clear queue to clear out old messages
            ch.queue_delete(smoker_temp_queue)
            ch.queue_delete(foodA_temp_queue)
            ch.queue_delete(foodB_temp_queue)

            # use the channel to declare a durable queue
            # a durable queue will survive a RabbitMQ server restart
            # and help ensure messages are processed in order
            # messages will not be deleted until the consumer acknowledges
            ch.queue_declare(smoker_temp_queue, durable=True)
            ch.queue_declare(foodA_temp_queue, durable=True)
            ch.queue_declare(foodB_temp_queue, durable=True)
    
            for row in reader:
                Time,Channel1,Channel2,Channel3 = row

                # convert numbers to floats
                try:
                    smoker_temp = float(Channel1)
                    #get smoker temp and send message
                    fstring_smoker_message = f"{Time}, {smoker_temp}"
                    smoker_message = fstring_smoker_message.encode()
                    # use the channel to publish a message to the queue
                    ch.basic_publish(exchange="", routing_key=smoker_temp_queue, body=smoker_message)
                    print(f" [x] Sent {smoker_message} on {smoker_temp_queue}")
                except ValueError:
                    pass

                try:
                    foodA_temp = float(Channel2)
                    # get food A temp and send message
                    fstring_foodA_message = f"{Time}, {foodA_temp}"
                    foodA_message = fstring_foodA_message.encode()
                    # use the channel to publish a message to the queue
                    ch.basic_publish(exchange="", routing_key=foodA_temp_queue, body=foodA_message)
                    print(f" [x] Sent {foodA_message} on {foodA_temp_queue}")
                except ValueError:
                    pass
    
                try:
                    foodB_temp = float(Channel3)
                    # get food B and send message
                    fstring_foodB_message = f"{Time}, {foodB_temp}"
                    foodB_message = fstring_foodB_message.encode()
                    # use the channel to publish a message to the queue
                    ch.basic_publish(exchange="", routing_key=foodB_temp_queue, body=foodB_message)
                    print(f" [x] Sent {foodB_message} on {foodB_temp_queue}")
                except ValueError:
                    pass
            
                    # read values every half minute
                time.sleep(30)

        except pika.exceptions.AMQPConnectionError as e:
            print(f"Error: Connection to RabbitMQ server failed: {e}")
            sys.exit(1)
        finally:
        # close the connection to the server
            conn.close()

# Standard Python idiom to indicate main program entry point
# This allows us to import this module and use its functions
# without executing the code below.
# If this is the program being run, then execute the code below
if __name__ == "__main__":  
    
    offer_rabbitmq_admin_site("False")

    main("localhost")
