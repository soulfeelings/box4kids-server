#!/usr/bin/env python3
"""
Скрипт для запуска RabbitMQ воркеров
"""

import sys
import logging
from workers.toybox_worker import ToyBoxWorker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    if len(sys.argv) != 2:
        print("Usage: python start_worker.py <worker_type>")
        print("Available workers: toybox")
        return
    
    worker_type = sys.argv[1]
    
    if worker_type == "toybox":
        worker = ToyBoxWorker()
        worker.start()
    else:
        print(f"Unknown worker type: {worker_type}")
        print("Available workers: toybox")

if __name__ == "__main__":
    main() 