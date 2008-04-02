# Kickstart file automatically generated by anaconda.

install
url --url http://download.fedora.redhat.com/pub/fedora/linux/releases/8/Fedora/i386/os/

%include common-install.ks

# Create some fake iSCSI partitions
logvol /iscsi3 --name=iSCSI3 --vgname=VolGroup00 --size=64 --grow
logvol /iscsi4 --name=iSCSI4 --vgname=VolGroup00 --size=64 --grow
logvol /iscsi5 --name=iSCSI5 --vgname=VolGroup00 --size=64 --grow

repo --name=f8 --mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=fedora-8&arch=i386
repo --name=f8-updates --mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f8&arch=i386
repo --name=ovirt-management --baseurl=http://ovirt.et.redhat.com/repos/ovirt-management-repo/i386/

%packages
%include common-pkgs.ks

%post

%include common-post.ks

%include devel-post.ks

# get the PXE boot image; this can take a while
PXE_URL=http://ovirt.org/download
IMAGE=ovirt-pxe-host-image-i386-0.3.tar.bz2
wget ${PXE_URL}/$IMAGE -O /tmp/$IMAGE
tar -C / -jxvf /tmp/$IMAGE
rm -f /tmp/$IMAGE

%end
