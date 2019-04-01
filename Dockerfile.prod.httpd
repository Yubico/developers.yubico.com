FROM alpine:3.9

RUN apk --no-cache add apache2

# dedicated user and group
RUN addgroup -S www && adduser -S -G www www

# required for pid file
RUN mkdir -p /run/apache2 && chown www:www /run/apache2

COPY --chown=0:0 httpd.conf /etc/apache2/
COPY --chown=0:0 ./dist /var/www/localhost/htdocs

EXPOSE 8080
USER www
CMD ["httpd", "-DFOREGROUND", "-f/etc/apache2/httpd.conf"]
