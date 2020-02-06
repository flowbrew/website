FROM nikolaik/python-nodejs:python3.8-nodejs12

# Sometimes ruby crashes when building with jekyll
# I don't know if it will fix it, but there is a chance
ENV BUNDLE_FORCE_RUBY_PLATFORM true

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
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
        "pytest==3.8.0" \
        "pyyaml==3.13" \
        "beautifulsoup4==4.6.3"\
        "path==13.1.0" \
        "slackclient==2.5.0" \
        "requests==2.21.0" \
        "toolz==0.9.0" \
        "fn==0.4.3" \
        "tinify==1.5.1" \
        "more-itertools==4.3.0" \
        "cachier==1.3.0"

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
RUN pip install --upgrade pip && pip install "selenium==3.141.0"
# ***

# Baking npm deps
WORKDIR /website
COPY package.json package.json  
RUN npm install
COPY . /website
