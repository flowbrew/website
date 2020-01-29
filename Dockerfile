FROM nikolaik/python-nodejs:latest

# Sometimes ruby crashes when building with jekyll
# I don't know if it will fix it, but there is a chance
ENV BUNDLE_FORCE_RUBY_PLATFORM true

RUN apt-get -y update && apt-get -y install \
        apt-utils \
        ruby-full \
        build-essential \
        zlib1g-dev

RUN gem install \
        jekyll \
        bundler \
        jekyll-redirect-from \
        public_suffix

RUN pip install --upgrade pip
RUN pip install \
        pytest \
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

RUN npm update && \
        npm install --global \
        mocha \
        @material/button \
        @material/drawer \
        @material/form-field \
        @material/icon-button \
        @material/list \
        @material/radio \
        @material/ripple \
        @material/textfield \
        @material/top-app-bar \
        jquery \
        js-cookie \
        lazysizes \
        @babel/core \
        @babel/preset-env \
        autoprefixer \
        babel-loader \
        babel-minify-webpack-plugin \
        core-js \
        css-loader \
        extract-loader \
        fibers \
        file-loader \
        mini-css-extract-plugin \
        postcss-loader \
        sass \
        sass-loader \
        style-loader \
        webpack \
        webpack-cli \
        webpack-dev-server

