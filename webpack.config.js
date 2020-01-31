const path = require('path');

const MinifyPlugin = require('babel-minify-webpack-plugin');

module.exports = {
  entry: [
    "./_includes/css/styles.scss", 
    "./_includes/js/shop.js", 
    "./_includes/js/ab.js"
  ],
  output: {
    filename: "[name].bundle.js",
    libraryTarget: "var",
    library: "Shop"
  },
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
      },
    ]
  },
  plugins: [
    new MinifyPlugin()
  ]
};
