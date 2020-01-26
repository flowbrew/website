function baseurl_link(url) {
  var base = "{{ '/' | relative_url }}";
  return (base == '/' ? '' : base) + url;
}

var ZOOM_HOVER_TIMEOUT = null;

$.fn.universalClick = function(f) {
  $(this).on("click", f);
};

function int_to_(d_, a, b, c) {
  var word = "";
  var d = d_ % 10;
  if (d == 0 || d >= 5 || (d_ >= 11 && d_ <= 14)) {
    word = a;
  } else if (d == 1) {
    word = b;
  } else {
    word = c;
  }
  return d_ + " " + word;
}

function int_to_days(d) {
  return int_to_(d, "дней", "день", "дня");
}

function int_to_hours(d) {
  return int_to_(d, "часов", "час", "часа");
}

function is_grid_supported() {
  try {
    var el = document.querySelector("body");
    return typeof el.style.grid === "string";
  } catch (err) {}
  return false;
}

function init_zoom() {
  target = $("div[zoom]");
  target.css("overflow", "hidden");
  $("div[zoom] img").css("position", "relative");

  function zoom_event_tick(zoomed_img) {
    clearTimeout(ZOOM_HOVER_TIMEOUT);
    ZOOM_HOVER_TIMEOUT = setTimeout(function() {
      zoomed_image_viewed(zoomed_img);
    }, 2000);
  }

  function on_enter() {
    zoom_event_tick(
      $(this)
        .children("img:visible")
        .attr("src")
    );
    $(this)
      .children("img")
      .css({
        "-webkit-transform": "scale(" + $(this).attr("zoom") + ")",
        transform: "scale(" + $(this).attr("zoom") + ")"
      });
  }

  function on_leave() {
    clearTimeout(ZOOM_HOVER_TIMEOUT);
    $(this)
      .children("img")
      .css("transform", "")
      .css("-webkit-transform", "")
      .css("transform-origin", "50% 50%");
  }

  function on_touchmove(e) {
    e.preventDefault();

    var xPos = e.originalEvent.touches[0].pageX;
    var yPos = e.originalEvent.touches[0].pageY;

    $(this)
      .children("img")
      .css({
        "transform-origin":
          ((xPos - $(this).offset().left) / $(this).width()) * 100 +
          "% " +
          ((yPos - $(this).offset().top) / $(this).height()) * 100 +
          "%"
      });
  }

  function on_move(e) {
    $(this)
      .children("img")
      .css({
        "transform-origin":
          ((e.pageX - $(this).offset().left) / $(this).width()) * 100 +
          "% " +
          ((e.pageY - $(this).offset().top) / $(this).height()) * 100 +
          "%"
      });
  }

  target.universalClick(on_enter);
  target.mouseenter(on_enter);
  target.mouseleave(on_leave);
  target.mousemove(on_move);
}

function init_preview() {
  target = $(".image-preview");
  target.first().addClass("image-preview-selected");

  function payload(x) {
    var old_id = $(".offer-img:visible").attr("id");
    var id = x.attr("id").replace("preview_", "z");
    if (old_id === id) {
      return;
    }
    $(".image-preview").removeClass("image-preview-selected");
    x.addClass("image-preview-selected");
    $(".offer-img").hide();
    $("#" + id).show();
    preview_selected(x.attr("id"), x.attr("src"));
  }

  target.mouseenter(function() {
    payload($(this));
  });

  target.universalClick(function() {
    payload($(this));
  });
}

function init_accordion() {
  $(".question-h").universalClick(function() {
    t = $(this);

    // Add the correct active class
    if (t.closest(".question").hasClass("active")) {
      // Remove active classes
      $(".question").removeClass("active");
    } else {
      // Remove active classes
      $(".question").removeClass("active");

      // Add the active class
      t.closest(".question").addClass("active");
    }

    // Show the content
    var content = t.next();
    if (!content.is(":visible")) {
      faq_opened(
        $(this)
          .find(".title")
          .html()
          .trim()
      );
    }
    content.slideToggle(100);
    $(".question .question-content")
      .not(content)
      .slideUp("fast");
  });
}

