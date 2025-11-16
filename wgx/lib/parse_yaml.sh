#!/usr/bin/env bash
set -euo pipefail

# parse_yaml FILE PREFIX
# Erzeugt Variablen wie:
#   class: rust-service
#   tasks:
#     smoke: "echo hi"
#
# -> PREFIX_class="rust-service"
# -> PREFIX_tasks_smoke="echo hi"

parse_yaml() {
  local file="$1"
  local prefix="${2:-}"

  local s='[[:space:]]*'
  local w='[a-zA-Z0-9_]*'
  local fs
  fs=$(echo @ | tr @ '\034')

  sed -ne "s|^\($s\)\($w\)$s:$s\"\(.*\)\"$s\$|\1$fs\2$fs\3|p" \
      -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p" "$file" |
  awk -F"$fs" -v prefix="$prefix" '
    {
      indent = length($1)/2
      vname[indent] = $2
      for (i in vname) if (i > indent) delete vname[i]

      if (length($3) > 0) {
        vn = ""
        for (i = 0; i <= indent; i++) {
          if (vname[i] == "") continue
          if (vn == "") vn = vname[i]
          else vn = vn "_" vname[i]
        }
        printf("%s%s=\"%s\"\n", prefix, vn, $3)
      }
    }
  '
}
