#!/usr/bin/env bash

# Simple YAML parser.
#
# Defines the function `parse_yaml`.
# Usage:
#   source parse_yaml.sh
#   eval $(parse_yaml <yaml-file> [prefix])
#
# This parses the YAML file and creates shell variables based on its structure.
# Example:
#   yaml file:
#     foo:
#       bar: "hello"
#
#   eval $(parse_yaml my.yml "config_")
#
#   echo $config_foo_bar -> "hello"

parse_yaml() {
   local prefix=$2
   local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
   sed -ne "s|^\($s\)\($w\)$s:$s\"\(.*\)\"$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  "$1" |
   awk -F"$fs" '{
      indent = length($1)/2;
      vname[indent] = $2;
      for (i in vname) {if (i > indent) {delete vname[i]}}
      if (length($3) > 0) {
         vn=""; for (i=0; i<=indent; i++) {vn=(vn)(vname[i])("_")}
         printf("%s%s=\"%s\"\n", "'"$prefix"'",vn, $3);
      }
   }' | sed 's/^_//'
}