// SHOPIFY
function we_have_stock(quantity) {
  $(".buy-button").universalClick(function() {
    buy_button_pressed($(this).attr("id"));
    window.location = baseurl_link("/checkout.html");
  });

  var word = quantity == 1 ? "Остался" : "Осталось";

  // $(".quantity").hide();

  $(".quantity").html(
    word + " <strong>" + quantity + '</strong> <i class="fas fa-gift"></i>'
  );

  $(".quantity-wrapper").css("visibility", "visible");
}

function out_of_stock() {
  $(".buy-button-text").html("РАСПРОДАНО");
  $(".buy-button").addClass("soldout");
}

function update_inventory_quantity(product) {
  if (product.quantity > 0) {
    we_have_stock(product.quantity);
  } else {
    out_of_stock();
  }
}

// EVENTS

$.fn.percentInViewport = function(heigh_correction) {
  var elementTop = $(this).offset().top - heigh_correction;
  var elementBottom = elementTop + $(this).outerHeight() + heigh_correction;

  var viewportTop = $(window).scrollTop();
  var viewportBottom = viewportTop + $(window).innerHeight();

  var l = elementBottom - elementTop;

  if (elementTop < viewportBottom && elementBottom > viewportTop) {
    return (
      Math.min(viewportBottom - elementTop, elementBottom - viewportTop) / l
    );
  }

  return 0.0;
};

function reset_viewport() {
  $("*").removeClass("is-in-viewport");
  on_viewport_changed();
}

function on_viewport_changed() {
  $(".auto-zoom").each(function() {
    var p = $(this).percentInViewport(0);
    if (p > 0.5) {
      $(this).addClass("is-in-viewport");
    } else if (p <= 0.0) {
      $(this).removeClass("is-in-viewport");
    }
  });
  $(".auto-zoom-ex").each(function() {
    var p = $(this).percentInViewport(25);
    if (p > 0) {
      $(this).addClass("is-in-viewport-ex");
    } else if (p <= 0.0) {
      $(this).removeClass("is-in-viewport-ex");
    }
  });
}

$(window).on("resize scroll", function() {
  on_viewport_changed();
});

function push_event(data) {
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push(data);
  //console.log(window.dataLayer);
}

function tab_focused() {
  reset_viewport();
  push_event({
    event: "tab_focused"
  });
}

function promotion_activated(name) {
  push_event({
    event: "promo",
    promo_name: name
  });
}

function preview_selected(hover_id, hover_data) {
  push_event({
    event: "preview_selected",
    hover_id: hover_id,
    hover_data: hover_data
  });
}

function element_hovered(hover_id, hover_data) {
  push_event({
    event: "element_hovered",
    hover_id: hover_id,
    hover_data: hover_data
  });
}

var LAST_SELECTED_TEXT = "";

function text_selected(selected_text) {
  if (LAST_SELECTED_TEXT == selected_text) {
    return;
  }
  LAST_SELECTED_TEXT = selected_text;
  if (selected_text == "") {
    return;
  }
  push_event({
    event: "text_selected",
    selected_text: selected_text
  });
}

function buy_button_pressed(buy_button_id) {
  push_event({
    event: "buy_button_pressed",
    buy_button_id: buy_button_id
  });
}

function form_input(id, text) {
  if (!text) {
    return;
  }
  push_event({
    event: "form_input",
    form_id: id,
    form_value: text
  });
}

function zoomed_image_viewed(zoomed_img) {
  push_event({
    event: "zoomed_image_viewed",
    zoomed_img: zoomed_img
  });
}

function page_loaded() {
  push_event({
    event: "page_loaded"
  });
}

function faq_opened(faq_title) {
  push_event({
    event: "faq_opened",
    faq_title: faq_title
  });
}

function send_grid_support() {
  push_event({
    event: "is_grid_supported",
    is_grid_supported: is_grid_supported() ? "yes" : "no"
  });
}

function resolution_detected(resolution) {
  push_event({
    event: "resolution_detected",
    resolution: resolution
  });
}

function resolution() {
  var res = $("html").css("--resolution");
  return res == undefined ? "" : res.trim();
}

