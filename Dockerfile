FROM nikolaik/python-nodejs:latest

# Sometimes ruby crashes when building with jekyll
# I don't know if it will fix it, but there is a chance
ENV BUNDLE_FORCE_RUBY_PLATFORM true

RUN apt-get -y update && apt-get -y install \
        apt-utils \
        ruby-full \
        build-essential \
        zlib1g-dev \
        rsync

RUN gem install \
        jekyll \
        bundler \
        jekyll-redirect-from \
        public_suffix

RUN pip install --upgrade pip
RUN pip install \
        "pytest!=5.3.4" \
        pyyaml \
        beautifulsoup4 \
        path \
        slackclient \
        requests \
        toolz \
        fn \
        tinify \
        more-itertools \
        cachier \
        selenium

RUN npm update && npm install -g npm

WORKDIR /website
COPY package.json package.json  
RUN npm install
COPY . /website
