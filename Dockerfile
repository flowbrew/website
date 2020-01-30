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
        cachier

RUN npm update && npm install -g npm

# *** Install Chrome & Selenium
# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable
# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
# set display port to avoid crash
ENV DISPLAY=:99
# install selenium
RUN pip install --upgrade pip && pip install selenium
# ***

# Baking npm deps
WORKDIR /website
COPY package.json package.json  
RUN npm install
COPY . /website
