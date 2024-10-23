import signal


def stop_signal_handler(signal, frame) -> None:
    global stop_signal_received
    stop_signal_received = True
    print("Stop signal received (CTRL + C), exiting...")
    # sys.exit(0)


stop_signal_received = False
signal.signal(signal.SIGINT, stop_signal_handler)


def register_signals():
    signal.signal(signal.SIGINT, stop_signal_handler)