function init_event_trackers() {
  resolution_detected(resolution());

  function run_text_selected_reader() {
    setTimeout(function() {
      var text = "";
      if (window.getSelection) {
        text = window.getSelection().toString();
      } else if (document.selection && document.selection.type != "Control") {
        text = document.selection.createRange().text;
      }
      text = text.trim();
      if (text) {
        text_selected(text);
      }
      run_text_selected_reader();
    }, 200);
  }
  run_text_selected_reader();

  $(".buy-button").mouseenter(function() {
    element_hovered($(this).attr("id"), null);
  });

  $("img").mouseenter(function() {
    element_hovered($(this).attr("id"), $(this).attr("src"));
  });

  $(window).on("blur focus", function(e) {
    var prevType = $(this).data("prevType");

    if (prevType != e.type) {
      switch (e.type) {
        case "blur":
          break;

        case "focus":
          tab_focused();
          break;
      }
    }

    $(this).data("prevType", e.type);
  });
}

function init_reading_time() {
  if ($(".reading-time").length && $("article").length) {
    var words = $("p, li, h1, h2, h3")
      .text()
      .split(" ").length;
    var minutes = Math.ceil(words / 200.0);
    var name = "минут";
    if (minutes <= 0) {
      name = "минут";
    } else if (minutes <= 1) {
      name = "минута";
    } else if (minutes <= 4) {
      name = "минуты";
    }
    $(".reading-time").html(minutes + " " + name);
  }
}

function init_navigation() {
  if (typeof mdc === "undefined") {
    return;
  }
  var drawer = mdc.drawer.MDCDrawer.attachTo(
    document.querySelector(".mdc-drawer")
  );
  var topAppBar = mdc.topAppBar.MDCTopAppBar.attachTo(
    document.querySelector(".mdc-top-app-bar")
  );
  $(".mdc-top-app-bar__navigation-icon--unbounded").universalClick(function() {
    drawer.open = !drawer.open;
  });
}

function mdc_set_textfield(selector, value) {
  var tf = mdc.textField.MDCTextField.attachTo(
    document.querySelector(selector).closest(".mdc-text-field")
  );
  tf.value = value ? value : "";
}

function foreach(array, f) {
  for (var i = 0; i < array.length; i++) {
    f(array[i]);
  }
}

function init_mdc() {
  $(function() {
    if (typeof mdc === "undefined") {
      return;
    }

    foreach(
      document.querySelectorAll(".mdc-text-field"),
      mdc.textField.MDCTextField.attachTo
    );

    foreach(
      document.querySelectorAll(".mdc-button"),
      mdc.ripple.MDCRipple.attachTo
    );
  });
}

function onPlayerStateChange(e) {
  e["data"] == YT.PlayerState.PLAYING &&
    setTimeout(onPlayerPercent, 1000, e["target"]);
  var video_data = e.target["getVideoData"](),
    label = video_data.title;

  // Get title of the current page
  var pageTitle = document.title;
  if (e["data"] == YT.PlayerState.PLAYING && YT.gtmLastAction == "p") {
    label = "Video Played - " + video_data.title;
    dataLayer.push({
      event: "youtube",
      eventCategory: "Youtube Videos",
      eventAction: pageTitle,
      eventLabel: label
    });
    YT.gtmLastAction = "";
  }

  if (e["data"] == YT.PlayerState.PAUSED) {
    label = "Video Paused - " + video_data.title;
    dataLayer.push({
      event: "youtube",
      eventCategory: "Youtube Videos",
      eventAction: pageTitle,
      eventLabel: label
    });
    YT.gtmLastAction = "p";
  }
}

function onPlayerError(e) {
  dataLayer.push({
    event: "error",
    eventCategory: "Youtube Videos",
    eventAction: "GTM",
    eventLabel: "youtube:" + e["target"]["src"] + "-" + e["data"]
  });
}

function onPlayerPercent(e) {
  if (e["getPlayerState"]() == YT.PlayerState.PLAYING) {
    var t =
      e["getDuration"]() - e["getCurrentTime"]() <= 1.5
        ? 1
        : (
            Math.floor((e["getCurrentTime"]() / e["getDuration"]()) * 4) / 4
          ).toFixed(2);
    if (!e["lastP"] || t > e["lastP"]) {
      var video_data = e["getVideoData"](),
        label = video_data.title;
      // Get title of the current page
      var pageTitle = document.title;
      e["lastP"] = t;
      label = t * 100 + "% Video played - " + video_data.title;
      dataLayer.push({
        event: "youtube",
        eventCategory: "Youtube Videos",
        eventAction: pageTitle,
        eventLabel: label
      });
    }
    e["lastP"] != 1 && setTimeout(onPlayerPercent, 1000, e);
  }
}

