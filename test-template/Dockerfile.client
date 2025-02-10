FROM docker.io/ubuntu:latest 

# Install dependencies
RUN apt-get update -y && apt-get install -y pip wget


# JAVA:

# Install java
RUN apt-get install -y openjdk-17-jdk maven

# Copying .java & pom files, maven library installs, removing unnecessary directories that were created
COPY ./java-health-check /opt/antithesis/java-health-check
WORKDIR /opt/antithesis/java-health-check
RUN mvn dependency:copy-dependencies -DoutputDirectory=target/lib
RUN mvn install
RUN rm -r target/classes/ target/generated-sources/ target/maven-archiver/ target/maven-status/


# RUST:

# Install rust
RUN apt-get install -y curl cargo protobuf-compiler
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
RUN echo 'source $HOME/.cargo/env' >> $HOME/.bashrc

# Copying rust folder and building an executable. (Executable is called from a .sh Test Composer file)
COPY ./rust-db-consistent-lines /opt/antithesis/rust-db-consistent-lines
RUN cargo build --manifest-path=/opt/antithesis/rust-db-consistent-lines/Cargo.toml

# Copying shell executables into Test Composer directory
COPY ./main/finally_db_consistent_lines.sh /opt/antithesis/test/v1/main/finally_db_consistent_lines.sh


# PYTHON:

# Install python and other dependencies
RUN apt-get install -y python3
RUN apt install -y python3-etcd3 python3-numpy python3-protobuf python3-filelock

# Install Antithesis Python SDK
RUN pip install antithesis cffi --break-system-packages

# Copying python entrypoint. It contains the lifecycle setup_complete message.
COPY ./entrypoint/entrypoint.py /entrypoint.py

# Copying python script into required directory for Test Composer
COPY ./main/parallel_driver_generate_traffic.py /opt/antithesis/test/v1/main/parallel_driver_generate_traffic.py


# GO:

# Install go
RUN wget https://golang.org/dl/go1.22.5.linux-amd64.tar.gz
RUN tar -C /usr/local -xzf go1.22.5.linux-amd64.tar.gz
ENV PATH=$PATH:/usr/local/go/bin 

# Copying go script and building an executable into Test Composer directory
WORKDIR /opt/antithesis

COPY ./main/go.mod ./go.mod
COPY ./main/go.sum ./go.sum
COPY ./main/serial_driver_validate_operations.go ./serial_driver_validate_operations.go
RUN go build -o /opt/antithesis/test/v1/main/serial_driver_validate_operations -race

# Copting shell executable into Test Composer directory
COPY ./main/eventually_health_check.sh /opt/antithesis/test/v1/main/eventually_health_check.sh


# EXTRA:

# Copying additional resources into a resources folder (could be any directory except for the test composer directory)
COPY ./resources/request.py /opt/antithesis/resources/request.py
COPY ./resources/local_file_helper.py /opt/antithesis/resources/local_file_helper.py

# Copying empty files to track operations and ids
COPY ./local-txt-files/operations.txt /opt/antithesis/local-txt-files/operations.txt
COPY ./local-txt-files/client-traffic-ids.txt /opt/antithesis/local-txt-files/client-traffic-ids.txt
