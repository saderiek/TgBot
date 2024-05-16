FROM postgres:latest

RUN rm -rf db-data/*

RUN mkdir -p /var/log/postgres/
RUN touch /var/log/postgres/postgres.log
RUN chmod 777 /var/log/postgres/postgres.log

COPY . .

RUN apt-get update && \
    apt-get install -y gettext-base

#COPY init.sh /docker-entrypoint-initdb.d/init.sh
#RUN chmod +x /docker-entrypoint-initdb.d/init.sh
#RUN chmod +r /docker-entrypoint-initdb.d/init.sh

COPY init.sql /docker-entrypoint-initdb.d/

RUN envsubst < /docker-entrypoint-initdb.d/init.sql > /docker-entrypoint-initdb.d/init.sql.tmp \
    && mv /docker-entrypoint-initdb.d/init.sql.tmp /docker-entrypoint-initdb.d/init.sql

RUN chown postgres /docker-entrypoint-initdb.d/init.sql
RUN chmod +r /docker-entrypoint-initdb.d/init.sql

EXPOSE 5432

#ENTRYPOINT ["/docker-entrypoint-initdb.d/init.sh"]
