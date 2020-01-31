const path = require("path");

const MinifyPlugin = require("babel-minify-webpack-plugin");

var config = {
  module: {
    rules: [
      {
        test: /\.scss$/,
        use: [
          {
            loader: "file-loader",
            options: {
              name: "bundle.css"
            }
          },
          {
            loader: "sass-loader",
            options: {
              sassOptions: {
                includePaths: ["./node_modules"]
              }
            }
          }
        ]
      },
      {
        test: /\.js$/,
        loader: "babel-loader",
        query: {
          presets: ["@babel/preset-env"]
        }
      }
    ]
  },
  plugins: [new MinifyPlugin()]
};

var shopConfig = Object.assign({}, config, {
  entry: ["./_includes/css/styles.scss", "./_includes/js/shop.js"],
  output: {
    filename: "shop.bundle.js",
    libraryTarget: "var",
    library: "Shop"
  }
});

var abConfig = Object.assign({}, config, {
  entry: ["./_includes/js/ab.js"],
  output: {
    filename: "ab.bundle.js",
    libraryTarget: "var",
    library: "AB"
  }
});

module.exports = [shopConfig, abConfig];
