<!--
   - SPDX-FileCopyrightText: 2023 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# How to issue self-signed certificate

The following steps could be used to issue self-signed certificate for testing purposes:
``` sh
git clone https://github.com/OpenVPN/easy-rsa
cd easy-rsa/easyrsa3
./easyrsa --subject-alt-name="DNS:localhost" gen-req localhost nopass
```

For more information, please visit official [README.md](https://github.com/OpenVPN/easy-rsa/blob/master/README.quickstart.md).
