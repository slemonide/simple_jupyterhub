# Simple Jupyterhub Deployment

This is a simple jupyterhub deployment to be used on a single server to run the hub + another server to store user backups.

Current features:
* https/tls using nginx as a reverse proxy with automatic certificates throuhg Let's Encrypt
* custom hub image
* user disk quotas (1G soft + 2G hard)
* periodic backups of user data to external server over simple ssh
* authenticate through GitHub

# Usage

To use without backups, simply do ` docker-compose up --build`. Make sure to setup `.env` file first!

## Disclaimer

These instructions assume you are running Ubuntu. They will likely not be much different for any other GNU/Linux.

## Setup environment

Copy `.env.dist` to `.env`, and fill in the blanks.
To get OAUTH id and secret, follow instructions here: https://docs.github.com/en/free-pro-team@latest/developers/apps/creating-an-oauth-app

* \<jupyter_address\> is something of the form `jupyterhub.example.com`
* \<backup_server_address\> is something of the form `backup-server.example.com`
* To generate a secure random password, you can for example, use:
`dd if=/dev/urandom bs=1 count=32 2>/dev/null | base64 -w 0 | rev | cut -b 2- | rev`
* Follow instructions below to properly setup backup server.
* Email for letsencrypt doesn't really matter, I never got any :(

Once you have your environment set up, everything should work fine.

## Setup disk quotas

To implement disk quotas, we use basic Linux filesystem disk quotas. In order for this to work, your root filesystem, and partitions where docker containers and volumes are mounted to, should be mounted with quotas on:
```bash
 sudo mount -o remount,usrquota,grpquota /
```

This will temporarily enable disk quotas until the next time you restart your server.

To make this permanent, edit `/etc/fstab` to something like:

`UUID=some-long-string-of-random-symbols / ext4 errors=remount-ro,usrquota,grpquota 0 0`

or

`/dev/sda1 / ext4 errors=remount-ro,usrquota,grpquota 0 0`

And then restart the server using `sudo reboot`. But first make sure you didn't make any typos since then your server wouldn't be able to boot and you wouldn't be able to ssh to it!

More info on disk quotas: https://linuxhint.com/disk_quota_ubuntu/

## Configure backups

For backups to work, you first need a second machine with a user `jupyter-backup` created on it.
This user needs to be accessible with ssh, but does not need password (we will connect to it using
ssh keys, which are more secure and easy to use):

```bash
# ssh to backup machine
localhost> ssh backup-machine
backup-machine> sudo adduser -q -gecos "" -disabled-password jupyter-backup
```

Now, for more advanced security, we should only allows this user to use `sftp`, and nothing else.
I.e. we will only use them for doing backups through `sftp` protocol that `restic` can utilize.

You have to edit your sshd config on the backup machine for that:
```bash
backup-machine> sudo vim /etc/ssh/sshd_config
```

First, if you have `Subsystem sftp /usr/lib/openssh/sftp-server`, replace it by:
`Subsystem sftp internal-sftp`.
If you don't have it, just add it at the end of file. `internal-sftp` is just a newer
version of `sftp-server` that works better with chroot.

Next, we need to setup a rule sot that all users `sftponly` group can only access the server through sftp:
```bash
Match group sftponly
     ChrootDirectory /home/%u
     X11Forwarding no
     AllowTcpForwarding no
     ForceCommand internal-sftp
```

This creates a chroot environment (a lighter analogue of docker, haha) for the user.
It then prevents them from using X11 forwarding, TCP forwarding, and forces them to only be able
to use the sftp.

Now restart your sshd server:
```bash
backup-machine> systemctl restart ssh
```

Next, we need to generate an ssh keypair to allow our restic container on jupyterhub machine to
automatically login to backup machine through sftp and store data there.

You do it on the jupyterhub machine:
```bash
jupyterhub-machine> cd ~/simple_jupyterhub/restic/ssh/
jupyterhub-machine> ssh-keygen -f id_rsa -P ""
```

This generate an ssh keypair with no password protection on privite key. We don't set the
password because we want restic to be able to connect to the backup server without prompting
for the password.

Keep privite key secure. If someone gets access to it, they can potentially remove/steal/modify
backups from the backup server.

In the directory we are currently in, there now should be two files, `id_rsa` (privite key), and
`id_rsa.pub` (public key).

Do `cat id_rsa.pub` to see its contents. We would have to copy them to the backup server for it to
recognize our jupyterhub server when it tries to connect.

Public key should look something like `ssh-rsa AAA...6p username@localhost`. Make sure you copy all
of it.

Now, add it to the backup server:

```bash
backup-machine> sudo mkdir ~jupyter-backup/.ssh
backup-machine> sudo vim ~jupyter-backup/.ssh/authorized_keys
```

Setup proper permissons for ssh folder:
```bash
backup-machine> sudo chown -R jupyter-backup:jupyter-backup ~jupyter-backup/.ssh/
backup-machine> sudo chmod 600 ~jupyter-backup/.ssh/authorized_keys
backup-machine> sudo chmod 700 ~jupyter-backup/.ssh/
```

Note: make sure you copy the last two commands in the exact order shown since the last command
makes `.ssh` directory unreadable by anyone except `jupyter-backup`.

As a check, right now you should be able to ssh as `juputer-backup` from your juputerhub server:

```bash
jupyterhub-machine> ssh -i id_rsa jupyter-backup@backup-machine
```

Now let's prevent that from happening:

```bash
backup-machine> sudo groupadd sftponly
backup-machine> sudo usermod -a -G sftponly jupyter-backup
```

Notice that we didn't really have to create this group before adding it to sshd config.
Groups and users are superficial on unix systems. They are just numers that exist.
Whe you create a user or a group, you simply assign a name to those numbers.

If you want to make it so that ssh logins work once again, do:
```bash
backup-machine> sudo gpasswd -d jupyter-backup sftponly
```

To test that `sftp` works, do:

```bash
jupyterhub-machine> echo "Hello, sftp!" > test
jupyterhub-machine> sftp -i id_rsa jupyter-backup@backup-machine
sftp> ls
sftp> lls
test
sftp> put test
Uploading test to /home/jupyter-backup/test
test                             100%   12    52.4KB/s   00:00
sftp> ls
test
sftp> lls
```

`ls` lists files on remote machine, and `lls` lists local files.

It now works!

## Using restic to inspect backups

It's important to manually check that you are actually making backups.

To do so, install restic on any of your computers, or use it from the container: `docker-compose exec restic bash`.

Then, to chech snapshots: `restic -r "sftp:${BACKUP_USER}@${BACKUP_SERVER}:${BACKUP_REPO_PATH}" snapshots`.
Snapshots are basically like commits in git, but opposite to commits, snapshots can be
empty. I.e. we will always get a new snapshot every time we make a snaphsot, even
if there is no new data added.

To restore a snapshot with id \<snapshot-id\>, use
`restic -r "sftp:${BACKUP_USER}@${BACKUP_SERVER}:${BACKUP_REPO_PATH}" restore <snapshot-id> --target /`.
It's fairly easy to restore to previous snapshot, and then get back to current version as well. Just like git.

Restic can also restore particular file/directory as opposed to rollbacking the whole system.
See <https://restic.readthedocs.io/en/latest/050_restore.html> for more info.

For more info, read restic documentation: <https://restic.readthedocs.io/en/latest/>
