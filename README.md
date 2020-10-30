# Simple Jupyterhub Deployment

This is a simple jupyterhub deployment to be used on a single server to run the hub + another server to store user backups.

Current features:
* https/tls using nginx as a reverse proxy with automatic certificates throuhg Let's Encrypt
* custom hub image
* user disk quotas (1G soft + 2G hard)
* periodic backups of user data to external server over simple ssh
* authenticate through GitHub

# Usage

To use without backups, simply do ` docker-compose up --build`.

## Configure backups

For backups to work, you first need a second machine with a user `jupyter-backup` created on it.
This user needs to be accessible with ssh, but does not need password (we will connect to it using
ssh keys, which are more secure and easy to use):

```bash

```

Hence, next you need to generate an ssh keypair: a privite and a public key.
Privite key stays on the server running the hub, and public key needs to be added



Backups volumes to `/data/jypyterhub/backup/restic/mnt/restic/` at the start of every hour.

Restic basically works like git.

To work with it, first get inside its container, `docker-compose exec restic bash`.

Then, to chech snapshots: `restic -r /mnt/restic/ snapshots`
Snapshots are basically like commits in git, but opposite to commits, snapshots can be
empty. I.e. we will always get a new snapshot recorc every time we make a snaphsot, even
if there is no new data added.

To restore a snapshot with id \<snapshot-id\>, use `restic -r /mnt/restic/ restore <snapshot-id> --target /`.
It's fairly easy to restore to previous snapshot, and then get back to current version as well. Just like git.

Restic can also restore particular file/directory as opposed to rollbacking the whole system.
See <https://restic.readthedocs.io/en/latest/050_restore.html> for more info.

For more info, read restic documentation: <https://restic.readthedocs.io/en/latest/>

## SFTP remote backups

1. For this to work, create user which would store backups on a remote machine.
2. Generate an ssh key in the restic container.
3. Then add corresponding public key to `.ssh/authorized_keys`
4. Configure urls of remote machine in the dockerfile.
5. Done!

