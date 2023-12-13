Connecting to the Server
========================

Access to the cstock server requires connecting to a VPN.
Follow the steps below to connect to the VPN and access the server.

## Prerequisites

Before you will be able to login to the cStock server you will need two accounts:

1. A VPN account (or access to shared VPN credentials).
2. An account on the cStock server (or access to shared server credentials)

If you don't have these, ask a system administrator to provide you access.


## VPN set up

To access the VPN you will need to set up your VPN account and two-factor application.
You may need to install an older version of Sophos Authenticator to get the two-factor codes to work.

Once you've gotten set up, download the provided OpenVPN config file and save it locally.

## Logging in to the VPN

On Ubuntu, login to the VPN by running:

```bash
sudo openvpn --config ~/user__ssl_vpn_config.ovpn
```

Enter your credentials, which are you username, followed by your password + 2FA code appended together.
So if your password is `hunter2` and the 2-factor code is `123456`,
you would enter `hunter2123456` for the password field.

For different operating systems, refer to the VPN documentation provided by the system administrator.

## Logging in to cstock

Once on the VPN, you can access cstock by running:

```bash
ssh user@10.10.100.77
```

Replace `user` with your username, or use the `cstock` user for shared access.
