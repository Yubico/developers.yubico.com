// obtain plugin
var cc = initCookieConsent();

// run plugin with your configuration
cc.run({
  current_lang: "en",
  autoclear_cookies: true, // default: false
  page_scripts: true, // default: false

  // mode: 'opt-in'                          // default: 'opt-in'; value: 'opt-in' or 'opt-out'
  // delay: 0,                               // default: 0
  // auto_language: '',                      // default: null; could also be 'browser' or 'document'
  // autorun: true,                          // default: true
  // force_consent: false,                   // default: false
  // hide_from_bots: false,                  // default: false
  // remove_cookie_tables: false             // default: false
  // cookie_name: 'cc_cookie',               // default: 'cc_cookie'
  // cookie_expiration: 182,                 // default: 182 (days)
  // cookie_necessary_only_expiration: 182   // default: disabled
  // cookie_domain: location.hostname,       // default: current domain
  // cookie_path: '/',                       // default: root
  // cookie_same_site: 'Lax',                // default: 'Lax'
  // use_rfc_cookie: false,                  // default: false
  // revision: 0,                            // default: 0

  gui_options: {
    consent_modal: {
      layout: "box", // box/cloud/bar
      position: "bottom left", // bottom/middle/top + left/right/center
      transition: "slide", // zoom/slide
      swap_buttons: true, // enable to invert buttons
    },
    settings_modal: {
      layout: "box", // box/bar
      // position: 'left',           // left/right
      transition: "slide", // zoom/slide
    },
  },

  onFirstAction: function (user_preferences, cookie) {
    // callback triggered only once on the first accept/reject action
  },

  onAccept: function (cookie) {
    // callback triggered on the first accept/reject action, and after each page load
  },

  onChange: function (cookie, changed_categories) {
    // callback triggered when user changes preferences after consent has already been given
  },

  languages: {
    en: {
      consent_modal: {
        description:
          "We use cookies to ensure that you get the best experience on our site and to present relevant content and advertising. By browsing this site without restricting the use of cookies, you consent to our and third party use of cookies as set out in our Cookie Notice.",
        secondary_btn: {
          text: "Preferences",
          role: "c-settings", // 'settings' or 'accept_necessary'
        },
        primary_btn: {
          text: "Accept all",
          role: "accept_all", // 'accept_selected' or 'accept_all'
        },
      },
      settings_modal: {
        title: "Cookie preferences",
        save_settings_btn: "Save settings",
        accept_all_btn: "Accept all",
        reject_all_btn: "Reject all",
        close_btn_label: "Close",
        cookie_table_headers: [
          { col1: "Name" },
          { col2: "Domain" },
          { col3: "Expiration" },
          { col4: "Description" },
        ],
        blocks: [
          {
            title: "Privacy Overview",
            description:
              "Developers.yubico.com uses cookies to improve your experience while navigating through the website. The information does not usually identify you, but it can give you a more personalized web experience. Blocking some types of cookies may impact your experience on our site and the services we are able to offer.",
          },
          {
            title: "Strictly necessary cookies",
            description:
              "These cookies are necessary for the website to function and cannot be switched off in our systems. They are usually only set in response to actions made by you which amount to a request for services, such as setting your privacy preferences, logging in or filling in forms. You can set your browser to block or alert you about these cookies, but some parts of the site will not then work. These cookies do not store any personally identifiable information.",
            toggle: {
              value: "necessary",
              enabled: true,
              readonly: true, // cookie categories with readonly=true are all treated as "necessary cookies"
            },
          },
          {
            title: "Functional cookies",
            description:
              "These cookies enable the website to provide enhanced functionality and personalization. They may set by us or by third party providers whose services we have added to our pages. If you do not allow these cookies then some or all of these services may not function properly.",
            toggle: {
              value: "functional",
              enabled: false,
              readonly: false,
            },
            cookie_table: [
              // list of all expected cookies
              {
                col1: "NID",
                col2: "google.com",
                col3: "6 months",
                col4: "This cookie is installed by Google Custom Search.",
              },
              {
                col1: "__gsas",
                col2: "google.com",
                col3: "1 year and 1 month",
                col4: "This cookie is installed by Google Custom Search.",
              },{
                col1: "^__utm",
                col2: "google.com",
                col3: "5 months to 2 years",
                col4: "This is a pattern type cookie set by Google Custom Search.",
                is_regex: true,
              },
            ],
          },
          {
            title: "Performance and Analytics cookies",
            description:
              "These cookies allow the website to remember the choices you have made in the past",
            toggle: {
              value: "analytics", // your cookie category
              enabled: false,
              readonly: false,
            },
            cookie_table: [
              // list of all expected cookies
              {
                col1: "1P_JAR",
                col2: "google.com",
                col3: "1 month",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "AEC",
                col2: "google.com",
                col3: "6 months",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "ANID",
                col2: "google.com",
                col3: "3.5 months",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "APISID",
                col2: "google.com",
                col3: "1 day",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "DV",
                col2: "google.com",
                col3: "1 day",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "HSID",
                col2: "google.com",
                col3: "1 day",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "NID",
                col2: "google.com",
                col3: "6 months",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "OGPC",
                col2: "google.com",
                col3: "4 months",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "OTZ",
                col2: "google.com",
                col3: "9 days",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "SAPISID",
                col2: "google.com",
                col3: "1 year",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "SID",
                col2: "google.com",
                col3: "2 years",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "SIDCC",
                col2: "google.com",
                col3: "1 year",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "SSID",
                col2: "google.com",
                col3: "2 years",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "_ga", // match all cookies starting with "_ga"
                col2: "google.com",
                col3: "2 years",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "^_gat",
                col2: "google.com",
                col3: "2 years",
                col4: "This is a pattern type cookie set by Google Tag Manager.",
                is_regex: true,
              },
              {
                col1: "_gid",
                col2: "google.com",
                col3: "1 day",
                col4: "This cookie is installed by Google Tag Manager.",
              },
              {
                col1: "^__Secure-",
                col2: "google.com",
                col3: "1 month",
                col4: "This is a pattern type cookie set by Google Tag Manager.",
                is_regex: true,
              },
              {
                col1: "^hj",
                col2: "hotjar.com",
                col3: "1 year",
                col4: "This is a pattern type cookie set by the hotjar feedback widget.",
                is_regex: true,
              }
            ],
          },
          {
            title: "More information",
            description:
              'For more details relative to cookies and other sensitive data, please read the <a href="https://www.yubico.com/support/terms-conditions/privacy-notice/" class="cc-link">privacy policy</a>.<br>For any queries in relation to our policy on cookies and your choices, please <a class="cc-link" href="https://support.yubico.com/">contact us</a>.',
          },
        ],
      },
    },
  },
});
