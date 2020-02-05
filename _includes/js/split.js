import Cookies from "js-cookie";

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

export function split_test_io(base, current_sha, traffic_allocation) {
  if (!traffic_allocation || !current_sha) {
    return;
  }

  var host =
    location.protocol +
    "//" +
    location.hostname +
    (location.port ? ":" + location.port : "");
  var path = '/' + (window.location.pathname + window.location.search).replace(
    base,
    ""
  );

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

  window.location.replace(host + base + allocated_branch + path);
}
