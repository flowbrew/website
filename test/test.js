var assert = require("assert");
var pure = require("../_includes/js/pure");

describe("Test", function() {
  describe("#testFun()", function() {
    it("should return -1", function() {
      assert.equal(pure.testFun(), -1);
    });
  });
});
