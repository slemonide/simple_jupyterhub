FROM mazzolino/restic

COPY ssh /root/.ssh
RUN chmod 700 /root/.ssh \
 && chmod 644 /root/.ssh/id_rsa.pub \
 && chmod 600 /root/.ssh/id_rsa \
 && chmod 644 /root/.ssh/config
