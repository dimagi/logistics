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

### Setting up two-factor authentication

You will be given a username and password from the system administrator.
To set up your authenticator app, first download an old version of Sophos authenticator.
Version 3.4 ([available for Android here](https://sophos-gmbh-authenticator.en.aptoide.com/app))
has been tested and confirmed to work.

Next, navigate to [https://41.87.6.124:445](https://41.87.6.124:445) to access the Sophos user portal
and supply the username and password you were given.
Once logged in, you will be presented with a QR code to scan to gain access to the portal for your account.
To scan the code, open the authenticator and scan the QR code. At the top left, click proceed to login to the portal.

## Logging in to the VPN

Once you've gotten set up, download the provided OpenVPN config file and save it locally.

On Ubuntu, login to the VPN by running:

```bash
sudo openvpn --config ~/user__ssl_vpn_config.ovpn
```

Enter your credentials, which are you username, followed by your password + 2FA code appended together.
So if your password is `hunter2` and the 2-factor code is `123456`,
you would enter `hunter2123456` for the password field.

For different operating systems, refer to the VPN documentation provided by the system administrator.

## Logging in to cstock

Once on the VPN, you can access cstock using the SSH command by running:

```bash
ssh cstock@10.10.100.77
```

If you have an individual user account, replace `cstock` with your username.

For more information on using SSH, see [this page](https://www.ucl.ac.uk/isd/what-ssh-and-how-do-i-use-it).
