
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
%global minor          32
%global patch          4
%global image_registry container-registry.oracle.com/olcne

%global image_version %{version}

Name:          kubernetes-container-image
Version:       1.32.4
Release:       1%{?dist}
Summary:       Container cluster management
License:       ASL 2.0
Group:         System/Management
URL:           https://kubernetes.io
Vendor:        Oracle America
ExclusiveArch: x86_64 ppc64le %{arm} aarch64
Source:        %{name}-%{version}.tar.bz2

%description
Kubernetes (K8s) is an open-source system for automating deployment, scaling, and management of containerized applications.

%package -n kubeadm-container-images
Summary: Contains Oracle built k8s docker images

%description -n kubeadm-container-images
Contains Oracle built k8s docker images

%prep
%setup -q -n %{name}-%{version}

%build
export KUBE_GIT_TREE_STATE=clean
export KUBE_GIT_VERSION=v%{version}+%{release}
export KUBE_GIT_MAJOR=%{major}
export KUBE_GIT_MINOR=%{minor}

export KUBE_EXTRA_GOPATH=$(pwd)/Godeps/_workspace
export GOPATH=$(pwd)/Godeps/_workspace

make WHAT='cmd/kube-proxy cmd/kube-apiserver cmd/kube-controller-manager cmd/kube-scheduler cmd/kubectl' GOFLAGS="-trimpath=false" GOLDFLAGS="-X main.VERSION=v%{version}"

%ifarch %{arm} arm64 aarch64
arch=aarch64
%else
arch=x86_64
%endif

chmod +x build-k8s-docker.sh
./build-k8s-docker.sh \
    %{image_version} \
    _output/bin \
    %{image_registry} \
    %{oraclelinux} \
    ${arch}

%install
mkdir -p %{buildroot}/usr/local/share/olcne
install -m 755 -d %{buildroot}/usr/local/share/olcne
images=(kube-apiserver.tar kube-controller-manager.tar kube-scheduler.tar kube-proxy.tar kubectl.tar)
for bin in "${images[@]}"; do
  echo "+++ INSTALLING DOCKER IMAGES ${bin}"
  install -p -m 755 -t %{buildroot}/usr/local/share/olcne _output/bin/oracle_docker/${bin}
done

%files -n kubeadm-container-images
%license LICENSE THIRD_PARTY_LICENSES.txt
/usr/local/share/olcne/kube-apiserver.tar
/usr/local/share/olcne/kube-controller-manager.tar
/usr/local/share/olcne/kube-scheduler.tar
/usr/local/share/olcne/kube-proxy.tar
/usr/local/share/olcne/kubectl.tar

%changelog
* Thu Feb 12 2026 Oracle Cloud Native Environment Authors <noreply@oracle.com> - 1.32.4-1
- Added Oracle specific build files for Kubernetes
