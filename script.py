import os
import subprocess
import time
import sys

def run_command(cmd, check=True, capture_output=False):
    if capture_output:
        result = subprocess.run(cmd, shell=True, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    else:
        subprocess.run(cmd, shell=True, check=check)

pid = run_command("/home/ec2-user/opensearch/jdk/bin/jps -l | grep opensearch | awk '{print $1}'", capture_output=True)
print("pid is " + str(pid))

def collect_cpu(size, scenario):
    if not os.path.exists("async-profiler-3.0-linux-x64.tar.gz"):
        run_command("wget https://github.com/async-profiler/async-profiler/releases/download/v3.0/async-profiler-3.0-linux-x64.tar.gz")

    if os.path.exists("async-profiler-3.0-linux-x64.tar.gz") and not os.path.exists("async-profiler-3.0-linux-x64.tar"):
        run_command("gunzip async-profiler-3.0-linux-x64.tar.gz")

    if not os.path.exists("async-profiler-3.0-linux-x64"):
        run_command("tar -xvf async-profiler-3.0-linux-x64.tar")

    os.chdir("async-profiler-3.0-linux-x64")

    run_command("sudo sysctl -w kernel.perf_event_paranoid=1")
    run_command("sudo sysctl -w kernel.kptr_restrict=0")
    os.makedirs("/home/ec2-user/rule_test_output/cpu", exist_ok=True)
    file_name = f"/home/ec2-user/rule_test_output/cpu/{size}_{scenario}_flamegraph1.html"
    run_command(f"sudo -u ec2-user ./bin/asprof -d 180 {pid} -f {file_name}")

def collect_jvm(size, scenario):
    print("Taking first heap dump...")
    os.makedirs("/home/ec2-user/rule_test_output/jvm", exist_ok=True)
    file_name1 = f"/home/ec2-user/rule_test_output/jvm/{size}_{scenario}_heap1.hprof"
    run_command(f"/home/ec2-user/opensearch/jdk/bin/jmap -dump:live,format=b,file={file_name1} {pid}")
    run_command(f"gzip -9 {file_name1}")

    time.sleep(10)

    print("Taking second heap dump...")
    file_name2 = f"/home/ec2-user/rule_test_output/jvm/{size}_{scenario}_heap2.hprof"
    run_command(f"/home/ec2-user/opensearch/jdk/bin/jmap -dump:live,format=b,file={file_name2} {pid}")
    run_command(f"gzip -9 {file_name2}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <size> <scenario>")
        print("size: small, medium, large")
        print("scenario: 0,1,2,3,4")
        sys.exit(1)

    size = sys.argv[1].lower()
    scenario = sys.argv[2]

    if size not in ("small", "medium", "large"):
        print("Error: size must be one of small, medium, large")
        sys.exit(1)

    if scenario not in ("0", "1", "2", "3", "4"):
        print("Error: scenario must be an integer from 0 to 4")
        sys.exit(1)

    print(f"Running script with size={size} and scenario={scenario}")

    collect_cpu(size, scenario)
    collect_jvm(size, scenario)

if __name__ == "__main__":
    main()