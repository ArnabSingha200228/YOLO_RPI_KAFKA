# Object Detection using YOLO in qemu emulated Raspberry Pi connected to a Kafka network
## 1) Installing Qemu and simulating rpi on qemu
> Download Raspberry Pi OS (64-bit) from Raspberry Pi operating system images.(File already downloadad in local machine). Here we downloaded Raspberry Pi OS (64-bit) with desktop, Kernel version: 6.1, Debian version: 11 (bullseye), Release date: May 3rd 2023, named 2023-05-03-raspios-bullseye-arm64.img.

**I. Install the required packages on your host system:**
Cross compilers for arm64 -

	$ sudo apt install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu
	
 Qemu itself
	
	$ sudo apt install qemu qemubuilder qemu-system-gui qemu-system-arm qemu-utils \
    qemu-system-data qemu-system
    
**II. Build the Linux kernel for qemu arm64 (You can download the kernel from  [Kernel.org ](https://www.kernel.org/)):**

	$ wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.1.34.tar.xz
	$ tar xvJf linux-6.1.34.tar.xz
	$ cd linux-6.1.34
   >
    $ # create a .config file
    $ ARCH=arm64 CROSS_COMPILE=/bin/aarch64-linux-gnu- make defconfig
    $ # Use the kvm_guest config as the base defconfig, which is suitable for qemu
    $ ARCH=arm64 CROSS_COMPILE=/bin/aarch64-linux-gnu- make kvm_guest.config
    $ # Build the kernel
    $ ARCH=arm64 CROSS_COMPILE=/bin/aarch64-linux-gnu- make -j8
   >
    $ cp arch/arm64/boot/Image /home/mydir
**III. Mount the image for enabling ssh and configuring username and password:**

i) Get the correct offset value with the help of  `fdisk`  utility:
    
	$ fdisk -l 2023-05-03-raspios-bullseye-arm64.img
   >
	Disk 2023-05-03-raspios-bullseye-arm64.img: 4.11 GiB, 4412407808 bytes, 8617984 sectors
    Units: sectors of 1 * 512 = 512 bytes
    Sector size (logical/physical): 512 bytes / 512 bytes
    I/O size (minimum/optimal): 512 bytes / 512 bytes
    Disklabel type: dos
    Disk identifier: 0x3e247b30
    Device                                 Boot  Start     End Sectors  Size Id Type
    2023-05-03-raspios-bullseye-arm64.img1        8192  532479  524288  256M  c W95 FAT32 (LBA)
    2023-05-03-raspios-bullseye-arm64.img2      532480 8617983 8085504  3.9G 83 Linux

As we can see, we have two partitions inside the downloaded image. The first device (partition) is the bootable partition, and the second one is the root filesystem. The first partition is what will be mounted as `/boot` in Raspberry Pi, and this is where we'll need to create some files.  
Obtain the correct **offset** of the first device by multiplying the start of the first partition (here 8192) by the sector size (here 512). Here it will be calculated as **8192 * 512 = 4194304**

ii)  Mount the image in  `/mnt/rpi`  directory:

	$ # mkdir /mnt/rpi if necessery    
    $ sudo mkdir /mnt/rpi
    $ sudo mount -o loop,offset=4194304 2023-05-03-raspios-bullseye-arm64.img /mnt/rpi
iii)  Create a file named  `ssh`  to enable ssh
  
    $ cd /mnt/rpi
    $ sudo touch ssh
iv) Additionally, create a file named  `userconf.txt`  in the same directory and put your desired username and password there, like  `<username>:<hashed-password>`  (might be better to leave the username as  `pi`). This will be your default credentials:
    
    $ openssl passwd -6                                     # Generate the <hashed-password>
    $ echo 'pi:<hashed-password>' | sudo tee userconf.txt   # Put them inside `userconf.txt`
v) Finally, unmount the image:
    
    $ sudo umount /mnt/rpi
vi) Create a startup script:
	
	$ nano rpistart.sh