var GTM_YTLISTENERS = [];

function onYouTubeIframeAPIReady() {
  YT.gtmLastAction = "p";
  GTM_YTLISTENERS = $("iframe")
    .filter(function(index) {
      return /youtube.com\/embed/.test($(this).attr("src"));
    })
    .map(function() {
      return new YT.Player($(this).attr("id"), {
        events: {
          onStateChange: onPlayerStateChange,
          onError: onPlayerError
        }
      });
    });
}

// Enhanced Ecommerce

function ec_product_details(product) {
  push_event({
    event: "product_details",
    ecommerce: {
      currencyCode: product.currency,
      detail: {
        products: [
          {
            id: product.id,
            name: product.name,
            price: product.price
          }
        ]
      }
    }
  });
}

function ec_promo_viewed(promo) {
  push_event({
    event: "promo_viewed",
    ecommerce: {
      promoView: {
        promotions: [
          {
            id: promo.id,
            position: promo.position
          }
        ]
      }
    }
  });
}

function ec_promo_clicked(promo, cb) {
  setTimeout(cb, 2000);
  push_event({
    event: "promo_clicked",
    ecommerce: {
      promoClick: {
        promotions: [
          {
            id: promo.id,
            position: promo.position
          }
        ]
      }
    },
    eventCallback: cb,
    eventTimeout: 2000
  });
}

function ec_checkout(product, step, option, quantity) {
  push_event({
    event: "checkout",
    ecommerce: {
      currencyCode: product.currency,
      checkout: {
        actionField: { step: step, option: option },
        products: [
          {
            id: product.id,
            name: product.name,
            price: product.price,
            quantity: quantity
          }
        ]
      }
    }
  });
}

function ec_checkout_d(product, step) {
  ec_checkout(product, step, null, 1);
}

function ec_refund(t_id) {
  push_event({
    event: "refund",
    ecommerce: {
      refund: {
        actionField: { id: t_id }
      }
    }
  });
}

function ec_purchase(t_id, product, revenue, shipping, quantity, coupon, cb) {
  setTimeout(cb, 2000);
  push_event({
    event: "purchase",
    ecommerce: {
      currencyCode: product.currency,
      purchase: {
        actionField: {
          id: t_id,
          revenue: revenue,
          shipping: shipping,
          coupon: coupon
        },
        products: [
          {
            id: product.id,
            name: product.name,
            price: product.price,
            quantity: quantity
          }
        ]
      }
    },
    eventCallback: cb,
    eventTimeout: 2000
  });
}

function getUrlVars() {
  var vars = {};
  var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(
    m,
    key,
    value
  ) {
    vars[key] = value;
  });
  return vars;
}

function getUrlParam(parameter, defaultvalue) {
  var urlparameter = defaultvalue;
  if (window.location.href.indexOf(parameter) > -1) {
    urlparameter = getUrlVars()[parameter];
  }
  return urlparameter;
}

function _init_promocode_from_url() {
  var code = getUrlParam("code", "").toUpperCase();
  if (code) {
    set_promocode_2(code, NORMAL_PROMOCODE_EXPIRATION);
  }
}

function set_promocode(code) {
  if (code) {
    Cookies.set("promocode", code, { expires: 30 });
  } else {
    Cookies.remove("promocode");
  }
}

function set_promocode_2(code, expires) {
  set_promocode(code);
  set_promocode_expiration(code, expires);
}

function set_promocode_2_notify(code, expires) {
  set_promocode_2(code, expires);
  promotion_activated(code);
}

function promocode_expiration_to_str(name) {
  return "promocode_" + name + "_expiration";
}

function set_promocode_expiration(name, expires) {
  var name_str = promocode_expiration_to_str(name);

  if (expires === undefined) {
    Cookies.remove(name_str);
    return;
  }

  if (!(promocode_expiration_in_days(name) === undefined)) {
    return;
  }

  var date = new Date();
  date.setDate(date.getDate() + expires);

  Cookies.set(name_str, date.toISOString(), { expires: 60 });
}

