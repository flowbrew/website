import Cookies from "js-cookie";
var urljoin = require("url-join");

function weightedRand2(spec) {
  var i,
    sum = 0,
    r = Math.random();
  for (i in spec) {
    sum += spec[i];
    if (r <= sum) return i;
  }
}

const C_SHA_COOKIE = "split_test_master_sha";
const C_ALLOCATED_BRANCH = "split_test_allocated_branch";

function trim_s(x) {
  return x.replace(/^\/+|\/+$/g, "");
}

function isEmpty(obj) {
  for (var prop in obj) {
    if (obj.hasOwnProperty(prop)) {
      return false;
    }
  }

  return JSON.stringify(obj) === JSON.stringify({});
}

export function split_test_io(base, current_sha, traffic_allocation) {
  if (!traffic_allocation || isEmpty(traffic_allocation) || !current_sha) {
    return;
  }

  if (window.location.search.includes("__disable_split_test=1")) {
    return;
  }

  var host =
    location.protocol +
    "//" +
    location.hostname +
    (location.port ? ":" + location.port : "");
  var path =
    "/" + (window.location.pathname + window.location.search).replace(base, "");

  const old_sha = Cookies.get(C_SHA_COOKIE);
  var allocated_branch = Cookies.get(C_ALLOCATED_BRANCH);

  if (old_sha != current_sha) {
    // new experiment occurred
    Cookies.remove(C_SHA_COOKIE);
    Cookies.remove(C_ALLOCATED_BRANCH);

    allocated_branch = weightedRand2(traffic_allocation);
  }

  Cookies.set(C_SHA_COOKIE, current_sha, { expires: 30 });
  Cookies.set(C_ALLOCATED_BRANCH, allocated_branch, { expires: 30 });

  if (!allocated_branch) {
    // no need to redirect on master
    return;
  }

  window.location.replace(
    urljoin([host, base, allocated_branch, path].map(trim_s))
  );
}

export function try_redirect_to_backup_page_io(branch_prefix) {
  var host =
    location.protocol +
    "//" +
    location.hostname +
    (location.port ? ":" + location.port : "");
  var path = (window.location.pathname + window.location.search).substr(1);

  var parts = path.split("/");

  if (!parts) {
    return;
  }

  if (parts[0].startsWith(branch_prefix)) {
    window.location.replace(
      urljoin([host].concat(parts.slice(1)).map(trim_s))
      );
  } else if (parts[0] == "blog" && parts.length > 1) {
    window.location.replace(
      urljoin([host, "blog", window.location.search].map(trim_s))
      );
  }
}
