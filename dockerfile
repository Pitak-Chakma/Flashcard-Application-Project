# Use official PHP image with Apache
FROM php:8.2-apache

# Install mysqli extension
RUN docker-php-ext-install mysqli

# Enable Apache mod_rewrite
RUN a2enmod rewrite

# Copy application files
COPY public/ /var/www/html/
COPY config.php /var/www/html/

# Set environment variables
ENV APACHE_DOCUMENT_ROOT /var/www/html
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf


