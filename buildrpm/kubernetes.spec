
%global debug_package   %{nil}
%global _find_debuginfo_dwz_opts %{nil}
%global _dwz_low_mem_die_limit 0
%global _buildhost build-ol%{?oraclelinux}-%{?_arch}.oracle.com

#I really need this, otherwise "version_ldflags=$(kube::version_ldflags)"
# does not work
%global _buildshell /bin/bash
%global _checkshell /bin/bash

# k8s release version major.minor
%global major          1
%global minor          34
%global patch          3
%global k8s_repo       kubernetes

Name:          kubernetes
Version:       1.34.3
Release:       1%{?dist}
Summary:       Container cluster management
License:       ASL 2.0
Group:         System/Management
URL:           https://kubernetes.io
Vendor:        Oracle America
ExclusiveArch: x86_64 ppc64le %{arm} aarch64
Source:        %{name}-%{version}.tar.bz2
Source31:      genmanpages.sh
Source40:      10-kubeadm.conf
Source41:      kubelet.service
Source43:      k8s.conf
Source44:      br_netfilter.conf
Source46:      kubectl-proxy.service
Source47:      10-kubectl-proxy.conf
Source51:      kubelet
BuildRequires: golang
BuildRequires: systemd
BuildRequires: rsync
BuildRequires: pandoc
BuildRequires: git

%description
Kubernetes (K8s) is an open-source system for automating deployment, scaling, and management of containerized applications.

%package -n kubelet
Summary: Container cluster management
BuildRequires: golang
BuildRequires: systemd
BuildRequires: curl
BuildRequires: gcc
BuildRequires: glibc
BuildRequires: glibc-static
BuildRequires: binutils

Requires: iptables >= 1.4.21
Requires: socat
Requires: util-linux
Requires: ethtool
Requires: iproute
Requires: iproute-tc
Requires: ebtables
Requires: conntrack
Requires: containernetworking-cni
Requires: openssl
Requires: kata-containers
Requires: %{_sysconfdir}/crio/1.34

%description -n kubelet
The node agent of Kubernetes, the container cluster manager.

%package -n kubectl
Summary: Command-line utility for interacting with a Kubernetes cluster.

%description -n kubectl
Command-line utility for interacting with a Kubernetes cluster.

%package -n kubeadm
Summary: Command-line utility for administering a Kubernetes cluster.

%description -n kubeadm
Command-line utility for administering a Kubernetes cluster.

%prep
%setup -q -n %{k8s_repo}-%{version}

dirs=$(ls | grep -v "^Godeps")

# Move all the code under src/k8s.io/kubernetes directory
mkdir -p src/k8s.io/kubernetes
mv $(ls | grep -v "^src$") src/k8s.io/kubernetes/
mv .go-version src/k8s.io/kubernetes/

%build
pushd src/k8s.io/kubernetes/
export KUBE_EXTRA_GOPATH=$(pwd)/Godeps/_workspace

export GOPATH=$(pwd)/Godeps/_workspace
export KUBE_GIT_TREE_STATE=clean
export KUBE_GIT_VERSION=v%{version}+%{release}
export KUBE_GIT_MAJOR=%{major}
export KUBE_GIT_MINOR=%{minor}

go version

make WHAT='cmd/kubelet cmd/kubectl cmd/kubeadm' GOFLAGS="-trimpath=false" GOLDFLAGS="-X main.VERSION=v%{version}"

bash hack/update-generated-docs.sh

# convert md to man
pushd docs
pushd admin
cp kube-apiserver.md kube-controller-manager.md kube-proxy.md kube-scheduler.md kubelet.md ..
popd
cp %{SOURCE31} genmanpages.sh
bash genmanpages.sh
popd
popd

%install
pushd src/k8s.io/kubernetes/
. hack/lib/init.sh

%ifarch %{arm} arm64 aarch64
output_path="${KUBE_OUTPUT_BIN}/linux/arm64"
%else
output_path="${KUBE_OUTPUT_BIN}/linux/amd64"
%endif

binaries=(kubelet kubectl kubeadm)
install -m 755 -d %{buildroot}%{_bindir}
for bin in "${binaries[@]}"; do
  echo "+++ INSTALLING ${bin}"
  install -p -m 755 -t %{buildroot}%{_bindir} ${output_path}/${bin}
done

# install the bash completion
install -d -m 0755 %{buildroot}%{_datadir}/bash-completion/completions/
%{buildroot}%{_bindir}/kubectl completion bash > %{buildroot}%{_datadir}/bash-completion/completions/kubectl

