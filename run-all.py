import subprocess
import time

def start_mock_api():
    return subprocess.Popen(["uvicorn", "mock-api:app", "--host", "0.0.0.0", "--port", "5000", "--reload"])

def start_scheduler_api():
    return subprocess.Popen(["uvicorn", "bm-scheduler-q:app", "--host", "0.0.0.0", "--port", "8080", "--reload"])

if __name__ == "__main__":
    # Activate Mock API
    mock_process = start_mock_api()
    time.sleep(2)

    # Activate Scheduler API
    scheduler_process = start_scheduler_api()

    try:
        # Wait for the processes to finish
        mock_process.wait()
        scheduler_process.wait()
    except KeyboardInterrupt:
        print("Stopping services...")
        mock_process.terminate()
        scheduler_process.terminate()