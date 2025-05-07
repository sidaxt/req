# from flask import Flask, jsonify
# from concurrent.futures import ThreadPoolExecutor, TimeoutError
# import time

# app = Flask(__name__)
# executor = ThreadPoolExecutor(max_workers=2)

# def long_running_task():
#     # Simulate a long-running task (10 seconds)
#     time.sleep(200)
#     return {"message": "Task completed successfully"}

# @app.route('/run-task')
# def run_task():
#     future = executor.submit(long_running_task)
#     try:
#         result = future.result(timeout=15)  # Wait up to 5 seconds
#         return jsonify(result)
#     except TimeoutError:
#         future.cancel()
#         return jsonify({"error": "Task timed out after 5 seconds"}), 504

# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=2)

def long_running_task():
    time.sleep(10)  # Simulate a long-running process
    return {"message": "Task completed successfully"}

@app.route('/run-task')
def run_task():
    # Get timeout from query param, default to 5 seconds if not provided
    try:
        timeout = float(request.args.get('timeout', 5))
    except ValueError:
        return jsonify({"error": "Invalid timeout value"}), 400

    future = executor.submit(long_running_task)
    try:
        result = future.result(timeout=timeout)
        return jsonify(result)
    except TimeoutError:
        future.cancel()
        return jsonify({"error": f"Task timed out after {timeout} seconds"}), 504

if __name__ == '__main__':
    app.run(debug=True)

