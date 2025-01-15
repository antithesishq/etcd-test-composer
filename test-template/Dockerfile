FROM docker.io/ubuntu:latest 

# Install python and other dependencies
RUN apt-get update -y && apt-get install -y \
    python3 pip wget python3-etcd3 python3-numpy python3-protobuf python3-filelock

# Install java
RUN apt-get install -y openjdk-17-jdk

# Install Antithesis Python SDK
RUN pip install antithesis cffi --break-system-packages

# Install go
RUN wget https://golang.org/dl/go1.22.5.linux-amd64.tar.gz
RUN tar -C /usr/local -xzf go1.22.5.linux-amd64.tar.gz
ENV PATH=$PATH:/usr/local/go/bin 

# Copy entrypoint that will produce a lifecycle message
COPY ./entrypoint/entrypoint.py /entrypoint.py

# Copy scripts & executables into required directory for Test Composer
COPY ./main/parallel_driver_generate_traffic.py /opt/antithesis/test/v1/main/parallel_driver_generate_traffic.py

COPY ./main/eventually_health_check.sh /opt/antithesis/test/v1/main/eventually_health_check.sh

WORKDIR /opt/antithesis

COPY ./main/go.mod /opt/antithesis/go.mod
COPY ./main/go.sum /opt/antithesis/go.sum
COPY ./main/serial_driver_validate_operations.go /opt/antithesis/serial_driver_validate_operations.go

RUN go build -o /opt/antithesis/test/v1/main/serial_driver_validate_operations -race

# Copy additional resources into a resources folder (could be any directory except for the test composer directory)
COPY ./resources/request.py /opt/antithesis/resources/request.py
COPY ./resources/local_file_helper.py /opt/antithesis/resources/local_file_helper.py

# Need empty files to track operations and ids
COPY ./local-txt-files/operations.txt /opt/antithesis/local-txt-files/operations.txt
COPY ./local-txt-files/client-traffic-ids.txt /opt/antithesis/local-txt-files/client-traffic-ids.txt

COPY ./java-validation /opt/antithesis/java-validation
