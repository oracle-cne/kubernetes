#!/bin/bash -x
#
# Copyright (c) 2019-2025, Oracle and/or its affiliates. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -o errexit
set -o nounset
set -o pipefail

if [[ ${#} -eq 0 ]] ; then
    echo "usage:" >&2
    echo "  ${0} version k8s_binary_location golang_version" >&2
    exit 1
fi

VERSION=v${1}
BINARY_LOCATION=${2}
REGISTRY=${3:-container-registry.oracle.com/olcne}
if [[ ${4} == 9 ]] ; then
  DOCKER_FILE_PATH=./olm/builds/Dockerfile.oracle.ol9
  KUBECTL_DOCKER=./olm/builds/Dockerfile.kubectl.ol9
else
  DOCKER_FILE_PATH=./olm/builds/Dockerfile.oracle.ol8
  KUBECTL_DOCKER=./olm/builds/Dockerfile.kubectl.ol8
fi
export REGISTRY
export BASEIMAGE
ARCH=${5:-x86_64}
echo ARCH=${ARCH}

mkdir -p ${BINARY_LOCATION}/oracle_docker
KUBE_BINARY="kube-apiserver kube-scheduler kube-controller-manager"
for BINARY in ${KUBE_BINARY}; do
        cp ${BINARY_LOCATION}/${BINARY} .

        if [[ ${4} == 9 ]] ; then
          docker build --squash --network=host --build-arg https_proxy=${https_proxy} --build-arg VERSION=${VERSION} --build-arg BINARY=${BINARY} -t ${REGISTRY}/${BINARY}:${VERSION} -f ${DOCKER_FILE_PATH} .
        else
          docker build --squash --build-arg https_proxy=${https_proxy} --build-arg VERSION=${VERSION} --build-arg BINARY=${BINARY} -t ${REGISTRY}/${BINARY}:${VERSION} -f ${DOCKER_FILE_PATH} .
        fi
        docker save -o ${BINARY_LOCATION}/oracle_docker/${BINARY}.tar ${REGISTRY}/${BINARY}:${VERSION}
done

# BUILD KUBECTL
cp ${BINARY_LOCATION}/kubectl .
docker build --build-arg https_proxy=${https_proxy} --build-arg VERSION=${VERSION} --build-arg BINARY=kubectl -t ${REGISTRY}/kubectl:${VERSION} -f ${KUBECTL_DOCKER} .
docker save -o ${BINARY_LOCATION}/oracle_docker/kubectl.tar ${REGISTRY}/kubectl:${VERSION}

# TODO: remove this once OL7 is deprecated
# kube-proxy iptables hack
BINARY=kube-proxy
mkdir kube-proxy
cp buildrpm/kube-proxy/* kube-proxy/.
cp ${BINARY_LOCATION}/kube-proxy kube-proxy/.
cp LICENSE kube-proxy/.
cp THIRD_PARTY_LICENSES.txt kube-proxy/.
pushd kube-proxy/
if [[ ${4} == 9 ]] ; then
  docker build --squash --network=host --build-arg https_proxy=${https_proxy} --build-arg VERSION=${VERSION} -t ${REGISTRY}/${BINARY}:${VERSION} -f ./Dockerfile.kube-proxy .
else
  docker build --squash --build-arg https_proxy=${https_proxy} --build-arg VERSION=${VERSION} -t ${REGISTRY}/${BINARY}:${VERSION} -f ./Dockerfile.kube-proxy .
fi
popd
docker save -o ${BINARY_LOCATION}/oracle_docker/${BINARY}.tar ${REGISTRY}/${BINARY}:${VERSION}
