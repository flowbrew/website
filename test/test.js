var assert = require("assert");

var pure = require("../_includes/js/pure");
var ab = require("../_includes/js/ab");

describe("Test", function() {
  describe("#testFun()", function() {
    it("should return -1", function() {
      assert.equal(pure.testFun(), -1);
    });
  });
});
