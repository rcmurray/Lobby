import threading
import queue
from flask import Flask, request, jsonify

app = Flask(__name__)

# Queue to hold the tasks
task_queue = queue.Queue()

# Worker function for the consumer
def worker():
    while True:
        task = task_queue.get()
        if task is None:
            break

        # Process the task (replace this with your actual task processing logic)
        result = f"Processed: {task}"
        print(result)

# Create and start the consumer thread
consumer_thread = threading.Thread(target=worker)
consumer_thread.start()

# Route to handle incoming tasks from the web interface
# @app.route('/add_task', methods=['POST','GET'])
@app.get('/login/<username>')
def login_get(username):
# def add_task(username):
    task_queue.put(username)
    return username
    # task_data = request.json
    # if 'task' in task_data:
    #     task = task_data['task']
    #     task_queue.put(task)
    #     return jsonify({"status": "Task added successfully."})
    #
    # return jsonify({"error": "Invalid request."}), 400

# Main route to display the web interface
@app.route('/')
def index():
    return "Welcome to the Producer-Consumer Queue!"

# Shut down the consumer thread when the server stops
def shutdown_server():
    task_queue.put(None)
    consumer_thread.join()

if __name__ == '__main__':
    app.run(debug=True, threaded=True)

    # When the server is shut down, stop the consumer thread as well
    shutdown_server()