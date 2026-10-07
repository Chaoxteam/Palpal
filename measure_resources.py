"""Run on Windows: py tools/measure_resources.py PID --seconds 300.
Requires psutil. Samples metrics only, never process content or activity.
"""
import argparse
import csv
import time
import psutil
parser=argparse.ArgumentParser()
parser.add_argument('pid',type=int)
parser.add_argument('--seconds',type=int,default=300)
parser.add_argument('--output',default='palpal-resources.csv')
args=parser.parse_args()
process=psutil.Process(args.pid)
with open(args.output,'w',newline='') as output:
    writer=csv.writer(output);writer.writerow(['elapsed','cpu_percent','rss_bytes','read_bytes','write_bytes'])
    start=time.monotonic()
    while time.monotonic()-start<args.seconds:
        cpu=process.cpu_percent(interval=5)
        io=process.io_counters()
        writer.writerow([round(time.monotonic()-start,1),cpu,process.memory_info().rss,io.read_bytes,io.write_bytes])