function promocode_expiration_in_(name, x) {
  try {
    var t2_str = Cookies.get(promocode_expiration_to_str(name));

    if (!t2_str) {
      return undefined;
    }

    var t1 = new Date();
    var t2 = Date.parse(t2_str);

    return Math.ceil((t2 - t1) / (1000 * x));
  } catch (err) {}
  return undefined;
}

function promocode_expiration_in_hours(name) {
  return promocode_expiration_in_(name, 60 * 60);
}

function promocode_expiration_in_days(name) {
  return promocode_expiration_in_(name, 60 * 60 * 24);
}

function promocode() {
  return Cookies.get("promocode");
}

var WELCOME_PROMOCODE10 = "GIFT10";
var NORMAL_PROMOCODE_EXPIRATION = 2;

function process_coupon(coupon_str) {
  if (!coupon_str) {
    return 0.0;
  }

  var coupon = coupon_str.toUpperCase();

  var expiration = promocode_expiration_in_days(coupon);
  if (!(expiration === undefined) && expiration <= 0) {
    return 0.0;
  }

  if (coupon === "flb10".toUpperCase()) {
    return 0.1;
  } else if (coupon === "fb10".toUpperCase()) {
    return 0.1;
  } else if (coupon === WELCOME_PROMOCODE10.toUpperCase()) {
    return 0.1;
  } else if (coupon === "flow15".toUpperCase()) {
    return 0.15;
  }

  return 0.0;
}

document.addEventListener("DOMContentLoaded", function() {
  init_on_document_ready();
});

// REMARKETING

var OFFER_VIEWED = "OFFER_VIEWED";
var BLOG_VIEWED = "BLOG_VIEWED";
var CHECKOUT_VIEWED = "CHECKOUT_VIEWED";
var BOUGHT = "BOUGHT";

function _goal(name) {
  return "goal_" + name;
}

function _add_goal(name, value, expires) {
  if (name) {
    Cookies.set(_goal(name), _get_goal(name) + value, { expires: expires });
  }
}

function _add_goal_d(name) {
  _add_goal(name, 1, 30);
}

function _get_goal(name) {
  try {
    var res = parseInt(Cookies.get(_goal(name)));
    return res ? res : 0;
  } catch (err) {}
  return 0;
}

function _welcome_bonus_promotion() {
  if (_get_goal(BOUGHT) > 0) {
    return;
  }

  if (_get_goal(CHECKOUT_VIEWED) > 0 || _get_goal(OFFER_VIEWED) > 1) {
    set_promocode_2_notify(WELCOME_PROMOCODE10, NORMAL_PROMOCODE_EXPIRATION);
  }
}

function includes(str, substr) {
  if (!str) {
    return false;
  }
  return str.indexOf(substr) !== -1;
}

// This funcion is being called before DOM and should decide whether we will give discount or not. This is a basic crude remarketing based on our cookie data.
function promotion_processor() {
  var path = window.location.pathname;

  if (path == baseurl_link("/")) {
    _add_goal_d(OFFER_VIEWED);
  }
  if (includes(path, baseurl_link("/blog"))) {
    _add_goal_d(BLOG_VIEWED);
  }
  if (path == baseurl_link("/checkout.html")) {
    _add_goal_d(CHECKOUT_VIEWED);
  }
  if (includes(path, encodeURI("спасибо"))) {
    var code_to_delete = promocode();
    if (code_to_delete) {
      set_promocode_expiration(code_to_delete, undefined);
      set_promocode_expiration(code_to_delete, -1);
    }
    set_promocode(false);
    _add_goal_d(BOUGHT);
  }

  _init_promocode_from_url();

  if (!promocode()) {
    _welcome_bonus_promotion();
  }
}

// ***

function init_before_dom() {
  promotion_processor();
}

function init_global() {
  init_event_trackers();
  init_accordion();
  init_navigation();
  init_reading_time();
}

function init_on_document_ready() {
  send_grid_support();
  $("body").show();
  init_mdc();
  reset_viewport();
  page_loaded();
}

// *** //

init_before_dom();
