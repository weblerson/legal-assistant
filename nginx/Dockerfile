FROM nginx:1.25-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/nginx.conf

# Copy the static website files (index.html)
# to the directory we specified in nginx.conf
COPY static/ /usr/share/nginx/html