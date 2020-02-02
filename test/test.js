var assert = require("assert");

var pure = require("../_includes/js/pure");
var Split = require("../_includes/js/split");

describe("Test", function() {
  describe("#testFun()", function() {
    it("should return -1", function() {
      assert.equal(pure.testFun(), -1);
    });
  });
});