# install manpages
install -d %{buildroot}%{_mandir}/man1
install -p -m 644 docs/man/man1/kubectl* %{buildroot}%{_mandir}/man1
install -p -m 644 docs/man/man1/kubelet* %{buildroot}%{_mandir}/man1
install -p -m 644 docs/man/man1/kubeadm* %{buildroot}%{_mandir}/man1
# from k8s tarball copied docs/man/man1/*.1

# EXTRA FOR KUBEADM/KUBELET
install -m 755 -d %{buildroot}%{_sysconfdir}/systemd/system/kubelet.service.d/
install -p -m 644 -t %{buildroot}%{_sysconfdir}/systemd/system/kubelet.service.d %{SOURCE40}
install -m 755 -d %{buildroot}%{_sysconfdir}/systemd/system/kubectl-proxy.service.d/
install -p -m 644 -t %{buildroot}%{_sysconfdir}/systemd/system/kubectl-proxy.service.d %{SOURCE47}

install -m 755 -d %{buildroot}%{_sysconfdir}/kubernetes/manifests/
install -m 755 -d %{buildroot}%{_sysconfdir}/systemd/system/
install -m 755 -d %{buildroot}/usr/libexec/kubernetes/kubelet-plugins/volume/exec/

install -p -m 644 -t %{buildroot}%{_sysconfdir}/systemd/system/ %{SOURCE41}
install -p -m 644 -t %{buildroot}%{_sysconfdir}/systemd/system/ %{SOURCE46}
install -d -m 755 %{buildroot}/etc/sysctl.d
install -p -m 644 -t %{buildroot}/etc/sysctl.d %{SOURCE43}
install -d -m 755 %{buildroot}/etc/modules-load.d
install -p -m 644 -t %{buildroot}/etc/modules-load.d %{SOURCE44}

install -d -m 755 %{buildroot}/etc/sysconfig
install -p -m 755 -t %{buildroot}/etc/sysconfig %{SOURCE51}

popd
mv src/k8s.io/kubernetes/*.md .
mv src/k8s.io/kubernetes/LICENSE .
mv src/k8s.io/kubernetes/THIRD_PARTY_LICENSES.txt .

%check
#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files -n kubelet
%license LICENSE THIRD_PARTY_LICENSES.txt
%{_bindir}/kubelet
%{_sysconfdir}/sysconfig/kubelet
%{_sysconfdir}/systemd/system/kubelet.service
%config(noreplace) %{_sysconfdir}/systemd/system/kubelet.service.d/10-kubeadm.conf
%{_sysconfdir}/kubernetes/manifests/
/usr/libexec/kubernetes/kubelet-plugins/volume/exec
%doc *.md
%{_mandir}/man1/kubelet*
/etc/sysctl.d/k8s.conf
/etc/modules-load.d/br_netfilter.conf

%files -n kubeadm
%license LICENSE THIRD_PARTY_LICENSES.txt
%doc *.md
%{_mandir}/man1/kubeadm*
%{_bindir}/kubeadm

%files -n kubectl
%license LICENSE THIRD_PARTY_LICENSES.txt
%{_bindir}/kubectl
%{_sysconfdir}/systemd/system/kubectl-proxy.service.d/10-kubectl-proxy.conf
%{_sysconfdir}/systemd/system/kubectl-proxy.service
%doc *.md
%{_mandir}/man1/kubectl*
%{_datadir}/bash-completion/completions/kubectl

%pre -n kubeadm
# check if this is an upgrade
if [ "$1" == "2" ]; then
    #check if we are upgrading from earlier than 1.11
    # upgrade
    RPM_VERSION=`/bin/rpm -q --queryformat='%{VERSION}' kubeadm 2>&1`
    _major_version=`echo $RPM_VERSION | /bin/awk -F '.' '{print $2}'`
    # any version prior to 1.11 are not compatible
    if [ "${_major_version}" -lt "11" ]; then
        if [ -z "${FORCE_UPDATE_12_FROM_9}" ]; then
            echo 'Can not upgrade kubeadm from version prior to 1.11 due to upgrade compatibility'
            exit 1
        fi
        echo "Upgrading kubeadm forcefully from version earlier that 1.11"
    fi
fi

%post -n kubelet
modprobe br_netfilter
sysctl -p /etc/sysctl.d/k8s.conf
%systemd_post kubelet
if [ $1 -gt 1 ] ; then
  systemctl daemon-reload >/dev/null 2>&1
  systemctl try-restart kubelet >/dev/null 2>&1
fi

%preun -n kubelet
%systemd_preun kubelet

%postun -n kubelet
%systemd_postun_with_restart kubelet

%changelog
* Wed Dec 10 2025 Oracle Cloud Native Environment Authors <noreply@oracle.com> - 1.34.3-1
- Added Oracle specific build files for Kubernetes
