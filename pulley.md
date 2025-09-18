# kubernetes

This oracle-template should automatically onboard new upstream kubernetes releases into the Kubernetes/kubernetes pipeline.

Tag format as specified in template.json is as follows.

 - major: [0-9] - a single character in the range between 0 & 9
 - minor: [0-9] - a single character in the range between 0 & 9
 - patch: [[:digit:]]+ - [:digit:] matches a digit [0-9]; + Quantifier - matches between one and unlimited times

Version information in spec files is templated as follows (ignore whitespace between braces, it is here to prevent pulley processing).

 - { {{$version := printf "%s.%s.%s" .major .minor .patch}} } <- Use golang templates to define a version variable; 1st line in spec file.
 - Version: { {{ $version }} } <- Note triple-braced template invocation here to print version.

Created container as specified in Jenkinsfile is as follows (ignore whitespace between braces, it is to prevent pulley processing).

 - container-registry.oracle.com/Kubernetes/X:v{ {{.major}} }.{ {{.minor}} }.{ {{.patch}} }