>
Paste the following code there

	$ qemu-system-aarch64 -machine virt -cpu cortex-a72 -smp 6 -m 4G \
	    -kernel Image -append "root=/dev/vda2 rootfstype=ext4 rw panic=0 console=ttyAMA0" \
	    -drive format=raw,file=2024-10-22-raspios-bullseye-arm64.img,if=none,id=hd0 \
	    -device virtio-blk,drive=hd0,bootindex=0 \
	    -netdev tap,id=mynet,ifname=tap0,script=no,downscript=no \
	    -device virtio-net-pci,netdev=mynet \
	    -monitor telnet:127.0.0.1:5555,server,nowait
vii) Start the qemu:

	$ ./rpistart.sh
	$ sudo ip addr add 192.168.76.2/24 dev eth0
	$ sudo ip link set dev eth0 up
Now login with your id and password.

**IV. Setup networkng between rpi and host**
	
i) Install bridge utilities in the Host machine (if not already installed):
	
	$ sudo apt install bridge-utils

ii) Create a TAP interface (in Host machine):

	$ sudo ip tuntap add dev tap0 mode tap user $(whoami)
	$ sudo ip link set tap0 up
	$ sudo ip addr add 192.168.76.1/24 dev tap0
iii) Run in guest machine:

	$ sudo nano /etc/dhcpcd.conf
iv) Append to file
	
	$ interface eth0
	$ static ip_address=192.168.76.2/24
	$ static routers=192.168.76.1
	$ static domain_name_servers=8.8.8.8
Save and exit.

v) Test the connection:

	$ ping 192.168.76.1      # Ping host
	$ ssh <youruser>@192.168.76.1  # SSH from guest to host
Restart if required.

vi) Activate ssh if needed

	$ sudo systemctl enable ssh
	$ sudo systemctl start ssh

> Note :  The networking setup of the host machine may be repeated if the machine is restarted.

**V. Expanding the disk size of rpi**

Resize the disk image (Make sure your VM is _shut down_, then on your _host_ machine run):

	$ qemu-img resize -f raw 2024-10-22-raspios-bullseye-arm64.img +32G
This adjust the amount of increase as per your need.

Now in Guest machine login an run:

	$ sudo fdisk /dev/sda
n the `fdisk>` prompt:

	p      # print partitions; note the START of /dev/sda2
	d      # delete partition 2
	n      # new partition → primary (p), number 2
	       # For START, enter the exact same sector you noted.
	       # For END, just press ENTER to use all remaining space.
	w      # write changes
>
	$	sudo reboot
After reboot, grow the filesystem:

	$ sudo resize2fs /dev/sda2

Check with: 

	$ df -h

**VI. Setting up YOLO**
1) Download/create a dataset that is annotated to be compatible with YOLO.
2) Run YOLO fine tuning / Training from scratch. 
We are not going to do it here. We have a model trained `best.pt`which was trained beforehand, in a furniture dataset.
3) We import the model in out code and simply infer.

**VII. Socket Programming and others**
The qemu emulated rpi can't directly connect to the network outside the host machine. So we will need to communicate between qemu emulated rpi and the host machine. The host machine is working like a proxy to the qemu. We have the corresponding file in the machine. 

## 2) Setting up Kafka
**I. Kafka installation**
1) Install java

		$ sudo apt update
		$ sudo apt install default-jdk

2) Download Zookeeper and Kafka binaries

		$ wget https://downloads.apache.org/kafka/3.7.0/kafka_2.13-3.7.0.tgz
		$ tar -xzf kafka_2.13-3.7.0.tgz
		$ cd kafka_2.13-3.7.0
3)  Setup for communication

	i) Start Zookeeper

		 $ bin/zookeeper-server-start.sh config/zookeeper.properties

	ii) Start Kafka server
	
		 $ bin/kafka-server-start.sh config/server.properties
	iii) Create a Kafka topic

		$ bin/kafka-topics.sh --create --topic test-topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1


## 3) Starting the system

**I. Start the consumer**
	In the terminal of the consumer machine activate necessary virtual environment and run -
	
	$ python consumer1.py
	
**I. Start the Receiver + Producer**
		In the terminal of the producer machine activate necessary virtual environment and run -
		
	$ python receiver_producer1.py

**I. Start the rpi sender**
	In the terminal of the rpi activate necessary virtual environment and run -
	
	$ python YOLO_sender.py
	
