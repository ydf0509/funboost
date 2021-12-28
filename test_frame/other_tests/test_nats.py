from pynats import NATSClient
import nb_log
# #pip install nats-python
# with NATSClient('nats://192.168.6.134:4222') as client:
#     # Connect
#     client.connect()
#
#     # Subscribe
#     def callback(msg):
#         print(type(msg))
#         print(f"Received a message with subject {msg.subject}: {msg}")
#
#     client.subscribe(subject="test-subject", callback=callback)
#
#     # Publish a message
#     for i in range(10):
#         client.publish(subject="test-subject", payload=f"test-payload_{i}".encode())
#
#     # wait for 1 message
#     client.wait()


client = NATSClient('nats://192.168.6.134:4222')
# Connect
client.connect()

# Subscribe
def callback(msg):
    print(type(msg))
    print(f"Received a message with subject {msg.subject}: {msg}")

client.subscribe(subject="test_queue66c", callback=callback)

# Publish a message
for i in range(10):
    client.publish(subject="test-subject2", payload=f"test-payload_{i}".encode())

    # wait for 1 message
client.wait()