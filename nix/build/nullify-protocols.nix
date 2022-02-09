protocols: final: prev:
builtins.mapAttrs (name: pkg:
  if builtins.any (proto: !isNull (builtins.match "tezos.*${proto}.*" name))
  protocols.ignored then
    null
  else
    pkg) prev
