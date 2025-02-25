FROM php:8.1-apache

RUN docker-php-ext-install pdo pdo_mysql

COPY ./public /var/www/html
COPY ./src /var/www/src

RUN chown -R www-data:www-data /var/www
RUN chmod -R 755 /var/www

EXPOSE 80